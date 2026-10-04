from __future__ import annotations

import textwrap

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.offsetbox import AnnotationBbox, DrawingArea
from matplotlib.patches import Circle, Wedge
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
    split_benchmarks,
)


configure_plot_style()

PARSER = create_analysis_parser(
    "Generate the benchmark evolution timeline.",
    output="assets/benchmark_evolution.png",
    strict_resolution=True,
)
PARSER.add_argument("--detail-output", default=None, help="Optional fully labeled model-row timeline image.")


def process_data(models_df, facets_df, as_of=None, strict_resolution=False):
    """Keep every scoped inventory row; pie ratios retain the legacy weighting.

    Ratios are conditional on mentions with a headline projection. Coverage is
    the projected weight before that final normalization, not a confidence score.
    """
    category_cols = MODE_ORDER
    as_of = latest_release_date(models_df) if as_of is None else pd.Timestamp(as_of).normalize()
    scoped_models = models_df.copy().fillna("")
    scoped_models["release_date"] = pd.to_datetime(scoped_models["release date"], errors="raise").dt.normalize()
    scoped_models = scoped_models.loc[scoped_models["release_date"] <= as_of].copy()
    # A timeline entry is an inventory row, even when names/dates/pages match.
    scoped_models["model_key"] = [f"timeline-row-{i}" for i in range(len(scoped_models))]
    events = build_model_facet_events(
        scoped_models,
        facets_df,
        ["headline_task_mode"],
        as_of,
        strict_resolution=strict_resolution,
    )

    models_data = []
    groups = {key: group for key, group in events.groupby("model_key", sort=False)}
    for model in scoped_models.to_dict("records"):
        group = groups.get(model["model_key"], events.iloc[:0])
        category_weights = group.groupby("Category")["Weight"].sum()
        total_weight = category_weights.sum()
        ratios = (
            [category_weights.get(category, 0.0) / total_weight for category in category_cols]
            if total_weight > 0
            else [0] * len(category_cols)
        )
        models_data.append(
            {
                "Model": model["Model name"],
                "Provider": model["Provider"],
                "Date": model["release_date"],
                "Ratios": ratios,
                "ProjectionCoverage": float(total_weight),
                "RawMentionCount": len(split_benchmarks(model["benchmarks"])),
                "TotalHits": int(group["resolved_mentions_on_release"].max()) if not group.empty else 0,
                "Status": (
                    "empty" if not split_benchmarks(model["benchmarks"])
                    else "unclassified" if total_weight == 0
                    else "partial" if total_weight < 1 - 1e-9
                    else "projected"
                ),
            }
        )

    return pd.DataFrame(models_data, columns=[
        "Model", "Provider", "Date", "Ratios", "ProjectionCoverage",
        "RawMentionCount", "TotalHits", "Status",
    ]), category_cols


def assign_collision_lanes(frame, separation_days, footprint_col=None):
    """Place nearby labels in separate vertical lanes without changing dates.

    The caller chooses the horizontal footprint of a wrapped label. The first
    available lane is reused only after that footprint clears the prior entry.
    """
    if separation_days <= 0:
        raise ValueError("separation_days must be positive")
    layout = frame.sort_values(["Provider", "Date", "Model"], kind="stable").copy()
    lanes = []
    lane_ends_by_provider = {}
    for row in layout.itertuples(index=False):
        date_number = mdates.date2num(row.Date)
        width = getattr(row, footprint_col) if footprint_col else separation_days
        if width <= 0:
            raise ValueError("All horizontal footprints must be positive")
        start, end = date_number - width / 2, date_number + width / 2
        lane_ends = lane_ends_by_provider.setdefault(row.Provider, [])
        lane = next((i for i, prior_end in enumerate(lane_ends) if start >= prior_end), len(lane_ends))
        if lane == len(lane_ends):
            lane_ends.append(end)
        else:
            lane_ends[lane] = end
        lanes.append(lane)
    layout["Lane"] = lanes
    return layout


def _pie_marker(ratios, colors, status, size=23):
    """A fixed-area glyph; its area never encodes benchmark counts."""
    drawing = DrawingArea(size, size, 0, 0)
    center = size / 2
    if status in {"empty", "unclassified"}:
        drawing.add_artist(Circle(
            (center, center), center - 1,
            facecolor="white" if status == "empty" else "#d9dde2",
            edgecolor="#64748b", linewidth=1,
            hatch=None if status == "empty" else "///",
        ))
    else:
        angle = 90
        for ratio, color in zip(ratios, colors):
            if ratio > 0:
                drawing.add_artist(Wedge(
                    (center, center), center - 1, angle, angle + 360 * ratio,
                    facecolor=color, edgecolor="white", linewidth=0.45,
                ))
                angle += 360 * ratio
    return drawing


def select_name_labels(frame):
    """Name the first row per provider/year and the latest row per provider.

    Name breaks same-day ties deterministically; selection never hides markers.
    """
    ordered = frame.sort_values(["Provider", "Date", "Model"], kind="stable").copy()
    selected = ordered.groupby([ordered["Provider"], ordered["Date"].dt.year], sort=False).head(1).index
    latest = ordered.groupby("Provider", sort=False).tail(1).index
    return frame.index.isin(selected.union(latest))


def generate_graph(as_of=None, output_path="assets/benchmark_evolution.png", strict_resolution=False, detail_output=None):
    models_df_raw = load_models()
    facets_df = load_benchmark_facets(add_headline_projection=True)
    if as_of is None:
        as_of = latest_release_date(models_df_raw)
    as_of = pd.Timestamp(as_of).normalize()

    df, cat_cols = process_data(models_df_raw, facets_df, as_of=as_of, strict_resolution=strict_resolution)

    _draw_timeline(df, cat_cols, as_of, output_path, detail=False)
    if detail_output:
        _draw_timeline(df, cat_cols, as_of, detail_output, detail=True)


def _draw_timeline(df, cat_cols, as_of, output_path, detail=False):
    if df.empty:
        fig, ax = plt.subplots(figsize=(12, 3.5))
        ax.axis("off")
        ax.text(0.5, 0.6, "No model release rows at this cutoff", ha="center", fontsize=18, weight="bold")
        ax.text(0.5, 0.4, f"As of {as_of.date()} · later inventory rows are excluded", ha="center", fontsize=12)
        save_figure(fig, output_path)
        plt.close(fig)
        return

    providers = sorted(df["Provider"].dropna().unique())
    colors = sns.color_palette("Set2", n_colors=len(cat_cols))
    min_date = pd.Timestamp(df["Date"].min()) - pd.DateOffset(days=70)
    max_date = pd.Timestamp(max(df["Date"].max(), as_of)) + pd.DateOffset(days=70)
    # Seventeen-character wrapped labels occupy at most about 90 points. Add
    # padding; convert that footprint to days on the shared 14-inch plotting area.
    points_to_days = (max_date - min_date).days / (14 * 72)
    prepared = df.copy()
    prepared["ShowLabel"] = True if detail else select_name_labels(prepared)
    prepared["FootprintDays"] = (105 if detail else 30) * points_to_days
    layout = assign_collision_lanes(prepared, 30 * points_to_days, footprint_col="FootprintDays")
    lane_counts = [int(layout.loc[layout["Provider"] == provider, "Lane"].max()) + 1 for provider in providers]
    if not detail:
        name_layout = assign_collision_lanes(prepared.loc[prepared["ShowLabel"]], 105 * points_to_days)
        layout["NameLabelLane"] = name_layout["Lane"].reindex(layout.index)
        label_lane_counts = [int(name_layout.loc[name_layout["Provider"] == provider, "Lane"].max()) + 1 for provider in providers]
        panel_heights = [0.25 + count * 0.34 + label_count * 0.50
                         for count, label_count in zip(lane_counts, label_lane_counts)]
    else:
        label_lane_counts = [0] * len(providers)
        panel_heights = [0.5 + count * 0.98 for count in lane_counts]
    height = sum(panel_heights) + (2.7 if detail else 2.4)
    fig, axes = plt.subplots(
        len(providers), 1, figsize=(16, height), sharex=True,
        gridspec_kw={"height_ratios": panel_heights}, squeeze=False,
    )
    fig.subplots_adjust(left=0.055, right=0.96, top=1 - 0.6 / height,
                        bottom=1.85 / height, hspace=0.2)
    fig.suptitle(
        f"Model releases and reported benchmark mix · as of {as_of.date()}",
        fontsize=19, weight="bold", y=1 - 0.13 / height,
    )
    for ax, provider, lane_count, label_lane_count in zip(axes[:, 0], providers, lane_counts, label_lane_counts):
        ax.set_title(provider, loc="left", fontsize=13, weight="bold", pad=3)
        ax.axhline(0, color="#94a3b8", linewidth=1, zorder=1)
        ax.set_xlim(min_date, max_date)
        ax.set_ylim(-0.16, lane_count + label_lane_count * 1.5 + 0.2)
        ax.set_yticks([])
        ax.grid(axis="x", color="#dbe2e8", linewidth=0.65)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for row in layout.loc[layout["Provider"] == provider].itertuples(index=False):
            y = row.Lane + (0.76 if detail else 0.5)
            ax.plot([row.Date, row.Date], [0, y], color="#cbd5e1", linewidth=0.8, zorder=1)
            ax.scatter(row.Date, 0, s=10, color="#64748b", zorder=2)
            ax.add_artist(AnnotationBbox(
                _pie_marker(row.Ratios, colors, row.Status), (row.Date, y),
                frameon=False, pad=0, zorder=3,
            ))
            if not row.ShowLabel:
                continue
            name = textwrap.fill(str(row.Model), width=17, break_long_words=False, break_on_hyphens=False)
            details = row.Date.strftime("%Y-%m-%d")
            if row.Status == "empty":
                details += "\nempty list"
            elif row.Status == "unclassified":
                details += "\nno projection"
            elif row.Status == "partial":
                details += f"\n{row.ProjectionCoverage:.0%} projected"
            label_y = lane_count + row.NameLabelLane * 1.5 + 0.7 if not detail else None
            ax.annotate(
                name + "\n" + details, (row.Date, y),
                xytext=(0, -17) if detail else (row.Date, label_y),
                textcoords="offset points" if detail else "data", ha="center", va="top" if detail else "center", fontsize=8.5,
                linespacing=1.12, zorder=4,
                bbox={"boxstyle": "square,pad=0.12", "facecolor": "white", "edgecolor": "none", "alpha": 0.96},
                arrowprops=None if detail else {"arrowstyle": "-", "color": "#94a3b8", "linewidth": 0.8},
            )
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.tick_params(axis="x", labelsize=9)
    axes[-1, 0].set_xlabel("Actual release date · vertical lanes separate nearby model rows", fontsize=11, labelpad=9)
    legend_handles = [
        Line2D([], [], marker="o", linestyle="none", markerfacecolor=color, markeredgecolor="white",
               markersize=9, label=category)
        for category, color in zip(cat_cols, colors)
    ]
    legend_handles.extend([
        Line2D([], [], marker="o", linestyle="none", markerfacecolor="white", markeredgecolor="#64748b", markersize=9, label="Empty benchmark list"),
        Line2D([], [], marker="o", linestyle="none", markerfacecolor="#d9dde2", markeredgecolor="#64748b", markersize=9, label="Mentions without projection"),
    ])
    fig.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, 0.66 / height), ncol=4,
               frameon=False, fontsize=9, columnspacing=1.8)
    fig.text(0.5, 0.12 / height,
             ("Every model row is shown; selected names label the first row per provider/year and the latest provider row.\n" if not detail else "Every model row is shown and labeled.\n")
             + "Fixed-size markers include joint-page models; area does not encode benchmark counts.\n"
             "Slices show raw resolved mention shares conditional on a taxonomy projection. Active labels include provisional annotations; colors describe reporting, not capability.",
             ha="center", va="bottom", fontsize=8.6, color="#475569", linespacing=1.4)
    save_figure(fig, output_path)
    plt.close(fig)


if __name__ == "__main__":
    args = PARSER.parse_args()
    generate_graph(
        as_of=parse_as_of(args.as_of),
        output_path=args.output,
        strict_resolution=args.strict_resolution,
        detail_output=args.detail_output,
    )
