from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns

from scripts.analysis_utils import create_analysis_parser
from scripts.plot_utils import (
    MODE_ORDER,
    build_model_facet_events,
    build_rolling_share_trend,
    configure_plot_style,
    draw_rolling_composition,
    latest_release_date,
    load_benchmark_facets,
    load_models,
    parse_as_of,
    save_figure,
    set_rolling_date_limits,
    validate_window_days,
)


configure_plot_style()

PARSER = create_analysis_parser(
    "Generate the rolling benchmark task-mode trend chart.",
    window_days=180,
    output="assets/benchmark_growth.png",
    strict_resolution=True,
)


def generate_trend_graph(as_of=None, window_days=180, output_path="assets/benchmark_growth.png", strict_resolution=False):
    window_days = validate_window_days(window_days)
    models_df = load_models()
    facets_df = load_benchmark_facets(add_headline_projection=True)
    if as_of is None:
        as_of = latest_release_date(models_df)

    events_df = build_model_facet_events(
        models_df,
        facets_df,
        ["headline_task_mode"],
        as_of,
        strict_resolution=strict_resolution,
    )
    category_cols = MODE_ORDER
    trend_data, min_date = build_rolling_share_trend(events_df, as_of, window_days, category_cols)

    fig, ax = plt.subplots(figsize=(16, 9))
    colors = sns.color_palette("Set2", n_colors=len(category_cols))

    ax.set_title(
        f"Benchmark Task-Mode Projection (Trailing {window_days}-day, as of {as_of.date()})",
        fontsize=20,
        weight="bold",
        pad=20,
    )
    if trend_data.empty:
        ax.text(0.5, 0.5, "No covered task-mode mentions at this cutoff.",
                transform=ax.transAxes, ha="center", va="center", fontsize=14)
        ax.set_axis_off()
    else:
        draw_rolling_composition(ax, trend_data, category_cols, colors)
        ax.set_ylabel("Share of covered model-row weight", fontsize=14, labelpad=10)
        ax.set_xlabel("Time", fontsize=14, labelpad=10)

        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc="upper left", fontsize=12, title="Task-mode projection", bbox_to_anchor=(1.02, 1))

        ax.grid(True, which="major", axis="y", linestyle="--", alpha=0.5)
        ax.grid(False, axis="x")

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=45)

        set_rolling_date_limits(ax, min_date, as_of)
        ax.set_ylim(0, 1.0)
    fig.text(
        0.01, 0.005,
        "Each benchmark-bearing model row has one unit split across recorded mentions; repeat appearances count. Joint variants contribute separately.\n"
        "Shares normalize covered label weight within each trailing window. Empty windows remain gaps; no extra smoothing. Active labels include provisional annotations.\n"
        "Task mode is a priority projection, not the strict interaction-tag measure. Vertical snapshot glyphs mark isolated covered dates.",
        fontsize=9, color="#555555",
    )
    plt.tight_layout(rect=[0, 0.08, 1, 1])

    save_figure(fig, output_path)
    plt.close(fig)


if __name__ == "__main__":
    args = PARSER.parse_args()
    generate_trend_graph(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        output_path=args.output,
        strict_resolution=args.strict_resolution,
    )
