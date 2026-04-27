import argparse
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import seaborn as sns

try:
    from taxonomy_utils import CanonicalResolver, benchmark_id as canonical_benchmark_id
except ImportError:
    from scripts.taxonomy_utils import CanonicalResolver, benchmark_id as canonical_benchmark_id

sns.set_theme(style="whitegrid")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]

TAXONOMY_PATH = Path("data/benchmark_catalog.csv")
ALIAS_PATH = Path("data/benchmark_aliases.csv")

MODE_ORDER = [
    "Agentic",
    "Multimodal Perception",
    "Generative Reasoning",
    "Constraint Satisfaction",
    "Knowledge Retrieval",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the benchmark evolution timeline.")
    parser.add_argument(
        "--as-of",
        help="Include model releases on or before this date (YYYY-MM-DD). Defaults to the latest release date in data/models.csv.",
    )
    parser.add_argument(
        "--output",
        default="assets/benchmark_evolution.png",
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


def process_data(models_df, taxonomy_df, as_of=None, strict_resolution=False):
    mode_lookup = build_mode_lookup(taxonomy_df)
    category_cols = MODE_ORDER
    unresolved = []

    models_data = []
    for _, row in models_df.iterrows():
        model_name = row.get("Model name")
        if pd.isna(model_name):
            continue

        provider = row.get("Provider")
        date_str = row.get("release date")
        date = pd.to_datetime(date_str)
        if as_of is not None and date > as_of:
            continue

        bench_list = split_benchmarks(row.get("benchmarks", ""))

        cat_counts = {c: 0 for c in category_cols}
        total_hits = 0

        for bench in bench_list:
            mode = find_mode(bench, mode_lookup)
            if mode and mode in cat_counts:
                cat_counts[mode] += 1
                total_hits += 1
            elif bench:
                unresolved.append((str(model_name), bench))

        ratios = [cat_counts[c] / total_hits for c in category_cols] if total_hits > 0 else [0] * len(category_cols)

        models_data.append(
            {
                "Model": model_name,
                "Provider": provider,
                "Date": date,
                "Ratios": ratios,
                "TotalHits": total_hits,
            }
        )

    warn_unresolved(unresolved, strict_resolution)
    return pd.DataFrame(models_data), category_cols


def generate_graph(as_of=None, output_path="assets/benchmark_evolution.png", strict_resolution=False):
    models_df_raw, taxonomy_df = load_data()
    if as_of is None:
        as_of = pd.to_datetime(models_df_raw["release date"]).max().normalize()

    df, cat_cols = process_data(models_df_raw, taxonomy_df, as_of=as_of, strict_resolution=strict_resolution)

    if df.empty:
        print("No data.")
        return

    df = df.sort_values("Date")

    fig, ax = plt.subplots(figsize=(16, 9))

    providers = sorted(df["Provider"].dropna().unique())
    y_map = {p: i for i, p in enumerate(providers)}

    colors = sns.color_palette("Set2", n_colors=len(cat_cols))

    ax.set_title(
        f"Evolution of Frontier Model Benchmarks by Task Mode (as of {as_of.date()})",
        fontsize=20,
        weight="bold",
        pad=20,
    )
    ax.set_xlabel("Release Date", fontsize=14, labelpad=10)

    for p in providers:
        y = y_map[p]
        ax.axhline(y, color="gray", alpha=0.3, linestyle="-", linewidth=1.5, zorder=1)

    ax.set_yticks(range(len(providers)))
    ax.set_yticklabels(providers, fontsize=14, fontweight="bold")
    ax.tick_params(axis="y", length=0)

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45, fontsize=10)

    min_date = df["Date"].min() - pd.Timedelta(days=60)
    max_date = max(df["Date"].max(), as_of) + pd.Timedelta(days=60)
    ax.set_xlim(min_date, max_date)
    ax.set_ylim(-0.8, len(providers) - 0.2)

    pie_history = {p: [] for p in providers}
    pie_close_threshold = 15
    pie_x_offset = 8

    for idx, row in df.iterrows():
        provider = row["Provider"]
        y_val = y_map[provider]
        date_val = row["Date"]
        x_val = mdates.date2num(date_val)
        ratios = row["Ratios"]

        close = [p for p in pie_history[provider] if abs(x_val - p) < pie_close_threshold]
        offset_days = pie_x_offset * len(close)
        adjusted_x = x_val + offset_days
        pie_history[provider].append(adjusted_x)

        if sum(ratios) == 0:
            ax.scatter(mdates.num2date(adjusted_x), y_val, s=100, color="#cccccc", zorder=3)
        else:
            sub_ax = inset_axes(
                ax,
                width=0.55,
                height=0.55,
                loc="center",
                bbox_to_anchor=(adjusted_x, y_val),
                bbox_transform=ax.transData,
                borderpad=0,
            )
            sub_ax.pie(ratios, colors=colors, startangle=90)
            sub_ax.set_aspect("equal")
            sub_ax.axis("off")

        offset_y = 30 if idx % 2 == 0 else -35
        ax.annotate(
            row["Model"],
            (mdates.num2date(adjusted_x), y_val),
            xytext=(0, offset_y),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8, ec="none"),
            arrowprops=dict(arrowstyle="-", color="gray", alpha=0.5),
        )

    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=12, label=cat)
        for cat, c in zip(cat_cols, colors)
    ]

    ax.legend(
        handles=legend_handles,
        title="Task Mode",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=False,
        fontsize=11,
        title_fontsize=12,
    )

    plt.subplots_adjust(bottom=0.2)
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Graph generated at {output_path}")


if __name__ == "__main__":
    args = parse_args()
    generate_graph(
        as_of=parse_as_of(args.as_of),
        output_path=args.output,
        strict_resolution=args.strict_resolution,
    )
