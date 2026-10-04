"""Rebuild the project's evidence tables, overview figures, and README."""

from __future__ import annotations

import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from analysis.benchmark_lifecycle.analyze import markdown_table
from analysis.project_overview.metrics import build_overview_tables
from scripts.analysis_utils import create_analysis_parser, default_resolver
from scripts.plot_utils import configure_plot_style, save_figure


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent
EXPORT_TABLES = (
    "coverage_by_provider", "annual_inventory", "sharing_summary",
    "diffusion_horizons", "interaction_classification", "interaction_trends",
    "provider_interaction_trends",
)


def percent(value: object) -> str:
    return "—" if value is None or pd.isna(value) else f"{float(value):.1%}"


def number(value: object) -> str:
    return "—" if value is None or pd.isna(value) else f"{int(value):,}"


def sharing_title(summary: dict) -> str:
    observed = summary["observed_benchmarks"]
    if (observed and summary["shared_benchmarks"] / observed < 0.5
            and summary["shared_mention_share"] > 0.5):
        return "A small shared set accounts for most reporting"
    return "Benchmark sharing across providers"


def plot_sharing(sharing: pd.DataFrame, summary: dict, path: Path) -> None:
    configure_plot_style()
    fig, ax = plt.subplots(figsize=(12, 4.8))
    labels = [
        f"Observed identities\nn = {summary['observed_benchmarks']:,}",
        f"Benchmark–announcement observations\nn = {summary['launch_mentions']:,}",
        f"Equal weight per announcement\nn = {summary['benchmark_bearing_launches']:,}",
    ]
    left = [0.0, 0.0, 0.0]
    colors = ["#c2cbd2", "#5c92ad", "#287a69"]
    for index, row in enumerate(sharing.itertuples(index=False)):
        values = [row.benchmark_share, row.mention_share, row.announcement_weight_share]
        values = [0.0 if pd.isna(value) else float(value) for value in values]
        color = colors[min(index, len(colors) - 1)]
        label = f"{int(row.provider_count)} provider" + ("s" if row.provider_count != 1 else "")
        ax.barh(range(3), values, left=left, height=0.53, color=color, label=label)
        for pos, value in enumerate(values):
            if value > 0.045:
                ax.text(left[pos] + value / 2, pos, percent(value), ha="center", va="center",
                        color="white" if index else "#27343f", weight="bold", fontsize=12)
            left[pos] += value
    ax.set_yticks(range(3), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
    ax.set_xlabel("Share of the observed sample")
    ax.grid(False, axis="y")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.23), ncol=max(1, len(sharing)), frameon=False)
    fig.suptitle(sharing_title(summary), weight="bold", fontsize=17, y=1.02)
    fig.text(0.015, 0.005,
             f"Through {summary['as_of']}. Shared status uses the full sample at this cutoff. "
             "Each canonical identity counts once per announcement.\n"
             "Equal announcement weight divides one unit across each page's benchmark set; pages without recorded benchmarks are excluded.",
             fontsize=9, color="#555555")
    fig.subplots_adjust(left=0.32, right=0.98, bottom=0.22, top=0.81)
    save_figure(fig, str(path))
    plt.close(fig)


def plot_interaction(trends: pd.DataFrame, summary: dict, path: Path) -> None:
    configure_plot_style()
    data = trends[(trends["unit"] == "announcement") & (trends["benchmark_bearing_units"] > 0)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), sharey=True)
    years = sorted(data["release_year"].unique())
    series = [
        ("all_active", "All active labels", "#52688f", "o"),
        ("confidence_ge_0_7", "Labels rated ≥0.70", "#ba743e", "s"),
    ]
    for variant, label, color, marker in series:
        points = data[data["variant"] == variant].sort_values("release_year")
        axes[0].plot(points["release_year"], points["positive_share"], marker=marker,
                     color=color, linewidth=2.2, label=label)
        for point in points.itertuples(index=False):
            if not pd.isna(point.positive_share):
                axes[0].annotate(percent(point.positive_share), (point.release_year, point.positive_share),
                                 xytext=(0, 9 if variant == "all_active" else -18),
                                 textcoords="offset points", ha="center", fontsize=9, color=color)
    for variant, label, color, marker in [
        ("confidence_ge_0_7", "At least one label rated ≥0.70", "#ba743e", "s"),
        ("accepted", "At least one accepted label", "#287a69", "D"),
    ]:
        points = data[data["variant"] == variant].sort_values("release_year")
        axes[1].plot(points["release_year"], points["coverage_share"], marker=marker,
                     color=color, linewidth=2.2, label=label)
    counts = data[data["variant"] == "all_active"].set_index("release_year")["benchmark_bearing_units"]
    for ax in axes:
        ax.set_xticks(years, [f"{year}{' YTD' if year == int(summary['as_of'][:4]) else ''}\nn={int(counts.loc[year])}" for year in years])
        ax.set_ylim(-0.065, 1.08)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1))
        ax.set_xlabel("Announcement year")
        ax.grid(False, axis="x")
        ax.legend(loc="upper left", bbox_to_anchor=(0, -0.22), frameon=False, fontsize=10)
    axes[0].set_title("Tool / environment interaction labels", loc="left", weight="bold")
    axes[0].set_ylabel("Share of the announcement-weighted portfolio")
    axes[1].set_title("Interaction-label coverage", loc="left", weight="bold")
    fig.suptitle("Interaction labels and annotation coverage", fontsize=17, weight="bold", y=0.99)
    fig.text(0.015, 0.005,
             "The rating threshold is a sensitivity filter, not manual approval. Missing labels remain in the denominator.\n"
             "A tool/environment label is required; code generation, unit-test scoring, or planning alone do not qualify.",
             fontsize=9, color="#555555")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.85, bottom=0.32, wspace=0.13)
    save_figure(fig, str(path))
    plt.close(fig)


def readme_values(tables: dict[str, pd.DataFrame], summary: dict) -> dict[str, str]:
    values = {key.upper(): number(value) for key, value in summary.items() if isinstance(value, (int, float)) and not isinstance(value, bool)}
    values["AS_OF"] = summary["as_of"]
    values["DIFFUSION_FOLLOWUP_END"] = summary["diffusion_followup_end"] or "—"
    values["SNAPSHOT_BADGE"] = summary["as_of"].replace("-", "--")
    latest_year = summary["latest_release_year"]
    values["LATEST_YEAR"] = str(latest_year) if latest_year is not None else "—"
    values["UNOBSERVED_BENCHMARKS"] = number(summary["catalog_benchmarks"] - summary["observed_benchmarks"])
    values["SHARED_BENCHMARK_SHARE"] = percent(summary["shared_benchmarks"] / summary["observed_benchmarks"] if summary["observed_benchmarks"] else None)
    values["SHARED_MENTION_SHARE"] = percent(summary["shared_mention_share"])
    values["SHARED_ANNOUNCEMENT_SHARE"] = percent(summary["shared_announcement_weight_share"])
    values["SHARING_TITLE"] = sharing_title(summary)
    values["SHARING_FINDING"] = (
        f"**{values['SHARED_BENCHMARK_SHARE']} of observed benchmark identities appear across providers**. "
        f"These identities account for **{values['SHARED_MENTION_SHARE']} of benchmark–announcement observations**."
        if summary["observed_benchmarks"] else
        "No benchmark observations fall within this cutoff; sharing proportions are undefined."
    )
    values["SHARING_WEIGHTING_INTERPRETATION"] = (
        "The shared majority persists under equal announcement weighting. "
        "Long tables and jointly announced variants therefore do not explain it by themselves."
        if summary["shared_mention_share"] is not None and summary["shared_mention_share"] > 0.5
        and summary["shared_announcement_weight_share"] > 0.5 else
        "This weighting limits the influence of long tables and jointly announced model variants."
    )
    median = summary["shared_conditional_median_lag_days"]
    values["CONDITIONAL_MEDIAN_LAG"] = "—" if median is None or pd.isna(median) else f"{median:g}"
    values["DIFFUSION_MEDIAN_FINDING"] = (
        "No identity appears across providers at this cutoff, so the conditional median lag is undefined."
        if median is None else
        f"Among shared identities, the median gap between first and second provider sightings is **{median:g} days**."
    )
    values["SINGLETON_FINDING"] = (
        f"**{values['SINGLE_LAUNCH_BENCHMARKS']} identities appear on one announcement.** Of these,\n"
        f"**{values['SINGLE_LAUNCH_FIRST_SEEN_LATEST_YEAR']} first enter the sample in {values['LATEST_YEAR']}**."
        if summary["observed_benchmarks"] else
        "There are no observed reporting histories at this cutoff."
    )

    coverage = tables["coverage_by_provider"][["provider", "model_rows", "launch_events", "benchmark_bearing_launches", "first_release", "last_release"]].copy()
    coverage.columns = ["Provider", "Model rows", "Announcements", "With benchmarks", "First tracked", "Latest tracked"]
    values["PROVIDER_TABLE"] = markdown_table(coverage)

    diffusion = tables["diffusion_horizons"].copy()
    diffusion["diffusion_share"] = diffusion["diffusion_share"].map(percent)
    diffusion = diffusion[["horizon_days", "eligible_benchmarks", "diffused_benchmarks", "diffusion_share"]]
    diffusion.columns = ["Follow-up window", "Eligible identities", "Seen at a second provider within window", "Share"]
    diffusion["Follow-up window"] = diffusion["Follow-up window"].map(lambda value: f"{int(value)} days")
    values["DIFFUSION_TABLE"] = markdown_table(diffusion)

    trends = tables["interaction_trends"]
    scoped = trends[(trends["unit"] == "announcement") & (trends["benchmark_bearing_units"] > 0)]
    active = scoped[scoped["variant"].eq("all_active")].sort_values("release_year")
    if len(active) >= 2:
        first, last = active.iloc[0], active.iloc[-1]
        direction = "rises" if last["positive_share"] > first["positive_share"] else "falls"
        if abs(last["positive_share"] - first["positive_share"]) < 1e-12:
            comparison = f"is unchanged at **{percent(first['positive_share'])}** between **{int(first['release_year'])}** and **{int(last['release_year'])}**"
        else:
            comparison = (f"{direction} from **{percent(first['positive_share'])} in {int(first['release_year'])}** "
                          f"to **{percent(last['positive_share'])} in {int(last['release_year'])}**")
        values["INTERACTION_FINDING"] = f"The annual share carrying tool or environment interaction labels {comparison}, using all active labels."
    elif len(active) == 1:
        values["INTERACTION_FINDING"] = (
            f"Only **{int(active.iloc[0]['release_year'])}** has benchmark-bearing announcements at this cutoff; "
            "a trend across years cannot be assessed."
        )
    else:
        values["INTERACTION_FINDING"] = "No benchmark-bearing announcements fall within this cutoff; annual interaction shares are undefined."
    annual_rows = []
    for year, group in scoped.groupby("release_year", sort=True):
        indexed = group.set_index("variant")
        annual_rows.append({
            "Year": f"{year}{' YTD' if year == int(summary['as_of'][:4]) else ''}",
            "Announcements": number(indexed.loc["all_active", "benchmark_bearing_units"]),
            "All active labels": percent(indexed.loc["all_active", "positive_share"]),
            "Labels rated ≥0.70": percent(indexed.loc["confidence_ge_0_7", "positive_share"]),
            "Coverage at ≥0.70": percent(indexed.loc["confidence_ge_0_7", "coverage_share"]),
            "Accepted-label coverage": percent(indexed.loc["accepted", "coverage_share"]),
        })
    values["INTERACTION_TABLE"] = markdown_table(pd.DataFrame(annual_rows, columns=["Year", "Announcements", "All active labels", "Labels rated ≥0.70", "Coverage at ≥0.70", "Accepted-label coverage"]))
    latest = trends[trends["release_year"].eq(latest_year) & trends["variant"].eq("all_active")].set_index("unit")
    values["LATEST_ANNOUNCEMENT_INTERACTION_SHARE"] = percent(latest.loc["announcement", "positive_share"] if "announcement" in latest.index else None)
    values["LATEST_MODEL_INTERACTION_SHARE"] = percent(latest.loc["model_row", "positive_share"] if "model_row" in latest.index else None)
    values["UNIT_SENSITIVITY_FINDING"] = (
        "Changing the unit from announcements to model rows gives\n"
        f"**{values['LATEST_ANNOUNCEMENT_INTERACTION_SHARE']} versus {values['LATEST_MODEL_INTERACTION_SHARE']}** "
        f"for the {values['LATEST_YEAR']} all-active estimate."
        if "announcement" in latest.index and latest.loc["announcement", "benchmark_bearing_units"] > 0 else
        "No benchmark-bearing announcements occur in the latest tracked release year; its unit comparison is undefined."
    )

    examples = tables["lifecycles"].set_index("benchmark_id").reindex([
        "benchmark_gsm8k", "benchmark_humaneval", "benchmark_swe_bench_verified",
        "benchmark_terminal_bench_3_0", "benchmark_terminal_bench_4_0",
    ]).dropna(subset=["benchmark_name"])
    examples = examples[["benchmark_name", "first_seen", "last_seen", "launch_count", "provider_count"]].copy()
    examples.columns = ["Benchmark identity", "First observed", "Last observed", "Announcements", "Providers"]
    values["LIFECYCLE_TABLE"] = markdown_table(examples)
    return values


def render_readme(template: str, values: dict[str, str]) -> str:
    def substitute(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise ValueError(f"Missing README value: {key}")
        return values[key]
    return re.sub(r"\{\{([A-Z_]+)\}\}", substitute, template)


def main() -> None:
    parser = create_analysis_parser(__doc__ or "Generate project overview")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--asset-dir", type=Path, default=ROOT / "assets")
    parser.add_argument("--readme-path", type=Path, help="Write the repository-facing README to this path; omitted for isolated analysis runs.")
    args = parser.parse_args()
    tables, summary = build_overview_tables(
        pd.read_csv(ROOT / "data/models.csv").fillna(""),
        pd.read_csv(ROOT / "data/benchmarks.csv").fillna(""),
        pd.read_csv(ROOT / "data/benchmark_facets.csv").fillna(""),
        default_resolver(), args.as_of,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.asset_dir.mkdir(parents=True, exist_ok=True)
    for key in EXPORT_TABLES:
        tables[key].to_csv(args.output_dir / f"{key}.csv", index=False)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    plot_sharing(tables["sharing_summary"], summary, args.asset_dir / "benchmark_shared_core.png")
    plot_interaction(tables["interaction_trends"], summary, args.asset_dir / "interaction_taxonomy_sensitivity.png")
    if args.readme_path:
        template = (OUTPUT_DIR / "README.template.md").read_text(encoding="utf-8")
        args.readme_path.parent.mkdir(parents=True, exist_ok=True)
        args.readme_path.write_text(render_readme(template, readme_values(tables, summary)), encoding="utf-8")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
