import argparse
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


RULE_SEED_CONFIDENCE = 0.6
LEGACY_SEED_CONFIDENCE = 0.7
FRONTIER_LAB_AUTHOR_LABELS = [
    "OpenAI",
    "Anthropic",
    "Google",
    "DeepMind",
    "Microsoft",
    "xAI",
]
FACET_COLUMNS = [
    "benchmark_id",
    "facet_axis",
    "facet_label",
    "label_weight",
    "classification_confidence",
    "review_status",
    "rationale",
]
MANUAL_FACET_REQUIRED_COLUMNS = [
    "facet_axis",
    "facet_label",
    "label_weight",
    "classification_confidence",
    "review_status",
    "rationale",
]
BENCHMARK_COLUMNS = [
    "benchmark_id",
    "benchmark_name",
    "reference_link",
    "source_author",
    "frontier_lab_author_affiliations",
    "legacy_task_mode",
    "legacy_task_domain",
    "legacy_rationale",
    "review_status",
]


def read_csv_or_empty(path, columns):
    if not path.exists():
        return pd.DataFrame(columns=columns)

    data = pd.read_csv(path).fillna("")
    missing = set(columns) - set(data.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return data


def read_required_csv(path, columns):
    if not path.exists():
        raise FileNotFoundError(f"Required source CSV not found: {path}")

    data = pd.read_csv(path).fillna("")
    missing = set(columns) - set(data.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    if data.empty:
        raise ValueError(f"Required source CSV has no rows: {path}")
    return data


def read_existing_facets(path):
    return read_csv_or_empty(path, FACET_COLUMNS)[FACET_COLUMNS].copy()


def read_manual_facets(path):
    if not path.exists():
        return pd.DataFrame(columns=["benchmark_name", *FACET_COLUMNS])

    data = pd.read_csv(path).fillna("")
    missing = set(MANUAL_FACET_REQUIRED_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    if "benchmark_id" not in data.columns and "benchmark_name" not in data.columns:
        raise ValueError(f"{path} must include either benchmark_id or benchmark_name")
    return data.copy()


def stable_id(prefix, *parts):
    raw = " ".join(str(part) for part in parts if str(part).strip())
    slug = re.sub(r"[^a-z0-9]+", "_", raw.casefold()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not slug:
        slug = "unknown"
    return f"{prefix}_{slug}"


def normalize_name(value):
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def read_aliases(path):
    if not path.exists():
        return pd.DataFrame(columns=["alias", "benchmark_id", "match_type", "notes"])

    aliases = pd.read_csv(path).fillna("")
    required = {"alias", "benchmark_id"}
    missing = required - set(aliases.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return aliases


def build_canonical_lookup(benchmarks_df, aliases_df):
    canonical = {}
    for name in benchmarks_df["benchmark_name"]:
        name = str(name).strip()
        canonical[normalize_name(name)] = name

    name_by_id = dict(zip(benchmarks_df["benchmark_id"], benchmarks_df["benchmark_name"]))
    for _, row in aliases_df.iterrows():
        alias = str(row["alias"]).strip()
        benchmark_id = str(row["benchmark_id"]).strip()
        if not alias or not benchmark_id:
            continue
        if benchmark_id not in name_by_id:
            raise ValueError(f"Alias target {benchmark_id!r} is not in canonical benchmark table")

        key = normalize_name(alias)
        target = name_by_id[benchmark_id]
        if key in canonical and canonical[key] != target:
            raise ValueError(f"Alias collision for {alias!r}: {canonical[key]!r} vs {target!r}")
        canonical[key] = target

    return canonical


def duplicate_values(values):
    seen = set()
    duplicates = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def validate_benchmark_source(benchmarks_df):
    empty_names = benchmarks_df[
        benchmarks_df["benchmark_name"].astype(str).str.strip() == ""
    ].index.tolist()
    if empty_names:
        raise ValueError(f"benchmarks.csv has empty benchmark_name values on rows {[idx + 2 for idx in empty_names]}")

    empty_ids = benchmarks_df[
        benchmarks_df["benchmark_id"].astype(str).str.strip() == ""
    ].index.tolist()
    if empty_ids:
        raise ValueError(f"benchmarks.csv has empty benchmark_id values on rows {[idx + 2 for idx in empty_ids]}")

    duplicate_names = duplicate_values(
        normalize_name(name) for name in benchmarks_df["benchmark_name"]
    )
    if duplicate_names:
        raise ValueError(f"benchmarks.csv has duplicate benchmark names after normalization: {duplicate_names}")

    duplicate_ids = duplicate_values(str(benchmark_id).strip() for benchmark_id in benchmarks_df["benchmark_id"])
    if duplicate_ids:
        raise ValueError(f"benchmarks.csv has duplicate benchmark_id values: {duplicate_ids}")

    mismatched_ids = [
        f"{row['benchmark_name']} -> {row['benchmark_id']} expected {stable_id('benchmark', row['benchmark_name'])}"
        for _, row in benchmarks_df.iterrows()
        if str(row["benchmark_id"]).strip() != stable_id("benchmark", row["benchmark_name"])
    ]
    if mismatched_ids:
        raise ValueError(f"benchmarks.csv has unexpected benchmark_id values: {mismatched_ids[:10]}")


def infer_frontier_lab_author_affiliations(row, reference_link=None, source_author=None):
    if source_author is None:
        source_author = str(row.get("source_author", "")).strip()
    if reference_link is None:
        reference_link = str(row.get("reference_link", "")).strip()
    rationale = str(row.get("rationale", "") or row.get("legacy_rationale", "")).strip()
    text = " ".join([source_author, reference_link, rationale])
    text_lower = text.casefold()
    labels = []

    def add(label):
        if label not in labels:
            labels.append(label)

    # Authorship only: do not treat funding/backing or release-page hosting as
    # benchmark author affiliation.
    source_without_backing = re.sub(r"backed by\s+google", "", source_author, flags=re.IGNORECASE)

    for label in ["OpenAI", "Anthropic", "Microsoft", "xAI"]:
        if re.search(rf"(?<![A-Za-z]){re.escape(label)}(?![A-Za-z])", source_without_backing, flags=re.IGNORECASE):
            add(label)

    if re.search(r"(?<![A-Za-z])Google(?![A-Za-z])", source_without_backing, flags=re.IGNORECASE):
        add("Google")

    if "deepmind" in text_lower:
        # Represent Google DeepMind as atomic Google + DeepMind tags.
        add("Google")
        add("DeepMind")

    for marker in [
        "github.com/google-research",
        "huggingface.co/datasets/google/",
        "blog.google/",
    ]:
        if marker in reference_link.casefold():
            add("Google")

    if not labels:
        return "none"

    ordered = [label for label in FRONTIER_LAB_AUTHOR_LABELS if label in labels]
    return "; ".join(ordered)


def normalize_benchmarks(benchmarks_df):
    rows = []
    for _, row in benchmarks_df.fillna("").iterrows():
        benchmark_name = str(row["benchmark_name"]).strip()
        if not benchmark_name:
            continue
        benchmark_id = str(row.get("benchmark_id", "")).strip() or stable_id("benchmark", benchmark_name)
        reference_link = str(row.get("reference_link", "")).strip()
        source_author = str(row.get("source_author", "")).strip()
        frontier_lab_author_affiliations = (
            str(row.get("frontier_lab_author_affiliations", "")).strip()
            or infer_frontier_lab_author_affiliations(
                row,
                reference_link=reference_link,
                source_author=source_author,
            )
        )
        review_status = str(row.get("review_status", "")).strip() or "legacy_seed"
        rows.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": benchmark_name,
                "reference_link": reference_link,
                "source_author": source_author,
                "frontier_lab_author_affiliations": frontier_lab_author_affiliations,
                "legacy_task_mode": str(row.get("legacy_task_mode", "") or row.get("task_mode", "")).strip(),
                "legacy_task_domain": str(row.get("legacy_task_domain", "") or row.get("task_domain", "")).strip(),
                "legacy_rationale": str(row.get("legacy_rationale", "") or row.get("rationale", "")).strip(),
                "review_status": review_status,
            }
        )
    return pd.DataFrame(rows, columns=BENCHMARK_COLUMNS).sort_values("benchmark_name").reset_index(drop=True)


def text_blob(row):
    return " ".join(
        [
            str(row.get("benchmark_name", "")),
            str(row.get("legacy_task_mode", "")),
            str(row.get("legacy_task_domain", "")),
            str(row.get("legacy_rationale", "")),
            str(row.get("source_author", "")),
        ]
    ).casefold()


def infer_domain(row):
    name = str(row["benchmark_name"]).casefold()
    legacy_domain = str(row["legacy_task_domain"]).strip()
    text = text_blob(row)

    if legacy_domain in {"General/Commonsense", "STEM/Math", "Coding/Engineering"}:
        return legacy_domain
    if any(token in name for token in ["bar exam", "biglaw", "law"]):
        return "Law"
    if any(token in name for token in ["bio", "health", "medical", "biology"]):
        return "Bio/Medicine"
    if "finance" in name:
        return "Finance"
    if any(token in name for token in ["ctf", "cyber"]):
        return "Cybersecurity"
    if any(token in name for token in ["multilingual", "polyglot"]) or "translation" in text:
        return "Multilingual"
    return "Other Specialized"


def infer_construct_claim(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])
    text = text_blob(row)

    if mode == "Agentic":
        if "browse" in name or "web" in name:
            return "web_navigation"
        if "mcp" in name or "tool" in name or "function" in text:
            return "tool_use"
        if "osworld" in name or "computer" in text or "desktop" in text:
            return "computer_use"
        return "agentic_task_completion"
    if mode == "Multimodal Perception":
        if "doc" in name or "chart" in name or "screen" in name:
            return "document_understanding"
        return "multimodal_understanding"
    if mode == "Constraint Satisfaction":
        if "jailbreak" in name or "safety" in text or "refusal" in text:
            return "safety_or_refusal"
        return "instruction_following"
    if mode == "Knowledge Retrieval":
        if "facts" in name or "factual" in text:
            return "factual_knowledge"
        return "factual_knowledge"
    is_math = "math" in name or domain == "STEM/Math"
    is_science = any(token in name for token in ["aime", "gpqa", "hmmt", "imo"])
    if is_math:
        return "mathematical_reasoning"
    if is_science:
        return "scientific_reasoning"
    if domain == "Coding/Engineering":
        return "software_engineering" if any(token in name for token in ["swe", "terminal", "openrca"]) else "coding"
    if domain == "Specialized (Law/Bio/Finance)":
        return "domain_expertise"
    return "reasoning"


def infer_task_mechanism(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])
    text = text_blob(row)

    if re.search(r"\bswe(?:-bench|-lancer)?\b", name):
        return "repository_issue_resolution"
    if "terminal" in name:
        return "terminal_operation"
    if "browse" in name or "webvoyager" in name:
        return "browser_navigation"
    if any(token in name for token in ["mcp", "tool", "tau", "finance agent", "complexfunc", "vending"]):
        return "tool_calling"
    if "osworld" in name:
        return "computer_control_task"
    if "screen" in name:
        return "visual_grounding"
    if mode == "Constraint Satisfaction":
        return "adversarial_refusal" if "jailbreak" in name else "format_constrained_output"
    if mode == "Multimodal Perception":
        if "video" in name or "activitynet" in name or "egoschema" in name or "vatex" in name:
            return "video_question_answering"
        if "doc" in name or "chart" in name or "infographic" in name:
            return "document_parsing"
        if "fleurs" in name or "covost" in name:
            return "speech_or_audio_translation"
        return "visual_question_answering"
    if "lmarena" in name or "arena" in name:
        return "human_preference_comparison"
    if domain == "Coding/Engineering":
        if "sql" in name:
            return "sql_generation"
        if "ctf" in name or "cyber" in name:
            return "security_challenge_solving"
        return "code_generation"
    if domain == "STEM/Math" or "math" in name or any(token in name for token in ["aime", "hmmt", "imo"]):
        return "math_problem_solving"
    if mode == "Knowledge Retrieval":
        if "facts" in name:
            return "factuality_verification"
        return "short_answer_qa"
    if "mmlu" in name or "gpqa" in name or "mcqa" in name:
        return "multiple_choice_qa"
    return "free_form_generation"


def infer_modality(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])

    if "video" in name or "activitynet" in name or "egoschema" in name or "vatex" in name:
        return "video"
    if "fleurs" in name or "covost" in name:
        return "audio"
    if any(token in name for token in ["doc", "chart", "infographic", "screen"]):
        return "document_layout" if "screen" not in name else "desktop_ui"
    if mode == "Multimodal Perception" or any(token in name for token in ["mmmu", "mathvista", "vqa", "ai2d", "charxiv"]):
        return "image"
    if any(token in name for token in ["browse", "webvoyager"]):
        return "browser_ui"
    if "osworld" in name:
        return "desktop_ui"
    if any(token in name for token in ["mcp", "tool", "tau", "finance agent", "vending"]):
        return "tool_api"
    if domain == "Coding/Engineering" or any(token in name for token in ["code", "swe", "terminal"]):
        return "code"
    return "text"


def infer_interaction_pattern(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])

    if "browse" in name or "webvoyager" in name:
        return "browser_or_web_interaction"
    if "terminal" in name or "swe" in name or "cybergym" in name:
        return "terminal_or_codebase_interaction"
    if "osworld" in name or "screen" in name:
        return "computer_control"
    if any(token in name for token in ["mcp", "tool", "tau", "finance agent", "vending", "complexfunc"]):
        return "single_turn_tool_use"
    if mode == "Agentic":
        return "environment_interaction"
    if "multi-if" in name or "mrcr" in name:
        return "multi_turn_dialogue"
    return "static_prompt_response"


def infer_metric_type(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])

    if "lmarena" in name or "arena" in name:
        return "win_rate"
    if any(token in name for token in ["swe", "humaneval", "livecode", "aider", "terminal"]):
        return "unit_test_pass_rate"
    if mode == "Agentic":
        return "completion_rate"
    if "jailbreak" in name:
        return "safety_violation_rate"
    if mode == "Constraint Satisfaction":
        return "exact_match"
    if mode == "Knowledge Retrieval" or "simpleqa" in name:
        return "exact_match"
    if domain == "Coding/Engineering":
        return "pass_at_k"
    return "accuracy"


def infer_context_pressure(row):
    name = str(row["benchmark_name"]).casefold()
    if "needle" in name or "long context" in name:
        return "long_context_primary"
    if "mrcr" in name or "egoschema" in name:
        return "long_context_supporting"
    return "none"


def infer_lifecycle_risk(row):
    name = str(row["benchmark_name"]).casefold()
    source = str(row["source_author"]).casefold()
    text = text_blob(row)

    if "hidden" in name or "internal" in text:
        return "private_or_opaque_eval"
    if "openai" in source or "google" in source or "anthropic" in source or "scale" in source:
        return "provider_created_benchmark"
    if "lmarena" in name or "judge" in text or "human voting" in text:
        return "unclear_metric"
    return "none_identified"


def seed_status_and_confidence(row, default_status, default_confidence):
    row_status = str(row.get("review_status", "")).strip()
    if row_status == "needs_review":
        return "needs_review", min(default_confidence, RULE_SEED_CONFIDENCE)
    if row_status in {"accepted", "disputed"}:
        return row_status, default_confidence
    return default_status, default_confidence


def add_facet_row(rows, row, axis, label, status, confidence, rationale, label_weight=1.0):
    if not label:
        return
    rows.append(
        {
            "benchmark_id": row["benchmark_id"],
            "facet_axis": axis,
            "facet_label": label,
            "label_weight": label_weight,
            "classification_confidence": confidence,
            "review_status": status,
            "rationale": rationale,
        }
    )


def build_seed_facets(benchmarks_df):
    rows = []
    for _, row in benchmarks_df.iterrows():
        projected_seed_labels = {
            "headline_task_mode": str(row["legacy_task_mode"]).strip(),
            "domain": infer_domain(row),
        }
        for axis, label in projected_seed_labels.items():
            if not label:
                continue
            status, confidence = seed_status_and_confidence(
                row,
                default_status="legacy_seed",
                default_confidence=LEGACY_SEED_CONFIDENCE,
            )
            add_facet_row(
                rows,
                row,
                axis,
                label,
                status,
                confidence,
                row["legacy_rationale"],
            )

        inferred_axes = {
            "construct_claim": infer_construct_claim(row),
            "task_mechanism": infer_task_mechanism(row),
            "modality": infer_modality(row),
            "interaction_pattern": infer_interaction_pattern(row),
            "metric_type": infer_metric_type(row),
            "context_pressure": infer_context_pressure(row),
            "benchmark_lifecycle_risk": infer_lifecycle_risk(row),
        }
        for axis, label in inferred_axes.items():
            status, confidence = seed_status_and_confidence(
                row,
                default_status="needs_review",
                default_confidence=RULE_SEED_CONFIDENCE,
            )
            rationale = (
                f"Rule-based multi-facet seed inferred from legacy task_mode={row['legacy_task_mode']!r}, "
                f"task_domain={row['legacy_task_domain']!r}, benchmark name, and legacy rationale."
            )
            add_facet_row(rows, row, axis, label, status, confidence, rationale)

    return normalize_facet_frame(pd.DataFrame(rows, columns=FACET_COLUMNS))


def normalize_facet_frame(facets_df):
    if facets_df.empty:
        return pd.DataFrame(columns=FACET_COLUMNS)

    facets_df = facets_df[FACET_COLUMNS].fillna("").copy()
    for column in ["benchmark_id", "facet_axis", "facet_label", "review_status", "rationale"]:
        facets_df[column] = facets_df[column].astype(str).str.strip()
    for column in ["label_weight", "classification_confidence"]:
        facets_df[column] = pd.to_numeric(facets_df[column], errors="raise")
    return facets_df.sort_values(["benchmark_id", "facet_axis", "facet_label"]).reset_index(drop=True)


def manual_facets_to_final(manual_facets_df, benchmarks_df, canonical_lookup):
    if manual_facets_df.empty:
        return pd.DataFrame(columns=FACET_COLUMNS)

    id_by_name = dict(zip(benchmarks_df["benchmark_name"], benchmarks_df["benchmark_id"]))
    known_ids = set(benchmarks_df["benchmark_id"])
    rows = []
    for _, row in manual_facets_df.iterrows():
        benchmark_id = str(row.get("benchmark_id", "")).strip()
        benchmark_name = str(row.get("benchmark_name", "")).strip()
        if not benchmark_id and benchmark_name:
            canonical_name = canonical_lookup.get(normalize_name(benchmark_name))
            if not canonical_name:
                raise ValueError(f"benchmark_facet_manual.csv references unknown benchmark_name: {benchmark_name!r}")
            benchmark_id = id_by_name[canonical_name]
        if benchmark_id not in known_ids:
            raise ValueError(f"benchmark_facet_manual.csv references unknown benchmark_id: {benchmark_id!r}")

        rows.append(
            {
                "benchmark_id": benchmark_id,
                "facet_axis": str(row["facet_axis"]).strip(),
                "facet_label": str(row["facet_label"]).strip(),
                "label_weight": row["label_weight"],
                "classification_confidence": row["classification_confidence"],
                "review_status": str(row["review_status"]).strip(),
                "rationale": str(row["rationale"]).strip(),
            }
        )
    return normalize_facet_frame(pd.DataFrame(rows, columns=FACET_COLUMNS))


def merge_facet_tables(benchmarks_df, existing_facets_df, manual_facets_df, canonical_lookup):
    benchmark_ids = set(benchmarks_df["benchmark_id"])
    existing_facets_df = normalize_facet_frame(existing_facets_df)
    existing_facets_df = existing_facets_df[existing_facets_df["benchmark_id"].isin(benchmark_ids)].copy()

    missing_benchmark_ids = benchmark_ids - set(existing_facets_df["benchmark_id"])
    if missing_benchmark_ids:
        seed_source = benchmarks_df[benchmarks_df["benchmark_id"].isin(missing_benchmark_ids)]
        existing_facets_df = pd.concat(
            [existing_facets_df, build_seed_facets(seed_source)],
            ignore_index=True,
        )

    manual_final_df = manual_facets_to_final(manual_facets_df, benchmarks_df, canonical_lookup)
    if not manual_final_df.empty:
        manual_keys = set(zip(manual_final_df["benchmark_id"], manual_final_df["facet_axis"]))
        existing_facets_df = existing_facets_df[
            ~existing_facets_df.apply(
                lambda row: (row["benchmark_id"], row["facet_axis"]) in manual_keys,
                axis=1,
            )
        ]
        existing_facets_df = pd.concat([existing_facets_df, manual_final_df], ignore_index=True)

    return normalize_facet_frame(existing_facets_df)


def build_normalized_data():
    benchmarks_source_df = read_required_csv(DATA_DIR / "benchmarks.csv", BENCHMARK_COLUMNS)
    aliases_df = read_aliases(DATA_DIR / "benchmark_aliases.csv")
    existing_facets_df = read_existing_facets(DATA_DIR / "benchmark_facets.csv")
    manual_facets_df = read_manual_facets(DATA_DIR / "benchmark_facet_manual.csv")

    validate_benchmark_source(benchmarks_source_df)
    benchmarks_df = normalize_benchmarks(benchmarks_source_df)
    canonical_lookup = build_canonical_lookup(benchmarks_df, aliases_df)
    facets_df = merge_facet_tables(
        benchmarks_df,
        existing_facets_df,
        manual_facets_df,
        canonical_lookup,
    )

    facets_df.to_csv(DATA_DIR / "benchmark_facets.csv", index=False)

    print(f"Read {len(benchmarks_df)} benchmarks")
    print(f"Wrote {len(facets_df)} benchmark facets")
    if not manual_facets_df.empty:
        print("Applied temporary manual facet rows from data/benchmark_facet_manual.csv")


def main():
    parser = argparse.ArgumentParser(description="Build normalized benchmark facet data.")
    parser.parse_args()
    build_normalized_data()


if __name__ == "__main__":
    main()
