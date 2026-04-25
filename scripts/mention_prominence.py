#!/usr/bin/env python3
"""Manual release mention prominence overrides.

Prominence is intentionally sourced from a local override CSV. This module does
not fetch or scrape provider pages; reviewers add source-backed rows explicitly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set, Tuple

import pandas as pd

from taxonomy_utils import (
    ALLOWED_MENTION_PROMINENCE,
    ALLOWED_REVIEW_STATUS,
    MENTION_PROMINENCE_DEFAULT,
    MENTION_PROMINENCE_WEIGHTS,
)


REQUIRED_PROMINENCE_OVERRIDE_COLUMNS = {
    "mention_id",
    "mention_prominence",
    "evidence_id",
    "review_status",
    "rationale",
}


def empty_prominence_overrides_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=sorted(REQUIRED_PROMINENCE_OVERRIDE_COLUMNS))


def read_prominence_overrides(path: Path) -> pd.DataFrame:
    if not path.exists():
        return empty_prominence_overrides_frame()

    overrides = pd.read_csv(path).fillna("")
    missing = REQUIRED_PROMINENCE_OVERRIDE_COLUMNS - set(overrides.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return overrides


def coerce_prominence(value: str) -> str:
    prominence = str(value or "").strip()
    return prominence or MENTION_PROMINENCE_DEFAULT


def weight_for_prominence(prominence: str) -> float:
    prominence = coerce_prominence(prominence)
    if prominence not in MENTION_PROMINENCE_WEIGHTS:
        raise ValueError(f"Invalid mention_prominence value: {prominence!r}")
    return MENTION_PROMINENCE_WEIGHTS[prominence]


def apply_prominence_weights(release_mentions: pd.DataFrame) -> pd.DataFrame:
    release_mentions = release_mentions.copy()
    release_mentions["mention_prominence"] = release_mentions["mention_prominence"].map(coerce_prominence)
    release_mentions["mention_weight"] = release_mentions["mention_prominence"].map(weight_for_prominence)
    return release_mentions


def active_prominence_overrides(overrides: pd.DataFrame) -> pd.DataFrame:
    if overrides.empty:
        return overrides.copy()
    return overrides[overrides["review_status"].map(str).str.strip() != "deprecated"].copy()


def validate_prominence_overrides(
    overrides: pd.DataFrame,
    *,
    known_mention_ids: Optional[Set[str]] = None,
    known_evidence_ids: Optional[Set[str]] = None,
) -> Tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing = REQUIRED_PROMINENCE_OVERRIDE_COLUMNS - set(overrides.columns)
    if missing:
        return [f"mention prominence overrides missing required columns: {sorted(missing)}"], warnings

    if overrides.empty:
        return errors, warnings

    normalized = overrides.fillna("").copy()
    for column in REQUIRED_PROMINENCE_OVERRIDE_COLUMNS:
        normalized[column] = normalized[column].map(lambda value: str(value).strip())

    empty_mentions = normalized[normalized["mention_id"] == ""].index.tolist()
    if empty_mentions:
        errors.append(
            "mention prominence overrides have empty mention_id values on rows "
            f"{[idx + 2 for idx in empty_mentions]}"
        )

    duplicate_ids = normalized[normalized["mention_id"] != ""]["mention_id"]
    duplicates = sorted(value for value in duplicate_ids[duplicate_ids.duplicated()].unique())
    if duplicates:
        errors.append(f"mention prominence overrides have duplicate mention_id values: {duplicates}")

    invalid_prominence = sorted(set(normalized["mention_prominence"]) - ALLOWED_MENTION_PROMINENCE - {""})
    if invalid_prominence:
        errors.append(
            "mention prominence overrides have invalid mention_prominence values "
            f"{invalid_prominence}; use explicit labels only, or remove the row to keep "
            f"{MENTION_PROMINENCE_DEFAULT!r}"
        )

    blank_prominence = normalized[normalized["mention_prominence"] == ""].index.tolist()
    if blank_prominence:
        errors.append(
            "mention prominence overrides have blank mention_prominence values on rows "
            f"{[idx + 2 for idx in blank_prominence]}"
        )

    invalid_statuses = sorted(set(normalized["review_status"]) - ALLOWED_REVIEW_STATUS - {""})
    if invalid_statuses:
        errors.append(f"mention prominence overrides have invalid review_status values: {invalid_statuses}")

    blank_status = normalized[normalized["review_status"] == ""].index.tolist()
    if blank_status:
        errors.append(
            "mention prominence overrides have blank review_status values on rows "
            f"{[idx + 2 for idx in blank_status]}"
        )

    if known_mention_ids is not None:
        missing_mentions = sorted(set(normalized["mention_id"]) - known_mention_ids - {""})
        if missing_mentions:
            errors.append(f"mention prominence overrides reference missing mention_id values: {missing_mentions}")

    if known_evidence_ids is not None:
        missing_evidence = sorted(set(normalized["evidence_id"]) - known_evidence_ids - {""})
        if missing_evidence:
            errors.append(f"mention prominence overrides reference missing evidence_id values: {missing_evidence}")

    accepted_without_evidence = normalized[
        (normalized["review_status"] == "accepted") & (normalized["evidence_id"] == "")
    ].index.tolist()
    if accepted_without_evidence:
        errors.append(
            "accepted mention prominence overrides must cite evidence_id values on rows "
            f"{[idx + 2 for idx in accepted_without_evidence]}"
        )

    missing_rationale = normalized[
        (normalized["review_status"].isin(["accepted", "disputed"])) & (normalized["rationale"] == "")
    ].index.tolist()
    if missing_rationale:
        warnings.append(
            "accepted or disputed mention prominence overrides should include rationale on rows "
            f"{[idx + 2 for idx in missing_rationale]}"
        )

    return errors, warnings


def apply_prominence_overrides(
    release_mentions: pd.DataFrame,
    overrides: pd.DataFrame,
    *,
    strict: bool = True,
) -> tuple[pd.DataFrame, int]:
    errors, _ = validate_prominence_overrides(
        overrides,
        known_mention_ids=set(release_mentions["mention_id"]) if "mention_id" in release_mentions.columns else None,
    )
    if errors and strict:
        raise ValueError("; ".join(errors))

    updated = apply_prominence_weights(release_mentions)
    if overrides.empty:
        return updated, 0

    active = active_prominence_overrides(overrides)
    if active.empty:
        return updated, 0

    active_by_id = active.set_index("mention_id")
    known_mention_ids = set(updated["mention_id"])
    for mention_id, row in active_by_id.iterrows():
        prominence = str(row["mention_prominence"]).strip()
        if mention_id not in known_mention_ids:
            continue
        updated.loc[updated["mention_id"] == mention_id, "mention_prominence"] = prominence

    updated = apply_prominence_weights(updated)
    return updated, len(active_by_id)
