import argparse
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from plot_utils import (  # noqa: E402
    DATA_DIR,
    build_rolling_share_trend,
    configure_plot_style,
    latest_release_date,
    parse_as_of,
    save_figure,
    split_benchmarks,
    validate_window_days,
    warn_unresolved,
)
from taxonomy_utils import CanonicalResolver  # noqa: E402


configure_plot_style()

DEFAULT_AXES = ["domain", "modality", "interaction_pattern", "context_pressure"]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate rolling trends from benchmark facets.")
    parser.add_argument(
        "--as-of",
        help="Include model releases on or before this date (YYYY-MM-DD). Defaults to latest models.csv release date.",
    )
    parser.add_argument("--window-days", type=int, default=180, help="Rolling window size in days.")
    parser.add_argument(
        "--axes",
        default=",".join(DEFAULT_AXES),
        help="Comma-separated facet axes to plot.",
    )
    parser.add_argument(
        "--output",
        default="assets/benchmark_facet_trends.png",
        help="Output image path.",
    )
    parser.add_argument(
        "--top-labels",
        type=int,
        default=10,
        help="Maximum labels to show per axis before grouping the remainder into Other.",
    )
    parser.add_argument(
        "--strict-resolution",
        action="store_true",
        help="Fail if any benchmark mention does not resolve by exact name or explicit alias.",
    )
    return parser.parse_args()


def split_axes(value):
    axes = [axis.strip() for axis in value.split(",") if axis.strip()]
    if not axes:
        raise ValueError("--axes must include at least one facet axis.")
    return axes


def load_inputs():
    models_path = DATA_DIR / "models.csv"
    benchmarks_path = DATA_DIR / "benchmarks.csv"
    aliases_path = DATA_DIR / "benchmark_aliases.csv"
    facets_path = DATA_DIR / "benchmark_facets.csv"
    if not models_path.exists() or not benchmarks_path.exists() or not facets_path.exists():
        raise FileNotFoundError("Run scripts/build_normalized_data.py before generating facet trends.")

    models = pd.read_csv(models_path).fillna("")
    resolver = CanonicalResolver.from_files(benchmarks_path, aliases_path if aliases_path.exists() else None)
    facets = pd.read_csv(facets_path).fillna("")
    return models, facets, resolver


def build_model_mentions(models, resolver, strict_resolution=False):
    rows = []
    unresolved = []
    for _, model in models.fillna("").iterrows():
        provider = str(model.get("Provider", "")).strip()
        model_name = str(model.get("Model name", "")).strip()
        release_date = str(model.get("release date", "")).strip()
        model_key = "|".join([provider, model_name, release_date])
        raw_mentions = split_benchmarks(model.get("benchmarks", ""))

        for raw_mention in raw_mentions:
            resolution = resolver.resolve(raw_mention)
            if not resolution:
                unresolved.append(f"{provider} / {model_name} / {raw_mention}")
                continue
            rows.append(
                {
                    "model_key": model_key,
                    "release_date": release_date,
                    "benchmark_id": resolution.benchmark_id,
                    "raw_mention": raw_mention,
                    "raw_weight": 1.0,
                }
            )

    warn_unresolved(
        unresolved,
        strict_resolution,
        resolution_hint="Add canonical benchmark rows or explicit aliases to resolve them.",
        sample_separator="; ",
    )

    return pd.DataFrame(
        rows,
        columns=["model_key", "release_date", "benchmark_id", "raw_mention", "raw_weight"],
    )


def normalize_mentions(mentions, as_of):
    mentions = mentions.copy()
    mentions["release_date"] = pd.to_datetime(mentions["release_date"], errors="raise")
    mentions["raw_weight"] = pd.to_numeric(mentions["raw_weight"], errors="coerce").fillna(1.0)
    mentions = mentions[mentions["release_date"] <= as_of].copy()
    if mentions.empty:
        return mentions

    model_totals = mentions.groupby("model_key")["raw_weight"].transform("sum")
    mentions["normalized_model_weight"] = mentions["raw_weight"] / model_totals.where(model_totals > 0, 1.0)
    return mentions


def active_facets_for_axis(facets, axis):
    axis_facets = facets[
        (facets["facet_axis"] == axis)
        & (facets["review_status"] != "deprecated")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ].copy()
    return axis_facets


def events_for_axis(mentions, facets, axis, top_labels):
    axis_facets = active_facets_for_axis(facets, axis)
    if mentions.empty or axis_facets.empty:
        return pd.DataFrame(columns=["Date", "Category", "Weight"])

    mentions_with_id = mentions.reset_index(drop=True).reset_index(names="mention_row_id")
    joined = mentions_with_id.merge(axis_facets, on="benchmark_id", how="inner")
    label_counts = joined.groupby("mention_row_id")["facet_label"].transform("count")
    joined["Weight"] = joined["normalized_model_weight"] / label_counts.where(label_counts > 0, 1.0)
    joined = joined[joined["Weight"] > 0].copy()

    if top_labels > 0:
        totals = joined.groupby("facet_label")["Weight"].sum().sort_values(ascending=False)
        keep = set(totals.head(top_labels).index)
        joined["facet_label"] = joined["facet_label"].where(joined["facet_label"].isin(keep), "Other")

    return joined.rename(columns={"release_date": "Date", "facet_label": "Category"})[
        ["Date", "Category", "Weight"]
    ]


def plot_axis(ax, trend, axis, window_days, as_of):
    if trend.empty:
        ax.text(0.5, 0.5, f"No {axis} events", transform=ax.transAxes, ha="center", va="center")
        ax.set_axis_off()
        return

    labels = list(trend.columns)
    colors = sns.color_palette("tab20", n_colors=len(labels))
    ax.stackplot(trend.index, [trend[label] for label in labels], labels=labels, colors=colors, alpha=0.9)
    title = axis.replace("_", " ").title()
    ax.set_title(f"{title} Trend (facet data, {window_days}-day, as of {as_of.date()})", fontsize=14, weight="bold")
    ax.set_ylabel("Share of weighted mentions", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.5)
    ax.grid(False, axis="x")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)


def generate_facet_trends(
    as_of=None,
    window_days=180,
    axes=None,
    output_path=None,
    top_labels=10,
    strict_resolution=False,
):
    window_days = validate_window_days(window_days)
    axes = axes or DEFAULT_AXES
    output_path = output_path or "assets/benchmark_facet_trends.png"
    models, facets, resolver = load_inputs()
    if as_of is None:
        as_of = latest_release_date(models)

    mentions = build_model_mentions(models, resolver, strict_resolution=strict_resolution)
    mentions = normalize_mentions(mentions, as_of)
    if mentions.empty:
        print("No model benchmark mentions found.")
        return

    fig_height = max(4.5 * len(axes), 7)
    fig, axs = plt.subplots(len(axes), 1, figsize=(17, fig_height), sharex=True)
    if len(axes) == 1:
        axs = [axs]

    min_dates = []
    for ax, axis in zip(axs, axes):
        events = events_for_axis(mentions, facets, axis, top_labels)
        trend, min_date = build_rolling_share_trend(events, as_of, window_days)
        if min_date is not None:
            min_dates.append(min_date)
        plot_axis(ax, trend, axis, window_days, as_of)

    if min_dates:
        for ax in axs:
            ax.set_xlim(min(min_dates), as_of)
    axs[-1].set_xlabel("Time", fontsize=12)
    plt.xticks(rotation=45)
    fig.suptitle("Benchmark Trends by Multi-Facet Taxonomy", fontsize=18, weight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    save_figure(fig, output_path)
    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    generate_facet_trends(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        axes=split_axes(args.axes),
        output_path=args.output,
        top_labels=args.top_labels,
        strict_resolution=args.strict_resolution,
    )
