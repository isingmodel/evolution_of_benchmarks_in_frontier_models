#!/usr/bin/env python3
"""Prototype narrative-strategy analyses for benchmark release-page data.

The project studies which benchmarks are named on public model release pages.
This script treats each release page as a rhetorical portfolio: a page with 30
benchmarks should not automatically count as 3x a page with 10 benchmarks when
estimating strategic emphasis, so most shares use per-release normalized
mention weights. Raw mention counts are still emitted for density analyses.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA_DIR = ROOT / "data"

from scripts.analysis_utils import (
    build_resolved_mentions,
    create_analysis_parser,
    scope_models_as_of,
)
from scripts.plot_utils import load_benchmark_facets
from scripts.taxonomy_utils import CanonicalResolver, split_benchmark_mentions


OUTPUTS = {
    "mention_inventory": HERE / "mention_inventory.csv",
    "unresolved_mentions": HERE / "unresolved_mentions.csv",
    "launch_density": HERE / "launch_benchmark_density.csv",
    "provider_headline_portfolio": HERE / "provider_headline_portfolio.csv",
    "provider_signature_lift": HERE / "provider_signature_lift.csv",
    "release_strategy_frames": HERE / "release_strategy_frames.csv",
    "annual_strategy_frames": HERE / "annual_strategy_frames.csv",
    "risk_by_release": HERE / "risk_private_usage_by_release.csv",
    "risk_by_provider": HERE / "risk_private_usage_by_provider.csv",
    "provider_risk_portfolio": HERE / "provider_risk_portfolio.csv",
}

CHARTS = {
    "headline_heatmap": HERE / "provider_headline_portfolio_heatmap.png",
    "strategy_trend": HERE / "static_to_work_simulation_trend.png",
    "risk_escalation": HERE / "provider_created_or_private_escalation.png",
}

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

MULTIMODAL_MODALITIES = {
    "image",
    "video",
    "audio",
    "document_layout",
    "browser_ui",
    "desktop_ui",
    "multimodal_mixed",
}

SPECIALIZED_DOMAINS = {
    "Law",
    "Bio/Medicine",
    "Finance",
    "Cybersecurity",
    "Other Specialized",
}

PROVIDER_CREATED_OR_PRIVATE_RISKS = {
    "private_or_opaque_eval",
    "provider_created_benchmark",
}

PARSER = create_analysis_parser(__doc__ or "Analyze release-page narrative strategy.")


def configure_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]


def load_data(as_of: str | None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, CanonicalResolver]:
    models = pd.read_csv(DATA_DIR / "models.csv").fillna("")
    models, _ = scope_models_as_of(models, as_of)
    models["release_date"] = pd.to_datetime(models["release date"], errors="raise")
    models["release_year"] = models["release_date"].dt.year
    models["model_key"] = (
        models["Provider"].astype(str)
        + "|"
        + models["Model name"].astype(str)
        + "|"
        + models["release date"].astype(str)
    )

    benchmarks = pd.read_csv(DATA_DIR / "benchmarks.csv").fillna("")
    facets = load_benchmark_facets(add_headline_projection=True)
    resolver = CanonicalResolver.from_files(DATA_DIR / "benchmarks.csv", DATA_DIR / "benchmark_aliases.csv")
    return models, benchmarks, facets, resolver


def build_mentions(models: pd.DataFrame, resolver: CanonicalResolver) -> tuple[pd.DataFrame, pd.DataFrame]:
    resolved, unresolved = build_resolved_mentions(
        models,
        resolver,
        unresolved_policy="collect",
    )
    mentions = resolved[
        [
            "provider",
            "model_name",
            "link",
            "release_date",
            "release_year",
            "model_key",
            "raw_mention",
            "benchmark_id",
            "benchmark_name",
            "match_source",
            "match_type",
            "resolved_benchmark_count_for_release",
            "release_weight",
        ]
    ].rename(
        columns={
            "provider": "Provider",
            "model_name": "Model name",
            "resolved_benchmark_count_for_release": "resolved_mentions_on_release",
            "release_weight": "release_normalized_weight",
        }
    )
    unresolved_df = unresolved.rename(
        columns={"provider": "Provider", "model_name": "Model name"}
    )
    return mentions, unresolved_df


def facet_sets(facets: pd.DataFrame) -> dict[str, dict[str, set[str]]]:
    active = facets[
        (facets["review_status"] != "deprecated")
        & (facets["facet_axis"].astype(str).str.strip() != "")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ]
    by_benchmark: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for _, row in active.iterrows():
        by_benchmark[row["benchmark_id"]][row["facet_axis"]].add(row["facet_label"])
    return by_benchmark


def add_release_frame_flags(mentions: pd.DataFrame, facets: pd.DataFrame) -> pd.DataFrame:
    by_benchmark = facet_sets(facets)
    rows = []
    for _, mention in mentions.iterrows():
        labels = by_benchmark.get(mention["benchmark_id"], {})
        interactions = labels.get("interaction_pattern", set())
        mechanisms = labels.get("task_mechanism", set())
        claims = labels.get("construct_claim", set())
        modalities = labels.get("modality", set())
        domains = labels.get("domain", set())
        risk_labels = labels.get("benchmark_lifecycle_risk", set())

        is_work = bool(interactions & WORK_INTERACTIONS or mechanisms & WORK_MECHANISMS or claims & WORK_CLAIMS)
        is_static = bool("static_prompt_response" in interactions and mechanisms & STATIC_MECHANISMS and not is_work)
        is_multimodal = bool(modalities & MULTIMODAL_MODALITIES)
        is_specialized = bool(domains & SPECIALIZED_DOMAINS)
        is_provider_created_private = bool(risk_labels & PROVIDER_CREATED_OR_PRIVATE_RISKS)
        is_private_opaque = "private_or_opaque_eval" in risk_labels
        is_provider_created = "provider_created_benchmark" in risk_labels
        is_explicit_internal_named = "internal" in str(mention["benchmark_name"]).casefold()
        has_lifecycle_risk = bool(risk_labels - {"none_identified"})

        rows.append(
            {
                **mention.to_dict(),
                "is_static_exam": is_static,
                "is_work_simulation": is_work,
                "is_multimodal_or_ui": is_multimodal,
                "is_specialized_domain": is_specialized,
                "is_provider_created_or_private": is_provider_created_private,
                "is_private_or_opaque_eval": is_private_opaque,
                "is_provider_created_benchmark": is_provider_created,
                "is_explicit_internal_named": is_explicit_internal_named,
                "has_nonzero_lifecycle_risk": has_lifecycle_risk,
                "lifecycle_risk_labels": "; ".join(sorted(risk_labels)),
                "headline_task_modes": "; ".join(sorted(labels.get("headline_task_mode", set()))),
            }
        )

    return pd.DataFrame(rows)


def axis_share_table(
    mentions: pd.DataFrame,
    facets: pd.DataFrame,
    axis: str,
    group_cols: list[str],
    label_col_name: str,
) -> pd.DataFrame:
    axis_facets = facets[
        (facets["facet_axis"] == axis)
        & (facets["review_status"] != "deprecated")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ][["benchmark_id", "facet_label"]].copy()
    if axis_facets.empty or mentions.empty:
        return pd.DataFrame()

    mentions_with_id = mentions.reset_index(drop=True).reset_index(names="mention_row_id")
    joined = mentions_with_id.merge(axis_facets, on="benchmark_id", how="inner")
    label_counts = joined.groupby("mention_row_id")["facet_label"].transform("count")
    joined["axis_weight"] = joined["release_normalized_weight"] / label_counts.where(label_counts > 0, 1)
    grouped = (
        joined.groupby(group_cols + ["facet_label"], as_index=False)
        .agg(
            weighted_mentions=("axis_weight", "sum"),
            raw_mentions=("facet_label", "size"),
            releases=("model_key", "nunique"),
        )
        .rename(columns={"facet_label": label_col_name})
    )
    totals = grouped.groupby(group_cols)["weighted_mentions"].transform("sum")
    grouped["share"] = grouped["weighted_mentions"] / totals.where(totals > 0, 1)
    return grouped.sort_values(group_cols + ["share"], ascending=[True] * len(group_cols) + [False])


def launch_density(models: pd.DataFrame, mentions: pd.DataFrame, unresolved: pd.DataFrame) -> pd.DataFrame:
    resolved_counts = mentions.groupby("model_key").size().rename("resolved_benchmark_mentions")
    unresolved_counts = (
        unresolved.assign(model_key=unresolved["Provider"] + "|" + unresolved["Model name"] + "|" + unresolved["release_date"])
        .groupby("model_key")
        .size()
        .rename("unresolved_benchmark_mentions")
        if not unresolved.empty
        else pd.Series(dtype="int64", name="unresolved_benchmark_mentions")
    )
    out = models[
        ["Provider", "Model name", "link", "release_date", "release_year", "model_key", "benchmarks"]
    ].copy()
    out["raw_benchmark_mentions"] = out["benchmarks"].apply(lambda value: len(split_benchmark_mentions(value)))
    out = out.join(resolved_counts, on="model_key").join(unresolved_counts, on="model_key")
    out["resolved_benchmark_mentions"] = out["resolved_benchmark_mentions"].fillna(0).astype(int)
    out["unresolved_benchmark_mentions"] = out["unresolved_benchmark_mentions"].fillna(0).astype(int)
    out["resolution_rate"] = out["resolved_benchmark_mentions"] / out["raw_benchmark_mentions"].where(
        out["raw_benchmark_mentions"] > 0, 1
    )
    out["release_date"] = out["release_date"].dt.date.astype(str)
    return out.drop(columns=["benchmarks", "model_key"]).sort_values(["release_date", "Provider", "Model name"])


def provider_headline_portfolio(mentions: pd.DataFrame, facets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    portfolio = axis_share_table(
        mentions,
        facets,
        axis="headline_task_mode",
        group_cols=["Provider"],
        label_col_name="headline_task_mode",
    )
    if portfolio.empty:
        return portfolio, portfolio

    global_totals = (
        portfolio.groupby("headline_task_mode", as_index=False)["weighted_mentions"].sum().rename(
            columns={"weighted_mentions": "global_weighted_mentions"}
        )
    )
    global_total = global_totals["global_weighted_mentions"].sum()
    global_totals["global_share"] = global_totals["global_weighted_mentions"] / global_total
    lift = portfolio.merge(global_totals, on="headline_task_mode", how="left")
    lift["lift_vs_global"] = lift["share"] / lift["global_share"].where(lift["global_share"] > 0, pd.NA)
    lift = lift.sort_values(["Provider", "lift_vs_global", "share"], ascending=[True, False, False])
    return portfolio, lift


def release_strategy_frames(mentions_with_flags: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    flag_cols = [
        "is_static_exam",
        "is_work_simulation",
        "is_multimodal_or_ui",
        "is_specialized_domain",
    ]
    rows = []
    for (provider, model_name, release_date, release_year), group in mentions_with_flags.groupby(
        ["Provider", "Model name", "release_date", "release_year"]
    ):
        base = {
            "Provider": provider,
            "Model name": model_name,
            "release_date": release_date.date().isoformat(),
            "release_year": int(release_year),
            "resolved_benchmark_mentions": int(len(group)),
        }
        for flag in flag_cols:
            base[f"{flag}_share"] = float(group.loc[group[flag], "release_normalized_weight"].sum())
            base[f"{flag}_raw_mentions"] = int(group[flag].sum())
        rows.append(base)

    by_release = pd.DataFrame(rows).sort_values(["release_date", "Provider", "Model name"])
    value_cols = [f"{flag}_share" for flag in flag_cols]
    by_year = (
        by_release.groupby("release_year", as_index=False)[value_cols]
        .mean()
        .rename(columns={"release_year": "year"})
    )
    by_year["release_pages_with_benchmarks"] = by_release.groupby("release_year")["Model name"].count().values
    return by_release, by_year


def private_risk_tables(
    mentions_with_flags: pd.DataFrame,
    facets: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    for (provider, model_name, release_date, release_year), group in mentions_with_flags.groupby(
        ["Provider", "Model name", "release_date", "release_year"]
    ):
        provider_created_private_group = group[group["is_provider_created_or_private"]]
        private_opaque_group = group[group["is_private_or_opaque_eval"]]
        provider_created_group = group[group["is_provider_created_benchmark"]]
        internal_named_group = group[group["is_explicit_internal_named"]]
        risk_group = group[group["has_nonzero_lifecycle_risk"]]
        rows.append(
            {
                "Provider": provider,
                "Model name": model_name,
                "release_date": release_date.date().isoformat(),
                "release_year": int(release_year),
                "resolved_benchmark_mentions": int(len(group)),
                "provider_created_or_private_share": float(
                    provider_created_private_group["release_normalized_weight"].sum()
                ),
                "provider_created_or_private_raw_mentions": int(len(provider_created_private_group)),
                "private_or_opaque_share": float(private_opaque_group["release_normalized_weight"].sum()),
                "private_or_opaque_raw_mentions": int(len(private_opaque_group)),
                "provider_created_benchmark_share": float(
                    provider_created_group["release_normalized_weight"].sum()
                ),
                "provider_created_benchmark_raw_mentions": int(len(provider_created_group)),
                "explicit_internal_named_share": float(internal_named_group["release_normalized_weight"].sum()),
                "explicit_internal_named_raw_mentions": int(len(internal_named_group)),
                "nonzero_lifecycle_risk_share": float(risk_group["release_normalized_weight"].sum()),
                "nonzero_lifecycle_risk_raw_mentions": int(len(risk_group)),
                "provider_created_or_private_benchmarks": "; ".join(
                    sorted(provider_created_private_group["benchmark_name"].unique())
                ),
                "explicit_internal_named_benchmarks": "; ".join(sorted(internal_named_group["benchmark_name"].unique())),
            }
        )

    by_release = pd.DataFrame(rows).sort_values(["release_date", "Provider", "Model name"])
    by_provider = (
        mentions_with_flags.assign(
            provider_created_or_private_weight=lambda df: df["release_normalized_weight"]
            * df["is_provider_created_or_private"].astype(float),
            private_or_opaque_weight=lambda df: df["release_normalized_weight"]
            * df["is_private_or_opaque_eval"].astype(float),
            provider_created_benchmark_weight=lambda df: df["release_normalized_weight"]
            * df["is_provider_created_benchmark"].astype(float),
            explicit_internal_named_weight=lambda df: df["release_normalized_weight"]
            * df["is_explicit_internal_named"].astype(float),
            nonzero_lifecycle_risk_weight=lambda df: df["release_normalized_weight"]
            * df["has_nonzero_lifecycle_risk"].astype(float),
        )
        .groupby("Provider", as_index=False)
        .agg(
            release_pages_with_benchmarks=("model_key", "nunique"),
            weighted_mentions=("release_normalized_weight", "sum"),
            provider_created_or_private_weighted_mentions=("provider_created_or_private_weight", "sum"),
            provider_created_or_private_raw_mentions=("is_provider_created_or_private", "sum"),
            private_or_opaque_weighted_mentions=("private_or_opaque_weight", "sum"),
            private_or_opaque_raw_mentions=("is_private_or_opaque_eval", "sum"),
            provider_created_benchmark_weighted_mentions=("provider_created_benchmark_weight", "sum"),
            provider_created_benchmark_raw_mentions=("is_provider_created_benchmark", "sum"),
            explicit_internal_named_weighted_mentions=("explicit_internal_named_weight", "sum"),
            explicit_internal_named_raw_mentions=("is_explicit_internal_named", "sum"),
            nonzero_lifecycle_risk_weighted_mentions=("nonzero_lifecycle_risk_weight", "sum"),
            nonzero_lifecycle_risk_raw_mentions=("has_nonzero_lifecycle_risk", "sum"),
        )
    )
    by_provider["provider_created_or_private_share"] = (
        by_provider["provider_created_or_private_weighted_mentions"] / by_provider["weighted_mentions"]
    )
    by_provider["private_or_opaque_share"] = (
        by_provider["private_or_opaque_weighted_mentions"] / by_provider["weighted_mentions"]
    )
    by_provider["provider_created_benchmark_share"] = (
        by_provider["provider_created_benchmark_weighted_mentions"] / by_provider["weighted_mentions"]
    )
    by_provider["explicit_internal_named_share"] = (
        by_provider["explicit_internal_named_weighted_mentions"] / by_provider["weighted_mentions"]
    )
    by_provider["nonzero_lifecycle_risk_share"] = (
        by_provider["nonzero_lifecycle_risk_weighted_mentions"] / by_provider["weighted_mentions"]
    )

    risk_portfolio = axis_share_table(
        mentions_with_flags,
        facets,
        axis="benchmark_lifecycle_risk",
        group_cols=["Provider"],
        label_col_name="lifecycle_risk",
    )
    return by_release, by_provider.sort_values("provider_created_or_private_share", ascending=False), risk_portfolio


def write_csv(df: pd.DataFrame, path: Path) -> None:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.date.astype(str)
    out.to_csv(path, index=False)


def plot_headline_heatmap(portfolio: pd.DataFrame) -> None:
    if portfolio.empty:
        return
    pivot = portfolio.pivot(index="Provider", columns="headline_task_mode", values="share").fillna(0)
    desired_order = [
        "Generative Reasoning",
        "Knowledge Retrieval",
        "Multimodal Perception",
        "Agentic",
        "Constraint Satisfaction",
    ]
    pivot = pivot[[col for col in desired_order if col in pivot.columns]]
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".0%",
        cmap=sns.color_palette("crest", as_cmap=True),
        linewidths=0.6,
        linecolor="white",
        cbar_kws={"label": "Share of release-normalized benchmark mentions"},
        ax=ax,
    )
    ax.set_title("Provider Benchmark Portfolio by Headline Task Mode", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(CHARTS["headline_heatmap"], dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_strategy_trend(annual: pd.DataFrame) -> None:
    if annual.empty:
        return
    plot_df = annual.rename(
        columns={
            "is_static_exam_share": "Static exams",
            "is_work_simulation_share": "Work simulations",
            "is_multimodal_or_ui_share": "Multimodal/UI evals",
            "is_specialized_domain_share": "Specialized domains",
        }
    ).melt(
        id_vars=["year"],
        value_vars=["Static exams", "Work simulations", "Multimodal/UI evals", "Specialized domains"],
        var_name="frame",
        value_name="mean_release_share",
    )
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    palette = {
        "Static exams": "#4C78A8",
        "Work simulations": "#F58518",
        "Multimodal/UI evals": "#54A24B",
        "Specialized domains": "#B279A2",
    }
    sns.lineplot(
        data=plot_df,
        x="year",
        y="mean_release_share",
        hue="frame",
        marker="o",
        linewidth=2.4,
        palette=palette,
        ax=ax,
    )
    ax.set_title("Benchmark Framing Drift on Release Pages", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Mean share of each benchmarked release page")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_ylim(0, max(0.7, min(1.0, plot_df["mean_release_share"].max() + 0.12)))
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(CHARTS["strategy_trend"], dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_risk_escalation(by_release: pd.DataFrame) -> None:
    if by_release.empty:
        return
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    plot_df = by_release.copy()
    plot_df["release_date"] = pd.to_datetime(plot_df["release_date"])
    sns.lineplot(
        data=plot_df,
        x="release_date",
        y="provider_created_or_private_share",
        hue="Provider",
        marker="o",
        linewidth=2.2,
        ax=ax,
    )
    ax.set_title("Provider-Created or Private/Opaque Benchmark Share by Release Page", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Share of release-normalized benchmark mentions")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.set_ylim(0, max(0.45, min(1.0, plot_df["provider_created_or_private_share"].max() + 0.12)))
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(CHARTS["risk_escalation"], dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = PARSER.parse_args()
    configure_style()
    HERE.mkdir(parents=True, exist_ok=True)

    models, benchmarks, facets, resolver = load_data(args.as_of)
    mentions, unresolved = build_mentions(models, resolver)
    mentions = mentions.merge(
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
    )
    mentions_with_flags = add_release_frame_flags(mentions, facets)

    density = launch_density(models, mentions, unresolved)
    portfolio, lift = provider_headline_portfolio(mentions, facets)
    by_release, by_year = release_strategy_frames(mentions_with_flags)
    risk_release, risk_provider, risk_portfolio = private_risk_tables(mentions_with_flags, facets)

    write_csv(mentions_with_flags, OUTPUTS["mention_inventory"])
    write_csv(unresolved, OUTPUTS["unresolved_mentions"])
    write_csv(density, OUTPUTS["launch_density"])
    write_csv(portfolio, OUTPUTS["provider_headline_portfolio"])
    write_csv(lift, OUTPUTS["provider_signature_lift"])
    write_csv(by_release, OUTPUTS["release_strategy_frames"])
    write_csv(by_year, OUTPUTS["annual_strategy_frames"])
    write_csv(risk_release, OUTPUTS["risk_by_release"])
    write_csv(risk_provider, OUTPUTS["risk_by_provider"])
    write_csv(risk_portfolio, OUTPUTS["provider_risk_portfolio"])

    plot_headline_heatmap(portfolio)
    plot_strategy_trend(by_year)
    plot_risk_escalation(risk_release)

    print(f"Wrote {len(OUTPUTS)} CSV files and {len(CHARTS)} charts under {HERE.relative_to(ROOT)}")
    if not unresolved.empty:
        print(f"Unresolved mentions skipped: {len(unresolved)}")


if __name__ == "__main__":
    main()
