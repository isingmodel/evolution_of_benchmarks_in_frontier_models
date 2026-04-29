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
    ALIAS_PATH,
    BENCHMARKS_PATH,
    configure_plot_style,
    latest_release_date,
    load_models,
    parse_as_of,
    save_figure,
    split_benchmarks,
    validate_window_days,
    warn_unresolved,
)
from taxonomy_utils import CanonicalResolver  # noqa: E402


configure_plot_style()


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a smoothed trend of benchmark counts per model release.")
    parser.add_argument(
        "--as-of",
        help="Include model releases on or before this date (YYYY-MM-DD). Defaults to the latest release date in data/models.csv.",
    )
    parser.add_argument("--window-days", type=int, default=90, help="Moving-average smoothing window size in days.")
    parser.add_argument(
        "--output",
        default="assets/benchmark_count_per_release.png",
        help="Output image path.",
    )
    parser.add_argument(
        "--strict-resolution",
        action="store_true",
        help="Fail if any non-empty benchmark mention does not resolve by exact name or explicit alias.",
    )
    return parser.parse_args()


def build_release_counts(models_df, as_of, resolver=None, strict_resolution=False):
    resolver = resolver or CanonicalResolver.from_files(BENCHMARKS_PATH, ALIAS_PATH if ALIAS_PATH.exists() else None)
    rows = []
    unresolved = []

    for _, model in models_df.fillna("").iterrows():
        release_date = pd.to_datetime(model.get("release date", ""), errors="raise").normalize()
        if release_date > as_of:
            continue

        raw_mentions = split_benchmarks(model.get("benchmarks", ""))
        resolved_ids = []
        for raw_mention in raw_mentions:
            resolution = resolver.resolve(raw_mention)
            if resolution:
                resolved_ids.append(resolution.benchmark_id)
            else:
                unresolved.append((model.get("Model name", ""), raw_mention))

        rows.append(
            {
                "Provider": str(model.get("Provider", "")).strip(),
                "Model": str(model.get("Model name", "")).strip(),
                "Date": release_date,
                "BenchmarkCount": len(set(resolved_ids)),
                "RawMentionCount": len(raw_mentions),
                "ResolvedMentionCount": len(resolved_ids),
            }
        )

    warn_unresolved(
        unresolved,
        strict_resolution,
        resolution_hint="Add canonical benchmark rows or explicit aliases to resolve them.",
        sample_separator="; ",
    )
    return pd.DataFrame(rows)


def smooth_counts(counts_df, as_of, window_days):
    if counts_df.empty:
        return pd.DataFrame(columns=["Date", "SmoothedBenchmarkCount"])

    daily_index = pd.date_range(counts_df["Date"].min(), as_of, freq="D")
    daily = (
        counts_df.groupby("Date")
        .agg(total_benchmarks=("BenchmarkCount", "sum"), release_count=("BenchmarkCount", "size"))
        .reindex(daily_index, fill_value=0)
    )
    rolling_totals = daily["total_benchmarks"].rolling(window_days, min_periods=1).sum()
    rolling_releases = daily["release_count"].rolling(window_days, min_periods=1).sum()
    rolling_average = (rolling_totals / rolling_releases.where(rolling_releases > 0)).ffill()
    smoothed = rolling_average.ewm(span=30, adjust=False).mean()

    return pd.DataFrame(
        {
            "Date": daily_index,
            "SmoothedBenchmarkCount": smoothed.fillna(0).to_numpy(),
        }
    )


def generate_graph(
    as_of=None,
    window_days=180,
    output_path="assets/benchmark_count_per_release.png",
    strict_resolution=False,
):
    window_days = validate_window_days(window_days)
    models_df = load_models()
    if as_of is None:
        as_of = latest_release_date(models_df)

    counts = build_release_counts(models_df, as_of, strict_resolution=strict_resolution)
    if counts.empty:
        print("No model releases found.")
        return

    counts = counts.sort_values(["Date", "Provider", "Model"])
    trend = smooth_counts(counts, as_of, window_days)

    fig, ax = plt.subplots(figsize=(16, 9))
    providers = sorted(counts["Provider"].dropna().unique())
    palette = dict(zip(providers, sns.color_palette("Set2", n_colors=len(providers))))

    for provider in providers:
        provider_counts = counts[counts["Provider"] == provider]
        ax.scatter(
            provider_counts["Date"],
            provider_counts["BenchmarkCount"],
            s=85,
            alpha=0.82,
            color=palette[provider],
            edgecolor="white",
            linewidth=0.8,
            label=provider,
            zorder=3,
        )

    ax.plot(
        trend["Date"],
        trend["SmoothedBenchmarkCount"],
        color="#222222",
        linewidth=3,
        label=f"{window_days}-day moving average",
        zorder=4,
    )

    ax.set_title(
        f"Benchmarks Mentioned per Model Release (as of {as_of.date()})",
        fontsize=20,
        weight="bold",
        pad=18,
    )
    ax.set_ylabel("Unique resolved benchmarks per release", fontsize=13, labelpad=10)
    ax.set_xlabel("Release Date", fontsize=13, labelpad=10)
    ax.yaxis.set_major_locator(mtick.MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.45)
    ax.grid(False, axis="x")

    min_date = counts["Date"].min() - pd.Timedelta(days=45)
    max_date = max(counts["Date"].max(), as_of) + pd.Timedelta(days=45)
    ax.set_xlim(min_date, max_date)
    ax.set_ylim(bottom=0)
    plt.xticks(rotation=45, ha="right")

    ax.legend(loc="upper left", frameon=False, ncol=2, fontsize=10)
    fig.tight_layout()
    save_figure(fig, output_path)
    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    generate_graph(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        output_path=args.output,
        strict_resolution=args.strict_resolution,
    )
