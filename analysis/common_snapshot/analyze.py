#!/usr/bin/env python3
"""Build a small shared snapshot for downstream benchmark analyses."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = Path(__file__).resolve().parent

from scripts.analysis_utils import (
    build_resolved_mentions,
    create_analysis_parser,
    default_resolver,
    scope_models_as_of,
)


PARSER = create_analysis_parser(__doc__ or "Build the common analysis snapshot.")


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_mentions(as_of: str | None) -> pd.DataFrame:
    models = pd.read_csv(DATA_DIR / "models.csv").fillna("")
    models, _ = scope_models_as_of(models, as_of)
    benchmarks = {
        row["benchmark_id"]: row
        for row in read_csv_dicts(DATA_DIR / "benchmarks.csv")
    }
    resolved, unresolved = build_resolved_mentions(
        models,
        default_resolver(),
        unresolved_policy="collect",
    )

    rows: list[dict[str, object]] = []
    for mention in resolved.itertuples(index=False):
        benchmark = benchmarks[mention.benchmark_id]
        rows.append(
            {
                "provider": mention.provider,
                "model_name": mention.model_name,
                "release_date": mention.release_date_text,
                "release_year": str(mention.release_year),
                "raw_mention": mention.raw_mention,
                "benchmark_id": mention.benchmark_id,
                "benchmark_name": mention.benchmark_name,
                "match_source": mention.match_source,
                "match_type": mention.match_type,
                "source_author": benchmark["source_author"],
                "frontier_lab_author_affiliations": benchmark[
                    "frontier_lab_author_affiliations"
                ],
                "legacy_task_mode": benchmark["legacy_task_mode"],
                "legacy_task_domain": benchmark["legacy_task_domain"],
                "benchmark_review_status": benchmark["review_status"],
            }
        )

    if not unresolved.empty:
        unresolved_path = OUTPUT_DIR / "unresolved_mentions.txt"
        lines = [
            f"{row.provider} / {row.model_name} / {row.raw_mention}"
            for row in unresolved.itertuples(index=False)
        ]
        unresolved_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return pd.DataFrame(rows)


def write_summary_tables(mentions: pd.DataFrame) -> dict[str, Path]:
    paths: dict[str, Path] = {}

    provider_year = (
        mentions.groupby(["provider", "release_year"])
        .size()
        .reset_index(name="mention_count")
        .sort_values(["release_year", "provider"])
    )
    paths["provider_year_mentions"] = OUTPUT_DIR / "provider_year_mentions.csv"
    provider_year.to_csv(paths["provider_year_mentions"], index=False)

    top_benchmarks = (
        mentions.groupby("benchmark_name")
        .agg(
            mention_count=("benchmark_name", "size"),
            provider_count=("provider", "nunique"),
            first_seen=("release_date", "min"),
            latest_seen=("release_date", "max"),
            source_author=("source_author", "first"),
            frontier_lab_author_affiliations=(
                "frontier_lab_author_affiliations",
                "first",
            ),
        )
        .reset_index()
        .sort_values(["mention_count", "provider_count", "benchmark_name"], ascending=[False, False, True])
    )
    paths["top_benchmarks"] = OUTPUT_DIR / "top_benchmarks.csv"
    top_benchmarks.to_csv(paths["top_benchmarks"], index=False)

    task_mix = (
        mentions.groupby(["provider", "release_year", "legacy_task_mode"])
        .size()
        .reset_index(name="mention_count")
    )
    task_mix["share_within_provider_year"] = task_mix["mention_count"] / task_mix.groupby(
        ["provider", "release_year"]
    )["mention_count"].transform("sum")
    paths["provider_year_task_mix"] = OUTPUT_DIR / "provider_year_task_mix.csv"
    task_mix.to_csv(paths["provider_year_task_mix"], index=False)

    facets = pd.read_csv(DATA_DIR / "benchmark_facets.csv").fillna("")
    facets["classification_confidence"] = pd.to_numeric(
        facets["classification_confidence"],
        errors="coerce",
    )
    review_debt = (
        facets.groupby("facet_axis")
        .agg(
            row_count=("facet_axis", "size"),
            accepted_rows=("review_status", lambda s: int((s == "accepted").sum())),
            needs_review_rows=("review_status", lambda s: int((s == "needs_review").sum())),
            legacy_seed_rows=("review_status", lambda s: int((s == "legacy_seed").sum())),
            low_confidence_rows=(
                "classification_confidence",
                lambda s: int((s < 0.7).sum()),
            ),
        )
        .reset_index()
        .sort_values("facet_axis")
    )
    review_debt["accepted_share"] = review_debt["accepted_rows"] / review_debt["row_count"]
    review_debt["low_confidence_share"] = review_debt["low_confidence_rows"] / review_debt["row_count"]
    paths["facet_review_debt"] = OUTPUT_DIR / "facet_review_debt.csv"
    review_debt.to_csv(paths["facet_review_debt"], index=False)

    return paths


def write_markdown(mentions: pd.DataFrame, paths: dict[str, Path]) -> None:
    provider_counts = Counter(mentions["provider"])
    year_counts = Counter(mentions["release_year"])
    top_benchmarks = Counter(mentions["benchmark_name"]).most_common(10)
    mode_counts = Counter(mentions["legacy_task_mode"])
    domain_counts = Counter(mentions["legacy_task_domain"])

    lines = [
        "# Common Data Snapshot",
        "",
        "This folder contains lightweight baseline tables for the experimental analyses under `analysis/`.",
        "The numbers are derived only from local CSVs and use exact canonical benchmark resolution plus explicit aliases.",
        "",
        "## Baseline Counts",
        "",
        f"- Resolved benchmark mentions: {len(mentions)}",
        f"- Providers: {', '.join(f'{k}={v}' for k, v in sorted(provider_counts.items()))}",
        f"- Years: {', '.join(f'{k}={v}' for k, v in sorted(year_counts.items()))}",
        f"- Legacy task-mode mentions: {', '.join(f'{k}={v}' for k, v in mode_counts.most_common())}",
        f"- Legacy domain mentions: {', '.join(f'{k}={v}' for k, v in domain_counts.most_common())}",
        "",
        "## Top Benchmarks",
        "",
        "| Mentions | Benchmark |",
        "| ---: | --- |",
    ]
    for name, count in top_benchmarks:
        lines.append(f"| {count} | {name} |")

    lines.extend(
        [
            "",
            "## Output Tables",
            "",
            *[
                f"- `{path.name}`"
                for path in paths.values()
            ],
            "",
            "## Interpretation Caveat",
            "",
            "These tables describe what providers foregrounded on public release pages. They do not measure all evaluations, hidden evals, or model capability.",
        ]
    )
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = PARSER.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mentions = load_mentions(args.as_of)
    mentions_path = OUTPUT_DIR / "resolved_mentions.csv"
    mentions.to_csv(mentions_path, index=False)
    paths = {"resolved_mentions": mentions_path}
    paths.update(write_summary_tables(mentions))
    write_markdown(mentions, paths)
    print(f"Wrote common snapshot to {OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
