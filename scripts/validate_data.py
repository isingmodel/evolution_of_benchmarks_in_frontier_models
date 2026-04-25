import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from mention_prominence import (
    REQUIRED_PROMINENCE_OVERRIDE_COLUMNS,
    active_prominence_overrides,
    validate_prominence_overrides,
    weight_for_prominence,
)
from taxonomy_utils import (
    ALLOWED_ALIAS_MATCH_TYPE,
    ALLOWED_FACET_AXIS,
    ALLOWED_FACET_LABELS,
    ALLOWED_REVIEW_STATUS,
    ALLOWED_TASK_DOMAIN,
    ALLOWED_TASK_MODE,
    REQUIRED_FACET_AXES,
    CanonicalResolver,
    MENTION_PROMINENCE_DEFAULT,
    MENTION_PROMINENCE_WEIGHTS,
    benchmark_id,
    derive_headline_projection,
    exact_key,
    identity_key,
    split_benchmark_mentions,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

REQUIRED_MODEL_COLUMNS = {"Provider", "Model name", "link", "release date", "benchmarks"}
REQUIRED_TAXONOMY_COLUMNS = {
    "benchmark_name",
    "reference_link",
    "source_author",
    "task_mode",
    "task_domain",
    "rationale",
}
REQUIRED_ALIAS_COLUMNS = {"alias", "benchmark_id", "match_type", "notes"}
REQUIRED_BENCHMARK_COLUMNS = {
    "benchmark_id",
    "benchmark_name",
    "reference_link",
    "source_author",
    "legacy_task_mode",
    "legacy_task_domain",
    "legacy_rationale",
    "review_status",
}
REQUIRED_MENTION_COLUMNS = {
    "mention_id",
    "model_id",
    "provider",
    "model_name",
    "release_date",
    "source_url",
    "benchmark_id",
    "benchmark_name",
    "raw_mention",
    "mention_index",
    "mention_prominence",
    "mention_weight",
}
REQUIRED_FACET_COLUMNS = {
    "benchmark_id",
    "facet_axis",
    "facet_label",
    "label_weight",
    "classification_confidence",
    "evidence_id",
    "review_status",
    "rationale",
}
REQUIRED_MENTION_OVERRIDE_COLUMNS = {
    "mention_id",
    "facet_axis",
    "facet_label",
    "label_weight",
    "classification_confidence",
    "evidence_id",
    "review_status",
    "rationale",
}
REQUIRED_EVIDENCE_COLUMNS = {
    "evidence_id",
    "benchmark_id",
    "evidence_type",
    "title",
    "url",
    "source_date",
    "accessed_date",
    "notes",
}
ALLOWED_EVIDENCE_TYPE = {
    "benchmark_definition",
    "provider_mention",
    "technical_report",
    "model_card",
    "benchmark_card",
    "classification_rationale",
    "override_adjudication",
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
VALID_FACET_STATUSES = set(ALLOWED_REVIEW_STATUS) | {"legacy_seed"}
VALID_FACET_AXES = set(ALLOWED_FACET_AXIS) | {"headline_task_mode"}
VALID_MENTION_PROMINENCE = set(MENTION_PROMINENCE_WEIGHTS)


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


def normalize_taxonomy_frame(report, taxonomy, label):
    if "benchmark_name" in taxonomy.columns:
        report.require_columns(taxonomy, REQUIRED_TAXONOMY_COLUMNS, label)
        return taxonomy

    if "Benchmark" in taxonomy.columns:
        rename_map = {
            "Benchmark": "benchmark_name",
            "Reference Link": "reference_link",
            "author(Openai, google, academia, Meta, others)": "source_author",
            "Rationale": "rationale",
            "Main Category": "legacy_main_category",
        }
        return taxonomy.rename(columns={k: v for k, v in rename_map.items() if k in taxonomy.columns})

    report.error(f"{label} missing benchmark_name or Benchmark column")
    return taxonomy


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


def validate_legacy(report, models_path=None, taxonomy_path=None, alias_path=None):
    models_path = Path(models_path) if models_path else DATA_DIR / "models.csv"
    taxonomy_path = Path(taxonomy_path) if taxonomy_path else DATA_DIR / "benchmark_taxonomy_v2.csv"
    alias_path = Path(alias_path) if alias_path else DATA_DIR / "benchmark_aliases.csv"

    models = load_csv(models_path)
    taxonomy = load_csv(taxonomy_path)
    aliases = load_csv(alias_path)

    report.require_columns(models, REQUIRED_MODEL_COLUMNS, str(models_path))
    taxonomy = normalize_taxonomy_frame(report, taxonomy, str(taxonomy_path))
    if alias_path.exists():
        report.require_columns(aliases, REQUIRED_ALIAS_COLUMNS, str(alias_path))

    if report.errors:
        return models, taxonomy, aliases, None

    bad_dates = models[pd.to_datetime(models["release date"], errors="coerce").isna()]["Model name"].tolist()
    if bad_dates:
        report.error(f"Invalid model release dates: {bad_dates}")

    duplicate_canonical = duplicate_values(identity_key(name) for name in taxonomy["benchmark_name"])
    if duplicate_canonical:
        examples = []
        for key in duplicate_canonical:
            names = taxonomy[taxonomy["benchmark_name"].map(identity_key) == key]["benchmark_name"].tolist()
            examples.append(f"{key}: {names}")
        report.error(f"Duplicate canonical benchmark names after normalization: {examples}")

    if "task_mode" in taxonomy.columns:
        invalid_modes = sorted(set(taxonomy["task_mode"]) - ALLOWED_TASK_MODE - {""})
        if invalid_modes:
            report.error(f"Invalid task_mode values: {invalid_modes}")

    if "task_domain" in taxonomy.columns:
        invalid_domains = sorted(set(taxonomy["task_domain"]) - ALLOWED_TASK_DOMAIN - {""})
        if invalid_domains:
            report.error(f"Invalid task_domain values: {invalid_domains}")

    canonical_ids = {benchmark_id(name) for name in taxonomy["benchmark_name"]}
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
            report.error(f"Alias benchmark_id targets missing from taxonomy: {missing_targets}")

        invalid_match_types = sorted(set(aliases["match_type"]) - ALLOWED_ALIAS_MATCH_TYPE - {""})
        if invalid_match_types:
            report.error(f"Invalid alias match_type values: {invalid_match_types}")

        canonical_by_exact = {
            exact_key(name): benchmark_id(name)
            for name in taxonomy["benchmark_name"]
            if exact_key(name)
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
        resolver = CanonicalResolver.from_files(taxonomy_path, alias_path if alias_path.exists() else None)
    except Exception as exc:
        report.error(f"Failed to build canonical resolver: {exc}")
        return models, taxonomy, aliases, None

    unresolved = []
    mention_count = 0
    for mention in iter_legacy_mentions(models):
        mention_count += 1
        if not resolver.resolve(mention["raw_mention"]):
            unresolved.append(f"{mention['provider']} / {mention['model_name']} / {mention['raw_mention']}")

    if unresolved:
        report.error(f"Unresolved benchmark mentions without fuzzy matching: {unresolved}")
    else:
        print(f"Resolved {mention_count}/{mention_count} benchmark mentions by exact canonical name or explicit alias.")

    return models, taxonomy, aliases, resolver


def validate_facet_frame(
    report,
    facets,
    label,
    owner_column,
    known_owner_ids=None,
    require_required_facets=False,
    check_projection=False,
):
    for column in ["label_weight", "classification_confidence"]:
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
        (pd.to_numeric(facets["classification_confidence"], errors="coerce") < 0.7)
        & (~facets["review_status"].isin(["needs_review", "disputed"]))
    ]
    if not low_conf_bad_status.empty:
        report.error(f"{label} low-confidence rows must be marked needs_review or disputed")

    invalid_headline = sorted(
        set(facets[facets["facet_axis"] == "headline_task_mode"]["facet_label"]) - set(MODE_ORDER) - {""}
    )
    if invalid_headline:
        report.error(f"{label} has invalid headline_task_mode labels: {invalid_headline}")

    for axis, allowed_labels in ALLOWED_FACET_LABELS.items():
        invalid_labels = sorted(set(facets[facets["facet_axis"] == axis]["facet_label"]) - allowed_labels - {""})
        if invalid_labels:
            report.error(f"{label} has invalid {axis} labels: {invalid_labels}")

    active_facets = facets[facets["review_status"] != "deprecated"].copy()
    active_facets["label_weight"] = pd.to_numeric(active_facets["label_weight"], errors="coerce")
    for (owner_id, axis), group in active_facets.groupby([owner_column, "facet_axis"]):
        total = group["label_weight"].sum()
        if abs(total - 1.0) > 1e-6:
            report.error(f"{label} weights for {owner_id}/{axis} sum to {total}, expected 1.0")

    reviewed = facets[facets["review_status"].isin(["accepted", "disputed"])]
    if require_required_facets and not reviewed.empty:
        axes_by_owner = reviewed.groupby(owner_column)["facet_axis"].apply(lambda values: set(values))
        for owner_id, axes in axes_by_owner.items():
            missing = sorted(REQUIRED_FACET_AXES - axes)
            if missing:
                report.error(f"{label} {owner_id} missing required reviewed facets: {missing}")

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


def validate_generated_v3(report, models, resolver, data_dir=None):
    data_dir = Path(data_dir) if data_dir else DATA_DIR
    paths = {
        "benchmarks": data_dir / "benchmarks.csv",
        "release_mentions": data_dir / "release_mentions.csv",
        "mention_prominence_overrides": data_dir / "mention_prominence_overrides.csv",
        "facets": data_dir / "benchmark_facet_edges.csv",
        "mention_overrides": data_dir / "mention_facet_overrides.csv",
        "evidence": data_dir / "evidence.csv",
    }
    missing_core_paths = [
        path
        for key, path in paths.items()
        if key not in {"mention_overrides", "mention_prominence_overrides"} and not path.exists()
    ]
    if missing_core_paths:
        report.warning(
            "Generated v3 data not fully present yet: "
            + ", ".join(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path) for path in missing_core_paths)
        )

    frames = {key: load_csv(path) for key, path in paths.items() if path.exists()}
    if not frames:
        return

    if "benchmarks" in frames:
        report.require_columns(frames["benchmarks"], REQUIRED_BENCHMARK_COLUMNS, str(paths["benchmarks"]))
    if "release_mentions" in frames:
        report.require_columns(frames["release_mentions"], REQUIRED_MENTION_COLUMNS, str(paths["release_mentions"]))
    if "mention_prominence_overrides" in frames:
        report.require_columns(
            frames["mention_prominence_overrides"],
            REQUIRED_PROMINENCE_OVERRIDE_COLUMNS,
            str(paths["mention_prominence_overrides"]),
        )
    if "facets" in frames:
        report.require_columns(frames["facets"], REQUIRED_FACET_COLUMNS, str(paths["facets"]))
    if "mention_overrides" in frames:
        report.require_columns(
            frames["mention_overrides"],
            REQUIRED_MENTION_OVERRIDE_COLUMNS,
            str(paths["mention_overrides"]),
        )
    if "evidence" in frames:
        report.require_columns(frames["evidence"], REQUIRED_EVIDENCE_COLUMNS, str(paths["evidence"]))
    if report.errors:
        return

    benchmarks = frames.get("benchmarks", pd.DataFrame())
    release_mentions = frames.get("release_mentions", pd.DataFrame())
    mention_prominence_overrides = frames.get("mention_prominence_overrides", pd.DataFrame())
    facets = frames.get("facets", pd.DataFrame())
    mention_overrides = frames.get("mention_overrides", pd.DataFrame())
    evidence = frames.get("evidence", pd.DataFrame())

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

    benchmark_ids = set(benchmarks["benchmark_id"]) if not benchmarks.empty else None
    evidence_ids = set(evidence["evidence_id"]) if not evidence.empty else None
    mention_ids = set(release_mentions["mention_id"]) if not release_mentions.empty else None

    if not evidence.empty:
        duplicates = duplicate_values(evidence["evidence_id"])
        if duplicates:
            report.error(f"{paths['evidence']} has duplicate evidence_id values: {sorted(duplicates)}")

        invalid_evidence_types = sorted(set(evidence["evidence_type"]) - ALLOWED_EVIDENCE_TYPE - {""})
        if invalid_evidence_types:
            report.error(f"{paths['evidence']} has invalid evidence_type values: {invalid_evidence_types}")

        if benchmark_ids is not None:
            missing = sorted(set(evidence["benchmark_id"]) - benchmark_ids - {""})
            if missing:
                report.error(f"evidence references missing benchmark_id values: {missing}")

        empty_urls = evidence[evidence["url"].astype(str).str.strip() == ""]
        if not empty_urls.empty:
            report.warning(f"{len(empty_urls)} evidence rows have empty URLs inherited from legacy taxonomy.")

    if not release_mentions.empty:
        duplicates = duplicate_values(release_mentions["mention_id"])
        if duplicates:
            report.error(f"{paths['release_mentions']} has duplicate mention_id values: {sorted(duplicates)}")

        invalid_prominence = sorted(set(release_mentions["mention_prominence"]) - VALID_MENTION_PROMINENCE - {""})
        if invalid_prominence:
            report.error(f"{paths['release_mentions']} has invalid mention_prominence values: {invalid_prominence}")

        legacy_count = sum(1 for _ in iter_legacy_mentions(models))
        if len(release_mentions) != legacy_count:
            report.error(f"release_mentions row count {len(release_mentions)} != legacy mention count {legacy_count}")

        benchmark_names_by_id = (
            dict(zip(benchmarks["benchmark_id"], benchmarks["benchmark_name"])) if not benchmarks.empty else {}
        )
        for _, row in release_mentions.iterrows():
            expected_model_id = stable_id("model", row["provider"], row["model_name"], row["release_date"])
            try:
                mention_index = int(row["mention_index"])
            except ValueError:
                report.error(f"Invalid mention_index for {row['raw_mention']}: {row['mention_index']}")
                break
            expected_mention_id = stable_id("mention", expected_model_id, f"{mention_index:03d}")
            if row["model_id"] != expected_model_id:
                report.error(f"Unexpected model_id for {row['model_name']}: {row['model_id']} != {expected_model_id}")
                break
            if row["mention_id"] != expected_mention_id:
                report.error(f"Unexpected mention_id for {row['raw_mention']}: {row['mention_id']} != {expected_mention_id}")
                break
            resolved = resolver.resolve(row["raw_mention"]) if resolver else None
            if resolved and resolved.benchmark_id != row["benchmark_id"]:
                report.error(f"{row['raw_mention']} resolved to {resolved.benchmark_id}, not {row['benchmark_id']}")
                break
            if benchmark_names_by_id and row["benchmark_name"] != benchmark_names_by_id.get(row["benchmark_id"], ""):
                report.error(f"release_mentions benchmark_name mismatch for {row['raw_mention']}")
                break

        if benchmark_ids is not None:
            missing = sorted(set(release_mentions["benchmark_id"]) - benchmark_ids - {""})
            if missing:
                report.error(f"release_mentions references missing benchmark_id values: {missing}")

        mention_weights = pd.to_numeric(release_mentions["mention_weight"], errors="coerce")
        if mention_weights.isna().any() or (mention_weights < 0).any():
            report.error("release_mentions has invalid mention_weight; expected non-negative numeric values")
        else:
            mismatched_weights = []
            for _, row in release_mentions.iterrows():
                prominence = row["mention_prominence"] or MENTION_PROMINENCE_DEFAULT
                try:
                    expected_weight = weight_for_prominence(prominence)
                except ValueError:
                    continue
                actual_weight = float(row["mention_weight"])
                if abs(actual_weight - expected_weight) > 1e-9:
                    mismatched_weights.append(
                        f"{row['mention_id']}: {actual_weight} != {expected_weight} for {prominence}"
                    )
            if mismatched_weights:
                report.error(
                    "release_mentions mention_weight values must match the configured prominence weights: "
                    f"{mismatched_weights[:10]}"
                )

    if not mention_prominence_overrides.empty:
        errors, warnings = validate_prominence_overrides(
            mention_prominence_overrides,
            known_mention_ids=mention_ids,
            known_evidence_ids=evidence_ids,
        )
        for error in errors:
            report.error(f"{paths['mention_prominence_overrides']}: {error}")
        for warning in warnings:
            report.warning(f"{paths['mention_prominence_overrides']}: {warning}")

        if mention_ids is not None and not release_mentions.empty:
            release_prominence_by_id = dict(zip(release_mentions["mention_id"], release_mentions["mention_prominence"]))
            stale_overrides = []
            for _, row in active_prominence_overrides(mention_prominence_overrides).iterrows():
                mention_id = row["mention_id"]
                if mention_id not in release_prominence_by_id:
                    continue
                expected_prominence = row["mention_prominence"]
                actual_prominence = release_prominence_by_id[mention_id]
                if actual_prominence != expected_prominence:
                    stale_overrides.append(
                        f"{mention_id}: release_mentions has {actual_prominence!r}, "
                        f"override expects {expected_prominence!r}"
                    )
            if stale_overrides:
                report.error(
                    "mention prominence overrides have not been applied to release_mentions: "
                    f"{stale_overrides[:10]}"
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
        if evidence_ids is not None:
            missing_evidence = sorted(set(facets["evidence_id"]) - evidence_ids - {""})
            if missing_evidence:
                report.error(f"benchmark_facet_edges references missing evidence_id values: {missing_evidence}")

    if not mention_overrides.empty:
        validate_facet_frame(
            report,
            mention_overrides,
            str(paths["mention_overrides"]),
            "mention_id",
            known_owner_ids=mention_ids,
            require_required_facets=False,
            check_projection=False,
        )
        if evidence_ids is not None:
            missing_evidence = sorted(set(mention_overrides["evidence_id"]) - evidence_ids - {""})
            if missing_evidence:
                report.error(f"mention_facet_overrides references missing evidence_id values: {missing_evidence}")

    present = ", ".join(str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path) for path in paths.values() if path.exists())
    if present:
        print(f"Validated optional v3 data file(s): {present}.")


def main():
    parser = argparse.ArgumentParser(description="Validate benchmark taxonomy and generated v3 data.")
    parser.add_argument("--models", default=str(DATA_DIR / "models.csv"), help="Path to models CSV")
    parser.add_argument("--taxonomy", default=str(DATA_DIR / "benchmark_taxonomy_v2.csv"), help="Path to taxonomy CSV")
    parser.add_argument("--aliases", default=str(DATA_DIR / "benchmark_aliases.csv"), help="Path to benchmark aliases CSV")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Directory containing optional v3 CSVs")
    args = parser.parse_args()

    report = Report()
    models, _, _, resolver = validate_legacy(report, args.models, args.taxonomy, args.aliases)
    validate_generated_v3(report, models, resolver, args.data_dir)
    report.print()
    if report.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
