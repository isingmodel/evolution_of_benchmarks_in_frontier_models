from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

if __package__:
    from .taxonomy_utils import (
        HEADLINE_TO_LEGACY_TASK_MODE,
        CanonicalResolver,
        benchmark_id,
        derive_headline_projection,
        split_benchmark_mentions,
    )
else:
    from taxonomy_utils import (
        HEADLINE_TO_LEGACY_TASK_MODE,
        CanonicalResolver,
        benchmark_id,
        derive_headline_projection,
        split_benchmark_mentions,
    )


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

FACET_DOMAIN_ORDER = [
    "General/Commonsense",
    "STEM/Math",
    "Coding/Engineering",
    "Law",
    "Bio/Medicine",
    "Finance",
    "Cybersecurity",
    "Multilingual",
    "Visual/Document",
    "Other Specialized",
]


@dataclass(frozen=True)
class LegacyTaxonomy:
    mode: str
    domain: str


@dataclass(frozen=True)
class LegacyTaxonomyLookup:
    by_id: dict[str, LegacyTaxonomy]
    resolver: CanonicalResolver
    fallback_by_exact: Optional[dict[str, LegacyTaxonomy]] = None

    def resolve(self, raw_mention: str) -> Optional[LegacyTaxonomy]:
        resolution = self.resolver.resolve(raw_mention)
        if resolution:
            taxonomy = self.by_id.get(resolution.benchmark_id)
            if taxonomy:
                return taxonomy

        if self.fallback_by_exact is not None:
            return self.fallback_by_exact.get(legacy_lookup_key(raw_mention))

        return None


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


def legacy_lookup_key(value: object) -> str:
    return str(value).strip().casefold()


def legacy_benchmark_aliases(name: str) -> set[str]:
    key = legacy_lookup_key(name)
    aliases = {key} if key else set()
    if "/" in key:
        aliases.update(part.strip() for part in key.split("/") if part.strip())
    return aliases


def build_legacy_taxonomy_lookup(benchmarks: pd.DataFrame) -> LegacyTaxonomyLookup:
    by_id: dict[str, LegacyTaxonomy] = {}
    alias_path = ALIAS_PATH if ALIAS_PATH.exists() else None
    fallback_by_exact: Optional[dict[str, LegacyTaxonomy]] = {} if alias_path is None else None

    for _, row in benchmarks.fillna("").iterrows():
        name = str(row.get("benchmark_name", "")).strip()
        if not name:
            continue

        row_benchmark_id = str(row.get("benchmark_id", "")).strip() or benchmark_id(name)
        taxonomy = LegacyTaxonomy(
            mode=str(row.get("legacy_task_mode", "") or row.get("task_mode", "")).strip(),
            domain=str(row.get("legacy_task_domain", "") or row.get("task_domain", "")).strip(),
        )
        by_id[row_benchmark_id] = taxonomy
        if fallback_by_exact is not None:
            for alias in legacy_benchmark_aliases(name):
                fallback_by_exact[alias] = taxonomy

    resolver = CanonicalResolver.from_files(BENCHMARKS_PATH, alias_path)
    return LegacyTaxonomyLookup(by_id=by_id, resolver=resolver, fallback_by_exact=fallback_by_exact)


def add_derived_headline_task_mode(facets: pd.DataFrame) -> pd.DataFrame:
    """Add runtime headline projection rows derived from v3 facets.

    The canonical `benchmark_facets.csv` can remain v3-only while older
    exploratory analyses that group by `headline_task_mode` still get a stable
    chart projection. Existing non-deprecated headline rows are preserved.
    """
    if facets.empty:
        return facets

    output = facets.copy()
    active = output[
        (output["review_status"] != "deprecated")
        & (output["facet_label"].astype(str).str.strip() != "")
        & (output["facet_axis"].astype(str).str.strip() != "")
    ].copy()
    if active.empty:
        return output

    existing_headline_ids = set(
        active.loc[active["facet_axis"] == "headline_task_mode", "benchmark_id"]
    )
    derived_rows = []
    for benchmark_id_value, group in active.groupby("benchmark_id"):
        if benchmark_id_value in existing_headline_ids:
            continue
        labels_by_axis = {
            axis: axis_group["facet_label"].astype(str).tolist()
            for axis, axis_group in group.groupby("facet_axis")
        }
        projection = derive_headline_projection(labels_by_axis)
        legacy_label = HEADLINE_TO_LEGACY_TASK_MODE.get(projection or "")
        if not legacy_label:
            continue
        confidences = pd.to_numeric(group["classification_confidence"], errors="coerce").dropna()
        confidence = float(confidences.min()) if not confidences.empty else 0.7
        derived_rows.append(
            {
                "benchmark_id": benchmark_id_value,
                "facet_axis": "headline_task_mode",
                "facet_label": legacy_label,
                "classification_confidence": confidence,
                "review_status": "needs_review",
                "rationale": "Runtime headline projection derived from v3 facet labels for chart compatibility.",
            }
        )

    if not derived_rows:
        return output
    return pd.concat([output, pd.DataFrame(derived_rows)], ignore_index=True)


def load_benchmark_facets(add_headline_projection: bool = True) -> pd.DataFrame:
    facets = pd.read_csv(DATA_DIR / "benchmark_facets.csv").fillna("")
    if add_headline_projection:
        facets = add_derived_headline_task_mode(facets)
    return facets


def active_facets_for_axes(facets: pd.DataFrame, axes: Sequence[str]) -> pd.DataFrame:
    axes = list(axes)
    active = facets[
        (facets["facet_axis"].isin(axes))
        & (facets["review_status"] != "deprecated")
        & (facets["facet_label"].astype(str).str.strip() != "")
    ].copy()
    return active.drop_duplicates(["benchmark_id", "facet_axis", "facet_label"])


def build_model_facet_events(
    models: pd.DataFrame,
    facets: pd.DataFrame,
    axes: Sequence[str],
    as_of: pd.Timestamp,
    resolver: Optional[CanonicalResolver] = None,
    strict_resolution: bool = False,
) -> pd.DataFrame:
    """Build release-normalized, axis-fractional facet events.

    Each release page contributes 1.0 total weight per axis. That release weight
    is divided equally across resolved benchmark mentions, then equally across
    every active label assigned to that benchmark within the requested axis.
    """
    axes = list(axes)
    resolver = resolver or CanonicalResolver.from_files(BENCHMARKS_PATH, ALIAS_PATH if ALIAS_PATH.exists() else None)
    active = active_facets_for_axes(facets, axes)
    labels_by_key = {
        (benchmark_id_value, facet_axis): axis_group["facet_label"].astype(str).tolist()
        for (benchmark_id_value, facet_axis), axis_group in active.groupby(["benchmark_id", "facet_axis"])
    }

    rows = []
    unresolved = []
    missing_facets = []
    for _, model in models.fillna("").iterrows():
        provider = str(model.get("Provider", "")).strip()
        model_name = str(model.get("Model name", "")).strip()
        release_date = pd.to_datetime(model.get("release date", ""), errors="raise")
        if release_date > as_of:
            continue

        resolved_mentions = []
        for raw_mention in split_benchmarks(model.get("benchmarks", "")):
            resolution = resolver.resolve(raw_mention)
            if resolution:
                resolved_mentions.append((raw_mention, resolution.benchmark_id))
            else:
                unresolved.append((model_name, raw_mention))

        if not resolved_mentions:
            continue

        benchmark_weight = 1.0 / len(resolved_mentions)
        model_key = "|".join([provider, model_name, str(model.get("release date", "")).strip()])
        for raw_mention, benchmark_id_value in resolved_mentions:
            for axis in axes:
                labels = labels_by_key.get((benchmark_id_value, axis), [])
                if not labels:
                    missing_facets.append((model_name, f"{raw_mention} [{axis}]"))
                    continue
                label_weight = benchmark_weight / len(labels)
                for label in labels:
                    rows.append(
                        {
                            "model_key": model_key,
                            "Model": model_name,
                            "Provider": provider,
                            "Date": release_date,
                            "benchmark_id": benchmark_id_value,
                            "raw_mention": raw_mention,
                            "facet_axis": axis,
                            "Category": label,
                            "Weight": label_weight,
                        }
                    )

    warn_unresolved(unresolved, strict_resolution)
    if missing_facets:
        sample = ", ".join(sorted({unresolved_label(item) for item in missing_facets})[:10])
        print(f"Warning: resolved benchmark mentions without requested facet labels skipped ({len(missing_facets)}): {sample}.")

    return pd.DataFrame(
        rows,
        columns=[
            "model_key",
            "Model",
            "Provider",
            "Date",
            "benchmark_id",
            "raw_mention",
            "facet_axis",
            "Category",
            "Weight",
        ],
    )


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
