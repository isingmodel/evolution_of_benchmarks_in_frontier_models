#!/usr/bin/env python3
"""Provider-period benchmark showcase analysis.

This script studies benchmark mentions on public release pages. It does not
interpret the benchmark list as model capability. Each benchmark-bearing
release gets one unit of showcase weight, divided evenly across the benchmarks
listed on that release page, so providers with longer benchmark tables do not
automatically dominate the shares.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SCRIPT_DIR = ROOT / "scripts"
OUTPUT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(SCRIPT_DIR))

from taxonomy_utils import CanonicalResolver, split_benchmark_mentions  # noqa: E402


PROVIDER_ORDER = ["OpenAI", "Google", "Anthropic"]
PERIOD_ORDER = ["2022-2023", "2024", "2025", "2026 YTD"]
HYPOTHESIS_PERIOD_ORDER = ["2024", "2025-2026"]
AXES = [
    "context_pressure",
    "headline_task_mode",
    "domain",
    "modality",
    "interaction_pattern",
]

LONG_CONTEXT_LABELS = {"long_context_primary", "long_context_supporting"}
LONG_CONTEXT_PRIMARY_LABELS = {"long_context_primary"}

AGENTIC_HEADLINE_LABELS = {"Agentic"}
AGENTIC_CONSTRUCT_LABELS = {
    "agentic_task_completion",
    "tool_use",
    "web_navigation",
    "computer_use",
}
AGENTIC_INTERACTION_LABELS = {
    "single_turn_tool_use",
    "multi_step_planning",
    "environment_interaction",
    "browser_or_web_interaction",
    "terminal_or_codebase_interaction",
    "computer_control",
    "human_in_the_loop",
}

MULTIMODAL_MODALITY_LABELS = {
    "image",
    "video",
    "audio",
    "document_layout",
    "multimodal_mixed",
    "browser_ui",
    "desktop_ui",
}

CODING_DOMAIN_LABELS = {"Coding/Engineering", "Cybersecurity"}
CODING_MODALITY_LABELS = {"code"}
CODING_CONSTRUCT_LABELS = {"coding", "software_engineering"}
CODING_MECHANISM_LABELS = {
    "code_generation",
    "code_repair",
    "repository_issue_resolution",
    "unit_test_passing",
    "terminal_operation",
    "security_challenge_solving",
}
MENTION_COLUMNS = [
    "mention_id",
    "model_row_id",
    "provider",
    "model_name",
    "release_date",
    "release_date_text",
    "period",
    "hypothesis_period",
    "raw_mention",
    "benchmark_id",
    "benchmark_name",
    "match_source",
    "match_type",
    "raw_weight",
    "release_weight",
    "resolved_benchmark_count_for_release",
]
UNRESOLVED_COLUMNS = ["provider", "model_name", "release_date", "raw_mention"]
MENTION_LABEL_COLUMNS = [
    "context_pressure_labels",
    "headline_task_mode_labels",
    "domain_labels",
    "modality_labels",
    "interaction_pattern_labels",
]
MENTION_FLAG_COLUMNS = [
    "is_long_context_primary",
    "is_long_context_broad",
    "is_agentic",
    "is_multimodal",
    "is_coding",
    "is_coding_or_agentic",
    "is_coding_and_agentic",
]
BENCHMARK_DRIVER_COLUMNS = [
    "provider",
    "period",
    "benchmark_id",
    "benchmark_name",
    "raw_mention_count",
    "weighted_mentions",
    "models",
    "first_release_date",
    "last_release_date",
    *MENTION_FLAG_COLUMNS,
    "period_weight_denominator",
    "share_of_provider_period",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare provider benchmark showcase strategies over time."
    )
    parser.add_argument(
        "--as-of",
        help=(
            "Include model releases on or before this date (YYYY-MM-DD). "
            "Defaults to latest release date in data/models.csv."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory for generated CSV and PNG outputs.",
    )
    parser.add_argument(
        "--allow-unresolved",
        action="store_true",
        help="Skip unresolved benchmark mentions instead of failing.",
    )
    return parser.parse_args()


def non_overlapping_period(date: pd.Timestamp) -> str:
    year = int(date.year)
    if year <= 2023:
        return "2022-2023"
    if year == 2024:
        return "2024"
    if year == 2025:
        return "2025"
    return "2026 YTD"


def hypothesis_period(date: pd.Timestamp) -> str:
    year = int(date.year)
    if year == 2024:
        return "2024"
    if year >= 2025:
        return "2025-2026"
    return "pre-2024"


def order_frame(
    df: pd.DataFrame,
    period_column: str,
    period_order: list[str],
) -> pd.DataFrame:
    output = df.copy()
    provider_rank = {provider: idx for idx, provider in enumerate(PROVIDER_ORDER)}
    period_rank = {period: idx for idx, period in enumerate(period_order)}
    output["_period_rank"] = output[period_column].map(period_rank).fillna(999)
    output["_provider_rank"] = output["provider"].map(provider_rank).fillna(999)
    output = output.sort_values(["_period_rank", "_provider_rank", "provider"])
    return output.drop(columns=["_period_rank", "_provider_rank"])


def load_inputs(as_of: str | None) -> tuple[pd.DataFrame, pd.DataFrame, CanonicalResolver, pd.Timestamp]:
    models = pd.read_csv(DATA_DIR / "models.csv").fillna("")
    models["release_date"] = pd.to_datetime(models["release date"], errors="raise")
    cutoff = (
        pd.to_datetime(as_of, errors="raise").normalize()
        if as_of
        else models["release_date"].max().normalize()
    )
    models = models[models["release_date"] <= cutoff].copy()
    models["period"] = models["release_date"].map(non_overlapping_period)
    models["hypothesis_period"] = models["release_date"].map(hypothesis_period)
    models["raw_benchmark_count"] = models["benchmarks"].map(
        lambda value: len(split_benchmark_mentions(value))
    )
    models["has_benchmarks"] = models["raw_benchmark_count"] > 0

    facets = pd.read_csv(DATA_DIR / "benchmark_facets.csv").fillna("")
    resolver = CanonicalResolver.from_files(
        DATA_DIR / "benchmarks.csv",
        DATA_DIR / "benchmark_aliases.csv",
    )
    return models, facets, resolver, cutoff


def build_mentions(
    models: pd.DataFrame,
    resolver: CanonicalResolver,
    allow_unresolved: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    unresolved_rows = []
    mention_id = 0

    for model_row_id, model in models.reset_index(drop=True).iterrows():
        raw_mentions = split_benchmark_mentions(model["benchmarks"])
        if not raw_mentions:
            continue

        resolved_for_release = []
        for raw_mention in raw_mentions:
            resolution = resolver.resolve(raw_mention)
            if resolution is None:
                unresolved_rows.append(
                    {
                        "provider": model["Provider"],
                        "model_name": model["Model name"],
                        "release_date": model["release date"],
                        "raw_mention": raw_mention,
                    }
                )
                continue
            resolved_for_release.append((raw_mention, resolution))

        if unresolved_rows and not allow_unresolved:
            continue

        release_count = len(resolved_for_release)
        if release_count == 0:
            continue

        for raw_mention, resolution in resolved_for_release:
            rows.append(
                {
                    "mention_id": mention_id,
                    "model_row_id": model_row_id,
                    "provider": model["Provider"],
                    "model_name": model["Model name"],
                    "release_date": model["release_date"],
                    "release_date_text": model["release date"],
                    "period": model["period"],
                    "hypothesis_period": model["hypothesis_period"],
                    "raw_mention": raw_mention,
                    "benchmark_id": resolution.benchmark_id,
                    "benchmark_name": resolution.benchmark_name,
                    "match_source": resolution.match_source,
                    "match_type": resolution.match_type,
                    "raw_weight": 1.0,
                    "release_weight": 1.0 / release_count,
                    "resolved_benchmark_count_for_release": release_count,
                }
            )
            mention_id += 1

    unresolved = pd.DataFrame(unresolved_rows, columns=UNRESOLVED_COLUMNS)
    if not unresolved.empty and not allow_unresolved:
        sample = unresolved.head(20).to_dict("records")
        raise ValueError(
            "Unresolved benchmark mentions found. Add explicit aliases or "
            f"canonical rows before trusting this analysis. Sample: {sample}"
        )

    mentions = pd.DataFrame(rows, columns=MENTION_COLUMNS)
    return mentions, unresolved


def facet_lookup(facets: pd.DataFrame) -> dict[str, dict[str, set[str]]]:
    active = facets[
        (facets["review_status"] != "deprecated")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ].copy()
    lookup: dict[str, dict[str, set[str]]] = {}
    for axis, axis_rows in active.groupby("facet_axis"):
        lookup[axis] = (
            axis_rows.groupby("benchmark_id")["facet_label"]
            .apply(lambda values: set(map(str, values)))
            .to_dict()
        )
    return lookup


def labels_for(
    labels_by_axis: dict[str, dict[str, set[str]]],
    benchmark_id: str,
    axis: str,
) -> set[str]:
    return labels_by_axis.get(axis, {}).get(benchmark_id, set())


def add_flags(mentions: pd.DataFrame, labels_by_axis: dict[str, dict[str, set[str]]]) -> pd.DataFrame:
    output = mentions.copy()
    if mentions.empty:
        for column in MENTION_LABEL_COLUMNS:
            output[column] = ""
        for column in MENTION_FLAG_COLUMNS:
            output[column] = False
        return output

    output["context_pressure_labels"] = output["benchmark_id"].map(
        lambda bid: ";".join(sorted(labels_for(labels_by_axis, bid, "context_pressure")))
    )
    output["headline_task_mode_labels"] = output["benchmark_id"].map(
        lambda bid: ";".join(sorted(labels_for(labels_by_axis, bid, "headline_task_mode")))
    )
    output["domain_labels"] = output["benchmark_id"].map(
        lambda bid: ";".join(sorted(labels_for(labels_by_axis, bid, "domain")))
    )
    output["modality_labels"] = output["benchmark_id"].map(
        lambda bid: ";".join(sorted(labels_for(labels_by_axis, bid, "modality")))
    )
    output["interaction_pattern_labels"] = output["benchmark_id"].map(
        lambda bid: ";".join(sorted(labels_for(labels_by_axis, bid, "interaction_pattern")))
    )

    output["is_long_context_primary"] = output["benchmark_id"].map(
        lambda bid: bool(
            labels_for(labels_by_axis, bid, "context_pressure")
            & LONG_CONTEXT_PRIMARY_LABELS
        )
    )
    output["is_long_context_broad"] = output["benchmark_id"].map(
        lambda bid: bool(labels_for(labels_by_axis, bid, "context_pressure") & LONG_CONTEXT_LABELS)
    )
    output["is_agentic"] = output["benchmark_id"].map(
        lambda bid: bool(
            (labels_for(labels_by_axis, bid, "headline_task_mode") & AGENTIC_HEADLINE_LABELS)
            or (labels_for(labels_by_axis, bid, "construct_claim") & AGENTIC_CONSTRUCT_LABELS)
            or (labels_for(labels_by_axis, bid, "interaction_pattern") & AGENTIC_INTERACTION_LABELS)
        )
    )
    output["is_multimodal"] = output["benchmark_id"].map(
        lambda bid: bool(labels_for(labels_by_axis, bid, "modality") & MULTIMODAL_MODALITY_LABELS)
    )
    output["is_coding"] = output["benchmark_id"].map(
        lambda bid: bool(
            (labels_for(labels_by_axis, bid, "domain") & CODING_DOMAIN_LABELS)
            or (labels_for(labels_by_axis, bid, "modality") & CODING_MODALITY_LABELS)
            or (labels_for(labels_by_axis, bid, "construct_claim") & CODING_CONSTRUCT_LABELS)
            or (labels_for(labels_by_axis, bid, "task_mechanism") & CODING_MECHANISM_LABELS)
        )
    )
    output["is_coding_or_agentic"] = output["is_coding"] | output["is_agentic"]
    output["is_coding_and_agentic"] = output["is_coding"] & output["is_agentic"]
    return output


def weighted_share(group: pd.DataFrame, flag_column: str) -> float:
    denominator = group["release_weight"].sum()
    if denominator <= 0:
        return 0.0
    return float(group.loc[group[flag_column], "release_weight"].sum() / denominator)


def raw_share(group: pd.DataFrame, flag_column: str) -> float:
    denominator = len(group)
    if denominator <= 0:
        return 0.0
    return float(group[flag_column].sum() / denominator)


def summarize_provider_period(
    models: pd.DataFrame,
    mentions: pd.DataFrame,
    period_column: str,
    period_order: list[str],
) -> pd.DataFrame:
    model_summary = (
        models.groupby(["Provider", period_column], dropna=False)
        .agg(
            release_count=("Model name", "count"),
            benchmarked_release_count=("has_benchmarks", "sum"),
            models=("Model name", lambda values: " | ".join(map(str, values))),
        )
        .reset_index()
        .rename(columns={"Provider": "provider", period_column: "period"})
    )

    rows = []
    for (provider, period), group in mentions.groupby(["provider", period_column], dropna=False):
        denominator = group["release_weight"].sum()
        rows.append(
            {
                "provider": provider,
                "period": period,
                "raw_mention_count": len(group),
                "normalized_release_mentions": denominator,
                "unique_benchmark_count": group["benchmark_id"].nunique(),
                "avg_benchmarks_per_benchmarked_release": (
                    len(group) / group["model_name"].nunique()
                    if group["model_name"].nunique()
                    else 0.0
                ),
                "long_context_primary_share": weighted_share(group, "is_long_context_primary"),
                "long_context_broad_share": weighted_share(group, "is_long_context_broad"),
                "long_context_broad_raw_share": raw_share(group, "is_long_context_broad"),
                "agentic_share": weighted_share(group, "is_agentic"),
                "multimodal_share": weighted_share(group, "is_multimodal"),
                "coding_share": weighted_share(group, "is_coding"),
                "coding_or_agentic_share": weighted_share(group, "is_coding_or_agentic"),
                "coding_and_agentic_share": weighted_share(group, "is_coding_and_agentic"),
            }
        )

    mention_summary = pd.DataFrame(rows)
    if mention_summary.empty:
        mention_summary = pd.DataFrame(columns=["provider", "period"])

    summary = model_summary.merge(mention_summary, on=["provider", "period"], how="left")
    numeric_columns = [
        column
        for column in summary.columns
        if column
        not in {
            "provider",
            "period",
            "models",
        }
    ]
    summary[numeric_columns] = summary[numeric_columns].fillna(0)
    summary["share_metric_basis"] = "release-normalized benchmark mentions"
    return order_frame(summary, "period", period_order)


def axis_share_table(
    mentions: pd.DataFrame,
    facets: pd.DataFrame,
    period_column: str,
    period_order: list[str],
) -> pd.DataFrame:
    active_facets = facets[
        (facets["review_status"] != "deprecated")
        & (facets["facet_axis"].isin(AXES))
        & (facets["facet_label"].astype(str).str.strip() != "")
    ][["benchmark_id", "facet_axis", "facet_label", "review_status"]].copy()

    joined = mentions[
        ["mention_id", "provider", period_column, "benchmark_id", "release_weight"]
    ].merge(active_facets, on="benchmark_id", how="inner")
    if joined.empty:
        return pd.DataFrame()

    label_counts = joined.groupby(["mention_id", "facet_axis"])["facet_label"].transform("count")
    joined["axis_weight"] = joined["release_weight"] / label_counts.where(label_counts > 0, 1)

    denominator = (
        mentions.groupby(["provider", period_column])["release_weight"]
        .sum()
        .reset_index()
        .rename(columns={"release_weight": "period_weight_denominator", period_column: "period"})
    )

    output = (
        joined.groupby(["provider", period_column, "facet_axis", "facet_label"], dropna=False)
        .agg(
            weighted_mentions=("axis_weight", "sum"),
            raw_mention_count=("mention_id", "nunique"),
        )
        .reset_index()
        .rename(columns={period_column: "period"})
        .merge(denominator, on=["provider", "period"], how="left")
    )
    output["share"] = output["weighted_mentions"] / output["period_weight_denominator"]
    output = output.sort_values(
        ["period", "provider", "facet_axis", "share", "facet_label"],
        ascending=[True, True, True, False, True],
    )
    return order_frame(output, "period", period_order)


def benchmark_driver_table(
    mentions: pd.DataFrame,
    period_column: str,
    period_order: list[str],
) -> pd.DataFrame:
    if mentions.empty:
        return pd.DataFrame(columns=BENCHMARK_DRIVER_COLUMNS)

    denominator = (
        mentions.groupby(["provider", period_column])["release_weight"]
        .sum()
        .reset_index()
        .rename(columns={period_column: "period", "release_weight": "period_weight_denominator"})
    )

    bool_columns = [
        "is_long_context_primary",
        "is_long_context_broad",
        "is_agentic",
        "is_multimodal",
        "is_coding",
        "is_coding_or_agentic",
        "is_coding_and_agentic",
    ]
    grouped = (
        mentions.groupby(
            [
                "provider",
                period_column,
                "benchmark_id",
                "benchmark_name",
            ],
            dropna=False,
        )
        .agg(
            raw_mention_count=("mention_id", "count"),
            weighted_mentions=("release_weight", "sum"),
            models=("model_name", lambda values: " | ".join(sorted(set(map(str, values))))),
            first_release_date=("release_date_text", "min"),
            last_release_date=("release_date_text", "max"),
            **{column: (column, "max") for column in bool_columns},
        )
        .reset_index()
        .rename(columns={period_column: "period"})
        .merge(denominator, on=["provider", "period"], how="left")
    )
    grouped["share_of_provider_period"] = (
        grouped["weighted_mentions"] / grouped["period_weight_denominator"]
    )
    grouped = grouped.sort_values(
        ["period", "provider", "weighted_mentions", "benchmark_name"],
        ascending=[True, True, False, True],
    )
    return order_frame(grouped, "period", period_order)


def review_status_summary(facets: pd.DataFrame) -> pd.DataFrame:
    output = (
        facets.groupby(["facet_axis", "review_status"])
        .size()
        .reset_index(name="facet_row_count")
        .sort_values(["facet_axis", "review_status"])
    )
    totals = output.groupby("facet_axis")["facet_row_count"].transform("sum")
    output["share_of_axis_rows"] = output["facet_row_count"] / totals
    return output


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Wrote {path.relative_to(ROOT)}")


def write_placeholder_chart(output_path: Path, title: str, message: str, figsize: tuple[float, float]) -> None:
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ax.set_title(title, weight="bold")
    ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path.relative_to(ROOT)}")


def plot_long_context(summary: pd.DataFrame, output_path: Path) -> None:
    required_columns = {"provider", "period", "long_context_broad_share"}
    if summary.empty or not required_columns.issubset(summary.columns):
        write_placeholder_chart(
            output_path,
            "Long-Context Benchmark Emphasis by Provider",
            "No 2024-2026 long-context data is available for this cutoff.",
            (8.5, 4.8),
        )
        return

    plot_df = summary[summary["period"].isin(HYPOTHESIS_PERIOD_ORDER)].copy()
    if plot_df.empty:
        write_placeholder_chart(
            output_path,
            "Long-Context Benchmark Emphasis by Provider",
            "No 2024-2026 long-context data is available for this cutoff.",
            (8.5, 4.8),
        )
        return

    plot_df["long_context_broad_share"] = pd.to_numeric(
        plot_df["long_context_broad_share"],
        errors="coerce",
    ).fillna(0.0)
    plot_df["provider"] = pd.Categorical(plot_df["provider"], PROVIDER_ORDER, ordered=True)
    plot_df["period"] = pd.Categorical(
        plot_df["period"], HYPOTHESIS_PERIOD_ORDER, ordered=True
    )
    plot_df = plot_df.sort_values(["period", "provider"])

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    sns.barplot(
        data=plot_df,
        x="period",
        y="long_context_broad_share",
        hue="provider",
        hue_order=PROVIDER_ORDER,
        palette=["#4C78A8", "#F58518", "#54A24B"],
        ax=ax,
    )
    ax.set_title("Long-Context Benchmark Emphasis by Provider", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Share of release-normalized benchmark mentions")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, max(0.38, plot_df["long_context_broad_share"].max() * 1.22))
    ax.legend(title="", loc="upper right", frameon=True)

    for container in ax.containers:
        labels = [f"{bar.get_height():.0%}" if bar.get_height() > 0 else "0%" for bar in container]
        ax.bar_label(container, labels=labels, padding=3, fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path.relative_to(ROOT)}")


def plot_strategy_heatmap(summary: pd.DataFrame, output_path: Path) -> None:
    metrics = [
        "long_context_broad_share",
        "agentic_share",
        "coding_share",
        "multimodal_share",
    ]
    label_map = {
        "long_context_broad_share": "Long context",
        "agentic_share": "Agentic",
        "coding_share": "Coding",
        "multimodal_share": "Multimodal",
    }
    required_columns = {"provider", "period", *metrics}
    if summary.empty or not required_columns.issubset(summary.columns):
        write_strategy_heatmap_placeholder(output_path)
        return

    plot_df = summary[summary["period"].isin(["2024", "2025", "2026 YTD"])].copy()
    if plot_df.empty:
        write_strategy_heatmap_placeholder(output_path)
        return

    plot_df["column"] = plot_df["provider"] + " " + plot_df["period"]
    matrix = plot_df.set_index("column")[metrics].T
    matrix.index = [label_map[metric] for metric in metrics]

    column_order = [
        f"{provider} {period}"
        for period in ["2024", "2025", "2026 YTD"]
        for provider in PROVIDER_ORDER
        if f"{provider} {period}" in matrix.columns
    ]
    if not column_order:
        write_strategy_heatmap_placeholder(output_path)
        return

    matrix = matrix[column_order]
    matrix = matrix.fillna(0.0)

    fig_width = max(9.5, len(column_order) * 0.9)
    fig, ax = plt.subplots(figsize=(fig_width, 3.8))
    sns.heatmap(
        matrix,
        annot=matrix.map(lambda value: f"{value:.0%}"),
        fmt="",
        cmap="YlGnBu",
        vmin=0,
        vmax=max(0.65, float(matrix.max().max())),
        linewidths=0.5,
        cbar_kws={"format": mtick.PercentFormatter(1.0)},
        ax=ax,
    )
    ax.set_title("Provider Showcase Strategy Signals", weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=35)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path.relative_to(ROOT)}")


def write_strategy_heatmap_placeholder(output_path: Path) -> None:
    write_placeholder_chart(
        output_path,
        "Provider Showcase Strategy Signals",
        "No 2024-2026 provider strategy data is available for this cutoff.",
        (9.5, 3.8),
    )


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    models, facets, resolver, cutoff = load_inputs(args.as_of)
    mentions, unresolved = build_mentions(
        models,
        resolver,
        allow_unresolved=args.allow_unresolved,
    )
    labels_by_axis = facet_lookup(facets)
    mentions = add_flags(mentions, labels_by_axis)

    provider_period_summary = summarize_provider_period(
        models,
        mentions,
        "period",
        PERIOD_ORDER,
    )
    hypothesis_models = models[models["hypothesis_period"].isin(HYPOTHESIS_PERIOD_ORDER)].copy()
    hypothesis_mentions = mentions[
        mentions["hypothesis_period"].isin(HYPOTHESIS_PERIOD_ORDER)
    ].copy()
    provider_hypothesis_summary = summarize_provider_period(
        hypothesis_models,
        hypothesis_mentions,
        "hypothesis_period",
        HYPOTHESIS_PERIOD_ORDER,
    )

    provider_period_axis_shares = axis_share_table(
        mentions,
        facets,
        "period",
        PERIOD_ORDER,
    )
    provider_hypothesis_axis_shares = axis_share_table(
        hypothesis_mentions,
        facets,
        "hypothesis_period",
        HYPOTHESIS_PERIOD_ORDER,
    )

    benchmark_drivers = benchmark_driver_table(
        hypothesis_mentions,
        "hypothesis_period",
        HYPOTHESIS_PERIOD_ORDER,
    )
    long_context_drivers = benchmark_drivers[
        benchmark_drivers["is_long_context_broad"]
    ].copy()

    write_csv(mentions, output_dir / "release_benchmark_mentions.csv")
    write_csv(unresolved, output_dir / "unresolved_mentions.csv")
    write_csv(provider_period_summary, output_dir / "provider_period_summary.csv")
    write_csv(
        provider_hypothesis_summary,
        output_dir / "provider_hypothesis_period_summary.csv",
    )
    write_csv(
        provider_period_axis_shares,
        output_dir / "provider_period_axis_shares.csv",
    )
    write_csv(
        provider_hypothesis_axis_shares,
        output_dir / "provider_hypothesis_axis_shares.csv",
    )
    write_csv(benchmark_drivers, output_dir / "benchmark_drivers.csv")
    write_csv(
        long_context_drivers,
        output_dir / "long_context_benchmark_drivers.csv",
    )
    write_csv(review_status_summary(facets), output_dir / "facet_review_status_summary.csv")

    plot_long_context(
        provider_hypothesis_summary,
        output_dir / "provider_long_context_share.png",
    )
    plot_strategy_heatmap(
        provider_period_summary,
        output_dir / "provider_strategy_heatmap.png",
    )

    print(f"As-of date: {cutoff.date()}")
    print(f"Resolved benchmark mentions: {len(mentions)}")
    print(f"Unresolved benchmark mentions: {len(unresolved)}")


if __name__ == "__main__":
    main()
