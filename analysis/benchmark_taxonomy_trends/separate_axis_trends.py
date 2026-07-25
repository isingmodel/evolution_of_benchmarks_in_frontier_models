from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import seaborn as sns

from scripts.analysis_utils import create_analysis_parser
from scripts.plot_utils import (
    DATA_DIR,
    FACET_DOMAIN_ORDER,
    MODE_ORDER,
    build_model_facet_events,
    build_rolling_share_trend,
    configure_plot_style,
    latest_release_date,
    load_benchmark_facets,
    load_models,
    parse_as_of,
    save_figure,
    validate_window_days,
)
from scripts.taxonomy_utils import REVIEW_CONFIDENCE_THRESHOLD


configure_plot_style()

PARSER = create_analysis_parser(
    "Generate separate rolling benchmark trend charts by taxonomy axis.",
    window_days=180,
    output="assets/benchmark_growth_by_all_category.png",
    strict_resolution=True,
)
PARSER.add_argument(
    "--domain-output",
    help="Optional output image path for a standalone domain trend chart.",
)
PARSER.add_argument(
    "--review-debt-output",
    help="Optional output image path for review-debt metrics when v3 facet data exists.",
)


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


def generate_domain_graph(domain_trend, domain_cols, min_date, as_of, window_days, output_path):
    fig, ax = plt.subplots(figsize=(16, 9))
    domain_colors = sns.color_palette("tab20", n_colors=len(domain_cols))
    plot_axis_trend(
        ax,
        domain_trend,
        domain_cols,
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
    facet_path = DATA_DIR / "benchmark_facets.csv"
    if not facet_path.exists():
        print("Review-debt graph skipped: data/benchmark_facets.csv not found.")
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
                "low_confidence_share": (
                    group["classification_confidence"] < REVIEW_CONFIDENCE_THRESHOLD
                ).mean(),
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
    ax.legend(
        [f"Low confidence (<{REVIEW_CONFIDENCE_THRESHOLD:g})", "Needs review or disputed"],
        frameon=False,
    )
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
    models_df = load_models()
    facets_df = load_benchmark_facets(add_headline_projection=True)
    if as_of is None:
        as_of = latest_release_date(models_df)

    events = build_model_facet_events(
        models_df,
        facets_df,
        ["headline_task_mode", "domain"],
        as_of,
        strict_resolution=strict_resolution,
    )
    mode_events = events[events["facet_axis"] == "headline_task_mode"].copy()
    domain_events = events[events["facet_axis"] == "domain"].copy()

    mode_trend, mode_min_date = build_rolling_share_trend(mode_events, as_of, window_days, MODE_ORDER)
    domain_trend, domain_min_date = build_rolling_share_trend(domain_events, as_of, window_days, FACET_DOMAIN_ORDER)

    if mode_trend.empty and domain_trend.empty:
        print("No events found.")
        return

    fig, axes = plt.subplots(2, 1, figsize=(16, 13), sharex=True)
    mode_colors = sns.color_palette("Set2", n_colors=len(MODE_ORDER))
    domain_colors = sns.color_palette("tab20", n_colors=len(FACET_DOMAIN_ORDER))

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
        FACET_DOMAIN_ORDER,
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
        generate_domain_graph(domain_trend, FACET_DOMAIN_ORDER, domain_min_date, as_of, window_days, domain_output_path)

    if review_debt_output_path:
        generate_review_debt_graph(review_debt_output_path)


if __name__ == "__main__":
    args = PARSER.parse_args()
    generate_trend_graph(
        as_of=parse_as_of(args.as_of),
        window_days=args.window_days,
        output_path=args.output,
        domain_output_path=args.domain_output,
        review_debt_output_path=args.review_debt_output,
        strict_resolution=args.strict_resolution,
    )
