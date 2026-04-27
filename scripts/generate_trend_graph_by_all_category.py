import argparse
import os
from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from taxonomy_utils import CanonicalResolver, benchmark_id as canonical_benchmark_id

sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]

BENCHMARKS_PATH = Path("data/benchmarks.csv")
ALIAS_PATH = Path("data/benchmark_aliases.csv")

MODE_ORDER = [
    "Agentic",
    "Multimodal Perception",
    "Generative Reasoning",
    "Constraint Satisfaction",
    "Knowledge Retrieval",
]

DOMAIN_ORDER = [
    "STEM/Math",
    "Coding/Engineering",
    "General/Commonsense",
    "Specialized (Law/Bio/Finance)",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate separate rolling benchmark trend charts by taxonomy axis.")
    parser.add_argument(
        "--as-of",
        help="Include model releases on or before this date (YYYY-MM-DD). Defaults to the latest release date in data/models.csv.",
    )
    parser.add_argument(
        "--window-days",
        type=int,
        default=180,
        help="Rolling window size in days.",
    )
    parser.add_argument(
        "--output",
        default="assets/benchmark_growth_by_all_category.png",
        help="Output image path for the combined separate-axis chart.",
    )
    parser.add_argument(
        "--domain-output",
        help="Optional output image path for a standalone domain trend chart.",
    )
    parser.add_argument(
        "--review-debt-output",
        help="Optional output image path for review-debt metrics when v3 facet data exists.",
    )
    parser.add_argument(
        "--strict-resolution",
        action="store_true",
        help="Fail if any benchmark mention does not resolve by exact name or explicit alias.",
    )
    return parser.parse_args()


def load_data():
    models_df = pd.read_csv("data/models.csv")
    benchmarks_df = pd.read_csv(BENCHMARKS_PATH)
    return models_df, benchmarks_df


def normalize_name(value):
    return str(value).strip().casefold()


def benchmark_aliases(name):
    normalized = normalize_name(name)
    aliases = {normalized} if normalized else set()

    # Current v2 data encodes explicit alternatives as slash-separated names,
    # e.g. "MMLU / MMLU-Pro". Do not infer substring aliases beyond this.
    if "/" in normalized:
        aliases.update(part.strip() for part in normalized.split("/") if part.strip())

    return aliases


def build_lookup(benchmarks_df):
    exact_lookup = {}
    by_id = {}
    for _, row in benchmarks_df.iterrows():
        name = str(row.get("benchmark_name", "")).strip()
        mode = str(row.get("legacy_task_mode", "") or row.get("task_mode", "")).strip()
        domain = str(row.get("legacy_task_domain", "") or row.get("task_domain", "")).strip()
        if not name:
            continue

        benchmark_id = str(row.get("benchmark_id", "")).strip()
        if not benchmark_id and canonical_benchmark_id is not None:
            benchmark_id = canonical_benchmark_id(name)
        if benchmark_id:
            by_id[benchmark_id] = {"mode": mode, "domain": domain}

        for alias in benchmark_aliases(name):
            exact_lookup[alias] = {"mode": mode, "domain": domain}

    resolver = None
    if CanonicalResolver is not None and ALIAS_PATH.exists():
        resolver = CanonicalResolver.from_files(BENCHMARKS_PATH, ALIAS_PATH)

    return {"by_id": by_id, "exact": exact_lookup, "resolver": resolver}


def find_taxonomy(benchmark_name, lookup):
    resolver = lookup.get("resolver")
    if resolver is not None:
        resolution = resolver.resolve(benchmark_name)
        if not resolution:
            return None
        return lookup["by_id"].get(resolution.benchmark_id)

    return lookup["exact"].get(normalize_name(benchmark_name))


def split_benchmarks(value):
    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text or text.casefold() == "nan":
        return []

    return [b.strip() for b in text.split(",") if b.strip()]


def parse_as_of(value):
    if not value:
        return None

    parsed = pd.to_datetime(value, errors="raise")
    return parsed.normalize()


def validate_window_days(window_days):
    if window_days <= 0:
        raise ValueError("--window-days must be a positive integer.")
    return window_days


def warn_unresolved(unresolved, strict_resolution):
    if not unresolved:
        return

    sample = ", ".join(sorted({bench for _, bench in unresolved})[:10])
    message = (
        f"Unresolved benchmark mentions skipped ({len(unresolved)}): {sample}. "
        "Add explicit taxonomy/alias rows to resolve them; fuzzy substring matching is disabled."
    )
    if strict_resolution:
        raise ValueError(message)

    print(f"Warning: {message}")


def collect_axis_events(models_df, lookup, as_of):
    mode_events = []
    domain_events = []
    unresolved = []

    for _, row in models_df.iterrows():
        date = pd.to_datetime(row["release date"])
        if date > as_of:
            continue

        benchmarks = split_benchmarks(row.get("benchmarks", ""))
        if not benchmarks:
            continue

        resolved_mentions = []
        for bench in benchmarks:
            tx = find_taxonomy(bench, lookup)
            if not tx:
                unresolved.append((str(row.get("Model name", "")), bench))
                continue
            resolved_mentions.append(tx)

        if not resolved_mentions:
            continue

        base_weight = 1.0 / len(resolved_mentions)
        for tx in resolved_mentions:
            if tx["mode"]:
                mode_events.append({"Date": date, "Category": tx["mode"], "Weight": base_weight})
            if tx["domain"]:
                domain_events.append({"Date": date, "Category": tx["domain"], "Weight": base_weight})

    return pd.DataFrame(mode_events), pd.DataFrame(domain_events), unresolved


def build_trend_data(events_df, category_cols, as_of, window_days):
    if events_df.empty:
        return pd.DataFrame(columns=category_cols), None

    min_date = events_df["Date"].min()
    date_range = pd.date_range(start=min_date, end=as_of, freq="D")

    daily_counts = events_df.groupby(["Date", "Category"])["Weight"].sum().unstack(fill_value=0)
    daily_counts = daily_counts.reindex(date_range, fill_value=0)

    for c in category_cols:
        if c not in daily_counts.columns:
            daily_counts[c] = 0
    daily_counts = daily_counts[category_cols]

    rolling_data = daily_counts.rolling(window=window_days, min_periods=1).sum()
    trend_data = rolling_data.div(rolling_data.sum(axis=1), axis=0).ffill().fillna(0)

    for col in trend_data.columns:
        trend_data[col] = trend_data[col].ewm(span=30, adjust=False).mean()
    trend_data = trend_data.div(trend_data.sum(axis=1), axis=0).fillna(0)

    return trend_data, min_date


def plot_axis_trend(ax, trend_data, category_cols, colors, title, legend_title):
    if trend_data.empty:
        ax.text(0.5, 0.5, "No events found", transform=ax.transAxes, ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        return

    x = trend_data.index
    y = [trend_data[col] for col in category_cols]
    ax.stackplot(x, y, labels=category_cols, colors=colors, alpha=0.9)

    ax.set_title(title, fontsize=16, weight="bold", pad=12)
    ax.set_ylabel("Proportion of New Benchmarks", fontsize=14, labelpad=10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left", fontsize=10, title=legend_title, bbox_to_anchor=(1.02, 1))
    ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.5)
    ax.grid(False, axis="x")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.set_ylim(0, 1.0)


def save_figure(fig, output_path):
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Graph generated at {output_path}")


def generate_domain_graph(domain_trend, min_date, as_of, window_days, output_path):
    fig, ax = plt.subplots(figsize=(16, 9))
    domain_colors = sns.color_palette("Set3", n_colors=len(DOMAIN_ORDER))
    plot_axis_trend(
        ax,
        domain_trend,
        DOMAIN_ORDER,
        domain_colors,
        f"Benchmark Domain Trend (Rolling {window_days}-day, as of {as_of.date()})",
        "Domain",
    )
    if min_date is not None:
        ax.set_xlim(min_date, as_of)
    ax.set_xlabel("Time", fontsize=14, labelpad=10)
    plt.xticks(rotation=45)
    plt.tight_layout()
    save_figure(fig, output_path)
    plt.close(fig)


def generate_review_debt_graph(output_path):
    facet_path = "data/benchmark_facet_edges.csv"
    if not os.path.exists(facet_path):
        print("Review-debt graph skipped: data/benchmark_facet_edges.csv not found.")
        return

    facet_df = pd.read_csv(facet_path)
    required_cols = {"facet_axis", "review_status", "classification_confidence"}
    missing_cols = required_cols - set(facet_df.columns)
    if missing_cols:
        print(f"Review-debt graph skipped: missing columns {sorted(missing_cols)} in {facet_path}.")
        return

    facet_df["classification_confidence"] = pd.to_numeric(facet_df["classification_confidence"], errors="coerce")
    facet_df["review_status"] = facet_df["review_status"].fillna("").str.casefold()
    review_statuses = {"needs_review", "disputed"}

    summary_rows = []
    for facet_axis, group in facet_df.groupby("facet_axis", sort=True):
        summary_rows.append(
            {
                "facet_axis": facet_axis,
                "low_confidence_share": (group["classification_confidence"] < 0.7).mean(),
                "needs_review_or_disputed_share": group["review_status"].isin(review_statuses).mean(),
            }
        )

    if not summary_rows:
        print("Review-debt graph skipped: no facet rows found.")
        return

    summary = pd.DataFrame(summary_rows).set_index("facet_axis")

    fig, ax = plt.subplots(figsize=(14, 7))
    summary.plot(kind="bar", ax=ax, color=["#d95f02", "#7570b3"], width=0.8)
    ax.set_title("Benchmark Classification Review Debt", fontsize=18, weight="bold", pad=16)
    ax.set_xlabel("Facet Axis", fontsize=12)
    ax.set_ylabel("Share of Labels", fontsize=12)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, 1.0)
    ax.legend(["Low confidence (<0.7)", "Needs review or disputed"], frameon=False)
    ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.5)
    ax.grid(False, axis="x")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    save_figure(fig, output_path)
    plt.close(fig)


def generate_trend_graph(
    as_of=None,
    window_days=180,
    output_path="assets/benchmark_growth_by_all_category.png",
    domain_output_path=None,
    review_debt_output_path=None,
    strict_resolution=False,
):
    window_days = validate_window_days(window_days)
    models_df, benchmarks_df = load_data()
    if as_of is None:
        as_of = pd.to_datetime(models_df["release date"]).max().normalize()

    lookup = build_lookup(benchmarks_df)
    mode_events, domain_events, unresolved = collect_axis_events(models_df, lookup, as_of)
    warn_unresolved(unresolved, strict_resolution)

    mode_trend, mode_min_date = build_trend_data(mode_events, MODE_ORDER, as_of, window_days)
    domain_trend, domain_min_date = build_trend_data(domain_events, DOMAIN_ORDER, as_of, window_days)

    if mode_trend.empty and domain_trend.empty:
        print("No events found.")
        return

    fig, axes = plt.subplots(2, 1, figsize=(16, 13), sharex=True)
    mode_colors = sns.color_palette("Set2", n_colors=len(MODE_ORDER))
    domain_colors = sns.color_palette("Set3", n_colors=len(DOMAIN_ORDER))

    plot_axis_trend(
        axes[0],
        mode_trend,
        MODE_ORDER,
        mode_colors,
        f"Task Mode Trend (Rolling {window_days}-day, as of {as_of.date()})",
        "Task Mode",
    )
    plot_axis_trend(
        axes[1],
        domain_trend,
        DOMAIN_ORDER,
        domain_colors,
        f"Domain Trend (Rolling {window_days}-day, as of {as_of.date()})",
        "Domain",
    )

    min_dates = [d for d in [mode_min_date, domain_min_date] if d is not None]
    if min_dates:
        axes[0].set_xlim(min(min_dates), as_of)
        axes[1].set_xlim(min(min_dates), as_of)
    axes[1].set_xlabel("Time", fontsize=14, labelpad=10)
    fig.suptitle(
        "Benchmark Taxonomy Trends by Separate Axes",
        fontsize=20,
        weight="bold",
        y=0.99,
    )
    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    save_figure(fig, output_path)
    plt.close(fig)

    if domain_output_path:
        generate_domain_graph(domain_trend, domain_min_date, as_of, window_days, domain_output_path)

    if review_debt_output_path:
        generate_review_debt_graph(review_debt_output_path)


if __name__ == "__main__":
    args = parse_args()
    generate_trend_graph(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        output_path=args.output,
        domain_output_path=args.domain_output,
        review_debt_output_path=args.review_debt_output,
        strict_resolution=args.strict_resolution,
    )
