import argparse
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns

try:
    from taxonomy_utils import CanonicalResolver, benchmark_id as canonical_benchmark_id
except ImportError:
    from scripts.taxonomy_utils import CanonicalResolver, benchmark_id as canonical_benchmark_id

sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]

TAXONOMY_PATH = Path("data/benchmark_taxonomy_v2.csv")
ALIAS_PATH = Path("data/benchmark_aliases.csv")

MODE_ORDER = [
    "Agentic",
    "Multimodal Perception",
    "Generative Reasoning",
    "Constraint Satisfaction",
    "Knowledge Retrieval",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the rolling benchmark task-mode trend chart.")
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
        default="assets/benchmark_growth.png",
        help="Output image path.",
    )
    parser.add_argument(
        "--strict-resolution",
        action="store_true",
        help="Fail if any benchmark mention does not resolve by exact name or explicit alias.",
    )
    return parser.parse_args()


def load_data():
    models_df = pd.read_csv("data/models.csv")
    taxonomy_df = pd.read_csv(TAXONOMY_PATH)
    return models_df, taxonomy_df


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


def build_mode_lookup(taxonomy_df):
    exact_lookup = {}
    by_id = {}
    for _, row in taxonomy_df.iterrows():
        name = str(row.get("benchmark_name", "")).strip()
        mode = str(row.get("task_mode", "")).strip()
        if not name or not mode:
            continue

        if canonical_benchmark_id is not None:
            by_id[canonical_benchmark_id(name)] = mode

        for alias in benchmark_aliases(name):
            exact_lookup[alias] = mode

    resolver = None
    if CanonicalResolver is not None and ALIAS_PATH.exists():
        resolver = CanonicalResolver.from_files(TAXONOMY_PATH, ALIAS_PATH)

    return {"by_id": by_id, "exact": exact_lookup, "resolver": resolver}


def find_mode(benchmark_name, lookup):
    resolver = lookup.get("resolver")
    if resolver is not None:
        resolution = resolver.resolve(benchmark_name)
        if not resolution:
            return ""
        return lookup["by_id"].get(resolution.benchmark_id, "")

    return lookup["exact"].get(normalize_name(benchmark_name), "")


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


def generate_trend_graph(as_of=None, window_days=180, output_path="assets/benchmark_growth.png", strict_resolution=False):
    window_days = validate_window_days(window_days)
    models_df, taxonomy_df = load_data()
    if as_of is None:
        as_of = pd.to_datetime(models_df["release date"]).max().normalize()

    mode_lookup = build_mode_lookup(taxonomy_df)

    events = []
    unresolved = []
    for _, row in models_df.iterrows():
        date = pd.to_datetime(row["release date"])
        if date > as_of:
            continue

        benchmarks = split_benchmarks(row.get("benchmarks", ""))
        if not benchmarks:
            continue

        resolved_modes = []
        for bench in benchmarks:
            mode = find_mode(bench, mode_lookup)
            if mode:
                resolved_modes.append(mode)
            else:
                unresolved.append((str(row.get("Model name", "")), bench))

        if not resolved_modes:
            continue

        weight = 1.0 / len(resolved_modes)
        for mode in resolved_modes:
            events.append({"Date": date, "Category": mode, "Weight": weight})

    warn_unresolved(unresolved, strict_resolution)

    events_df = pd.DataFrame(events)
    if events_df.empty:
        print("No events found.")
        return

    min_date = events_df["Date"].min()
    date_range = pd.date_range(start=min_date, end=as_of, freq="D")

    daily_counts = events_df.groupby(["Date", "Category"])["Weight"].sum().unstack(fill_value=0)
    daily_counts = daily_counts.reindex(date_range, fill_value=0)

    category_cols = MODE_ORDER
    for c in category_cols:
        if c not in daily_counts.columns:
            daily_counts[c] = 0
    daily_counts = daily_counts[category_cols]

    rolling_data = daily_counts.rolling(window=window_days, min_periods=1).sum()
    trend_data = rolling_data.div(rolling_data.sum(axis=1), axis=0).ffill().fillna(0)

    for col in trend_data.columns:
        trend_data[col] = trend_data[col].ewm(span=30, adjust=False).mean()
    trend_data = trend_data.div(trend_data.sum(axis=1), axis=0).fillna(0)

    fig, ax = plt.subplots(figsize=(16, 9))
    colors = sns.color_palette("Set2", n_colors=len(category_cols))

    x = trend_data.index
    y = [trend_data[col] for col in category_cols]
    ax.stackplot(x, y, labels=category_cols, colors=colors, alpha=0.9)

    ax.set_title(
        f"Evolution of Benchmark Task Modes (Rolling {window_days}-day, as of {as_of.date()})",
        fontsize=20,
        weight="bold",
        pad=20,
    )
    ax.set_ylabel("Proportion of New Benchmarks", fontsize=14, labelpad=10)
    ax.set_xlabel("Time", fontsize=14, labelpad=10)

    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left", fontsize=12, title="Task Mode", bbox_to_anchor=(1.02, 1))

    ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.5)
    ax.grid(False, axis="x")

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)

    ax.set_xlim(min_date, as_of)
    ax.set_ylim(0, 1.0)
    plt.tight_layout()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Graph generated at {output_path}")


if __name__ == "__main__":
    args = parse_args()
    generate_trend_graph(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        output_path=args.output,
        strict_resolution=args.strict_resolution,
    )
