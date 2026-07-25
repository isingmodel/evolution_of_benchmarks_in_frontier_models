"""Shared infrastructure for reproducible benchmark analyses.

The project has several legitimate units of analysis, but canonical resolution
and per-release weighting must not drift between scripts. This module owns that
common layer and exposes explicit switches for the one important distinction:
README story tables deduplicate canonical identities within a release, while
mention-inventory analyses retain every raw surface form.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal, Sequence

import pandas as pd

from scripts.taxonomy_utils import CanonicalResolver, exact_key, split_benchmark_mentions


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BENCHMARKS_PATH = DATA_DIR / "benchmarks.csv"
ALIASES_PATH = DATA_DIR / "benchmark_aliases.csv"

STANDARD_MENTION_COLUMNS = [
    "mention_id",
    "model_row_id",
    "provider",
    "model_name",
    "link",
    "release_date",
    "release_date_text",
    "release_year",
    "model_key",
    "mention_position",
    "raw_mention",
    "benchmark_id",
    "benchmark_name",
    "match_source",
    "match_type",
    "raw_weight",
    "release_weight",
    "resolved_benchmark_count_for_release",
]
STANDARD_UNRESOLVED_COLUMNS = [
    "provider",
    "model_name",
    "release_date",
    "raw_mention",
]


def create_analysis_parser(
    description: str,
    *,
    include_as_of: bool = True,
    window_days: int | None = None,
    output: str | None = None,
    strict_resolution: bool = False,
) -> argparse.ArgumentParser:
    """Create the common CLI shared by analysis entrypoints."""
    parser = argparse.ArgumentParser(description=description)
    if include_as_of:
        parser.add_argument(
            "--as-of",
            help=(
                "Include model releases on or before this date (YYYY-MM-DD). "
                "Defaults to the latest release date in data/models.csv."
            ),
        )
    if window_days is not None:
        parser.add_argument(
            "--window-days",
            type=int,
            default=window_days,
            help="Rolling or moving-average window size in days.",
        )
    if output is not None:
        parser.add_argument("--output", default=output, help="Output path.")
    if strict_resolution:
        parser.add_argument(
            "--strict-resolution",
            action="store_true",
            help=(
                "Fail if any benchmark mention does not resolve by exact "
                "canonical name or explicit alias."
            ),
        )
    return parser


def default_resolver() -> CanonicalResolver:
    return CanonicalResolver.from_files(
        BENCHMARKS_PATH,
        ALIASES_PATH if ALIASES_PATH.exists() else None,
    )


def scope_models_as_of(
    models: pd.DataFrame,
    as_of: str | None,
) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Apply the same inclusive release-date cutoff across every analysis."""
    release_dates = pd.to_datetime(models["release date"], errors="raise")
    cutoff = (
        pd.to_datetime(as_of, errors="raise").normalize()
        if as_of
        else release_dates.max().normalize()
    )
    return models.loc[release_dates <= cutoff].copy(), cutoff


def build_resolved_mentions(
    models: pd.DataFrame,
    resolver: CanonicalResolver | None = None,
    *,
    deduplicate_within_release: bool = False,
    unresolved_policy: Literal["error", "collect", "drop_release"] = "error",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Resolve model benchmark lists and normalize surviving release weights.

    Raw-inventory analyses retain repeated surface forms. Story analyses can
    request canonical deduplication, which combines the raw forms in first-seen
    order and records their multiplicity in ``raw_weight``. In either mode, a
    release with resolved mentions contributes exactly one total unit.
    """
    if unresolved_policy not in {"error", "collect", "drop_release"}:
        raise ValueError(f"Unsupported unresolved_policy: {unresolved_policy}")

    resolver = resolver or default_resolver()
    mention_rows: list[dict[str, object]] = []
    unresolved_rows: list[dict[str, str]] = []
    mention_id = 0

    for model_row_id, model in models.fillna("").reset_index(drop=True).iterrows():
        provider = exact_key(model.get("Provider", ""))
        model_name = exact_key(model.get("Model name", ""))
        release_date_text = exact_key(model.get("release date", ""))
        release_date_value = model.get("release_date", "")
        release_date_source = (
            release_date_value
            if str(release_date_value).strip()
            else release_date_text
        )
        release_date = pd.to_datetime(release_date_source, errors="raise")
        model_key = exact_key(
            model.get("model_key", "")
        ) or "|".join([provider, model_name, release_date_text])
        link = exact_key(model.get("link", ""))
        raw_mentions = split_benchmark_mentions(model.get("benchmarks", ""))

        resolved_items: list[dict[str, object]] = []
        release_unresolved = []
        for mention_position, raw_mention in enumerate(raw_mentions, start=1):
            resolution = resolver.resolve(raw_mention)
            if resolution is None:
                unresolved = {
                    "provider": provider,
                    "model_name": model_name,
                    "release_date": release_date_text,
                    "raw_mention": raw_mention,
                }
                unresolved_rows.append(unresolved)
                release_unresolved.append(unresolved)
                continue
            resolved_items.append(
                {
                    "mention_position": mention_position,
                    "raw_mentions": [raw_mention],
                    "resolution": resolution,
                }
            )

        if release_unresolved and unresolved_policy == "drop_release":
            continue

        if deduplicate_within_release:
            deduplicated: dict[str, dict[str, object]] = {}
            for item in resolved_items:
                resolution = item["resolution"]
                existing = deduplicated.get(resolution.benchmark_id)
                if existing is None:
                    deduplicated[resolution.benchmark_id] = item
                else:
                    existing["raw_mentions"].extend(item["raw_mentions"])
            resolved_items = list(deduplicated.values())

        release_count = len(resolved_items)
        if release_count == 0:
            continue

        for item in resolved_items:
            resolution = item["resolution"]
            raw_mentions_for_item = item["raw_mentions"]
            mention_rows.append(
                {
                    "mention_id": mention_id,
                    "model_row_id": model_row_id,
                    "provider": provider,
                    "model_name": model_name,
                    "link": link,
                    "release_date": release_date,
                    "release_date_text": release_date_text,
                    "release_year": int(release_date.year),
                    "model_key": model_key,
                    "mention_position": int(item["mention_position"]),
                    "raw_mention": "; ".join(raw_mentions_for_item),
                    "benchmark_id": resolution.benchmark_id,
                    "benchmark_name": resolution.benchmark_name,
                    "match_source": resolution.match_source,
                    "match_type": resolution.match_type,
                    "raw_weight": float(len(raw_mentions_for_item)),
                    "release_weight": 1.0 / release_count,
                    "resolved_benchmark_count_for_release": release_count,
                }
            )
            mention_id += 1

    unresolved = pd.DataFrame(unresolved_rows, columns=STANDARD_UNRESOLVED_COLUMNS)
    if not unresolved.empty and unresolved_policy == "error":
        sample = unresolved.head(20).to_dict("records")
        raise ValueError(
            "Unresolved benchmark mentions found. Add explicit aliases or "
            f"canonical rows before trusting this analysis. Sample: {sample}"
        )

    mentions = pd.DataFrame(mention_rows, columns=STANDARD_MENTION_COLUMNS)
    return mentions, unresolved


def select_columns(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Return a copy with deterministic column order, including empty frames."""
    return frame.reindex(columns=list(columns)).copy()
