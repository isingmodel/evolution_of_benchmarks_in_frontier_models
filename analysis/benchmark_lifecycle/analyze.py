"""Generate reporting life cycles for the complete canonical benchmark catalog."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

from analysis.benchmark_lifecycle.lifecycle import build_lifecycle_tables
from scripts.analysis_utils import create_analysis_parser, default_resolver
from scripts.plot_utils import configure_plot_style, save_figure


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent
PROVIDER_STYLE = {
    "OpenAI": ("#27816d", "o", -0.16),
    "Google": ("#397ac3", "s", 0.0),
    "Anthropic": ("#b6683e", "^", 0.16),
}
# Editorial examples, not a ranking or an inferred benchmark-family mapping.
TIMELINE_IDS = [
    "benchmark_gsm8k",
    "benchmark_math",
    "benchmark_mmlu_mmlu_pro",
    "benchmark_humaneval",
    "benchmark_gpqa_diamond",
    "benchmark_hle_humanity_s_last_exam",
    "benchmark_swe_bench_verified",
    "benchmark_swe_bench_pro",
    "benchmark_osworld_verified",
    "benchmark_terminal_bench_2_0",
    "benchmark_terminal_bench_2_1",
    "benchmark_terminal_bench_3_0",
    "benchmark_terminal_bench_4_0",
    "benchmark_frontier_science_research",
    "benchmark_terminal_bench_science_0_1",
]


def plot_timeline(
    lifecycles: pd.DataFrame,
    launch_mentions: pd.DataFrame,
    cutoff: pd.Timestamp,
    output: Path,
) -> list[str]:
    """Plot actual launch observations with a bounded first-to-last span."""
    configure_plot_style()
    cutoff_datetime = cutoff.to_pydatetime()
    indexed = lifecycles.set_index("benchmark_id")
    selected = [
        benchmark_id for benchmark_id in TIMELINE_IDS
        if benchmark_id in indexed.index and indexed.loc[benchmark_id, "launch_count"] > 0
    ]
    fig, ax = plt.subplots(figsize=(14, max(4.5, 0.44 * len(selected) + 2.2)))
    if selected:
        positions = {benchmark_id: index for index, benchmark_id in enumerate(selected)}
        for benchmark_id in selected:
            row = indexed.loc[benchmark_id]
            ax.plot(
                pd.to_datetime([row["first_seen"], row["last_seen"]]),
                [positions[benchmark_id]] * 2,
                color="#c1c7cc", linewidth=2.4, zorder=1,
            )
        subset = launch_mentions[launch_mentions["benchmark_id"].isin(selected)]
        for provider, (color, marker, offset) in PROVIDER_STYLE.items():
            points = subset[subset["provider"] == provider]
            ax.scatter(
                pd.to_datetime(points["release_date"]),
                points["benchmark_id"].map(positions) + offset,
                color=color, marker=marker, s=31, linewidths=0.4,
                edgecolors="white", zorder=3,
            )
        ax.set_yticks(range(len(selected)), [indexed.loc[key, "benchmark_name"] for key in selected])
        ax.set_ylim(len(selected) - 0.5, -0.55)
        first_year = pd.to_datetime(indexed.loc[selected, "first_seen"]).min().year
        start = datetime(first_year, 1, 1)
    else:
        ax.text(0.5, 0.5, "No selected benchmark observations through this cutoff",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_yticks([])
        start = cutoff_datetime - timedelta(days=365)
    ax.set_xlim(start, cutoff_datetime + timedelta(days=35))
    ax.axvline(cutoff_datetime, color="#555555", linestyle="--", linewidth=1.1, zorder=2)
    ax.text(cutoff_datetime, 1.025, f"Cutoff {cutoff.date()}", transform=ax.get_xaxis_transform(),
            ha="right", va="bottom", fontsize=10, color="#555555")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[4, 7, 10]))
    ax.tick_params(axis="y", labelsize=11)
    ax.grid(axis="x", color="#e0e4e7", linewidth=0.8)
    ax.grid(axis="y", color="#edf0f2", linewidth=0.6)
    ax.set_xlabel("Launch date on the public pages covered by this dataset")
    handles = [
        Line2D([], [], marker=marker, color=color, linestyle="none", label=provider, markersize=7)
        for provider, (color, marker, _) in PROVIDER_STYLE.items()
    ]
    ax.legend(handles=handles, ncol=3, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.095))
    fig.suptitle("Benchmark reporting life cycles", fontsize=18, fontweight="bold", y=0.995)
    fig.text(0.01, 0.015,
             "Dots = distinct announcements. Grey spans = first to last observed mention; gaps are allowed.\n"
             "Selected examples; the report covers the full catalog. Last mention does not establish retirement.",
             fontsize=10, color="#555555")
    fig.subplots_adjust(left=0.31, right=0.985, top=0.86, bottom=0.13)
    save_figure(fig, str(output))
    plt.close(fig)
    return selected


def build_summary(
    lifecycles: pd.DataFrame, launches: pd.DataFrame,
    launch_mentions: pd.DataFrame, cutoff: pd.Timestamp,
    window_days: int, selected: list[str],
) -> dict[str, object]:
    observed = lifecycles["launch_count"] > 0
    return {
        "as_of": cutoff.date().isoformat(),
        "observation_unit": "provider + release date + normalized announcement URL",
        "recent_window_days": window_days,
        "model_rows": int(launches["model_row_count"].sum()),
        "launch_events": len(launches),
        "benchmark_bearing_launch_events": int(launches["has_benchmark_mentions"].sum()),
        "catalog_benchmarks": len(lifecycles),
        "observed_benchmarks": int(observed.sum()),
        "unobserved_benchmarks": int((~observed).sum()),
        "single_launch_benchmarks": int((lifecycles["launch_count"] == 1).sum()),
        "multiple_launch_benchmarks": int((lifecycles["launch_count"] > 1).sum()),
        "shared_benchmarks": int((lifecycles["provider_count"] > 1).sum()),
        "model_row_mentions": int(lifecycles["model_row_count"].sum()),
        "launch_mentions": len(launch_mentions),
        "selected_timeline_ids": selected,
        "interpretation": "First/last tracked mentions bound an observed reporting span; they do not establish creation, saturation or retirement.",
    }


def markdown_table(frame: pd.DataFrame) -> str:
    def cell(value: object) -> str:
        if pd.isna(value) or value == "":
            return "—"
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(frame.columns) + " |", "| " + " | ".join(["---"] * len(frame.columns)) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None))
    return "\n".join(lines)


def write_report(lifecycles: pd.DataFrame, summary: dict[str, object], output: Path) -> None:
    diffusion = lifecycles[lifecycles["provider_count"] > 1].sort_values(
        ["second_provider_lag_days", "first_seen", "benchmark_name"], kind="stable",
    ).head(10)
    diffusion = diffusion[["benchmark_name", "first_seen", "first_providers", "second_provider_lag_days", "third_provider_lag_days"]].rename(columns={
        "benchmark_name": "Benchmark", "first_seen": "First observed", "first_providers": "First providers",
        "second_provider_lag_days": "Second-provider lag (days)", "third_provider_lag_days": "Third-provider lag (days)",
    })
    catalog = lifecycles[["benchmark_name", "first_seen", "last_seen", "observed_span_days", "launch_count", "provider_count", "reporting_pattern", "review_status"]].rename(columns={
        "benchmark_name": "Benchmark", "first_seen": "First observed", "last_seen": "Last observed",
        "observed_span_days": "Span (days)", "launch_count": "Launches", "provider_count": "Providers",
        "reporting_pattern": "Reporting pattern", "review_status": "Identity review",
    })
    text = f"""# Benchmark reporting life cycles

Observation cutoff: **{summary['as_of']}**. This report covers all **{summary['catalog_benchmarks']}**
catalog identities: **{summary['observed_benchmarks']}** have an observed mention and
**{summary['unobserved_benchmarks']}** have no observed mention through this cutoff.

The **{summary['model_rows']}** model rows collapse to **{summary['launch_events']}** distinct
announcements, **{summary['benchmark_bearing_launch_events']}** of which contain recorded benchmarks.
Aliases are deduplicated within each model row and then within each announcement.
There are **{summary['launch_mentions']}** benchmark–announcement observations, compared with
**{summary['model_row_mentions']}** canonical benchmark–model-row observations.

**{summary['single_launch_benchmarks']}** identities appear on one announcement,
**{summary['multiple_launch_benchmarks']}** recur across announcements, and
**{summary['shared_benchmarks']}** appear across multiple providers.
These are descriptions of the covered public pages, not a survival estimate.

First observed is entry into this sample, not publication or private adoption.
First-to-last span is an observed lower bound and can be zero. Last observed is
not retirement. Unobserved dates, spans and diffusion lags are blank; a blank
follow-up share means no defined denominator, not zero repeat use.

## Outputs and interpretation

- [All benchmark life cycles](benchmark_lifecycles.csv): dates, counts, diffusion, recency and cadence-adjusted reporting measures.
- [Per-provider life cycles](provider_lifecycles.csv): each provider's first/last mention and follow-up denominator, including unadopted identities.
- [Launch inventory](launch_events.csv): every covered announcement, including pages with no recorded benchmarks.
- [Launch observations](launch_mentions.csv): benchmark IDs, dates, source URLs and mentioning model rows for tracing each timeline.
- [Run summary](summary.json): cutoff, observation units and catalog coverage.

Follow-up reporting share divides mentions after a provider's first adoption date
by that provider's covered announcements after that date. Empty benchmark pages
are included as reporting opportunities; omission cannot establish non-use.
The aggregate pools opportunities only from adopting providers. Same-day events
are distinct when their URLs differ, but no within-day follow-up order is assumed.
Per-provider post-last gaps use each provider's own last mention; the aggregate
post-last gap uses the benchmark's last mention across all adopting providers.
Recent counts cover the last {summary['recent_window_days']} calendar days inclusively.

Version and track identities follow the catalog. This analysis infers no family,
successor or replacement relationships. Existing combined historical identities
and provisional private-suite mappings affect the results; identity review status
is retained in the full table. See [methodology](README.md).

## Fast observed cross-provider diffusion

These lags use every provider's first observed date. Same-day first-adopter ties
remain ties, with zero second/third-provider lag.

{markdown_table(diffusion)}

## Complete catalog

`single_launch` means one announcement; `repeated_one_provider` means several
announcements from one provider; `shared_across_providers` means at least two
providers. `unobserved` means no covered mention by this cutoff. These labels
do not describe benchmark maturity, quality, inactivity or retirement.

{markdown_table(catalog)}
"""
    output.write_text(text, encoding="utf-8")


def main() -> None:
    parser = create_analysis_parser(__doc__ or "Benchmark reporting life cycles", window_days=180)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--asset-dir", type=Path, default=ROOT / "assets")
    args = parser.parse_args()
    models = pd.read_csv(ROOT / "data/models.csv").fillna("")
    benchmarks = pd.read_csv(ROOT / "data/benchmarks.csv").fillna("")
    lifecycles, providers, launches, mentions, cutoff = build_lifecycle_tables(
        models, benchmarks, default_resolver(), args.as_of, args.window_days,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.asset_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in [
        ("benchmark_lifecycles", lifecycles), ("provider_lifecycles", providers),
        ("launch_events", launches), ("launch_mentions", mentions),
    ]:
        frame.to_csv(args.output_dir / f"{name}.csv", index=False)
    selected = plot_timeline(lifecycles, mentions, cutoff, args.asset_dir / "benchmark_lifecycle.png")
    summary = build_summary(lifecycles, launches, mentions, cutoff, args.window_days, selected)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_report(lifecycles, summary, args.output_dir / "report.md")
    print(json.dumps({key: value for key, value in summary.items() if key != "selected_timeline_ids"}, indent=2))


if __name__ == "__main__":
    main()
