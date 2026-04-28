import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns

if __package__:
    from .plot_utils import (
        MODE_ORDER,
        build_legacy_taxonomy_lookup,
        build_rolling_share_trend,
        configure_plot_style,
        latest_release_date,
        load_models_and_benchmarks,
        parse_as_of,
        save_figure,
        split_benchmarks,
        validate_window_days,
        warn_unresolved,
    )
else:
    from plot_utils import (
        MODE_ORDER,
        build_legacy_taxonomy_lookup,
        build_rolling_share_trend,
        configure_plot_style,
        latest_release_date,
        load_models_and_benchmarks,
        parse_as_of,
        save_figure,
        split_benchmarks,
        validate_window_days,
        warn_unresolved,
    )


configure_plot_style()


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


def generate_trend_graph(as_of=None, window_days=180, output_path="assets/benchmark_growth.png", strict_resolution=False):
    window_days = validate_window_days(window_days)
    models_df, benchmarks_df = load_models_and_benchmarks()
    if as_of is None:
        as_of = latest_release_date(models_df)

    taxonomy_lookup = build_legacy_taxonomy_lookup(benchmarks_df)

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
            taxonomy = taxonomy_lookup.resolve(bench)
            mode = taxonomy.mode if taxonomy else ""
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

    category_cols = MODE_ORDER
    trend_data, min_date = build_rolling_share_trend(events_df, as_of, window_days, category_cols)

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

    save_figure(fig, output_path)
    plt.close(fig)


if __name__ == "__main__":
    args = parse_args()
    generate_trend_graph(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        output_path=args.output,
        strict_resolution=args.strict_resolution,
    )
