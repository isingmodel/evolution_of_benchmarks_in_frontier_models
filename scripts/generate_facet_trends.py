import argparse
import os
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns


sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]

DATA_DIR = Path("data")
DEFAULT_AXES = ["domain", "modality", "interaction_pattern", "context_pressure"]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate rolling trends from benchmark facet edges.")
    parser.add_argument(
        "--as-of",
        help="Include model releases on or before this date (YYYY-MM-DD). Defaults to latest release_mentions date.",
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
    return parser.parse_args()


def parse_as_of(value):
    if not value:
        return None
    return pd.to_datetime(value, errors="raise").normalize()


def validate_window_days(window_days):
    if window_days <= 0:
        raise ValueError("--window-days must be a positive integer.")
    return window_days


def split_axes(value):
    axes = [axis.strip() for axis in value.split(",") if axis.strip()]
    if not axes:
        raise ValueError("--axes must include at least one facet axis.")
    return axes


def load_inputs():
    mentions_path = DATA_DIR / "release_mentions.csv"
    facets_path = DATA_DIR / "benchmark_facet_edges.csv"
    if not mentions_path.exists() or not facets_path.exists():
        raise FileNotFoundError("Run scripts/build_normalized_data.py before generating facet trends.")

    mentions = pd.read_csv(mentions_path).fillna("")
    facets = pd.read_csv(facets_path).fillna("")
    return mentions, facets


def normalize_mentions(mentions, as_of):
    mentions = mentions.copy()
    mentions["release_date"] = pd.to_datetime(mentions["release_date"], errors="raise")
    mentions["mention_weight"] = pd.to_numeric(mentions["mention_weight"], errors="coerce").fillna(1.0)
    mentions = mentions[mentions["release_date"] <= as_of].copy()
    if mentions.empty:
        return mentions

    model_totals = mentions.groupby("model_id")["mention_weight"].transform("sum")
    mentions["normalized_mention_weight"] = mentions["mention_weight"] / model_totals.where(model_totals > 0, 1.0)
    return mentions


def active_facets_for_axis(facets, axis):
    axis_facets = facets[
        (facets["facet_axis"] == axis)
        & (facets["review_status"] != "deprecated")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ].copy()
    axis_facets["label_weight"] = pd.to_numeric(axis_facets["label_weight"], errors="coerce").fillna(0.0)
    return axis_facets


def events_for_axis(mentions, facets, axis, top_labels):
    axis_facets = active_facets_for_axis(facets, axis)
    if mentions.empty or axis_facets.empty:
        return pd.DataFrame(columns=["Date", "Category", "Weight"])

    joined = mentions.merge(axis_facets, on="benchmark_id", how="inner")
    joined["Weight"] = joined["normalized_mention_weight"] * joined["label_weight"]
    joined = joined[joined["Weight"] > 0].copy()

    if top_labels > 0:
        totals = joined.groupby("facet_label")["Weight"].sum().sort_values(ascending=False)
        keep = set(totals.head(top_labels).index)
        joined["facet_label"] = joined["facet_label"].where(joined["facet_label"].isin(keep), "Other")

    return joined.rename(columns={"release_date": "Date", "facet_label": "Category"})[
        ["Date", "Category", "Weight"]
    ]


def build_trend(events, as_of, window_days):
    if events.empty:
        return pd.DataFrame(), None

    min_date = events["Date"].min()
    date_range = pd.date_range(start=min_date, end=as_of, freq="D")
    daily = events.groupby(["Date", "Category"])["Weight"].sum().unstack(fill_value=0)
    daily = daily.reindex(date_range, fill_value=0)

    rolling = daily.rolling(window=window_days, min_periods=1).sum()
    trend = rolling.div(rolling.sum(axis=1), axis=0).ffill().fillna(0)
    for col in trend.columns:
        trend[col] = trend[col].ewm(span=30, adjust=False).mean()
    trend = trend.div(trend.sum(axis=1), axis=0).fillna(0)
    return trend, min_date


def plot_axis(ax, trend, axis, window_days, as_of):
    if trend.empty:
        ax.text(0.5, 0.5, f"No {axis} events", transform=ax.transAxes, ha="center", va="center")
        ax.set_axis_off()
        return

    labels = list(trend.columns)
    colors = sns.color_palette("tab20", n_colors=len(labels))
    ax.stackplot(trend.index, [trend[label] for label in labels], labels=labels, colors=colors, alpha=0.9)
    title = axis.replace("_", " ").title()
    ax.set_title(
        f"{title} Trend (experimental facet data, {window_days}-day, as of {as_of.date()})",
        fontsize=14,
        weight="bold",
    )
    ax.set_ylabel("Share of weighted mentions", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.5)
    ax.grid(False, axis="x")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)


def save_figure(fig, output_path):
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Graph generated at {output_path}")


def generate_facet_trends(as_of=None, window_days=180, axes=None, output_path=None, top_labels=10):
    window_days = validate_window_days(window_days)
    axes = axes or DEFAULT_AXES
    output_path = output_path or "assets/benchmark_facet_trends.png"
    mentions, facets = load_inputs()
    if as_of is None:
        as_of = pd.to_datetime(mentions["release_date"], errors="raise").max().normalize()

    mentions = normalize_mentions(mentions, as_of)
    if mentions.empty:
        print("No release mentions found.")
        return

    fig_height = max(4.5 * len(axes), 7)
    fig, axs = plt.subplots(len(axes), 1, figsize=(17, fig_height), sharex=True)
    if len(axes) == 1:
        axs = [axs]

    min_dates = []
    for ax, axis in zip(axs, axes):
        events = events_for_axis(mentions, facets, axis, top_labels)
        trend, min_date = build_trend(events, as_of, window_days)
        if min_date is not None:
            min_dates.append(min_date)
        plot_axis(ax, trend, axis, window_days, as_of)

    if min_dates:
        for ax in axs:
            ax.set_xlim(min(min_dates), as_of)
    axs[-1].set_xlabel("Time", fontsize=12)
    plt.xticks(rotation=45)
    fig.suptitle("Benchmark Trends by Multi-Facet Taxonomy", fontsize=18, weight="bold", y=0.995)
    fig.text(
        0.5,
        0.012,
        f"Weighted by release-normalized mention_weight x label_weight. Top {top_labels} labels per axis are shown; smaller labels are grouped into Other. Facet data remains review-heavy.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.025, 1, 0.985])
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
    )
