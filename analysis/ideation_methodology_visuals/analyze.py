#!/usr/bin/env python3
"""Prototype richer benchmark-evolution analyses.

This script is intentionally self-contained under analysis/ideation_methodology_visuals.
It reads the repository source CSVs, resolves release-page benchmark mentions with
CanonicalResolver, and writes prototype charts/tables back to this folder.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch, Rectangle
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from plot_utils import add_derived_headline_task_mode  # noqa: E402
from taxonomy_utils import CanonicalResolver, split_benchmark_mentions  # noqa: E402


MODE_ORDER = [
    "Agentic",
    "Multimodal Perception",
    "Generative Reasoning",
    "Constraint Satisfaction",
    "Knowledge Retrieval",
]

STATUS_ORDER = ["accepted", "legacy_seed", "needs_review", "disputed"]
STATUS_COLORS = {
    "accepted": "#2f9d6a",
    "legacy_seed": "#7d91b3",
    "needs_review": "#e9a23b",
    "disputed": "#c95555",
}

PROVIDER_ORDER = ["OpenAI", "Google", "Anthropic"]


def configure_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["figure.dpi"] = 120


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, CanonicalResolver]:
    models = pd.read_csv(DATA_DIR / "models.csv").fillna("")
    benchmarks = pd.read_csv(DATA_DIR / "benchmarks.csv").fillna("")
    facets = add_derived_headline_task_mode(pd.read_csv(DATA_DIR / "benchmark_facets.csv").fillna(""))
    resolver = CanonicalResolver.from_files(
        DATA_DIR / "benchmarks.csv",
        DATA_DIR / "benchmark_aliases.csv",
    )
    return models, benchmarks, facets, resolver


def build_mentions(models: pd.DataFrame, resolver: CanonicalResolver) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    unresolved: list[str] = []
    mention_id = 0

    for _, model in models.iterrows():
        provider = str(model.get("Provider", "")).strip()
        model_name = str(model.get("Model name", "")).strip()
        release_date = pd.to_datetime(str(model.get("release date", "")).strip(), errors="raise")
        model_key = "|".join([provider, model_name, release_date.strftime("%Y-%m-%d")])
        raw_mentions = split_benchmark_mentions(model.get("benchmarks", ""))
        if not raw_mentions:
            continue

        for raw_mention in raw_mentions:
            resolution = resolver.resolve(raw_mention)
            if resolution is None:
                unresolved.append(f"{provider} / {model_name} / {raw_mention}")
                continue
            rows.append(
                {
                    "mention_row_id": mention_id,
                    "provider": provider,
                    "model_name": model_name,
                    "model_key": model_key,
                    "release_date": release_date,
                    "raw_mention": raw_mention,
                    "benchmark_id": resolution.benchmark_id,
                    "benchmark_name": resolution.benchmark_name,
                    "match_source": resolution.match_source,
                    "match_type": resolution.match_type,
                }
            )
            mention_id += 1

    if unresolved:
        sample = "; ".join(unresolved[:10])
        raise ValueError(
            f"Unresolved benchmark mentions skipped ({len(unresolved)}): {sample}. "
            "Add canonical benchmark rows or explicit aliases; fuzzy matching is disabled."
        )

    mentions = pd.DataFrame(rows)
    if mentions.empty:
        return mentions

    mention_counts = mentions.groupby("model_key")["mention_row_id"].transform("count")
    mentions["model_normalized_weight"] = 1.0 / mention_counts
    return mentions


def active_facets(facets: pd.DataFrame, axis: str | None = None) -> pd.DataFrame:
    active = facets[
        (facets["review_status"] != "deprecated")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ].copy()
    if axis is not None:
        active = active[active["facet_axis"] == axis].copy()
    active["classification_confidence"] = pd.to_numeric(
        active["classification_confidence"], errors="coerce"
    ).fillna(0.0)
    return active


def window_mentions(mentions: pd.DataFrame, latest: pd.Timestamp, days: int) -> pd.DataFrame:
    start = latest - pd.Timedelta(days=days)
    return mentions[mentions["release_date"] >= start].copy()


def facet_contributions(
    mentions: pd.DataFrame,
    facets: pd.DataFrame,
    axis: str,
) -> pd.DataFrame:
    axis_facets = active_facets(facets, axis)
    joined = mentions.merge(axis_facets, on="benchmark_id", how="inner")
    if joined.empty:
        return joined

    label_counts = joined.groupby("mention_row_id")["facet_label"].transform("count")
    joined["weight"] = joined["model_normalized_weight"] / label_counts.where(label_counts > 0, 1.0)
    return joined


def choose_axis_labels(contrib: pd.DataFrame, axis: str, max_labels: int) -> list[str]:
    if axis == "headline_task_mode":
        present = set(contrib["facet_label"])
        return [label for label in MODE_ORDER if label in present]

    totals = contrib.groupby("facet_label")["weight"].sum().sort_values(ascending=False)
    return list(totals.head(max_labels).index)


def wrap_label(value: str, width: int = 16) -> str:
    text = str(value).replace("_", " ")
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False)) or text


def format_share(value: float) -> str:
    if 0 < value < 0.005:
        return "<1%"
    return f"{value:.0%}"


def write_provider_strategy_fingerprints(
    mentions: pd.DataFrame,
    facets: pd.DataFrame,
    latest: pd.Timestamp,
    window_days: int = 365,
) -> None:
    recent = window_mentions(mentions, latest, window_days)
    axes = [
        ("headline_task_mode", "Headline Projection", 5),
        ("domain", "Domain", 6),
        ("interaction_pattern", "Interaction", 6),
        ("context_pressure", "Context Pressure", 5),
        ("benchmark_lifecycle_risk", "Lifecycle Risk", 5),
    ]

    long_rows: list[pd.DataFrame] = []
    matrix_specs: list[tuple[str, str, list[str], pd.DataFrame]] = []

    for axis, title, max_labels in axes:
        contrib = facet_contributions(recent, facets, axis)
        if contrib.empty:
            continue
        labels = choose_axis_labels(contrib, axis, max_labels)
        filtered = contrib[contrib["facet_label"].isin(labels)].copy()
        grouped = (
            filtered.groupby(["provider", "facet_axis", "facet_label"], as_index=False)["weight"]
            .sum()
            .rename(columns={"weight": "weighted_mentions"})
        )
        denominators = (
            contrib.groupby(["provider", "facet_axis"], as_index=False)["weight"]
            .sum()
            .rename(columns={"weight": "axis_weight_total"})
        )
        grouped = grouped.merge(denominators, on=["provider", "facet_axis"], how="left")
        grouped["share_of_provider_axis"] = grouped["weighted_mentions"] / grouped[
            "axis_weight_total"
        ].where(grouped["axis_weight_total"] > 0, 1.0)
        long_rows.append(grouped)

        matrix = grouped.pivot(index="provider", columns="facet_label", values="share_of_provider_axis")
        matrix = matrix.reindex(index=[p for p in PROVIDER_ORDER if p in recent["provider"].unique()])
        matrix = matrix.reindex(columns=labels).fillna(0.0)
        matrix_specs.append((axis, title, labels, matrix))

    output_csv = OUT_DIR / "provider_strategy_fingerprints.csv"
    pd.concat(long_rows, ignore_index=True).sort_values(
        ["facet_axis", "provider", "share_of_provider_axis"], ascending=[True, True, False]
    ).to_csv(output_csv, index=False)

    fig, axs = plt.subplots(1, len(matrix_specs), figsize=(21, 5.4), constrained_layout=False)
    cmap = sns.color_palette("crest", as_cmap=True)

    for i, (axis, title, labels, matrix) in enumerate(matrix_specs):
        ax = axs[i]
        sns.heatmap(
            matrix,
            ax=ax,
            cmap=cmap,
            vmin=0,
            vmax=1,
            cbar=i == len(matrix_specs) - 1,
            cbar_kws={"format": mtick.PercentFormatter(1.0), "shrink": 0.72},
            linewidths=0.7,
            linecolor="white",
            annot=matrix.map(format_share),
            fmt="",
            annot_kws={"fontsize": 8},
        )
        ax.set_title(title, fontsize=12, pad=10)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticklabels([wrap_label(label, 14) for label in labels], rotation=0, fontsize=8)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=10)
        if i > 0:
            ax.set_yticklabels([])

    start = latest - pd.Timedelta(days=window_days)
    fig.suptitle(
        "Provider Strategy Fingerprints From Release-Page Benchmark Mentions",
        fontsize=17,
        weight="bold",
        y=1.02,
    )
    fig.text(
        0.5,
        -0.02,
        (
            f"Window: {start.date()} to {latest.date()}. Each model release receives equal total weight; "
            "multi-label facet axes split a benchmark mention equally across labels."
        ),
        ha="center",
        fontsize=10,
    )
    plt.tight_layout()
    fig.savefig(OUT_DIR / "provider_strategy_fingerprints.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def group_small_labels(
    frame: pd.DataFrame,
    column: str,
    weight_col: str = "weight",
    min_share: float = 0.025,
    top_n: int = 8,
) -> pd.Series:
    totals = frame.groupby(column)[weight_col].sum().sort_values(ascending=False)
    total = totals.sum()
    keep = set(totals.head(top_n).index)
    keep.update(totals[totals / total >= min_share].index)
    return frame[column].where(frame[column].isin(keep), "Other")


def pair_axis_contributions(
    mentions: pd.DataFrame,
    facets: pd.DataFrame,
    source_axis: str,
    target_axis: str,
) -> pd.DataFrame:
    left = active_facets(facets, source_axis)[
        ["benchmark_id", "facet_label", "review_status", "classification_confidence"]
    ].rename(
        columns={
            "facet_label": "source_label",
            "review_status": "source_review_status",
            "classification_confidence": "source_confidence",
        }
    )
    right = active_facets(facets, target_axis)[
        ["benchmark_id", "facet_label", "review_status", "classification_confidence"]
    ].rename(
        columns={
            "facet_label": "target_label",
            "review_status": "target_review_status",
            "classification_confidence": "target_confidence",
        }
    )

    pairs = mentions.merge(left, on="benchmark_id", how="inner").merge(right, on="benchmark_id", how="inner")
    if pairs.empty:
        return pairs

    source_counts = pairs.groupby("mention_row_id")["source_label"].transform("nunique")
    target_counts = pairs.groupby("mention_row_id")["target_label"].transform("nunique")
    pairs["weight"] = pairs["model_normalized_weight"] / (
        source_counts.where(source_counts > 0, 1.0) * target_counts.where(target_counts > 0, 1.0)
    )
    pairs["pair_confidence"] = (pairs["source_confidence"] + pairs["target_confidence"]) / 2.0
    pairs["pair_accepted"] = (
        (pairs["source_review_status"] == "accepted") & (pairs["target_review_status"] == "accepted")
    ).astype(float)
    return pairs


def stacked_positions(labels: list[str], totals: pd.Series, gap: float = 0.015) -> dict[str, tuple[float, float]]:
    available = 1.0 - gap * (len(labels) - 1)
    y = 0.0
    positions: dict[str, tuple[float, float]] = {}
    for label in labels:
        height = float(totals[label]) * available
        positions[label] = (y, y + height)
        y += height + gap
    return positions


def ribbon_path(x0: float, x1: float, y0a: float, y0b: float, y1a: float, y1b: float) -> MplPath:
    mid = (x0 + x1) / 2
    verts = [
        (x0, y0a),
        (mid, y0a),
        (mid, y1a),
        (x1, y1a),
        (x1, y1b),
        (mid, y1b),
        (mid, y0b),
        (x0, y0b),
        (x0, y0a),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.LINETO,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CURVE4,
        MplPath.CLOSEPOLY,
    ]
    return MplPath(verts, codes)


def write_domain_interaction_alluvial(
    mentions: pd.DataFrame,
    facets: pd.DataFrame,
    latest: pd.Timestamp,
    window_days: int = 365,
) -> None:
    recent = window_mentions(mentions, latest, window_days)
    pairs = pair_axis_contributions(recent, facets, "domain", "interaction_pattern")
    if pairs.empty:
        return

    pairs["source_label_grouped"] = group_small_labels(pairs, "source_label", top_n=8)
    pairs["target_label_grouped"] = group_small_labels(pairs, "target_label", top_n=8)

    flow = (
        pairs.groupby(["source_label_grouped", "target_label_grouped"], as_index=False)
        .agg(
            weight=("weight", "sum"),
            mean_confidence=("pair_confidence", "mean"),
            accepted_pair_share=("pair_accepted", "mean"),
            raw_mentions=("mention_row_id", "nunique"),
        )
        .rename(columns={"source_label_grouped": "source_domain", "target_label_grouped": "target_interaction"})
    )
    flow = flow[flow["weight"] > 0].copy()
    flow["share"] = flow["weight"] / flow["weight"].sum()
    flow.sort_values(["source_domain", "weight"], ascending=[True, False]).to_csv(
        OUT_DIR / "domain_interaction_flow.csv", index=False
    )

    source_totals = flow.groupby("source_domain")["share"].sum().sort_values(ascending=False)
    target_totals = flow.groupby("target_interaction")["share"].sum().sort_values(ascending=False)
    source_labels = list(source_totals.index)
    target_labels = list(target_totals.index)

    source_pos = stacked_positions(source_labels, source_totals)
    target_pos = stacked_positions(target_labels, target_totals)
    source_cum = {label: source_pos[label][0] for label in source_labels}
    target_cum = {label: target_pos[label][0] for label in target_labels}

    palette = dict(zip(source_labels, sns.color_palette("tab10", n_colors=len(source_labels)).as_hex()))

    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.04, 1.04)
    ax.axis("off")

    for _, row in flow.sort_values("share", ascending=True).iterrows():
        source = row["source_domain"]
        target = row["target_interaction"]
        source_height = row["share"] / source_totals[source] * (source_pos[source][1] - source_pos[source][0])
        target_height = row["share"] / target_totals[target] * (target_pos[target][1] - target_pos[target][0])
        y0a, y0b = source_cum[source], source_cum[source] + source_height
        y1a, y1b = target_cum[target], target_cum[target] + target_height
        source_cum[source] += source_height
        target_cum[target] += target_height

        confidence_alpha = float(np.clip(0.20 + 0.65 * row["mean_confidence"], 0.25, 0.85))
        patch = PathPatch(
            ribbon_path(0.18, 0.82, y0a, y0b, y1a, y1b),
            facecolor=palette[source],
            edgecolor="white",
            lw=0.25,
            alpha=confidence_alpha,
        )
        ax.add_patch(patch)

    for label in source_labels:
        y0, y1 = source_pos[label]
        ax.add_patch(Rectangle((0.08, y0), 0.07, y1 - y0, facecolor=palette[label], edgecolor="white", lw=1))
        ax.text(0.06, (y0 + y1) / 2, wrap_label(label, 18), ha="right", va="center", fontsize=10)
        ax.text(0.155, (y0 + y1) / 2, format_share(source_totals[label]), ha="left", va="center", fontsize=9)

    for label in target_labels:
        y0, y1 = target_pos[label]
        ax.add_patch(Rectangle((0.85, y0), 0.07, y1 - y0, facecolor="#343a40", edgecolor="white", lw=1))
        ax.text(0.94, (y0 + y1) / 2, wrap_label(label, 22), ha="left", va="center", fontsize=10)
        ax.text(0.845, (y0 + y1) / 2, format_share(target_totals[label]), ha="right", va="center", fontsize=9)

    start = latest - pd.Timedelta(days=window_days)
    ax.text(0.115, 1.02, "Domain Facets", ha="center", va="bottom", fontsize=12, weight="bold")
    ax.text(0.885, 1.02, "Interaction Pattern Facets", ha="center", va="bottom", fontsize=12, weight="bold")
    fig.suptitle(
        "Facet Flow: What Domains Are Being Framed as Which Interaction Patterns?",
        fontsize=17,
        weight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.035,
        (
            f"Window: {start.date()} to {latest.date()}. Ribbons are weighted release-page mentions; "
            "a single benchmark can contribute fractional weight to multiple facet labels."
        ),
        ha="center",
        fontsize=10,
    )
    fig.savefig(OUT_DIR / "domain_interaction_alluvial.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_review_leverage(
    mentions: pd.DataFrame,
    benchmarks: pd.DataFrame,
    facets: pd.DataFrame,
    latest: pd.Timestamp,
    window_days: int = 365,
    top_n: int = 18,
) -> None:
    recent = window_mentions(mentions, latest, window_days)
    mention_totals = (
        recent.groupby(["benchmark_id", "benchmark_name"], as_index=False)
        .agg(
            recent_weighted_mentions=("model_normalized_weight", "sum"),
            recent_raw_mentions=("mention_row_id", "count"),
            providers=("provider", lambda values: "; ".join(sorted(set(values)))),
            provider_count=("provider", "nunique"),
        )
    )

    status_counts = (
        active_facets(facets)
        .groupby(["benchmark_id", "review_status"], as_index=False)
        .size()
        .rename(columns={"size": "facet_rows"})
    )
    status_wide = (
        status_counts.pivot(index="benchmark_id", columns="review_status", values="facet_rows")
        .fillna(0)
        .reset_index()
    )
    for status in STATUS_ORDER:
        if status not in status_wide.columns:
            status_wide[status] = 0
    status_wide["facet_rows_total"] = status_wide[STATUS_ORDER].sum(axis=1)
    for status in STATUS_ORDER:
        status_wide[f"{status}_share"] = status_wide[status] / status_wide["facet_rows_total"].where(
            status_wide["facet_rows_total"] > 0, 1.0
        )

    first_last = (
        mentions.groupby(["benchmark_id", "benchmark_name"], as_index=False)
        .agg(first_seen=("release_date", "min"), last_seen=("release_date", "max"), all_time_mentions=("mention_row_id", "count"))
    )
    review = (
        mention_totals.merge(status_wide, on="benchmark_id", how="left")
        .merge(first_last, on=["benchmark_id", "benchmark_name"], how="left")
        .merge(benchmarks[["benchmark_id", "source_author", "frontier_lab_author_affiliations"]], on="benchmark_id", how="left")
    )
    review[STATUS_ORDER] = review[STATUS_ORDER].fillna(0)
    for status in STATUS_ORDER:
        review[f"{status}_share"] = review[f"{status}_share"].fillna(0)
    review["nonaccepted_share"] = 1.0 - review["accepted_share"]
    review["review_leverage"] = review["recent_weighted_mentions"] * review["nonaccepted_share"]
    review.sort_values("review_leverage", ascending=False).to_csv(
        OUT_DIR / "review_leverage_benchmarks.csv", index=False
    )

    plot_df = review.sort_values("review_leverage", ascending=False).head(top_n).copy()
    plot_df = plot_df.sort_values("review_leverage", ascending=True)

    fig, ax = plt.subplots(figsize=(13, 9))
    left = np.zeros(len(plot_df))
    y = np.arange(len(plot_df))

    for status in STATUS_ORDER:
        widths = plot_df["recent_weighted_mentions"].to_numpy() * plot_df[f"{status}_share"].to_numpy()
        ax.barh(
            y,
            widths,
            left=left,
            height=0.72,
            color=STATUS_COLORS[status],
            label=status.replace("_", " "),
            edgecolor="white",
            linewidth=0.6,
        )
        left += widths

    labels = [wrap_label(name, 32) for name in plot_df["benchmark_name"]]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Recent model-normalized mention weight", fontsize=11)
    ax.xaxis.set_major_locator(mtick.MaxNLocator(6))
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    ax.grid(False, axis="y")
    ax.legend(loc="lower right", frameon=False, ncol=2)

    for yi, (_, row) in zip(y, plot_df.iterrows()):
        ax.text(
            row["recent_weighted_mentions"] + 0.025,
            yi,
            f"{row['provider_count']} provider{'s' if row['provider_count'] != 1 else ''}",
            va="center",
            fontsize=8,
            color="#4b5563",
        )

    start = latest - pd.Timedelta(days=window_days)
    ax.set_title("Review Leverage: High-Impact Benchmark Facets Still Driving Uncertainty", fontsize=16, pad=14)
    fig.text(
        0.5,
        0.02,
        (
            f"Window: {start.date()} to {latest.date()}. Bars rank benchmarks by recent mention weight "
            "multiplied by the share of active facet rows that are not accepted."
        ),
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=[0.0, 0.04, 0.94, 1.0])
    fig.savefig(OUT_DIR / "review_leverage_benchmarks.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_lifecycle_table(
    mentions: pd.DataFrame,
    benchmarks: pd.DataFrame,
    facets: pd.DataFrame,
) -> None:
    lifecycle_risk = (
        active_facets(facets, "benchmark_lifecycle_risk")
        .groupby("benchmark_id")
        .agg(
            lifecycle_risk_labels=("facet_label", lambda values: "; ".join(sorted(set(values)))),
            lifecycle_risk_review_status=("review_status", lambda values: "; ".join(sorted(set(values)))),
        )
        .reset_index()
    )
    lifecycle = (
        mentions.groupby(["benchmark_id", "benchmark_name"], as_index=False)
        .agg(
            first_seen=("release_date", "min"),
            last_seen=("release_date", "max"),
            raw_mentions=("mention_row_id", "count"),
            model_normalized_mentions=("model_normalized_weight", "sum"),
            provider_count=("provider", "nunique"),
            providers=("provider", lambda values: "; ".join(sorted(set(values)))),
        )
        .merge(benchmarks.drop(columns=["benchmark_name"]), on="benchmark_id", how="left")
        .merge(lifecycle_risk, on="benchmark_id", how="left")
    )
    lifecycle["active_days"] = (lifecycle["last_seen"] - lifecycle["first_seen"]).dt.days + 1
    lifecycle["mentions_per_active_month"] = lifecycle["raw_mentions"] / (lifecycle["active_days"] / 30.44).clip(lower=1)
    lifecycle.sort_values(["first_seen", "raw_mentions"], ascending=[True, False]).to_csv(
        OUT_DIR / "benchmark_lifecycle_table.csv", index=False
    )


def write_summary_stats(mentions: pd.DataFrame, facets: pd.DataFrame, latest: pd.Timestamp) -> None:
    recent = window_mentions(mentions, latest, 365)
    stats = {
        "latest_release_date": latest.date().isoformat(),
        "model_rows_with_benchmarks": mentions["model_key"].nunique(),
        "resolved_mentions": len(mentions),
        "unique_resolved_benchmarks": mentions["benchmark_id"].nunique(),
        "recent_365d_resolved_mentions": len(recent),
        "recent_365d_unique_benchmarks": recent["benchmark_id"].nunique(),
        "facet_rows": len(facets),
        "facet_needs_review_rows": int((facets["review_status"] == "needs_review").sum()),
        "facet_legacy_seed_rows": int((facets["review_status"] == "legacy_seed").sum()),
        "facet_accepted_rows": int((facets["review_status"] == "accepted").sum()),
    }
    pd.DataFrame([stats]).to_csv(OUT_DIR / "summary_stats.csv", index=False)


def main() -> None:
    configure_style()
    models, benchmarks, facets, resolver = load_inputs()
    mentions = build_mentions(models, resolver)
    latest = mentions["release_date"].max().normalize()

    write_summary_stats(mentions, facets, latest)
    write_provider_strategy_fingerprints(mentions, facets, latest)
    write_domain_interaction_alluvial(mentions, facets, latest)
    write_review_leverage(mentions, benchmarks, facets, latest)
    write_lifecycle_table(mentions, benchmarks, facets)

    print(f"Wrote prototype outputs to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
