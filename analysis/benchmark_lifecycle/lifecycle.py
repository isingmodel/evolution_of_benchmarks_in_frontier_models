"""Observed benchmark reporting histories, measured in release-page launches.

The tables describe appearances in tracked release pages. Their dates are not
benchmark publication dates, and a reporting gap does not establish retirement,
saturation, or replacement by another version.
"""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from numbers import Integral
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd

from scripts.analysis_utils import build_resolved_mentions, scope_models_as_of
from scripts.taxonomy_utils import CanonicalResolver, exact_key


LIFECYCLE_COLUMNS = [
    "benchmark_id", "benchmark_name", "review_status", "reporting_pattern",
    "first_seen", "last_seen", "observed_span_days", "days_since_last_seen",
    "launch_count", "model_row_count", "provider_count", "first_providers",
    "second_provider_date", "second_provider_lag_days", "third_provider_date",
    "third_provider_lag_days", "recent_launch_count", "adopter_followup_launches",
    "adopter_followup_mention_launches", "followup_mention_share",
    "adopter_launches_after_last_seen", "largest_within_provider_gap_launches",
]
PROVIDER_LIFECYCLE_COLUMNS = [
    "benchmark_id", "benchmark_name", "review_status", "provider",
    "first_seen", "last_seen", "observed_span_days", "launch_count",
    "model_row_count", "followup_launches", "followup_mention_launches",
    "followup_mention_share", "launches_after_last_seen", "days_since_last_seen",
    "largest_gap_launches",
]
LAUNCH_COLUMNS = [
    "launch_id", "provider", "release_date", "source_url", "model_names",
    "model_row_count", "benchmark_count", "has_benchmark_mentions",
]
LAUNCH_MENTION_COLUMNS = [
    "benchmark_id", "benchmark_name", "launch_id", "provider", "release_date",
    "source_url", "model_names", "model_row_count",
]

_LIFECYCLE_INTEGERS = [
    "observed_span_days", "days_since_last_seen", "launch_count", "model_row_count",
    "provider_count", "second_provider_lag_days", "third_provider_lag_days",
    "recent_launch_count", "adopter_followup_launches",
    "adopter_followup_mention_launches", "adopter_launches_after_last_seen",
    "largest_within_provider_gap_launches",
]
_PROVIDER_INTEGERS = [
    "observed_span_days", "launch_count", "model_row_count", "followup_launches",
    "followup_mention_launches", "launches_after_last_seen", "days_since_last_seen",
    "largest_gap_launches",
]


def normalize_source_url(value: object) -> str:
    """Remove reporting-irrelevant URL variants, retaining substantive queries.

    Query order and repeated nontracking parameters are retained. Path case and
    query values remain significant; fragments, trailing slashes, and common
    tracking parameters do not distinguish a launch.
    """
    # Taxonomy matching uses Unicode compatibility normalization, which is not
    # valid for URLs: e.g. /Ａ and /A can identify different source pages.
    url = "" if value is None or pd.isna(value) else str(value).strip()
    parts = urlsplit(url)
    query = [
        (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in {"gclid", "fbclid"}
    ]
    return urlunsplit((
        parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"),
        urlencode(query), "",
    ))


def _launch_id(key: tuple[str, str, str]) -> str:
    encoded = json.dumps(key, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "launch_" + hashlib.sha256(encoded).hexdigest()[:20]


def _frame(rows: list[dict], columns: list[str], integers: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=columns)
    for column in integers:
        frame[column] = pd.array(frame[column], dtype="Int64")
    if "followup_mention_share" in columns:
        frame["followup_mention_share"] = pd.array(
            frame["followup_mention_share"], dtype="Float64",
        )
    if "has_benchmark_mentions" in columns:
        frame["has_benchmark_mentions"] = frame["has_benchmark_mentions"].astype(bool)
    return frame


def _provider_metrics(mentions: list[dict], events: list[dict], cutoff: pd.Timestamp) -> dict:
    """Measure follow-up only after a provider's first observed adoption date."""
    if not mentions:
        return {
            "first_seen": "", "last_seen": "", "observed_span_days": pd.NA,
            "launch_count": 0, "model_row_count": 0, "followup_launches": pd.NA,
            "followup_mention_launches": pd.NA, "followup_mention_share": pd.NA,
            "launches_after_last_seen": pd.NA, "days_since_last_seen": pd.NA,
            "largest_gap_launches": pd.NA,
        }

    mention_dates = sorted({row["release_date"] for row in mentions})
    first, last = mention_dates[0], mention_dates[-1]
    followups = sum(event["release_date"] > first for event in events)
    followup_mentions = sum(row["release_date"] > first for row in mentions)
    # Within-day order is unknown. Only intervening dates define a reporting gap.
    largest_gap = max((
        sum(left < event["release_date"] < right for event in events)
        for left, right in zip(mention_dates, mention_dates[1:])
    ), default=0)
    return {
        "first_seen": first, "last_seen": last,
        "observed_span_days": (pd.Timestamp(last) - pd.Timestamp(first)).days,
        "launch_count": len(mentions),
        "model_row_count": sum(row["model_row_count"] for row in mentions),
        "followup_launches": followups,
        "followup_mention_launches": followup_mentions,
        "followup_mention_share": followup_mentions / followups if followups else pd.NA,
        "launches_after_last_seen": sum(event["release_date"] > last for event in events),
        "days_since_last_seen": (cutoff - pd.Timestamp(last)).days,
        "largest_gap_launches": largest_gap,
    }


def build_lifecycle_tables(
    models: pd.DataFrame,
    benchmarks: pd.DataFrame,
    resolver: CanonicalResolver,
    as_of: str | None = None,
    recent_window_days: int = 180,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Return catalog, provider, launch, and launch-mention histories plus cutoff.

    A launch is a provider/date/normalized-source-URL event, including pages with
    empty benchmark lists. Canonical mentions are deduplicated within each input
    model row and then within each launch. Model-row counts remain separate.

    All catalog rows survive the cutoff. Provider rows cross that catalog with
    providers in the original, unscoped model inventory. An unadopted benchmark
    has zero presence counts and missing follow-up/gap metrics; observed adopters
    with no later launches have zero opportunities and a missing reporting share.
    """
    if (
        isinstance(recent_window_days, bool)
        or not isinstance(recent_window_days, Integral)
        or recent_window_days <= 0
    ):
        raise ValueError("recent_window_days must be a positive integer")
    if models.empty and not as_of:
        raise ValueError("An explicit as_of date is required when models is empty")

    inventory = models.copy()
    if inventory.empty:
        for column in ["Provider", "Model name", "link", "release date", "benchmarks"]:
            if column not in inventory:
                inventory[column] = pd.Series(dtype="object")
    inventory_dates = pd.to_datetime(inventory["release date"], errors="raise")
    if inventory_dates.isna().any():
        raise ValueError("Every model row must have a valid release date before cutoff filtering")
    providers = sorted({exact_key(value) for value in inventory["Provider"].fillna("")} - {""})
    scoped, cutoff = scope_models_as_of(inventory, as_of)
    if pd.isna(cutoff):
        raise ValueError("Cannot determine a cutoff from models; provide an explicit as_of date")
    scoped = scoped.fillna("").reset_index(drop=True)
    dates = pd.to_datetime(scoped["release date"], errors="raise")
    if dates.isna().any():
        raise ValueError("Every scoped model row must have a valid release date")
    # Keep the shared resolver's date choice aligned with the shared scope helper.
    scoped["release_date"] = dates.dt.normalize()
    resolved, _ = build_resolved_mentions(
        scoped, resolver, deduplicate_within_release=True, unresolved_policy="error",
    )

    catalog = benchmarks.reindex(columns=["benchmark_id", "benchmark_name", "review_status"])
    catalog = catalog.fillna("")
    for column in ["benchmark_id", "review_status"]:
        catalog[column] = catalog[column].map(exact_key)
    # Keep canonical display labels faithful to the catalog, including τ³.
    catalog["benchmark_name"] = catalog["benchmark_name"].map(lambda value: str(value).strip())
    if catalog["benchmark_id"].duplicated().any():
        raise ValueError("The benchmark catalog must have unique benchmark_id values")
    if (catalog["benchmark_id"] == "").any() or (catalog["benchmark_name"] == "").any():
        raise ValueError("Every catalog row requires benchmark_id and benchmark_name")
    catalog = catalog.sort_values("benchmark_id", kind="stable")
    catalog_names = dict(zip(catalog["benchmark_id"], catalog["benchmark_name"]))
    absent_ids = set(resolved["benchmark_id"]) - set(catalog_names)
    if absent_ids:
        raise ValueError(f"Resolved benchmark IDs absent from catalog: {sorted(absent_ids)}")

    events_by_key: dict[tuple[str, str, str], dict] = {}
    row_keys: dict[int, tuple[str, str, str]] = {}
    for row_id, model in scoped.iterrows():
        provider = exact_key(model["Provider"])
        source_url = normalize_source_url(model.get("link", ""))
        if not provider:
            raise ValueError("Every scoped model row requires a nonempty Provider")
        source_parts = urlsplit(source_url)
        if source_parts.scheme not in {"http", "https"} or not source_parts.hostname:
            raise ValueError("Every scoped model row requires an absolute HTTP(S) source URL")
        key = (
            provider,
            model["release_date"].strftime("%Y-%m-%d"),
            source_url,
        )
        row_keys[row_id] = key
        event = events_by_key.setdefault(key, {
            "launch_id": _launch_id(key), "provider": key[0], "release_date": key[1],
            "source_url": key[2], "_model_names": set(), "model_row_count": 0,
            "_benchmark_ids": set(),
        })
        event["_model_names"].add(exact_key(model.get("Model name", "")))
        event["model_row_count"] += 1

    mentions_by_key: dict[tuple[str, tuple[str, str, str]], dict] = {}
    for mention in resolved.to_dict("records"):
        benchmark_id = mention["benchmark_id"]
        row_id = int(mention["model_row_id"])
        key = row_keys[row_id]
        event = events_by_key[key]
        event["_benchmark_ids"].add(benchmark_id)
        entry = mentions_by_key.setdefault((benchmark_id, key), {
            "benchmark_id": benchmark_id, "benchmark_name": catalog_names[benchmark_id],
            "launch_id": event["launch_id"], "provider": key[0], "release_date": key[1],
            "source_url": key[2], "_model_names": set(), "_model_row_ids": set(),
        })
        entry["_model_names"].add(mention["model_name"])
        entry["_model_row_ids"].add(row_id)

    launch_rows = []
    for event in events_by_key.values():
        launch_rows.append({
            **{key: value for key, value in event.items() if not key.startswith("_")},
            "model_names": "; ".join(sorted(event["_model_names"] - {""})),
            "benchmark_count": len(event["_benchmark_ids"]),
            "has_benchmark_mentions": bool(event["_benchmark_ids"]),
        })
    launch_rows.sort(key=lambda row: (
        row["release_date"], row["provider"], row["source_url"], row["launch_id"],
    ))
    mention_rows = []
    for entry in mentions_by_key.values():
        mention_rows.append({
            **{key: value for key, value in entry.items() if not key.startswith("_")},
            "model_names": "; ".join(sorted(entry["_model_names"] - {""})),
            "model_row_count": len(entry["_model_row_ids"]),
        })
    mention_rows.sort(key=lambda row: (
        row["release_date"], row["provider"], row["source_url"], row["benchmark_id"],
    ))

    events_by_provider = {provider: [] for provider in providers}
    for event in launch_rows:
        events_by_provider[event["provider"]].append(event)
    mentions_by_benchmark: dict[str, list[dict]] = {key: [] for key in catalog_names}
    for entry in mention_rows:
        mentions_by_benchmark[entry["benchmark_id"]].append(entry)

    lifecycle_rows = []
    provider_rows = []
    recent_start = (cutoff.date() - timedelta(days=int(recent_window_days) - 1)).isoformat()
    for benchmark in catalog.to_dict("records"):
        benchmark_id = benchmark["benchmark_id"]
        mentions = mentions_by_benchmark[benchmark_id]
        adopter_metrics = {}
        for provider in providers:
            provider_mentions = [row for row in mentions if row["provider"] == provider]
            metrics = _provider_metrics(provider_mentions, events_by_provider[provider], cutoff)
            provider_rows.append({**benchmark, "provider": provider, **metrics})
            if provider_mentions:
                adopter_metrics[provider] = metrics

        lifecycle = {
            **benchmark, "reporting_pattern": "unobserved", "first_seen": "",
            "last_seen": "", "observed_span_days": pd.NA, "days_since_last_seen": pd.NA,
            "launch_count": 0, "model_row_count": 0, "provider_count": 0,
            "first_providers": "", "second_provider_date": "",
            "second_provider_lag_days": pd.NA, "third_provider_date": "",
            "third_provider_lag_days": pd.NA, "recent_launch_count": 0,
            "adopter_followup_launches": pd.NA, "adopter_followup_mention_launches": pd.NA,
            "followup_mention_share": pd.NA, "adopter_launches_after_last_seen": pd.NA,
            "largest_within_provider_gap_launches": pd.NA,
        }
        if mentions:
            first = min(row["release_date"] for row in mentions)
            last = max(row["release_date"] for row in mentions)
            adoption_order = sorted(adopter_metrics, key=lambda p: (adopter_metrics[p]["first_seen"], p))
            followups = sum(row["followup_launches"] for row in adopter_metrics.values())
            followup_mentions = sum(row["followup_mention_launches"] for row in adopter_metrics.values())
            lifecycle.update({
                "reporting_pattern": (
                    "shared_across_providers" if len(adopter_metrics) > 1
                    else "single_launch" if len(mentions) == 1
                    else "repeated_one_provider"
                ),
                "first_seen": first, "last_seen": last,
                "observed_span_days": (pd.Timestamp(last) - pd.Timestamp(first)).days,
                "days_since_last_seen": (cutoff - pd.Timestamp(last)).days,
                "launch_count": len(mentions),
                "model_row_count": sum(row["model_row_count"] for row in mentions),
                "provider_count": len(adopter_metrics),
                "first_providers": "; ".join(sorted(
                    p for p, row in adopter_metrics.items() if row["first_seen"] == first
                )),
                "recent_launch_count": sum(row["release_date"] >= recent_start for row in mentions),
                "adopter_followup_launches": followups,
                "adopter_followup_mention_launches": followup_mentions,
                "followup_mention_share": followup_mentions / followups if followups else pd.NA,
                "adopter_launches_after_last_seen": sum(
                    event["release_date"] > last
                    for provider in adopter_metrics for event in events_by_provider[provider]
                ),
                "largest_within_provider_gap_launches": max(
                    row["largest_gap_launches"] for row in adopter_metrics.values()
                ),
            })
            for position, label in [(1, "second"), (2, "third")]:
                if len(adoption_order) > position:
                    adoption_date = adopter_metrics[adoption_order[position]]["first_seen"]
                    lifecycle[f"{label}_provider_date"] = adoption_date
                    lifecycle[f"{label}_provider_lag_days"] = (
                        pd.Timestamp(adoption_date) - pd.Timestamp(first)
                    ).days
        lifecycle_rows.append(lifecycle)

    return (
        _frame(lifecycle_rows, LIFECYCLE_COLUMNS, _LIFECYCLE_INTEGERS),
        _frame(provider_rows, PROVIDER_LIFECYCLE_COLUMNS, _PROVIDER_INTEGERS),
        _frame(launch_rows, LAUNCH_COLUMNS, ["model_row_count", "benchmark_count"]),
        _frame(mention_rows, LAUNCH_MENTION_COLUMNS, ["model_row_count"]),
        cutoff,
    )
