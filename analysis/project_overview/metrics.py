"""Reproducible inventory, sharing, diffusion, and strict interaction measures.

Announcement measures give each benchmark-bearing source event one total unit.
Model measures give each benchmark-bearing input row one total unit after alias
deduplication. Facet filtering retains those original denominators; confidence
scores select labels and are never interpreted as probabilities.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from analysis.benchmark_lifecycle.lifecycle import build_lifecycle_tables
from scripts.analysis_utils import build_resolved_mentions, scope_models_as_of
from scripts.taxonomy_utils import CanonicalResolver, exact_key


INTERACTION_LABELS = frozenset({
    "single_turn_tool_use", "environment_interaction", "browser_or_web_interaction",
    "terminal_or_codebase_interaction", "computer_control",
})
VARIANTS = ("all_active", "confidence_ge_0_7", "accepted")
COVERAGE_COLUMNS = [
    "provider", "model_rows", "launch_events", "benchmark_bearing_launches",
    "observed_benchmarks", "first_release", "last_release",
]
ANNUAL_COLUMNS = [
    "release_year", "model_rows", "launch_events", "benchmark_bearing_launches",
    "launch_mentions", "new_identities",
]
SHARING_COLUMNS = [
    "provider_count", "benchmark_count", "benchmark_share", "launch_mentions",
    "mention_share", "announcement_weight", "announcement_weight_share",
]
DIFFUSION_COLUMNS = [
    "horizon_days", "eligible_benchmarks", "diffused_benchmarks", "diffusion_share",
]
CLASSIFICATION_COLUMNS = [
    "benchmark_id", "benchmark_name", "variant", "interaction_labels", "positive", "covered",
]
TREND_COLUMNS = [
    "unit", "release_year", "variant", "benchmark_bearing_units",
    "positive_share", "coverage_share", "positive_share_among_covered",
]


def _ratio(numerator: float, denominator: float):
    return numerator / denominator if denominator else pd.NA


def _table(rows: list[dict], columns: list[str], integers=(), floats=(), booleans=()) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=columns)
    for column in integers:
        frame[column] = pd.array(frame[column], dtype="Int64")
    for column in floats:
        frame[column] = pd.array(frame[column], dtype="Float64")
    for column in booleans:
        frame[column] = pd.array(frame[column], dtype="boolean")
    return frame


def _classify_interaction(benchmarks: pd.DataFrame, facets: pd.DataFrame) -> pd.DataFrame:
    facets = facets.reindex(columns=[
        "benchmark_id", "facet_axis", "facet_label", "classification_confidence", "review_status",
    ]).fillna("")
    for column in ["benchmark_id", "facet_axis", "facet_label", "review_status"]:
        facets[column] = facets[column].map(exact_key)
    active = facets[
        facets["facet_axis"].eq("interaction_pattern")
        & facets["review_status"].ne("deprecated")
        & facets["facet_label"].ne("")
    ]
    retained = {
        "all_active": active,
        "confidence_ge_0_7": active[
            pd.to_numeric(active["classification_confidence"], errors="coerce").ge(0.7)
        ],
        "accepted": active[active["review_status"].eq("accepted")],
    }
    labels = {
        variant: group.groupby("benchmark_id")["facet_label"].agg(lambda values: set(values)).to_dict()
        for variant, group in retained.items()
    }
    rows = []
    for benchmark in benchmarks.sort_values("benchmark_id", kind="stable").itertuples(index=False):
        for variant in VARIANTS:
            interaction_labels = labels[variant].get(benchmark.benchmark_id, set())
            rows.append({
                "benchmark_id": benchmark.benchmark_id, "benchmark_name": benchmark.benchmark_name,
                "variant": variant, "interaction_labels": "; ".join(sorted(interaction_labels)),
                "positive": bool(interaction_labels & INTERACTION_LABELS) if interaction_labels else pd.NA,
                "covered": bool(interaction_labels),
            })
    return _table(rows, CLASSIFICATION_COLUMNS, booleans=["positive", "covered"])


def _interaction_trends(
    observations: dict[str, pd.DataFrame], classification: pd.DataFrame,
    years: list[int], providers: list[str] | None = None,
) -> pd.DataFrame:
    rows = []
    scopes = providers if providers is not None else [None]
    for provider in scopes:
        for unit, inventory in observations.items():
            scoped = inventory if provider is None else inventory[inventory["provider"].eq(provider)]
            for year in years:
                annual = scoped[scoped["release_year"].eq(year)]
                unit_count = annual["unit_id"].nunique()
                for variant in VARIANTS:
                    joined = annual.merge(
                        classification[classification["variant"].eq(variant)],
                        on="benchmark_id", how="left", validate="many_to_one",
                    )
                    positive = float(joined.loc[joined["positive"].fillna(False), "weight"].sum())
                    covered = float(joined.loc[joined["covered"].fillna(False), "weight"].sum())
                    row = {
                        "unit": unit, "release_year": year, "variant": variant,
                        "benchmark_bearing_units": unit_count,
                        "positive_share": _ratio(positive, unit_count),
                        "coverage_share": _ratio(covered, unit_count),
                        "positive_share_among_covered": _ratio(positive, covered),
                    }
                    if provider is not None:
                        row["provider"] = provider
                    rows.append(row)
    columns = (["provider"] if providers is not None else []) + TREND_COLUMNS
    return _table(
        rows, columns, integers=["release_year", "benchmark_bearing_units"],
        floats=["positive_share", "coverage_share", "positive_share_among_covered"],
    )


def build_overview_tables(
    models: pd.DataFrame, benchmarks: pd.DataFrame, facets: pd.DataFrame,
    resolver: CanonicalResolver, as_of: str | None = None,
) -> tuple[dict[str, pd.DataFrame], dict]:
    """Build complete overview outputs without inferring retirement or lineage.

    Sharing bins cover observed identities; unobserved identities remain in the
    full catalog tables and summary. Diffusion horizons include every observed
    identity with the complete calendar horizon available within the source
    series, including identities
    that never appear at another provider. First-day provider ties count as lag
    zero. Separate horizons have different eligible cohorts.
    """
    lifecycles, provider_lifecycles, events, mentions, cutoff = build_lifecycle_tables(
        models, benchmarks, resolver, as_of=as_of,
    )
    inventory = models.copy()
    if inventory.empty:
        for column in ["Provider", "Model name", "link", "release date", "benchmarks"]:
            if column not in inventory:
                inventory[column] = pd.Series(dtype="object")
    scoped, _ = scope_models_as_of(inventory, cutoff.date().isoformat())
    scoped = scoped.fillna("").reset_index(drop=True)
    # The validated source date governs both units, even when callers pass an
    # enriched frame containing a stale derived release_date column.
    scoped["release_date"] = pd.to_datetime(scoped["release date"]).dt.normalize()
    canonical, _ = build_resolved_mentions(
        scoped, resolver, deduplicate_within_release=True, unresolved_policy="error",
    )
    raw, _ = build_resolved_mentions(scoped, resolver, unresolved_policy="error")
    providers = sorted({exact_key(value) for value in inventory["Provider"].fillna("")} - {""})
    years = sorted(pd.to_datetime(scoped["release date"]).dt.year.unique().tolist())
    observed = lifecycles[lifecycles["launch_count"].gt(0)]

    coverage_rows = []
    for provider in providers:
        provider_events = events[events["provider"].eq(provider)]
        coverage_rows.append({
            "provider": provider, "model_rows": int(provider_events["model_row_count"].sum()),
            "launch_events": len(provider_events),
            "benchmark_bearing_launches": int(provider_events["has_benchmark_mentions"].sum()),
            "observed_benchmarks": mentions.loc[mentions["provider"].eq(provider), "benchmark_id"].nunique(),
            "first_release": provider_events["release_date"].min() if len(provider_events) else "",
            "last_release": provider_events["release_date"].max() if len(provider_events) else "",
        })
    coverage = _table(coverage_rows, COVERAGE_COLUMNS, integers=COVERAGE_COLUMNS[1:5])

    event_years = pd.to_datetime(events["release_date"]).dt.year
    mention_years = pd.to_datetime(mentions["release_date"]).dt.year
    first_years = pd.to_datetime(observed["first_seen"]).dt.year
    annual_rows = []
    for year in years:
        annual_events = events[event_years.eq(year)]
        annual_rows.append({
            "release_year": year, "model_rows": int(annual_events["model_row_count"].sum()),
            "launch_events": len(annual_events),
            "benchmark_bearing_launches": int(annual_events["has_benchmark_mentions"].sum()),
            "launch_mentions": int(mention_years.eq(year).sum()),
            "new_identities": int(first_years.eq(year).sum()),
        })
    annual = _table(annual_rows, ANNUAL_COLUMNS, integers=ANNUAL_COLUMNS)

    weighted_mentions = mentions.merge(observed[["benchmark_id", "provider_count"]], on="benchmark_id")
    weighted_mentions["weight"] = 1.0 / weighted_mentions.groupby("launch_id")["benchmark_id"].transform("size")
    bearing_events = int(events["has_benchmark_mentions"].sum())
    sharing_rows = []
    for count in range(1, len(providers) + 1):
        benchmarks_in_bin = int(observed["provider_count"].eq(count).sum())
        bin_mentions = weighted_mentions[weighted_mentions["provider_count"].eq(count)]
        weight = float(bin_mentions["weight"].sum())
        sharing_rows.append({
            "provider_count": count, "benchmark_count": benchmarks_in_bin,
            "benchmark_share": _ratio(benchmarks_in_bin, len(observed)),
            "launch_mentions": len(bin_mentions), "mention_share": _ratio(len(bin_mentions), len(mentions)),
            "announcement_weight": weight, "announcement_weight_share": _ratio(weight, bearing_events),
        })
    sharing = _table(
        sharing_rows, SHARING_COLUMNS, integers=["provider_count", "benchmark_count", "launch_mentions"],
        floats=["benchmark_share", "mention_share", "announcement_weight", "announcement_weight_share"],
    )

    # Moving AS_OF beyond the recorded series cannot create observed follow-up.
    # Use all input dates here: later rows establish coverage for a historical
    # cutoff even though their mentions are correctly excluded from that slice.
    source_end = pd.to_datetime(inventory["release date"]).max()
    followup_end = min(cutoff, source_end.normalize()) if not pd.isna(source_end) else None
    diffusion_rows = []
    for horizon in [30, 90, 180]:
        eligible = (
            observed[observed["first_seen"].le((followup_end.date() - timedelta(days=horizon)).isoformat())]
            if followup_end is not None else observed.iloc[:0]
        )
        diffused = int(eligible["second_provider_lag_days"].le(horizon).fillna(False).sum())
        diffusion_rows.append({
            "horizon_days": horizon, "eligible_benchmarks": len(eligible),
            "diffused_benchmarks": diffused, "diffusion_share": _ratio(diffused, len(eligible)),
        })
    diffusion = _table(
        diffusion_rows, DIFFUSION_COLUMNS,
        integers=["horizon_days", "eligible_benchmarks", "diffused_benchmarks"], floats=["diffusion_share"],
    )

    classification = _classify_interaction(lifecycles[["benchmark_id", "benchmark_name"]], facets)
    announcement_observations = weighted_mentions.rename(columns={"launch_id": "unit_id"})[
        ["unit_id", "provider", "release_date", "benchmark_id", "weight"]
    ].copy()
    announcement_observations["release_year"] = pd.to_datetime(announcement_observations["release_date"]).dt.year
    model_observations = canonical.rename(columns={"model_row_id": "unit_id", "release_weight": "weight"})[
        ["unit_id", "provider", "release_year", "benchmark_id", "weight"]
    ].copy()
    observations = {"announcement": announcement_observations, "model_row": model_observations}
    trends = _interaction_trends(observations, classification, years)
    provider_trends = _interaction_trends(observations, classification, years, providers)

    shared = observed[observed["provider_count"].gt(1)]
    shared_bins = sharing[sharing["provider_count"].gt(1)]
    shared_lags = shared["second_provider_lag_days"].dropna()
    latest_year = max(years) if years else None
    summary = {
        "as_of": cutoff.date().isoformat(), "model_rows": len(scoped), "launch_events": len(events),
        "diffusion_followup_end": followup_end.date().isoformat() if followup_end is not None else None,
        "benchmark_bearing_launches": bearing_events, "catalog_benchmarks": len(lifecycles),
        "observed_benchmarks": len(observed), "raw_model_mentions": len(raw),
        "canonical_model_mentions": len(canonical), "launch_mentions": len(mentions),
        "single_launch_benchmarks": int(observed["launch_count"].eq(1).sum()),
        "shared_benchmarks": len(shared),
        "shared_mention_share": int(shared["launch_count"].sum()) / len(mentions) if len(mentions) else None,
        "shared_announcement_weight_share": float(shared_bins["announcement_weight"].sum()) / bearing_events if bearing_events else None,
        "all_three_benchmarks": int(observed["provider_count"].eq(3).sum()),
        "shared_conditional_median_lag_days": float(shared_lags.median()) if len(shared_lags) else None,
        "latest_release_year": int(latest_year) if latest_year is not None else None,
        "single_launch_first_seen_latest_year": int((observed["launch_count"].eq(1) & first_years.eq(latest_year)).sum()) if latest_year is not None else 0,
        "facet_rows": len(facets),
        "facet_accepted": int(facets.get("review_status", pd.Series(dtype="object")).eq("accepted").sum()),
        "facet_needs_review": int(facets.get("review_status", pd.Series(dtype="object")).eq("needs_review").sum()),
        "facet_legacy_seed": int(facets.get("review_status", pd.Series(dtype="object")).eq("legacy_seed").sum()),
    }
    tables = {
        "coverage_by_provider": coverage, "annual_inventory": annual, "sharing_summary": sharing,
        "diffusion_horizons": diffusion, "interaction_classification": classification,
        "interaction_trends": trends, "provider_interaction_trends": provider_trends,
        "lifecycle": lifecycles, "provider_lifecycle": provider_lifecycles,
        "lifecycles": lifecycles, "provider_lifecycles": provider_lifecycles,
        "launch_events": events, "launch_mentions": mentions, "canonical_model_mentions": canonical,
    }
    return tables, summary
