from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import seaborn as sns

from scripts.analysis_utils import create_analysis_parser
from scripts.plot_utils import (
    MODE_ORDER,
    build_model_facet_events,
    configure_plot_style,
    latest_release_date,
    load_benchmark_facets,
    load_models,
    parse_as_of,
    save_figure,
)


configure_plot_style()

PARSER = create_analysis_parser(
    "Generate the benchmark evolution timeline.",
    output="assets/benchmark_evolution.png",
    strict_resolution=True,
)


def process_data(models_df, facets_df, as_of=None, strict_resolution=False):
    category_cols = MODE_ORDER
    events = build_model_facet_events(
        models_df,
        facets_df,
        ["headline_task_mode"],
        as_of,
        strict_resolution=strict_resolution,
    )

    if events.empty:
        return pd.DataFrame(), category_cols

    models_data = []
    for (_, model_name, provider, date), group in events.groupby(
        ["model_key", "Model", "Provider", "Date"], sort=False
    ):
        category_weights = group.groupby("Category")["Weight"].sum()
        total_weight = category_weights.sum()
        ratios = (
            [category_weights.get(category, 0.0) / total_weight for category in category_cols]
            if total_weight > 0
            else [0] * len(category_cols)
        )
        models_data.append(
            {
                "Model": model_name,
                "Provider": provider,
                "Date": date,
                "Ratios": ratios,
                # Pie size reflects resolved release-page benchmarks, not only
                # the subset that has a headline projection row.
                "TotalHits": int(group["resolved_mentions_on_release"].max()),
            }
        )

    return pd.DataFrame(models_data), category_cols


def generate_graph(as_of=None, output_path="assets/benchmark_evolution.png", strict_resolution=False):
    models_df_raw = load_models()
    facets_df = load_benchmark_facets(add_headline_projection=True)
    if as_of is None:
        as_of = latest_release_date(models_df_raw)

    df, cat_cols = process_data(models_df_raw, facets_df, as_of=as_of, strict_resolution=strict_resolution)

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

    min_date = df["Date"].min() - pd.to_timedelta(60, unit="D")
    max_date = max(df["Date"].max(), as_of) + pd.to_timedelta(60, unit="D")
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
    save_figure(fig, output_path)


if __name__ == "__main__":
    args = PARSER.parse_args()
    generate_graph(
        as_of=parse_as_of(args.as_of),
        output_path=args.output,
        strict_resolution=args.strict_resolution,
    )
