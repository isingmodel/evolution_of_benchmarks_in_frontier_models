#!/usr/bin/env python3
"""Generate README-ready story analyses from local benchmark data.

The generated outputs summarize release-page benchmark mentions. They should
not be read as model capability measurements or as complete evaluation records.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns

if __package__:
    from .taxonomy_utils import CanonicalResolver, exact_key, split_benchmark_mentions
else:
    from taxonomy_utils import CanonicalResolver, exact_key, split_benchmark_mentions


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT_DIR = ROOT / "analysis" / "readme_story"
DEFAULT_ASSET_DIR = ROOT / "assets"

PROVIDER_ORDER = ["OpenAI", "Google", "Anthropic"]

WORK_INTERACTIONS = {
    "single_turn_tool_use",
    "multi_step_planning",
    "environment_interaction",
    "browser_or_web_interaction",
    "terminal_or_codebase_interaction",
    "computer_control",
    "human_in_the_loop",
}
WORK_MECHANISMS = {
    "browser_navigation",
    "terminal_operation",
    "tool_calling",
    "computer_control_task",
    "repository_issue_resolution",
    "unit_test_passing",
    "code_repair",
    "sql_generation",
    "security_challenge_solving",
}
WORK_CLAIMS = {
    "agentic_task_completion",
    "tool_use",
    "web_navigation",
    "computer_use",
    "software_engineering",
}
STATIC_MECHANISMS = {
    "multiple_choice_qa",
    "short_answer_qa",
    "math_problem_solving",
    "factuality_verification",
}
SPECIALIZED_DOMAINS = {
    "Law",
    "Bio/Medicine",
    "Finance",
    "Cybersecurity",
    "Other Specialized",
}
LONG_CONTEXT_BROAD = {"long_context_primary", "long_context_supporting"}
LONG_CONTEXT_PRIMARY = {"long_context_primary"}
FRONTIER_LABS = {"OpenAI", "Anthropic", "Google", "DeepMind", "Microsoft", "xAI"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of",
        help="Include model releases on or before this date (YYYY-MM-DD). Defaults to latest models.csv date.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated CSV outputs.",
    )
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=DEFAULT_ASSET_DIR,
        help="Directory for generated README chart assets.",
    )
    return parser.parse_args()


def configure_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]


def load_inputs(as_of: str | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, CanonicalResolver, pd.Timestamp]:
    models = pd.read_csv(DATA_DIR / "models.csv").fillna("")
    models["release_date"] = pd.to_datetime(models["release date"], errors="raise")
    cutoff = pd.to_datetime(as_of, errors="raise").normalize() if as_of else models["release_date"].max().normalize()
    models = models[models["release_date"] <= cutoff].copy()
    models["release_year"] = models["release_date"].dt.year
    models["model_key"] = (
        models["Provider"].astype(str)
        + "|"
        + models["Model name"].astype(str)
        + "|"
        + models["release date"].astype(str)
    )

    benchmarks = pd.read_csv(DATA_DIR / "benchmarks.csv").fillna("")
    facets = pd.read_csv(DATA_DIR / "benchmark_facets.csv").fillna("")
    resolver = CanonicalResolver.from_files(DATA_DIR / "benchmarks.csv", DATA_DIR / "benchmark_aliases.csv")
    return models, benchmarks, facets, resolver, cutoff


def build_mentions(models: pd.DataFrame, resolver: CanonicalResolver) -> pd.DataFrame:
    rows = []
    unresolved = []
    for _, model in models.iterrows():
        raw_mentions = split_benchmark_mentions(model.get("benchmarks", ""))
        resolved: dict[str, dict[str, object]] = {}
        for raw_mention in raw_mentions:
            resolution = resolver.resolve(raw_mention)
            if not resolution:
                unresolved.append(f"{model['Provider']} / {model['Model name']} / {raw_mention}")
                continue
            entry = resolved.setdefault(
                resolution.benchmark_id,
                {
                    "raw_mentions": [],
                    "resolution": resolution,
                },
            )
            entry["raw_mentions"].append(raw_mention)

        if unresolved:
            continue
        if not resolved:
            continue

        release_weight = 1.0 / len(resolved)
        for entry in resolved.values():
            raw_mentions_for_benchmark = entry["raw_mentions"]
            resolution = entry["resolution"]
            rows.append(
                {
                    "provider": model["Provider"],
                    "model_name": model["Model name"],
                    "link": model["link"],
                    "release_date": model["release_date"],
                    "release_year": int(model["release_year"]),
                    "model_key": model["model_key"],
                    "raw_mention": "; ".join(raw_mentions_for_benchmark),
                    "benchmark_id": resolution.benchmark_id,
                    "benchmark_name": resolution.benchmark_name,
                    "release_weight": release_weight,
                    "raw_weight": float(len(raw_mentions_for_benchmark)),
                    "resolved_benchmark_count_for_release": len(resolved),
                }
            )

    if unresolved:
        sample = "; ".join(unresolved[:10])
        raise ValueError(f"Unresolved benchmark mentions found: {sample}")

    return pd.DataFrame(rows)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def build_facet_maps(facets: pd.DataFrame) -> tuple[dict[str, dict[str, set[str]]], pd.DataFrame]:
    active = facets[
        (facets["review_status"] != "deprecated")
        & (facets["facet_axis"].astype(str).str.strip() != "")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ].copy()
    by_benchmark: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for _, row in active.iterrows():
        by_benchmark[row["benchmark_id"]][row["facet_axis"]].add(row["facet_label"])

    status_counts = (
        active.groupby(["benchmark_id", "review_status"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for column in ["accepted", "legacy_seed", "needs_review", "disputed"]:
        if column not in status_counts.columns:
            status_counts[column] = 0
    status_counts["facet_rows_total"] = status_counts[
        ["accepted", "legacy_seed", "needs_review", "disputed"]
    ].sum(axis=1)
    status_counts["nonaccepted_share"] = 1.0 - (
        status_counts["accepted"] / status_counts["facet_rows_total"].where(status_counts["facet_rows_total"] > 0, 1)
    )
    return by_benchmark, status_counts


def add_metadata_and_flags(
    mentions: pd.DataFrame,
    benchmarks: pd.DataFrame,
    facet_map: dict[str, dict[str, set[str]]],
) -> pd.DataFrame:
    enriched = mentions.merge(
        benchmarks[
            [
                "benchmark_id",
                "source_author",
                "frontier_lab_author_affiliations",
                "legacy_task_mode",
                "legacy_task_domain",
                "review_status",
            ]
        ],
        on="benchmark_id",
        how="left",
        validate="many_to_one",
    )
    rows = []
    for _, row in enriched.iterrows():
        labels = facet_map.get(row["benchmark_id"], {})
        interactions = labels.get("interaction_pattern", set())
        mechanisms = labels.get("task_mechanism", set())
        claims = labels.get("construct_claim", set())
        domains = labels.get("domain", set())
        context = labels.get("context_pressure", set())

        is_work = bool(interactions & WORK_INTERACTIONS or mechanisms & WORK_MECHANISMS or claims & WORK_CLAIMS)
        is_static = bool("static_prompt_response" in interactions and mechanisms & STATIC_MECHANISMS and not is_work)
        is_specialized = bool(domains & SPECIALIZED_DOMAINS)

        out = row.to_dict()
        out.update(
            {
                "is_static_exam": is_static,
                "is_work_simulation": is_work,
                "is_specialized_domain": is_specialized,
                "is_long_context_broad": bool(context & LONG_CONTEXT_BROAD),
                "is_long_context_primary": bool(context & LONG_CONTEXT_PRIMARY),
                "context_pressure_labels": "; ".join(sorted(context)),
                "interaction_pattern_labels": "; ".join(sorted(interactions)),
                "task_mechanism_labels": "; ".join(sorted(mechanisms)),
                "construct_claim_labels": "; ".join(sorted(claims)),
                "domain_labels": "; ".join(sorted(domains)),
            }
        )
        rows.append(out)
    return pd.DataFrame(rows)


def pct(value: float) -> str:
    return f"{value:.1%}"


def write_static_work_outputs(enriched: pd.DataFrame, output_dir: Path, asset_dir: Path, cutoff: pd.Timestamp) -> None:
    release_frame = (
        enriched.groupby(["model_key", "provider", "model_name", "release_year"])
        .agg(
            static_exam_share=("is_static_exam", lambda s: float((s * enriched.loc[s.index, "release_weight"]).sum())),
            work_simulation_share=(
                "is_work_simulation",
                lambda s: float((s * enriched.loc[s.index, "release_weight"]).sum()),
            ),
            specialized_domain_share=(
                "is_specialized_domain",
                lambda s: float((s * enriched.loc[s.index, "release_weight"]).sum()),
            ),
            resolved_benchmark_mentions=("benchmark_id", "size"),
        )
        .reset_index()
    )
    annual = (
        release_frame.groupby("release_year")
        .agg(
            static_exam_share=("static_exam_share", "mean"),
            work_simulation_share=("work_simulation_share", "mean"),
            specialized_domain_share=("specialized_domain_share", "mean"),
            benchmarked_release_pages=("model_key", "nunique"),
        )
        .reset_index()
    )
    annual["year_label"] = annual["release_year"].astype(str)
    annual.loc[annual["release_year"] == cutoff.year, "year_label"] = f"{cutoff.year} YTD"
    annual.to_csv(output_dir / "static_work_annual.csv", index=False)
    release_frame.to_csv(output_dir / "static_work_release_frames.csv", index=False)

    contributor = (
        enriched[enriched["is_work_simulation"]]
        .groupby("benchmark_name")
        .agg(
            raw_mentions=("benchmark_id", "size"),
            release_weighted_mentions=("release_weight", "sum"),
            first_seen=("release_date", "min"),
            providers=("provider", lambda s: "; ".join(sorted(set(s)))),
            interaction_patterns=("interaction_pattern_labels", "first"),
            task_mechanisms=("task_mechanism_labels", "first"),
        )
        .reset_index()
        .sort_values(["release_weighted_mentions", "raw_mentions", "benchmark_name"], ascending=[False, False, True])
    )
    contributor.to_csv(output_dir / "work_simulation_top_contributors.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 6.5))
    x = range(len(annual))
    series = [
        ("static_exam_share", "Static exam-style", "#4c78a8"),
        ("work_simulation_share", "Work simulation", "#f58518"),
        ("specialized_domain_share", "Specialized domains", "#54a24b"),
    ]
    for column, label, color in series:
        ax.plot(x, annual[column], marker="o", linewidth=2.5, label=label, color=color)
        for idx, value in enumerate(annual[column]):
            ax.annotate(pct(value), (idx, value), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    labels = [
        f"{row.year_label}\nn={int(row.benchmarked_release_pages)}"
        for row in annual.itertuples(index=False)
    ]
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(0.65, annual[["static_exam_share", "work_simulation_share"]].max().max() + 0.08))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title("Release-Page Benchmark Framing: Static Exams to Work Simulations", fontsize=15, weight="bold")
    ax.set_ylabel("Mean share of benchmark mentions per benchmarked release page")
    ax.set_xlabel("Release year")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(True, axis="y", linestyle="--", alpha=0.45)
    ax.grid(False, axis="x")
    fig.tight_layout()
    fig.savefig(asset_dir / "static_to_work_simulation_trend.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def period_for_hypothesis(date: pd.Timestamp) -> str:
    if date.year == 2024:
        return "2024"
    if date.year >= 2025:
        return "2025-2026"
    return "pre-2024"


def write_long_context_outputs(enriched: pd.DataFrame, output_dir: Path, asset_dir: Path) -> None:
    scoped = enriched.copy()
    scoped["period"] = scoped["release_date"].map(period_for_hypothesis)
    scoped = scoped[scoped["period"].isin(["2024", "2025-2026"])].copy()

    summary = (
        scoped.groupby(["provider", "period"])
        .agg(
            release_weight_total=("release_weight", "sum"),
            raw_mentions=("benchmark_id", "size"),
            broad_long_context_weight=(
                "is_long_context_broad",
                lambda s: float((s * scoped.loc[s.index, "release_weight"]).sum()),
            ),
            primary_long_context_weight=(
                "is_long_context_primary",
                lambda s: float((s * scoped.loc[s.index, "release_weight"]).sum()),
            ),
            benchmarked_releases=("model_key", "nunique"),
        )
        .reset_index()
    )
    summary["broad_long_context_share"] = summary["broad_long_context_weight"] / summary[
        "release_weight_total"
    ].where(summary["release_weight_total"] > 0, 1)
    summary["primary_long_context_share"] = summary["primary_long_context_weight"] / summary[
        "release_weight_total"
    ].where(summary["release_weight_total"] > 0, 1)
    summary.to_csv(output_dir / "long_context_provider_period.csv", index=False)

    drivers = (
        scoped[scoped["is_long_context_broad"]]
        .groupby(["provider", "period", "benchmark_name"])
        .agg(
            release_weighted_mentions=("release_weight", "sum"),
            raw_mentions=("benchmark_id", "size"),
            models=("model_name", lambda s: "; ".join(sorted(set(s)))),
            context_pressure_labels=("context_pressure_labels", "first"),
        )
        .reset_index()
        .sort_values(["period", "provider", "release_weighted_mentions"], ascending=[True, True, False])
    )
    drivers.to_csv(output_dir / "long_context_drivers.csv", index=False)

    case_rows = []
    summary_2024 = summary[summary["period"] == "2024"].copy()
    for provider in PROVIDER_ORDER:
        row = summary_2024[summary_2024["provider"] == provider]
        provider_drivers = drivers[(drivers["provider"] == provider) & (drivers["period"] == "2024")]
        main_driver = ""
        if not provider_drivers.empty:
            d = provider_drivers.iloc[0]
            main_driver = f"{d['benchmark_name']} ({d['models']})"
        if row.empty:
            case_rows.append(
                {
                    "provider": provider,
                    "broad_long_context_share": 0.0,
                    "primary_long_context_share": 0.0,
                    "main_2024_driver": main_driver,
                    "benchmarked_releases": 0,
                }
            )
        else:
            r = row.iloc[0]
            case_rows.append(
                {
                    "provider": provider,
                    "broad_long_context_share": r["broad_long_context_share"],
                    "primary_long_context_share": r["primary_long_context_share"],
                    "main_2024_driver": main_driver,
                    "benchmarked_releases": int(r["benchmarked_releases"]),
                }
            )
    case = pd.DataFrame(case_rows)
    case.to_csv(output_dir / "long_context_2024_case_table.csv", index=False)

    x = range(len(case))
    width = 0.34
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width / 2 for i in x], case["broad_long_context_share"], width, label="Broad long-context", color="#4c78a8")
    ax.bar([i + width / 2 for i in x], case["primary_long_context_share"], width, label="Primary-only", color="#f58518")
    for i, row in case.iterrows():
        ax.annotate(
            pct(row["broad_long_context_share"]),
            (i - width / 2, row["broad_long_context_share"]),
            textcoords="offset points",
            xytext=(0, 5),
            ha="center",
            fontsize=8,
        )
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{p}\nn={n}" for p, n in zip(case["provider"], case["benchmarked_releases"], strict=True)])
    ax.set_ylim(0, max(0.38, case["broad_long_context_share"].max() + 0.08))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_title("2024 Long-Context Benchmark Emphasis by Provider", fontsize=15, weight="bold")
    ax.set_ylabel("Release-normalized share of benchmark mentions")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", linestyle="--", alpha=0.45)
    ax.grid(False, axis="x")
    fig.tight_layout()
    fig.savefig(asset_dir / "gemini_long_context_case.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def split_affiliations(value: str) -> set[str]:
    value = exact_key(value)
    if not value or value.casefold() == "none":
        return set()
    return {exact_key(part) for part in value.split(";") if exact_key(part)}


def labs_in_source_author(value: str) -> set[str]:
    value = re.sub(r"backed by\s+google", "", str(value), flags=re.IGNORECASE)
    labs = set()
    for lab in FRONTIER_LABS:
        if re.search(rf"(?<![A-Za-z]){re.escape(lab)}(?![A-Za-z])", value, flags=re.IGNORECASE):
            labs.add(lab)
    return labs


def write_borrowed_authority_outputs(enriched: pd.DataFrame, output_dir: Path) -> None:
    scoped = enriched[enriched["provider"].isin(["Anthropic", "Google"])].copy()
    scoped["period"] = scoped["release_date"].map(
        lambda date: "2023-2024" if date.year in {2023, 2024} else ("2025-2026" if date.year >= 2025 else "other")
    )
    scoped = scoped[scoped["period"].isin(["2023-2024", "2025-2026"])].copy()
    scoped["openai_source_author"] = scoped["source_author"].map(lambda value: "OpenAI" in labs_in_source_author(value))
    scoped["openai_frontier_affiliated"] = scoped["frontier_lab_author_affiliations"].map(
        lambda value: "OpenAI" in split_affiliations(value)
    )
    scoped["openai_source_or_affiliated"] = scoped["openai_source_author"] | scoped["openai_frontier_affiliated"]
    scoped["openai_strict_affiliation_only"] = scoped["frontier_lab_author_affiliations"].map(
        lambda value: split_affiliations(value) == {"OpenAI"}
    )

    rows = []
    groups = {
        "Anthropic": ["Anthropic"],
        "Google": ["Google"],
        "Anthropic+Google": ["Anthropic", "Google"],
    }
    for group_label, providers in groups.items():
        for period in ["2023-2024", "2025-2026"]:
            group = scoped[(scoped["provider"].isin(providers)) & (scoped["period"] == period)]
            total_mentions = len(group)
            release_weight_total = group["release_weight"].sum()
            openai_group = group[group["openai_source_or_affiliated"]]
            strict_group = group[group["openai_strict_affiliation_only"]]
            rows.append(
                {
                    "provider_group": group_label,
                    "period": period,
                    "total_mentions": total_mentions,
                    "release_weight_total": release_weight_total,
                    "openai_source_or_affiliated_mentions": len(openai_group),
                    "openai_source_or_affiliated_share": len(openai_group) / total_mentions if total_mentions else 0.0,
                    "openai_source_or_affiliated_release_normalized_share": (
                        openai_group["release_weight"].sum() / release_weight_total if release_weight_total else 0.0
                    ),
                    "strict_openai_affiliation_mentions": len(strict_group),
                    "strict_openai_affiliation_share": len(strict_group) / total_mentions if total_mentions else 0.0,
                    "unique_openai_linked_benchmarks": "; ".join(sorted(openai_group["benchmark_name"].unique())),
                }
            )
    pd.DataFrame(rows).to_csv(output_dir / "borrowed_benchmark_authority.csv", index=False)


def write_diffusion_outputs(enriched: pd.DataFrame, output_dir: Path) -> None:
    firsts = (
        enriched.groupby(["benchmark_id", "benchmark_name", "provider"])
        .agg(first_provider_date=("release_date", "min"), source_author=("source_author", "first"))
        .reset_index()
    )
    rows = []
    for (benchmark_id, benchmark_name), group in firsts.groupby(["benchmark_id", "benchmark_name"]):
        group = group.sort_values(["first_provider_date", "provider"])
        if group["provider"].nunique() < 2:
            continue
        first_date = group["first_provider_date"].min()
        first_providers = sorted(group[group["first_provider_date"] == first_date]["provider"].tolist())
        later = group[~group["provider"].isin(first_providers)].sort_values(["first_provider_date", "provider"])
        if later.empty:
            continue
        second = later.iloc[0]
        path = " -> ".join(
            f"{row.provider} ({row.first_provider_date.date().isoformat()})"
            for row in group.itertuples(index=False)
        )
        rows.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": benchmark_name,
                "first_tracked_public_mention": first_date.date().isoformat(),
                "first_tracked_providers": "; ".join(first_providers),
                "next_provider": second["provider"],
                "next_provider_date": second["first_provider_date"].date().isoformat(),
                "days_to_next_provider": int((second["first_provider_date"] - first_date).days),
                "public_mention_path": path,
                "source_author": group["source_author"].iloc[0],
            }
        )
    cascades = pd.DataFrame(rows).sort_values(["days_to_next_provider", "benchmark_name"])
    cascades.to_csv(output_dir / "public_benchmark_diffusion_cascades.csv", index=False)
    cascades.head(8).to_csv(output_dir / "public_benchmark_diffusion_fastest.csv", index=False)


def write_review_leverage_outputs(
    enriched: pd.DataFrame,
    status_counts: pd.DataFrame,
    output_dir: Path,
    asset_dir: Path,
    cutoff: pd.Timestamp,
) -> None:
    recent_start = cutoff - pd.Timedelta(days=365)
    recent = enriched[enriched["release_date"] >= recent_start].copy()
    weighted = (
        recent.groupby(["benchmark_id", "benchmark_name"])
        .agg(
            recent_weighted_mentions=("release_weight", "sum"),
            recent_raw_mentions=("benchmark_id", "size"),
            providers=("provider", lambda s: "; ".join(sorted(set(s)))),
            last_seen=("release_date", "max"),
        )
        .reset_index()
    )
    leverage = weighted.merge(status_counts, on="benchmark_id", how="left")
    for column in ["accepted", "legacy_seed", "needs_review", "disputed", "facet_rows_total", "nonaccepted_share"]:
        leverage[column] = leverage[column].fillna(0)
    leverage["review_leverage"] = leverage["recent_weighted_mentions"] * leverage["nonaccepted_share"]
    leverage = leverage.sort_values(["review_leverage", "recent_weighted_mentions"], ascending=[False, False])
    leverage.to_csv(output_dir / "review_leverage_benchmarks.csv", index=False)
    top = leverage.head(10).copy()
    top.to_csv(output_dir / "review_leverage_top.csv", index=False)

    plot_top = top.sort_values("review_leverage")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(plot_top["benchmark_name"], plot_top["review_leverage"], color="#d95f02", alpha=0.85)
    ax.set_title("High-Leverage Facet Review Targets", fontsize=15, weight="bold")
    ax.set_xlabel("Recent mention weight x non-accepted facet share")
    ax.set_ylabel("")
    ax.grid(True, axis="x", linestyle="--", alpha=0.45)
    ax.grid(False, axis="y")
    fig.tight_layout()
    fig.savefig(asset_dir / "review_leverage_benchmarks.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_run_summary(enriched: pd.DataFrame, output_dir: Path, cutoff: pd.Timestamp) -> None:
    summary = pd.DataFrame(
        [
            {"metric": "as_of", "value": cutoff.date().isoformat()},
            {"metric": "resolved_mentions", "value": str(len(enriched))},
            {"metric": "unique_benchmarks", "value": str(enriched["benchmark_id"].nunique())},
            {"metric": "benchmarked_releases", "value": str(enriched["model_key"].nunique())},
        ]
    )
    summary.to_csv(output_dir / "story_analysis_summary.csv", index=False)


def generate_story_analyses(as_of: str | None, output_dir: Path, asset_dir: Path) -> None:
    configure_style()
    output_dir = output_dir.resolve()
    asset_dir = asset_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)
    models, benchmarks, facets, resolver, cutoff = load_inputs(as_of)
    mentions = build_mentions(models, resolver)
    facet_map, status_counts = build_facet_maps(facets)
    enriched = add_metadata_and_flags(mentions, benchmarks, facet_map)
    enriched.to_csv(output_dir / "story_mentions_enriched.csv", index=False)

    write_static_work_outputs(enriched, output_dir, asset_dir, cutoff)
    write_long_context_outputs(enriched, output_dir, asset_dir)
    write_borrowed_authority_outputs(enriched, output_dir)
    write_diffusion_outputs(enriched, output_dir)
    write_review_leverage_outputs(enriched, status_counts, output_dir, asset_dir, cutoff)
    write_run_summary(enriched, output_dir, cutoff)
    print(f"Wrote story analysis outputs to {display_path(output_dir)}")
    print(f"Wrote story charts to {display_path(asset_dir)}")


def main() -> None:
    args = parse_args()
    generate_story_analyses(args.as_of, args.output_dir, args.asset_dir)


if __name__ == "__main__":
    main()
