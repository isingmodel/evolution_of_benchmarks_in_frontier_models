from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import pandas as pd

from scripts.taxonomy_utils import (
    ALLOWED_ALIAS_MATCH_TYPE,
    ALLOWED_FACET_AXIS,
    ALLOWED_FACET_LABELS,
    ALLOWED_REVIEW_STATUS,
    ALLOWED_TASK_DOMAIN,
    ALLOWED_TASK_MODE,
    REQUIRED_FACET_AXES,
    REVIEW_CONFIDENCE_THRESHOLD,
    CanonicalResolver,
    benchmark_id,
    derive_headline_projection,
    exact_key,
    identity_key,
    split_benchmark_mentions,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

REQUIRED_MODEL_COLUMNS = {"Provider", "Model name", "link", "release date", "benchmarks"}
REQUIRED_ALIAS_COLUMNS = {"alias", "benchmark_id", "match_type", "notes"}
REQUIRED_DISTINCTNESS_COLUMNS = {"benchmark_id_a", "benchmark_id_b", "note"}
REQUIRED_BENCHMARK_COLUMNS = {
    "benchmark_id",
    "benchmark_name",
    "reference_link",
    "source_author",
    "frontier_lab_author_affiliations",
    "legacy_task_mode",
    "legacy_task_domain",
    "legacy_rationale",
    "review_status",
}
REQUIRED_FACET_COLUMNS = {
    "benchmark_id",
    "facet_axis",
    "facet_label",
    "classification_confidence",
    "review_status",
    "rationale",
}
REQUIRED_MANUAL_FACET_COLUMNS = {
    "facet_axis",
    "facet_label",
    "classification_confidence",
    "review_status",
    "rationale",
}
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
VALID_FACET_STATUSES = set(ALLOWED_REVIEW_STATUS)
VALID_FACET_AXES = set(ALLOWED_FACET_AXIS)
ALLOWED_FRONTIER_LAB_AUTHOR_AFFILIATIONS = {
    "OpenAI",
    "Anthropic",
    "Google",
    "DeepMind",
    "Microsoft",
    "xAI",
}
NEAR_DUPLICATE_RATIO_THRESHOLD = 0.92
NEAR_DUPLICATE_CONTAINMENT_MIN_LENGTH = 7


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, message):
        self.errors.append(message)

    def warning(self, message):
        self.warnings.append(message)

    def require_columns(self, df, required, label):
        missing = required - set(df.columns)
        if missing:
            self.error(f"{label} missing required columns: {sorted(missing)}")

    def print(self):
        if self.errors:
            print("Validation errors:")
            for message in self.errors:
                print(f"- {message}")
        if self.warnings:
            print("Validation warnings:")
            for message in self.warnings:
                print(f"- {message}")
        if not self.errors and not self.warnings:
            print("Validation passed with no warnings.")
        elif not self.errors:
            print("Validation passed with warnings.")


def stable_id(prefix, *parts):
    raw = " ".join(str(part) for part in parts if str(part).strip())
    slug = re.sub(r"[^a-z0-9]+", "_", raw.casefold()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return f"{prefix}_{slug or 'unknown'}"


def duplicate_values(values):
    counts = Counter(values)
    return {value: count for value, count in counts.items() if value and count > 1}


def load_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


def normalize_benchmark_frame(report, benchmarks, label):
    if "benchmark_name" not in benchmarks.columns:
        report.error(f"{label} missing benchmark_name column")
        return benchmarks

    report.require_columns(benchmarks, REQUIRED_BENCHMARK_COLUMNS, label)
    return benchmarks


def normalized_edit_name(value: str) -> str:
    """Normalize names only for duplicate detection, never for resolution."""
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def normalized_name_tokens(value: str) -> tuple[str, ...]:
    """Split a canonical name at punctuation and whitespace boundaries."""
    return tuple(re.findall(r"[a-z0-9]+", str(value).casefold()))


def has_name_containment(left_name: str, right_name: str) -> bool:
    """Return whether the shorter name occurs as whole consecutive tokens."""
    left_tokens = normalized_name_tokens(left_name)
    right_tokens = normalized_name_tokens(right_name)
    if not left_tokens or not right_tokens or left_tokens == right_tokens:
        return False

    if len(normalized_edit_name(left_name)) <= len(normalized_edit_name(right_name)):
        shorter, longer = left_tokens, right_tokens
    else:
        shorter, longer = right_tokens, left_tokens

    # Seven characters admits "Firefox" while excluding terse benchmark
    # acronyms such as ARC, HLE, GPQA, and MMLU that would create noisy matches.
    if len("".join(shorter)) < NEAR_DUPLICATE_CONTAINMENT_MIN_LENGTH:
        return False

    width = len(shorter)
    return any(
        longer[index : index + width] == shorter
        for index in range(len(longer) - width + 1)
    )


def find_near_duplicate_benchmarks(
    benchmarks: pd.DataFrame,
    threshold: float = NEAR_DUPLICATE_RATIO_THRESHOLD,
) -> list[tuple[str, str, str, str, float]]:
    """Return suspicious identities while leaving every research row intact."""
    rows = benchmarks[["benchmark_id", "benchmark_name"]].to_dict(orient="records")
    near_duplicates = []
    for left, right in combinations(rows, 2):
        left_name = normalized_edit_name(left["benchmark_name"])
        right_name = normalized_edit_name(right["benchmark_name"])
        if not left_name or not right_name:
            continue
        ratio = SequenceMatcher(None, left_name, right_name).ratio()
        if ratio > threshold or has_name_containment(
            left["benchmark_name"],
            right["benchmark_name"],
        ):
            near_duplicates.append(
                (
                    str(left["benchmark_id"]),
                    str(left["benchmark_name"]),
                    str(right["benchmark_id"]),
                    str(right["benchmark_name"]),
                    ratio,
                )
            )
    return near_duplicates


def validate_benchmark_distinctness(
    report: Report,
    benchmarks: pd.DataFrame,
    distinctness_path: Path,
) -> None:
    """Warn on unresolved near-duplicates and validate explicit decisions."""
    reviewed_pairs: set[frozenset[str]] = set()
    if distinctness_path.exists():
        distinctness = load_csv(distinctness_path)
        report.require_columns(
            distinctness,
            REQUIRED_DISTINCTNESS_COLUMNS,
            str(distinctness_path),
        )
        if REQUIRED_DISTINCTNESS_COLUMNS.issubset(distinctness.columns):
            canonical_ids = set(benchmarks["benchmark_id"])
            seen_pairs: set[frozenset[str]] = set()
            for index, row in distinctness.iterrows():
                left = exact_key(row["benchmark_id_a"])
                right = exact_key(row["benchmark_id_b"])
                note = exact_key(row["note"])
                pair = frozenset({left, right})
                line_number = index + 2
                if not left or not right or left == right:
                    report.error(
                        f"{distinctness_path} line {line_number} must name two distinct benchmark IDs"
                    )
                    continue
                missing = sorted({left, right} - canonical_ids)
                if missing:
                    report.error(
                        f"{distinctness_path} line {line_number} references missing benchmark IDs: {missing}"
                    )
                    continue
                if not note:
                    report.error(
                        f"{distinctness_path} line {line_number} needs a review justification"
                    )
                if pair in seen_pairs:
                    report.error(
                        f"{distinctness_path} has a duplicate reviewed pair at line {line_number}"
                    )
                    continue
                seen_pairs.add(pair)
                reviewed_pairs.add(pair)

    unresolved = []
    for left_id, left_name, right_id, right_name, ratio in find_near_duplicate_benchmarks(
        benchmarks
    ):
        if frozenset({left_id, right_id}) in reviewed_pairs:
            continue
        unresolved.append(
            f"{left_name!r} ({left_id}) / {right_name!r} ({right_id}), ratio={ratio:.3f}"
        )
    if unresolved:
        report.warning(
            "Near-duplicate canonical benchmark identities need an explicit "
            "distinctness decision "
            f"(ratio > {NEAR_DUPLICATE_RATIO_THRESHOLD:.2f} or whole-token containment "
            f"with shorter name >= {NEAR_DUPLICATE_CONTAINMENT_MIN_LENGTH} characters): "
            + "; ".join(unresolved)
        )


def iter_legacy_mentions(models):
    for _, row in models.fillna("").iterrows():
        provider = exact_key(row.get("Provider", ""))
        model_name = exact_key(row.get("Model name", ""))
        release_date = exact_key(row.get("release date", ""))
        source_url = exact_key(row.get("link", ""))
        model_id = stable_id("model", provider, model_name, release_date)
        for mention_index, raw_mention in enumerate(split_benchmark_mentions(row.get("benchmarks", "")), start=1):
            yield {
                "provider": provider,
                "model_name": model_name,
                "release_date": release_date,
                "source_url": source_url,
                "model_id": model_id,
                "mention_index": mention_index,
                "raw_mention": raw_mention,
                "mention_id": stable_id("mention", model_id, f"{mention_index:03d}"),
            }


def validate_legacy(
    report,
    models_path=None,
    benchmarks_path=None,
    alias_path=None,
    distinctness_path=None,
):
    models_path = Path(models_path) if models_path else DATA_DIR / "models.csv"
    benchmarks_path = Path(benchmarks_path) if benchmarks_path else DATA_DIR / "benchmarks.csv"
    alias_path = Path(alias_path) if alias_path else DATA_DIR / "benchmark_aliases.csv"
    distinctness_path = (
        Path(distinctness_path)
        if distinctness_path
        else benchmarks_path.parent / "benchmark_distinctness.csv"
    )

    models = load_csv(models_path)
    benchmarks = load_csv(benchmarks_path)
    aliases = load_csv(alias_path)

    report.require_columns(models, REQUIRED_MODEL_COLUMNS, str(models_path))
    benchmarks = normalize_benchmark_frame(report, benchmarks, str(benchmarks_path))
    if alias_path.exists():
        report.require_columns(aliases, REQUIRED_ALIAS_COLUMNS, str(alias_path))

    if report.errors:
        return models, benchmarks, aliases, None

    bad_dates = models[pd.to_datetime(models["release date"], errors="coerce").isna()]["Model name"].tolist()
    if bad_dates:
        report.error(f"Invalid model release dates: {bad_dates}")

    duplicate_canonical = duplicate_values(identity_key(name) for name in benchmarks["benchmark_name"])
    if duplicate_canonical:
        examples = []
        for key in duplicate_canonical:
            names = benchmarks[benchmarks["benchmark_name"].map(identity_key) == key]["benchmark_name"].tolist()
            examples.append(f"{key}: {names}")
        report.error(f"Duplicate canonical benchmark names after normalization: {examples}")

    validate_benchmark_distinctness(report, benchmarks, distinctness_path)

    invalid_modes = sorted(set(benchmarks["legacy_task_mode"]) - ALLOWED_TASK_MODE - {""})
    if invalid_modes:
        report.error(f"Invalid legacy_task_mode values: {invalid_modes}")

    invalid_domains = sorted(set(benchmarks["legacy_task_domain"]) - ALLOWED_TASK_DOMAIN - {""})
    if invalid_domains:
        report.error(f"Invalid legacy_task_domain values: {invalid_domains}")

    canonical_ids = set(benchmarks["benchmark_id"])
    if alias_path.exists():
        empty_aliases = aliases[aliases["alias"].map(exact_key) == ""].index.tolist()
        if empty_aliases:
            report.error(f"Alias rows with empty alias values: {[idx + 2 for idx in empty_aliases]}")

        empty_targets = aliases[aliases["benchmark_id"].map(exact_key) == ""].index.tolist()
        if empty_targets:
            report.error(f"Alias rows with empty benchmark_id values: {[idx + 2 for idx in empty_targets]}")

        duplicate_aliases = duplicate_values(identity_key(alias) for alias in aliases["alias"])
        if duplicate_aliases:
            report.error(f"Duplicate aliases after normalization: {sorted(duplicate_aliases)}")

        missing_targets = sorted(set(aliases["benchmark_id"]) - canonical_ids - {""})
        if missing_targets:
            report.error(f"Alias benchmark_id targets missing from benchmarks: {missing_targets}")

        invalid_match_types = sorted(set(aliases["match_type"]) - ALLOWED_ALIAS_MATCH_TYPE - {""})
        if invalid_match_types:
            report.error(f"Invalid alias match_type values: {invalid_match_types}")

        canonical_by_exact = {
            exact_key(row["benchmark_name"]): row["benchmark_id"]
            for _, row in benchmarks.iterrows()
            if exact_key(row["benchmark_name"])
        }
        shadowing_aliases = []
        for _, row in aliases.iterrows():
            alias = exact_key(row.get("alias", ""))
            target = exact_key(row.get("benchmark_id", ""))
            if alias in canonical_by_exact and canonical_by_exact[alias] != target:
                shadowing_aliases.append(f"{alias} -> {target}, canonical target is {canonical_by_exact[alias]}")
        if shadowing_aliases:
            report.error(f"Aliases shadow canonical benchmark names with different targets: {shadowing_aliases}")

    try:
        resolver = CanonicalResolver.from_files(benchmarks_path, alias_path if alias_path.exists() else None)
    except Exception as exc:
        report.error(f"Failed to build canonical resolver: {exc}")
        return models, benchmarks, aliases, None

    unresolved = []
    mention_count = 0
    raw_mention_keys = set()
    for mention in iter_legacy_mentions(models):
        mention_count += 1
        raw_mention_keys.add(exact_key(mention["raw_mention"]))
        if not resolver.resolve(mention["raw_mention"]):
            unresolved.append(f"{mention['provider']} / {mention['model_name']} / {mention['raw_mention']}")

    if unresolved:
        report.error(f"Unresolved benchmark mentions without fuzzy matching: {unresolved}")
    else:
        print(f"Resolved {mention_count}/{mention_count} benchmark mentions by exact canonical name or explicit alias.")

    if alias_path.exists():
        unused_aliases = sorted(
            str(alias).strip()
            for alias in aliases["alias"]
            if exact_key(alias) not in raw_mention_keys
        )
        if unused_aliases:
            report.warning(
                f"Alias rows never used by models.csv mentions ({len(unused_aliases)}/{len(aliases)}): "
                + "; ".join(unused_aliases)
            )

    unused_canonical_names = sorted(
        str(name).strip()
        for name in benchmarks["benchmark_name"]
        if exact_key(name) not in raw_mention_keys
    )
    if unused_canonical_names:
        report.warning(
            "Canonical benchmark names never mentioned directly in models.csv "
            f"({len(unused_canonical_names)}; an alias may still reach the same ID): "
            + "; ".join(unused_canonical_names)
        )

    return models, benchmarks, aliases, resolver


def validate_facet_frame(
    report,
    facets,
    label,
    owner_column,
    known_owner_ids=None,
    require_required_facets=False,
    check_projection=False,
):
    core_columns = [owner_column, "facet_axis", "facet_label", "review_status"]
    for column in core_columns:
        blank_rows = facets[
            facets[column].astype(str).str.strip() == ""
        ].index.tolist()
        if blank_rows:
            report.error(
                f"{label} has blank {column} values on rows "
                f"{[index + 2 for index in blank_rows[:20]]}"
            )

    for column in ["classification_confidence"]:
        values = pd.to_numeric(facets[column], errors="coerce")
        if values.isna().any() or ((values < 0) | (values > 1)).any():
            report.error(f"{label} has invalid {column}; expected numeric values in [0, 1]")

    invalid_axes = sorted(set(facets["facet_axis"]) - VALID_FACET_AXES - {""})
    if invalid_axes:
        report.error(f"{label} has invalid facet_axis values: {invalid_axes}")

    invalid_statuses = sorted(set(facets["review_status"]) - VALID_FACET_STATUSES - {""})
    if invalid_statuses:
        report.error(f"{label} has invalid review_status values: {invalid_statuses}")

    if known_owner_ids is not None:
        missing_owners = sorted(set(facets[owner_column]) - known_owner_ids - {""})
        if missing_owners:
            report.error(f"{label} references missing {owner_column} values: {missing_owners}")

    low_conf_bad_status = facets[
        (
            pd.to_numeric(facets["classification_confidence"], errors="coerce")
            < REVIEW_CONFIDENCE_THRESHOLD
        )
        & (~facets["review_status"].isin(["needs_review", "disputed"]))
    ]
    if not low_conf_bad_status.empty:
        report.error(f"{label} low-confidence rows must be marked needs_review or disputed")

    invalid_headline = sorted(
        set(facets[facets["facet_axis"] == "headline_task_mode"]["facet_label"]) - set(MODE_ORDER) - {""}
    )
    if invalid_headline:
        report.error(f"{label} has invalid headline_task_mode labels: {invalid_headline}")

    active_facets = facets[facets["review_status"] != "deprecated"].copy()
    active_headline_rows = active_facets[active_facets["facet_axis"] == "headline_task_mode"]
    headline_counts = active_headline_rows.groupby(owner_column).size()
    multi_headline = headline_counts[headline_counts > 1]
    if not multi_headline.empty:
        report.error(
            f"{label} has multiple active headline_task_mode rows for: "
            f"{multi_headline.head(10).index.tolist()}"
        )

    for axis, allowed_labels in ALLOWED_FACET_LABELS.items():
        invalid_labels = sorted(set(facets[facets["facet_axis"] == axis]["facet_label"]) - allowed_labels - {""})
        if invalid_labels:
            report.error(f"{label} has invalid {axis} labels: {invalid_labels}")

    duplicate_facet_rows = active_facets.duplicated(
        subset=[owner_column, "facet_axis", "facet_label"],
        keep=False,
    )
    if duplicate_facet_rows.any():
        examples = active_facets.loc[
            duplicate_facet_rows,
            [owner_column, "facet_axis", "facet_label"],
        ].drop_duplicates().head(10)
        report.error(
            f"{label} has duplicate active facet rows: "
            f"{examples.to_dict(orient='records')}"
        )

    if require_required_facets:
        axes_by_owner = (
            active_facets.groupby(owner_column)["facet_axis"]
            .apply(lambda values: set(values))
            .to_dict()
        )
        owners_to_check = (
            set(known_owner_ids)
            if known_owner_ids is not None
            else set(active_facets[owner_column])
        )
        missing_by_owner = {
            owner_id: sorted(
                REQUIRED_FACET_AXES - axes_by_owner.get(owner_id, set())
            )
            for owner_id in sorted(owners_to_check)
            if REQUIRED_FACET_AXES - axes_by_owner.get(owner_id, set())
        }
        if missing_by_owner:
            preview = dict(list(missing_by_owner.items())[:20])
            report.error(
                f"{label} is missing required active facets for "
                f"{len(missing_by_owner)} {owner_column} value(s): {preview}"
            )

    if check_projection:
        for owner_id, group in active_facets.groupby(owner_column):
            labels_by_axis = {
                axis: axis_group["facet_label"].tolist()
                for axis, axis_group in group.groupby("facet_axis")
            }
            if not REQUIRED_FACET_AXES.issubset(labels_by_axis):
                continue
            if derive_headline_projection(labels_by_axis) is None:
                report.error(f"{label} headline projection is not derivable for {owner_id}")


def validate_frontier_lab_author_affiliations(report, benchmarks, path):
    empty_values = benchmarks[
        benchmarks["frontier_lab_author_affiliations"].astype(str).str.strip() == ""
    ]["benchmark_id"].tolist()
    if empty_values:
        report.error(f"{path} has empty frontier_lab_author_affiliations values: {empty_values[:10]}")

    for _, row in benchmarks.iterrows():
        benchmark_id_value = row["benchmark_id"]
        value = str(row["frontier_lab_author_affiliations"]).strip()
        if value in {"none", "needs_review"}:
            continue

        if "Google DeepMind" in value:
            report.error(
                f"{path} {benchmark_id_value} uses Google DeepMind; use 'Google; DeepMind' instead"
            )
            continue

        labels = [part.strip() for part in value.split(";")]
        if any(not label for label in labels):
            report.error(f"{path} {benchmark_id_value} has an empty frontier lab affiliation label")
            continue

        duplicates = duplicate_values(labels)
        if duplicates:
            report.error(
                f"{path} {benchmark_id_value} has duplicate frontier lab affiliation labels: {sorted(duplicates)}"
            )

        invalid_labels = sorted(set(labels) - ALLOWED_FRONTIER_LAB_AUTHOR_AFFILIATIONS)
        if invalid_labels:
            report.error(
                f"{path} {benchmark_id_value} has invalid frontier lab affiliation labels: {invalid_labels}"
            )

        if value != "; ".join(labels):
            report.error(
                f"{path} {benchmark_id_value} should separate frontier lab affiliations with '; '"
            )


def build_manual_benchmark_lookup(benchmarks, resolver):
    lookup = {}
    if not benchmarks.empty:
        lookup.update(
            {
                identity_key(row["benchmark_name"]): row["benchmark_id"]
                for _, row in benchmarks.iterrows()
            }
        )

    if resolver is not None:
        lookup.update(
            {
                identity_key(benchmark.benchmark_name): benchmark.benchmark_id
                for benchmark in resolver.canonical_by_exact.values()
            }
        )
        lookup.update(
            {
                identity_key(alias.alias): alias.benchmark_id
                for alias in resolver.alias_by_exact.values()
            }
        )

    return lookup


def validate_normalized_data(report, models, resolver, data_dir=None):
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    paths = {
        "benchmarks": data_dir / "benchmarks.csv",
        "facets": data_dir / "benchmark_facets.csv",
        "manual_facets": data_dir / "benchmark_facet_manual.csv",
    }
    missing_core_paths = [
        path
        for key, path in paths.items()
        if key
        not in {
            "manual_facets",
        }
        and not path.exists()
    ]
    if missing_core_paths:
        report.warning(
            "Generated normalized data not fully present yet: "
            + ", ".join(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path) for path in missing_core_paths)
        )

    frames = {key: load_csv(path) for key, path in paths.items() if path.exists()}
    if not frames:
        return

    if "benchmarks" in frames:
        report.require_columns(frames["benchmarks"], REQUIRED_BENCHMARK_COLUMNS, str(paths["benchmarks"]))
    if "manual_facets" in frames:
        report.require_columns(
            frames["manual_facets"],
            REQUIRED_MANUAL_FACET_COLUMNS,
            str(paths["manual_facets"]),
        )
        if "benchmark_id" not in frames["manual_facets"].columns and "benchmark_name" not in frames["manual_facets"].columns:
            report.error(f"{paths['manual_facets']} must include either benchmark_id or benchmark_name")
    if "facets" in frames:
        report.require_columns(frames["facets"], REQUIRED_FACET_COLUMNS, str(paths["facets"]))
    if report.errors:
        return

    benchmarks = frames.get("benchmarks", pd.DataFrame())
    manual_facets = frames.get("manual_facets", pd.DataFrame())
    facets = frames.get("facets", pd.DataFrame())

    if not benchmarks.empty:
        duplicates = duplicate_values(benchmarks["benchmark_id"])
        if duplicates:
            report.error(f"{paths['benchmarks']} has duplicate benchmark_id values: {sorted(duplicates)}")

        benchmark_name_duplicates = duplicate_values(identity_key(name) for name in benchmarks["benchmark_name"])
        if benchmark_name_duplicates:
            report.error(f"{paths['benchmarks']} has duplicate benchmark names: {sorted(benchmark_name_duplicates)}")

        mismatched_ids = [
            f"{row['benchmark_name']} -> {row['benchmark_id']} expected {benchmark_id(row['benchmark_name'])}"
            for _, row in benchmarks.iterrows()
            if row["benchmark_id"] != benchmark_id(row["benchmark_name"])
        ]
        if mismatched_ids:
            report.error(f"Unexpected benchmark_id values: {mismatched_ids[:10]}")

        invalid_statuses = sorted(set(benchmarks["review_status"]) - VALID_FACET_STATUSES - {""})
        if invalid_statuses:
            report.error(f"{paths['benchmarks']} has invalid review_status values: {invalid_statuses}")

        validate_frontier_lab_author_affiliations(report, benchmarks, paths["benchmarks"])

    benchmark_ids = set(benchmarks["benchmark_id"]) if not benchmarks.empty else None
    manual_benchmark_lookup = build_manual_benchmark_lookup(benchmarks, resolver)

    if not manual_facets.empty:
        manual_for_validation = manual_facets.copy()
        if "benchmark_id" not in manual_for_validation.columns:
            manual_for_validation["benchmark_id"] = ""

        if "benchmark_name" in manual_for_validation.columns and not benchmarks.empty:
            empty_ids = manual_for_validation["benchmark_id"].astype(str).str.strip() == ""
            manual_for_validation.loc[empty_ids, "benchmark_id"] = manual_for_validation.loc[
                empty_ids, "benchmark_name"
            ].map(lambda name: manual_benchmark_lookup.get(identity_key(name), "")).fillna("")

            unknown_names = sorted(
                str(name).strip()
                for _, name in manual_for_validation.loc[
                    empty_ids & (manual_for_validation["benchmark_id"].astype(str).str.strip() == ""),
                    "benchmark_name",
                ].items()
                if str(name).strip()
            )
            if unknown_names:
                report.error(f"{paths['manual_facets']} references unknown benchmark names: {unknown_names}")

        report.require_columns(manual_for_validation, REQUIRED_FACET_COLUMNS, str(paths["manual_facets"]))
        empty_ids = manual_for_validation["benchmark_id"].astype(str).str.strip() == ""
        if empty_ids.any():
            report.error(
                f"{paths['manual_facets']} has rows without benchmark_id or resolvable benchmark_name: "
                f"{[idx + 2 for idx in manual_for_validation[empty_ids].index.tolist()]}"
            )
        if not report.errors:
            validate_facet_frame(
                report,
                manual_for_validation,
                str(paths["manual_facets"]),
                "benchmark_id",
                known_owner_ids=benchmark_ids,
                require_required_facets=False,
                check_projection=False,
            )

    if not facets.empty:
        validate_facet_frame(
            report,
            facets,
            str(paths["facets"]),
            "benchmark_id",
            known_owner_ids=benchmark_ids,
            require_required_facets=True,
            check_projection=True,
        )

    present = ", ".join(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path) for path in paths.values() if path.exists())
    if present:
        print(f"Validated optional normalized data file(s): {present}.")


def main():
    parser = argparse.ArgumentParser(description="Validate benchmark source and generated normalized data.")
    parser.add_argument("--models", default=str(DATA_DIR / "models.csv"), help="Path to models CSV")
    parser.add_argument("--benchmarks", default=str(DATA_DIR / "benchmarks.csv"), help="Path to benchmarks CSV")
    parser.add_argument("--aliases", default=str(DATA_DIR / "benchmark_aliases.csv"), help="Path to benchmark aliases CSV")
    parser.add_argument(
        "--distinctness",
        default=str(DATA_DIR / "benchmark_distinctness.csv"),
        help="Path to reviewed near-duplicate identity decisions",
    )
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Directory containing optional normalized CSVs")
    args = parser.parse_args()

    report = Report()
    models, _, _, resolver = validate_legacy(
        report,
        args.models,
        args.benchmarks,
        args.aliases,
        args.distinctness,
    )
    validate_normalized_data(report, models, resolver, args.data_dir)
    report.print()
    if report.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
