#!/usr/bin/env python3
"""Analyze frontier-lab benchmark authorship in release-page mentions.

The unit of analysis is a benchmark mention on a public model release page, as
encoded in data/models.csv. This script does not measure model capability or
all evaluations used internally by a provider.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUT_DIR = Path(__file__).resolve().parent

from scripts.analysis_utils import (
    build_resolved_mentions,
    create_analysis_parser,
    scope_models_as_of,
)
from scripts.taxonomy_utils import CanonicalResolver, exact_key


CURRENT_PROVIDERS = ["OpenAI", "Google", "Anthropic"]
PERIODS = {
    "2023-2024": ("2023-01-01", "2024-12-31"),
    "2025-2026": ("2025-01-01", "2026-12-31"),
}
PROVIDER_LAB_GROUPS = {
    "OpenAI": {"OpenAI"},
    "Google": {"Google", "DeepMind"},
    "Anthropic": {"Anthropic"},
}
FRONTIER_LABS = {"OpenAI", "Google", "DeepMind", "Anthropic", "Microsoft", "xAI"}
LAB_GROUP_ORDER = ["OpenAI", "Google/DeepMind", "Anthropic", "Microsoft", "xAI"]
AUTHOR_POSITION_ORDER = [
    "own_lab_only",
    "mixed_own_and_competitor",
    "competitor_lab_only",
    "neutral_or_non_frontier",
]
AUTHOR_POSITION_LABELS = {
    "own_lab_only": "Own lab only",
    "mixed_own_and_competitor": "Mixed own + competitor",
    "competitor_lab_only": "Competitor frontier lab only",
    "neutral_or_non_frontier": "Neutral / academic / vendor",
}
LIFECYCLE_PROVIDER_OR_OPAQUE = {"provider_created_benchmark", "private_or_opaque_eval"}

PARSER = create_analysis_parser(__doc__ or "Analyze frontier-lab benchmark authorship.")


@dataclass(frozen=True)
class Mention:
    mention_id: str
    provider: str
    model_name: str
    release_date: str
    release_year: int
    period: str
    source_url: str
    mention_index: int
    raw_mention: str
    benchmark_id: str
    benchmark_name: str
    match_source: str
    match_type: str


def stable_id(prefix: str, *parts: object) -> str:
    raw = " ".join(str(part).strip().casefold() for part in parts if str(part).strip())
    slug = "".join(char if char.isalnum() else "_" for char in raw).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return f"{prefix}_{slug or 'unknown'}"


def split_semicolon_labels(value: str) -> set[str]:
    value = exact_key(value)
    if not value or value.casefold() == "none":
        return set()
    return {exact_key(part) for part in value.split(";") if exact_key(part)}


def labs_in_text(value: str) -> set[str]:
    """Return frontier-lab tokens explicitly present in a source-author string."""
    value = re.sub(r"backed by\s+google", "", value, flags=re.IGNORECASE)
    labs: set[str] = set()
    for lab in FRONTIER_LABS:
        if re.search(rf"(?<![A-Za-z]){re.escape(lab)}(?![A-Za-z])", value, flags=re.IGNORECASE):
            labs.add(lab)
    return labs


def provider_group(provider: str) -> set[str]:
    return PROVIDER_LAB_GROUPS.get(provider, {provider})


def lab_group(label: str) -> str:
    if label in {"Google", "DeepMind"}:
        return "Google/DeepMind"
    return label


def period_for_date(release_date: pd.Timestamp) -> str:
    for label, (start, end) in PERIODS.items():
        if pd.Timestamp(start) <= release_date <= pd.Timestamp(end):
            return label
    return "outside_scope"


def author_position(provider: str, affiliation_labs: set[str]) -> str:
    own_labs = provider_group(provider)
    if not affiliation_labs:
        return "neutral_or_non_frontier"
    has_own = bool(affiliation_labs & own_labs)
    has_competitor = bool(affiliation_labs - own_labs)
    if has_own and has_competitor:
        return "mixed_own_and_competitor"
    if has_own:
        return "own_lab_only"
    return "competitor_lab_only"


def load_facets(path: Path) -> pd.DataFrame:
    facets = pd.read_csv(path).fillna("")
    lifecycle = (
        facets[facets["facet_axis"] == "benchmark_lifecycle_risk"]
        .groupby("benchmark_id")["facet_label"]
        .apply(lambda values: "|".join(sorted(set(exact_key(value) for value in values if exact_key(value)))))
        .rename("lifecycle_labels")
        .reset_index()
    )
    return lifecycle


def iter_mentions(models: pd.DataFrame, resolver: CanonicalResolver) -> Iterable[Mention]:
    resolved, unresolved = build_resolved_mentions(
        models,
        resolver,
        unresolved_policy="collect",
    )
    if not unresolved.empty:
        path = OUT_DIR / "unresolved_mentions.csv"
        unresolved.to_csv(path, index=False)
        raise SystemExit(f"Unresolved benchmark mentions: {len(unresolved)}. See {path}")

    for mention in resolved.itertuples(index=False):
        provider = mention.provider
        model_name = mention.model_name
        release_date = mention.release_date_text
        release_ts = pd.Timestamp(release_date)
        model_id = stable_id("model", provider, model_name, release_date)
        yield Mention(
            mention_id=stable_id("mention", model_id, f"{mention.mention_position:03d}"),
            provider=provider,
            model_name=model_name,
            release_date=release_date,
            release_year=int(release_ts.year),
            period=period_for_date(release_ts),
            source_url=mention.link,
            mention_index=int(mention.mention_position),
            raw_mention=mention.raw_mention,
            benchmark_id=mention.benchmark_id,
            benchmark_name=mention.benchmark_name,
            match_source=mention.match_source,
            match_type=mention.match_type,
        )


def add_provenance_columns(mentions: pd.DataFrame, benchmarks: pd.DataFrame, lifecycle: pd.DataFrame) -> pd.DataFrame:
    enriched = mentions.merge(
        benchmarks[
            [
                "benchmark_id",
                "source_author",
                "frontier_lab_author_affiliations",
                "reference_link",
                "legacy_task_mode",
                "legacy_task_domain",
                "review_status",
            ]
        ],
        on="benchmark_id",
        how="left",
        validate="many_to_one",
    ).merge(lifecycle, on="benchmark_id", how="left", validate="many_to_one")
    enriched["lifecycle_labels"] = enriched["lifecycle_labels"].fillna("")

    affiliation_sets = enriched["frontier_lab_author_affiliations"].map(split_semicolon_labels)
    source_author_sets = enriched["source_author"].map(labs_in_text)
    enriched["frontier_lab_affiliation_labs"] = affiliation_sets.map(lambda labels: "; ".join(sorted(labels)) or "none")
    enriched["source_author_frontier_labs"] = source_author_sets.map(lambda labels: "; ".join(sorted(labels)) or "none")
    enriched["author_position"] = [
        author_position(provider, labs) for provider, labs in zip(enriched["provider"], affiliation_sets, strict=True)
    ]

    for provider in CURRENT_PROVIDERS:
        own = provider_group(provider)
        source_flag = source_author_sets.map(lambda labels, own=own: bool(labels & own))
        affiliation_flag = affiliation_sets.map(lambda labels, own=own: bool(labels & own))
        enriched[f"is_{provider.lower()}_source_author"] = source_flag
        enriched[f"is_{provider.lower()}_frontier_affiliated"] = affiliation_flag
        enriched[f"is_{provider.lower()}_source_or_affiliated"] = source_flag | affiliation_flag

    enriched["is_any_frontier_affiliated"] = affiliation_sets.map(bool)
    enriched["is_provider_created_lifecycle"] = enriched["lifecycle_labels"].str.contains(
        "provider_created_benchmark", regex=False
    )
    enriched["is_private_or_opaque_lifecycle"] = enriched["lifecycle_labels"].str.contains(
        "private_or_opaque_eval", regex=False
    )
    enriched["is_provider_created_or_opaque_lifecycle"] = (
        enriched["is_provider_created_lifecycle"] | enriched["is_private_or_opaque_lifecycle"]
    )
    enriched["is_own_provider_created_or_opaque"] = (
        enriched["author_position"].isin(["own_lab_only", "mixed_own_and_competitor"])
        & enriched["is_provider_created_or_opaque_lifecycle"]
    )
    return enriched


def write_provider_period_author_shares(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    grouped = scoped.groupby(["provider", "period"], sort=False)
    for (provider, period), group in grouped:
        total = len(group)
        counts = group["author_position"].value_counts().to_dict()
        row: dict[str, object] = {"provider": provider, "period": period, "total_mentions": total}
        for category in AUTHOR_POSITION_ORDER:
            count = counts.get(category, 0)
            row[f"{category}_mentions"] = count
            row[f"{category}_share"] = count / total if total else 0.0
        rows.append(row)
    output = pd.DataFrame(rows).sort_values(["provider", "period"])
    output.to_csv(OUT_DIR / "provider_period_author_shares.csv", index=False)
    return output


def write_provider_year_author_shares(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    grouped = scoped.groupby(["provider", "release_year"], sort=False)
    for (provider, year), group in grouped:
        total = len(group)
        counts = group["author_position"].value_counts().to_dict()
        row: dict[str, object] = {"provider": provider, "release_year": int(year), "total_mentions": total}
        for category in AUTHOR_POSITION_ORDER:
            count = counts.get(category, 0)
            row[f"{category}_mentions"] = count
            row[f"{category}_share"] = count / total if total else 0.0
        rows.append(row)
    output = pd.DataFrame(rows).sort_values(["provider", "release_year"])
    output.to_csv(OUT_DIR / "provider_year_author_shares.csv", index=False)
    return output


def write_openai_adoption_comparison(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[
        enriched["provider"].isin(["Anthropic", "Google"]) & enriched["period"].isin(PERIODS)
    ].copy()
    rows: list[dict[str, object]] = []
    grouped = scoped.groupby(["provider", "period"], sort=False)
    for (provider, period), group in grouped:
        total = len(group)
        openai_aff = int(group["is_openai_frontier_affiliated"].sum())
        openai_source = int(group["is_openai_source_author"].sum())
        openai_either = int(group["is_openai_source_or_affiliated"].sum())
        rows.append(
            {
                "provider": provider,
                "period": period,
                "total_mentions": total,
                "openai_frontier_affiliated_mentions": openai_aff,
                "openai_frontier_affiliated_share": openai_aff / total if total else 0.0,
                "openai_source_author_mentions": openai_source,
                "openai_source_author_share": openai_source / total if total else 0.0,
                "openai_source_or_affiliated_mentions": openai_either,
                "openai_source_or_affiliated_share": openai_either / total if total else 0.0,
                "unique_openai_source_or_affiliated_benchmarks": "; ".join(
                    sorted(group[group["is_openai_source_or_affiliated"]]["benchmark_name"].unique())
                ),
            }
        )

    combined_rows: list[dict[str, object]] = []
    for period, group in scoped.groupby("period", sort=False):
        total = len(group)
        openai_aff = int(group["is_openai_frontier_affiliated"].sum())
        openai_source = int(group["is_openai_source_author"].sum())
        openai_either = int(group["is_openai_source_or_affiliated"].sum())
        combined_rows.append(
            {
                "provider": "Anthropic+Google",
                "period": period,
                "total_mentions": total,
                "openai_frontier_affiliated_mentions": openai_aff,
                "openai_frontier_affiliated_share": openai_aff / total if total else 0.0,
                "openai_source_author_mentions": openai_source,
                "openai_source_author_share": openai_source / total if total else 0.0,
                "openai_source_or_affiliated_mentions": openai_either,
                "openai_source_or_affiliated_share": openai_either / total if total else 0.0,
                "unique_openai_source_or_affiliated_benchmarks": "; ".join(
                    sorted(group[group["is_openai_source_or_affiliated"]]["benchmark_name"].unique())
                ),
            }
        )
    output = pd.DataFrame(rows + combined_rows).sort_values(["provider", "period"])
    output.to_csv(OUT_DIR / "openai_adoption_period_comparison.csv", index=False)
    return output


def write_lifecycle_shares(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    for (provider, period), group in scoped.groupby(["provider", "period"], sort=False):
        total = len(group)
        provider_created = int(group["is_provider_created_lifecycle"].sum())
        private_opaque = int(group["is_private_or_opaque_lifecycle"].sum())
        either = int(group["is_provider_created_or_opaque_lifecycle"].sum())
        own_either = int(group["is_own_provider_created_or_opaque"].sum())
        rows.append(
            {
                "provider": provider,
                "period": period,
                "total_mentions": total,
                "provider_created_lifecycle_mentions": provider_created,
                "provider_created_lifecycle_share": provider_created / total if total else 0.0,
                "private_or_opaque_lifecycle_mentions": private_opaque,
                "private_or_opaque_lifecycle_share": private_opaque / total if total else 0.0,
                "provider_created_or_opaque_lifecycle_mentions": either,
                "provider_created_or_opaque_lifecycle_share": either / total if total else 0.0,
                "own_provider_created_or_opaque_mentions": own_either,
                "own_provider_created_or_opaque_share": own_either / total if total else 0.0,
            }
        )
    output = pd.DataFrame(rows).sort_values(["provider", "period"])
    output.to_csv(OUT_DIR / "provider_period_lifecycle_shares.csv", index=False)
    return output


def write_provider_year_lifecycle_shares(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    for (provider, year), group in scoped.groupby(["provider", "release_year"], sort=False):
        total = len(group)
        provider_created = int(group["is_provider_created_lifecycle"].sum())
        private_opaque = int(group["is_private_or_opaque_lifecycle"].sum())
        either = int(group["is_provider_created_or_opaque_lifecycle"].sum())
        own_either = int(group["is_own_provider_created_or_opaque"].sum())
        rows.append(
            {
                "provider": provider,
                "release_year": int(year),
                "total_mentions": total,
                "provider_created_lifecycle_mentions": provider_created,
                "provider_created_lifecycle_share": provider_created / total if total else 0.0,
                "private_or_opaque_lifecycle_mentions": private_opaque,
                "private_or_opaque_lifecycle_share": private_opaque / total if total else 0.0,
                "provider_created_or_opaque_lifecycle_mentions": either,
                "provider_created_or_opaque_lifecycle_share": either / total if total else 0.0,
                "own_provider_created_or_opaque_mentions": own_either,
                "own_provider_created_or_opaque_share": own_either / total if total else 0.0,
            }
        )
    output = pd.DataFrame(rows).sort_values(["provider", "release_year"])
    output.to_csv(OUT_DIR / "provider_year_lifecycle_shares.csv", index=False)
    return output


def write_cross_lab_matrix(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    for _, row in scoped.iterrows():
        labs = split_semicolon_labels(row["frontier_lab_author_affiliations"])
        if not labs:
            rows.append(
                {
                    "provider": row["provider"],
                    "period": row["period"],
                    "target_lab_group": "Neutral/no frontier lab",
                    "mention_id": row["mention_id"],
                    "benchmark_name": row["benchmark_name"],
                }
            )
            continue
        for target in sorted({lab_group(lab) for lab in labs}):
            rows.append(
                {
                    "provider": row["provider"],
                    "period": row["period"],
                    "target_lab_group": target,
                    "mention_id": row["mention_id"],
                    "benchmark_name": row["benchmark_name"],
                }
            )

    expanded = pd.DataFrame(rows)
    matrix = (
        expanded.groupby(["provider", "period", "target_lab_group"], as_index=False)
        .agg(mentions=("mention_id", "nunique"), unique_benchmarks=("benchmark_name", "nunique"))
        .sort_values(["provider", "period", "target_lab_group"])
    )
    matrix.to_csv(OUT_DIR / "cross_lab_adoption_matrix.csv", index=False)
    return matrix


def write_benchmark_lags(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    for benchmark_id, group in scoped.groupby("benchmark_id", sort=False):
        affiliation_labs = split_semicolon_labels(group["frontier_lab_author_affiliations"].iloc[0])
        owner_providers = [
            provider for provider in CURRENT_PROVIDERS if bool(provider_group(provider) & affiliation_labs)
        ]
        if not owner_providers:
            continue

        ordered = group.sort_values(["release_date", "provider", "mention_index"])
        owner_mask = ordered["provider"].isin(owner_providers)
        competitor_mask = ~owner_mask
        first_owner = ordered[owner_mask].head(1)
        first_competitor = ordered[competitor_mask].head(1)
        first_any = ordered.head(1).iloc[0]

        row: dict[str, object] = {
            "benchmark_id": benchmark_id,
            "benchmark_name": group["benchmark_name"].iloc[0],
            "source_author": group["source_author"].iloc[0],
            "frontier_lab_author_affiliations": group["frontier_lab_author_affiliations"].iloc[0],
            "owner_providers_in_dataset": "; ".join(owner_providers),
            "first_any_provider": first_any["provider"],
            "first_any_model": first_any["model_name"],
            "first_any_date": first_any["release_date"],
            "first_owner_provider": "",
            "first_owner_model": "",
            "first_owner_date": "",
            "first_competitor_provider": "",
            "first_competitor_model": "",
            "first_competitor_date": "",
            "release_page_lag_days": "",
            "competitor_preceded_owner_release_page_mention": "",
        }
        if not first_owner.empty:
            owner = first_owner.iloc[0]
            row["first_owner_provider"] = owner["provider"]
            row["first_owner_model"] = owner["model_name"]
            row["first_owner_date"] = owner["release_date"]
        if not first_competitor.empty:
            competitor = first_competitor.iloc[0]
            row["first_competitor_provider"] = competitor["provider"]
            row["first_competitor_model"] = competitor["model_name"]
            row["first_competitor_date"] = competitor["release_date"]
        if row["first_owner_date"] and row["first_competitor_date"]:
            lag = (pd.Timestamp(row["first_competitor_date"]) - pd.Timestamp(row["first_owner_date"])).days
            row["release_page_lag_days"] = int(lag)
            row["competitor_preceded_owner_release_page_mention"] = lag < 0
        rows.append(row)

    output = pd.DataFrame(rows).sort_values(["benchmark_name"])
    output.to_csv(OUT_DIR / "benchmark_first_adoption_lags.csv", index=False)
    return output


def write_high_signal_benchmarks(enriched: pd.DataFrame) -> pd.DataFrame:
    scoped = enriched[enriched["period"].isin(PERIODS)].copy()
    rows: list[dict[str, object]] = []
    for benchmark_id, group in scoped.groupby("benchmark_id", sort=False):
        provider_counts = Counter(group["provider"])
        affiliation_labs = split_semicolon_labels(group["frontier_lab_author_affiliations"].iloc[0])
        lab_groups = sorted({lab_group(lab) for lab in affiliation_labs})
        unique_providers = sorted(provider_counts)
        is_cross_provider = len(unique_providers) >= 2
        is_frontier_affiliated = bool(affiliation_labs)
        first = group.sort_values(["release_date", "provider", "mention_index"]).iloc[0]
        rows.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": group["benchmark_name"].iloc[0],
                "mention_count": len(group),
                "provider_count": len(unique_providers),
                "providers_mentioning": "; ".join(unique_providers),
                "openai_mentions": provider_counts.get("OpenAI", 0),
                "google_mentions": provider_counts.get("Google", 0),
                "anthropic_mentions": provider_counts.get("Anthropic", 0),
                "source_author": group["source_author"].iloc[0],
                "frontier_lab_author_affiliations": group["frontier_lab_author_affiliations"].iloc[0],
                "frontier_lab_groups": "; ".join(lab_groups) or "none",
                "lifecycle_labels": group["lifecycle_labels"].iloc[0],
                "first_seen_provider": first["provider"],
                "first_seen_model": first["model_name"],
                "first_seen_date": first["release_date"],
                "high_signal_reason": high_signal_reason(
                    is_cross_provider=is_cross_provider,
                    is_frontier_affiliated=is_frontier_affiliated,
                    lab_groups=lab_groups,
                    mention_count=len(group),
                ),
            }
        )
    output = pd.DataFrame(rows).sort_values(
        ["provider_count", "mention_count", "benchmark_name"], ascending=[False, False, True]
    )
    output.to_csv(OUT_DIR / "high_signal_benchmarks.csv", index=False)
    return output


def high_signal_reason(
    *, is_cross_provider: bool, is_frontier_affiliated: bool, lab_groups: list[str], mention_count: int
) -> str:
    if is_cross_provider and is_frontier_affiliated:
        return f"frontier_lab_cross_provider:{';'.join(lab_groups)}"
    if is_cross_provider and mention_count >= 6:
        return "neutral_cross_provider_anchor"
    if is_frontier_affiliated and mention_count >= 3:
        return f"frontier_lab_repeated_within_provider:{';'.join(lab_groups)}"
    return "lower_signal"


def write_chart(author_shares: pd.DataFrame) -> None:
    if author_shares.empty:
        return

    plot = author_shares.copy()
    plot["provider_period"] = plot["provider"] + "\n" + plot["period"]
    x = range(len(plot))
    colors = {
        "own_lab_only": "#2f6f9f",
        "mixed_own_and_competitor": "#6a4c93",
        "competitor_lab_only": "#d17a22",
        "neutral_or_non_frontier": "#6f7f80",
    }
    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = [0.0] * len(plot)
    for category in AUTHOR_POSITION_ORDER:
        values = plot[f"{category}_share"].tolist()
        ax.bar(
            list(x),
            values,
            bottom=bottom,
            label=AUTHOR_POSITION_LABELS[category],
            color=colors[category],
            width=0.72,
        )
        bottom = [old + new for old, new in zip(bottom, values, strict=True)]

    ax.set_ylim(0, 1)
    ax.set_ylabel("Share of benchmark mentions")
    ax.set_title("Release-page benchmark mentions by author-position category")
    ax.set_xticks(list(x))
    ax.set_xticklabels(plot["provider_period"], rotation=0)
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
    ax.grid(axis="y", color="#d0d7de", linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "provider_period_author_mix.png", dpi=180)
    plt.close(fig)


def write_methodology_summary(
    enriched: pd.DataFrame,
    author_shares: pd.DataFrame,
    openai_comparison: pd.DataFrame,
    lifecycle_shares: pd.DataFrame,
) -> None:
    summary = {
        "total_release_page_mentions": len(enriched),
        "unique_benchmarks_mentioned": enriched["benchmark_id"].nunique(),
        "models_with_mentions": enriched[["provider", "model_name", "release_date"]].drop_duplicates().shape[0],
        "providers": "; ".join(CURRENT_PROVIDERS),
        "periods": "; ".join(PERIODS),
    }
    with (OUT_DIR / "run_summary.txt").open("w", encoding="utf-8") as f:
        for key, value in summary.items():
            f.write(f"{key}: {value}\n")
        f.write("\nprovider_period_author_shares.csv\n")
        f.write(author_shares.to_string(index=False))
        f.write("\n\nopenai_adoption_period_comparison.csv\n")
        f.write(openai_comparison.to_string(index=False))
        f.write("\n\nprovider_period_lifecycle_shares.csv\n")
        f.write(lifecycle_shares.to_string(index=False))


def main() -> None:
    args = PARSER.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    resolver = CanonicalResolver.from_files(DATA_DIR / "benchmarks.csv", DATA_DIR / "benchmark_aliases.csv")
    models = pd.read_csv(DATA_DIR / "models.csv").fillna("")
    models, _ = scope_models_as_of(models, args.as_of)
    benchmarks = pd.read_csv(DATA_DIR / "benchmarks.csv").fillna("")
    lifecycle = load_facets(DATA_DIR / "benchmark_facets.csv")

    mentions = pd.DataFrame([mention.__dict__ for mention in iter_mentions(models, resolver)])
    if mentions.empty:
        raise SystemExit("No benchmark mentions found.")

    enriched = add_provenance_columns(mentions, benchmarks, lifecycle)
    enriched.to_csv(OUT_DIR / "mentions_enriched.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    author_shares = write_provider_period_author_shares(enriched)
    write_provider_year_author_shares(enriched)
    openai_comparison = write_openai_adoption_comparison(enriched)
    lifecycle_shares = write_lifecycle_shares(enriched)
    write_provider_year_lifecycle_shares(enriched)
    write_cross_lab_matrix(enriched)
    write_benchmark_lags(enriched)
    write_high_signal_benchmarks(enriched)
    write_chart(author_shares)
    write_methodology_summary(enriched, author_shares, openai_comparison, lifecycle_shares)

    print(f"Wrote analysis outputs to {OUT_DIR.relative_to(ROOT)}")
    print(f"Resolved mentions: {len(enriched)}")
    print(f"Unique benchmarks mentioned: {enriched['benchmark_id'].nunique()}")


if __name__ == "__main__":
    main()
