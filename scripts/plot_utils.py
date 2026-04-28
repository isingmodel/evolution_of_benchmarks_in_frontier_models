from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

if __package__:
    from .taxonomy_utils import CanonicalResolver, benchmark_id, split_benchmark_mentions
else:
    from taxonomy_utils import CanonicalResolver, benchmark_id, split_benchmark_mentions


DATA_DIR = Path("data")
BENCHMARKS_PATH = DATA_DIR / "benchmarks.csv"
ALIAS_PATH = DATA_DIR / "benchmark_aliases.csv"

MODE_ORDER = [
    "Agentic",
    "Multimodal Perception",
    "Generative Reasoning",
    "Constraint Satisfaction",
    "Knowledge Retrieval",
]

DOMAIN_ORDER = [
    "STEM/Math",
    "Coding/Engineering",
    "General/Commonsense",
    "Specialized (Law/Bio/Finance)",
]


@dataclass(frozen=True)
class LegacyTaxonomy:
    mode: str
    domain: str


@dataclass(frozen=True)
class LegacyTaxonomyLookup:
    by_id: dict[str, LegacyTaxonomy]
    resolver: CanonicalResolver

    def resolve(self, raw_mention: str) -> Optional[LegacyTaxonomy]:
        resolution = self.resolver.resolve(raw_mention)
        if not resolution:
            return None
        return self.by_id.get(resolution.benchmark_id)


def configure_plot_style() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Verdana", "Arial", "DejaVu Sans"]


def load_models() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "models.csv")


def load_models_and_benchmarks() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_models(), pd.read_csv(BENCHMARKS_PATH)


def latest_release_date(models: pd.DataFrame) -> pd.Timestamp:
    return pd.to_datetime(models["release date"], errors="raise").max().normalize()


def parse_as_of(value: Optional[str]) -> Optional[pd.Timestamp]:
    if not value:
        return None
    return pd.to_datetime(value, errors="raise").normalize()


def validate_window_days(window_days: int) -> int:
    if window_days <= 0:
        raise ValueError("--window-days must be a positive integer.")
    return window_days


def split_benchmarks(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    text = str(value).strip()
    if not text or text.casefold() == "nan":
        return []
    return split_benchmark_mentions(text)


def build_legacy_taxonomy_lookup(benchmarks: pd.DataFrame) -> LegacyTaxonomyLookup:
    by_id: dict[str, LegacyTaxonomy] = {}
    for _, row in benchmarks.fillna("").iterrows():
        name = str(row.get("benchmark_name", "")).strip()
        if not name:
            continue

        row_benchmark_id = str(row.get("benchmark_id", "")).strip() or benchmark_id(name)
        by_id[row_benchmark_id] = LegacyTaxonomy(
            mode=str(row.get("legacy_task_mode", "") or row.get("task_mode", "")).strip(),
            domain=str(row.get("legacy_task_domain", "") or row.get("task_domain", "")).strip(),
        )

    resolver = CanonicalResolver.from_files(
        BENCHMARKS_PATH,
        ALIAS_PATH if ALIAS_PATH.exists() else None,
    )
    return LegacyTaxonomyLookup(by_id=by_id, resolver=resolver)


def unresolved_label(item: object) -> str:
    if isinstance(item, (tuple, list)) and len(item) > 1:
        return str(item[1])
    return str(item)


def warn_unresolved(
    unresolved: Iterable[object],
    strict_resolution: bool,
    resolution_hint: str = "Add explicit taxonomy/alias rows to resolve them; fuzzy substring matching is disabled.",
    sample_separator: str = ", ",
) -> None:
    unresolved = list(unresolved)
    if not unresolved:
        return

    sample = sample_separator.join(sorted({unresolved_label(item) for item in unresolved})[:10])
    message = f"Unresolved benchmark mentions skipped ({len(unresolved)}): {sample}. {resolution_hint}"
    if strict_resolution:
        raise ValueError(message)

    print(f"Warning: {message}")


def build_rolling_share_trend(
    events: pd.DataFrame,
    as_of: pd.Timestamp,
    window_days: int,
    category_cols: Optional[Sequence[str]] = None,
) -> tuple[pd.DataFrame, Optional[pd.Timestamp]]:
    category_cols = list(category_cols) if category_cols is not None else None
    if events.empty:
        return pd.DataFrame(columns=category_cols or []), None

    min_date = events["Date"].min()
    date_range = pd.date_range(start=min_date, end=as_of, freq="D")

    daily = events.groupby(["Date", "Category"])["Weight"].sum().unstack(fill_value=0)
    daily = daily.reindex(date_range, fill_value=0)

    if category_cols is not None:
        for category in category_cols:
            if category not in daily.columns:
                daily[category] = 0
        daily = daily[category_cols]

    rolling = daily.rolling(window=window_days, min_periods=1).sum()
    trend = rolling.div(rolling.sum(axis=1), axis=0).ffill().fillna(0)
    for col in trend.columns:
        trend[col] = trend[col].ewm(span=30, adjust=False).mean()
    trend = trend.div(trend.sum(axis=1), axis=0).fillna(0)

    return trend, min_date


def save_figure(fig, output_path: str) -> None:
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Graph generated at {output_path}")
