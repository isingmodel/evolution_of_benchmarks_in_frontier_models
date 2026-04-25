#!/usr/bin/env python3
"""Classify benchmarks one-by-one with Gemini using the v3 multi-facet contract.

The safe default writes reviewable JSONL candidates. The script can also emit
candidate facet CSV rows or, when explicitly requested, a legacy v2-shaped CSV
derived from the v3 response.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from taxonomy_utils import ALLOWED_REVIEW_STATUS, REQUIRED_FACET_AXES, benchmark_id, derive_headline_projection

LEGACY_SCHEMA_COLUMNS: List[str] = [
    "benchmark_name",
    "reference_link",
    "source_author",
    "task_mode",
    "task_domain",
    "rationale",
]

CANDIDATE_FACET_COLUMNS: List[str] = [
    "benchmark_id",
    "benchmark_name",
    "reference_link",
    "source_author",
    "provider",
    "model_name",
    "release_page_url",
    "facet_axis",
    "facet_label",
    "label_weight",
    "classification_confidence",
    "evidence_id",
    "evidence",
    "review_status",
    "rationale",
    "headline_projection",
    "derived_headline_projection",
    "projection_rationale",
    "generated_by_model",
]

ALLOWED_TASK_MODE = {
    "Agentic",
    "Generative Reasoning",
    "Knowledge Retrieval",
    "Constraint Satisfaction",
    "Multimodal Perception",
}

ALLOWED_TASK_DOMAIN = {
    "STEM/Math",
    "Coding/Engineering",
    "General/Commonsense",
    "Specialized (Law/Bio/Finance)",
}

ALLOWED_HEADLINE_PROJECTION = {
    "Agentic / Environment Interaction",
    "Multimodal / Perceptual Understanding",
    "Constraint / Safety / Control",
    "Generative or Deliberative Reasoning",
    "Knowledge / Retrieval",
    "Long Context Projection",
    "needs_review",
}

HEADLINE_TO_LEGACY_TASK_MODE = {
    "Agentic / Environment Interaction": "Agentic",
    "Multimodal / Perceptual Understanding": "Multimodal Perception",
    "Constraint / Safety / Control": "Constraint Satisfaction",
    "Generative or Deliberative Reasoning": "Generative Reasoning",
    "Knowledge / Retrieval": "Knowledge Retrieval",
    "Long Context Projection": "Knowledge Retrieval",
}

ALLOWED_CONSTRUCT_CLAIM = {
    "reasoning",
    "mathematical_reasoning",
    "scientific_reasoning",
    "factual_knowledge",
    "coding",
    "software_engineering",
    "agentic_task_completion",
    "tool_use",
    "web_navigation",
    "computer_use",
    "multimodal_understanding",
    "document_understanding",
    "long_context_retrieval",
    "long_context_reasoning",
    "instruction_following",
    "safety_or_refusal",
    "domain_expertise",
    "preference_or_human_judgment",
}

ALLOWED_TASK_MECHANISM = {
    "multiple_choice_qa",
    "short_answer_qa",
    "free_form_generation",
    "math_problem_solving",
    "code_generation",
    "code_repair",
    "repository_issue_resolution",
    "unit_test_passing",
    "browser_navigation",
    "terminal_operation",
    "tool_calling",
    "visual_question_answering",
    "video_question_answering",
    "document_parsing",
    "long_context_retrieval",
    "long_context_synthesis",
    "format_constrained_output",
    "adversarial_refusal",
    "human_preference_comparison",
}

ALLOWED_DOMAIN = {
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
}

ALLOWED_MODALITY = {
    "text",
    "image",
    "video",
    "audio",
    "document_layout",
    "code",
    "browser_ui",
    "desktop_ui",
    "tool_api",
    "multimodal_mixed",
}

ALLOWED_INTERACTION_PATTERN = {
    "static_prompt_response",
    "single_turn_tool_use",
    "multi_turn_dialogue",
    "multi_step_planning",
    "environment_interaction",
    "browser_or_web_interaction",
    "terminal_or_codebase_interaction",
    "computer_control",
    "human_in_the_loop",
}

ALLOWED_METRIC_TYPE = {
    "accuracy",
    "exact_match",
    "pass_at_k",
    "unit_test_pass_rate",
    "win_rate",
    "human_preference",
    "LLM_judge",
    "rubric_score",
    "completion_rate",
    "safety_violation_rate",
    "latency_or_cost",
    "composite_score",
    "unknown",
}

ALLOWED_CONTEXT_PRESSURE = {
    "none",
    "short",
    "medium",
    "long_context_supporting",
    "long_context_primary",
}

ALLOWED_BENCHMARK_LIFECYCLE_RISK = {
    "contamination_risk",
    "saturation_risk",
    "private_or_opaque_eval",
    "version_instability",
    "provider_created_benchmark",
    "unclear_metric",
    "construct_validity_risk",
    "distribution_shift_risk",
}

ALLOWED_FACET_LABELS: Mapping[str, Set[str]] = {
    "construct_claim": ALLOWED_CONSTRUCT_CLAIM,
    "benchmark_construct_claim": ALLOWED_CONSTRUCT_CLAIM,
    "provider_construct_claim": ALLOWED_CONSTRUCT_CLAIM,
    "task_mechanism": ALLOWED_TASK_MECHANISM,
    "domain": ALLOWED_DOMAIN,
    "modality": ALLOWED_MODALITY,
    "interaction_pattern": ALLOWED_INTERACTION_PATTERN,
    "metric_type": ALLOWED_METRIC_TYPE,
    "context_pressure": ALLOWED_CONTEXT_PRESSURE,
    "benchmark_lifecycle_risk": ALLOWED_BENCHMARK_LIFECYCLE_RISK,
}

PROMPT_FACET_AXES = [
    "construct_claim",
    "task_mechanism",
    "domain",
    "modality",
    "interaction_pattern",
    "metric_type",
    "context_pressure",
    "benchmark_lifecycle_risk",
]

CANONICAL_OUTPUT_FILENAMES = {
    "benchmark_facet_edges.csv",
    "mention_facet_overrides.csv",
    "evidence.csv",
    "benchmarks.csv",
    "release_mentions.csv",
}


def label_options(axis: str) -> str:
    return " | ".join(sorted(ALLOWED_FACET_LABELS[axis]))


def build_prompt(row: Mapping[str, str]) -> str:
    input_payload = {
        "benchmark_name": row.get("benchmark_name", ""),
        "reference_link": row.get("reference_link", ""),
        "provider": row.get("provider", ""),
        "model_name": row.get("model_name", ""),
        "release_page_url": row.get("release_page_url", ""),
        "release_page_context": row.get("release_page_context", ""),
    }
    input_json = json.dumps(input_payload, ensure_ascii=False, indent=2)

    return f"""You are classifying one AI benchmark using Benchmark Classification Methodology v3.

Input JSON:
{input_json}

Task:
1) Classify the benchmark with multiple documented facets. Do not force a single exclusive label.
2) Distinguish benchmark identity from release-page framing when provider context is available.
3) Derive one headline_projection only after assigning facets.
4) Return exactly one JSON object only.
5) No markdown, no code fences, no extra text.

Allowed facet labels:
- construct_claim: {label_options("construct_claim")}
- task_mechanism: {label_options("task_mechanism")}
- domain: {label_options("domain")}
- modality: {label_options("modality")}
- interaction_pattern: {label_options("interaction_pattern")}
- metric_type: {label_options("metric_type")}
- context_pressure: {label_options("context_pressure")}
- benchmark_lifecycle_risk: {label_options("benchmark_lifecycle_risk")}

Output JSON schema:
{{
  "benchmark_name": "string",
  "reference_link": "string",
  "benchmark_construct_claim": ["labels from construct_claim"],
  "provider_construct_claim": ["labels from construct_claim, or [] if unavailable"],
  "facets": {{
    "construct_claim": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "task_mechanism": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "domain": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "modality": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "interaction_pattern": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "metric_type": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "context_pressure": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "benchmark_lifecycle_risk": [
      {{"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}}
    ]
  }},
  "headline_projection": "Agentic / Environment Interaction | Multimodal / Perceptual Understanding | Constraint / Safety / Control | Generative or Deliberative Reasoning | Knowledge / Retrieval | Long Context Projection | needs_review",
  "projection_rationale": "one concise sentence explaining why this projection was chosen",
  "review_status": "accepted | needs_review | disputed | deprecated",
  "rationale": "one concise sentence summarizing the classification"
}}

Rules:
- Evidence before label: use the reference link and release-page context when available. If evidence is weak, lower confidence and set review_status to needs_review.
- Projection is not identity: headline_projection is only for charts. Preserve all relevant facets even when one headline category is selected.
- Separate confidence from importance: classification_confidence reflects evidence quality, not release-page prominence.
- Weights within each facet axis should sum to approximately 1.0 when multiple labels are present.
- Long context is a facet. Use Long Context Projection only when context length is the primary release-page emphasis or benchmark bottleneck.
- If provider framing differs from the benchmark's original purpose, preserve both benchmark_construct_claim and provider_construct_claim.

Projection priority when a single headline category is required:
1) Long Context Projection, only when context length is the primary benchmark bottleneck
2) Agentic / Environment Interaction
3) Multimodal / Perceptual Understanding
4) Constraint / Safety / Control
5) Generative or Deliberative Reasoning
6) Knowledge / Retrieval

Now produce one JSON object for the given input."""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="data/benchmarks.csv", help="Source CSV with benchmark names/links")
    p.add_argument(
        "--output",
        default="data/benchmark_classification_candidates.jsonl",
        help="Output path for reviewable candidates",
    )
    p.add_argument(
        "--output-format",
        choices=["jsonl", "candidate-facets-csv", "legacy-csv"],
        default="",
        help="Defaults to jsonl for .jsonl outputs and candidate-facets-csv for .csv outputs",
    )
    p.add_argument("--model", default="gemini-3-pro-preview", help="Gemini model name")
    p.add_argument(
        "--api-key-file",
        default="secrets/gemini_api_key.txt",
        help="Path to a text file containing Gemini API key",
    )
    p.add_argument("--max-rows", type=int, default=0, help="Max rows to process (0 = all pending)")
    p.add_argument("--sleep", type=float, default=1.0, help="Seconds to sleep between API calls")
    p.add_argument("--retries", type=int, default=2, help="Retries per row after failures")
    p.add_argument("--init-only", action="store_true", help="Initialize output file and exit")
    p.add_argument("--force", action="store_true", help="Process rows even if an output candidate already exists")
    return p.parse_args()


def read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_legacy_csv(path: str, rows: List[Dict[str, str]]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEGACY_SCHEMA_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def init_candidate_csv(path: str) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANDIDATE_FACET_COLUMNS)
        w.writeheader()


def append_candidate_csv(path: str, rows: Sequence[Mapping[str, str]]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path_obj.exists() or path_obj.stat().st_size == 0
    with path_obj.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANDIDATE_FACET_COLUMNS)
        if needs_header:
            w.writeheader()
        w.writerows(rows)


def append_jsonl(path: str, record: Mapping[str, Any]) -> None:
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_initial_rows(source_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in source_rows:
        benchmark_name = (r.get("benchmark_name") or r.get("Benchmark") or r.get("raw_mention") or "").strip()
        if not benchmark_name:
            continue

        reference_link = (r.get("reference_link") or r.get("Reference Link") or "").strip()
        source_author = (r.get("source_author") or r.get("author(Openai, google, academia, Meta, others)") or "").strip()

        rows.append(
            {
                "benchmark_name": benchmark_name,
                "reference_link": reference_link,
                "source_author": source_author,
                "task_mode": "",
                "task_domain": "",
                "rationale": "",
            }
        )
    return rows


def build_input_rows(source_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for r in source_rows:
        benchmark_name = (r.get("benchmark_name") or r.get("Benchmark") or r.get("raw_mention") or "").strip()
        if not benchmark_name:
            continue

        reference_link = (r.get("reference_link") or r.get("Reference Link") or "").strip()
        source_author = (r.get("source_author") or r.get("author(Openai, google, academia, Meta, others)") or "").strip()
        row_benchmark_id = (r.get("benchmark_id") or "").strip() or benchmark_id(benchmark_name)
        release_page_url = (
            r.get("release_page_url")
            or r.get("source_url")
            or r.get("release_url")
            or r.get("link")
            or ""
        ).strip()

        rows.append(
            {
                "benchmark_id": row_benchmark_id,
                "benchmark_name": benchmark_name,
                "reference_link": reference_link,
                "source_author": source_author,
                "provider": (r.get("provider") or r.get("Provider") or "").strip(),
                "model_name": (r.get("model_name") or r.get("Model name") or "").strip(),
                "release_page_url": release_page_url,
                "release_page_context": (r.get("release_page_context") or r.get("provider_context") or "").strip(),
            }
        )
    return rows


def normalize_existing(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for r in rows:
        normalized.append(
            {
                "benchmark_name": (r.get("benchmark_name") or r.get("Benchmark") or "").strip(),
                "reference_link": (r.get("reference_link") or r.get("Reference Link") or "").strip(),
                "source_author": (r.get("source_author") or r.get("author(Openai, google, academia, Meta, others)") or "").strip(),
                "task_mode": (r.get("task_mode") or r.get("layer1_mode") or "").strip(),
                "task_domain": (r.get("task_domain") or r.get("layer2_domain") or "").strip(),
                "rationale": (r.get("rationale") or "").strip(),
            }
        )
    return [r for r in normalized if r["benchmark_name"]]


def extract_json(text: str) -> Dict[str, object]:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model response")
    return json.loads(m.group(0))


def as_string(value: object) -> str:
    return "" if value is None else str(value).strip()


def as_float(value: object, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid {field_name}: {value!r}") from e
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{field_name} must be between 0 and 1: {number}")
    return number


def normalize_label_list(value: object, field_name: str, allowed_labels: Set[str], allow_empty: bool) -> List[str]:
    if value is None:
        values: List[object] = []
    elif isinstance(value, list):
        values = value
    elif isinstance(value, str):
        values = [value]
    else:
        raise ValueError(f"{field_name} must be a list of strings")

    labels: List[str] = []
    for item in values:
        label = as_string(item)
        if not label:
            continue
        if label not in allowed_labels:
            raise ValueError(f"Invalid {field_name} label: {label}")
        if label not in labels:
            labels.append(label)

    if not allow_empty and not labels:
        raise ValueError(f"Missing {field_name}")
    return labels


def normalize_facet_entry(axis: str, entry: object) -> Dict[str, object]:
    if not isinstance(entry, dict):
        raise ValueError(f"Facet {axis} entries must be objects")

    label = as_string(entry.get("label"))
    if label not in ALLOWED_FACET_LABELS[axis]:
        raise ValueError(f"Invalid {axis} label: {label}")

    evidence = as_string(entry.get("evidence"))
    if not evidence:
        raise ValueError(f"Missing evidence for {axis}:{label}")

    return {
        "label": label,
        "label_weight": as_float(entry.get("label_weight"), f"{axis}:{label}.label_weight"),
        "classification_confidence": as_float(
            entry.get("classification_confidence"),
            f"{axis}:{label}.classification_confidence",
        ),
        "evidence": evidence,
    }


def normalize_facets(value: object) -> Dict[str, List[Dict[str, object]]]:
    if not isinstance(value, dict):
        raise ValueError("facets must be an object")

    unknown_axes = sorted(set(value) - set(PROMPT_FACET_AXES))
    if unknown_axes:
        raise ValueError(f"Unknown facet axes: {unknown_axes}")

    facets: Dict[str, List[Dict[str, object]]] = {}
    for axis in PROMPT_FACET_AXES:
        raw_entries = value.get(axis, [])
        if raw_entries is None:
            raw_entries = []
        if not isinstance(raw_entries, list):
            raise ValueError(f"facets.{axis} must be a list")
        entries = [normalize_facet_entry(axis, entry) for entry in raw_entries]
        if axis in REQUIRED_FACET_AXES and not entries:
            raise ValueError(f"Missing required facet axis: {axis}")
        facets[axis] = entries
    return facets


def minimum_confidence(facets: Mapping[str, Sequence[Mapping[str, object]]]) -> float:
    confidences = [
        float(entry["classification_confidence"])
        for entries in facets.values()
        for entry in entries
    ]
    return min(confidences) if confidences else 0.0


def has_weight_sum_issue(facets: Mapping[str, Sequence[Mapping[str, object]]]) -> bool:
    for entries in facets.values():
        if not entries:
            continue
        weight_sum = sum(float(entry["label_weight"]) for entry in entries)
        if weight_sum < 0.85 or weight_sum > 1.15:
            return True
    return False


def derive_projection_from_response(response: Mapping[str, object]) -> str:
    facets = response["facets"]
    if not isinstance(facets, dict):
        return "needs_review"

    labels_by_axis = {
        axis: [str(entry["label"]) for entry in entries]
        for axis, entries in facets.items()
        if isinstance(entries, list)
    }
    labels_by_axis["benchmark_construct_claim"] = response.get("benchmark_construct_claim", [])
    labels_by_axis["provider_construct_claim"] = response.get("provider_construct_claim", [])
    return derive_headline_projection(labels_by_axis) or "needs_review"


def validate_and_normalize_v3(parsed: Dict[str, object], original: Mapping[str, str]) -> Dict[str, object]:
    facets = normalize_facets(parsed.get("facets"))
    facet_construct_labels = [str(entry["label"]) for entry in facets["construct_claim"]]
    benchmark_claim_source = parsed.get("benchmark_construct_claim")
    if benchmark_claim_source is None:
        benchmark_claim_source = facet_construct_labels

    normalized: Dict[str, object] = {
        "benchmark_name": as_string(parsed.get("benchmark_name")) or original.get("benchmark_name", ""),
        "reference_link": as_string(parsed.get("reference_link")) or original.get("reference_link", ""),
        "benchmark_construct_claim": normalize_label_list(
            benchmark_claim_source,
            "benchmark_construct_claim",
            ALLOWED_CONSTRUCT_CLAIM,
            allow_empty=False,
        ),
        "provider_construct_claim": normalize_label_list(
            parsed.get("provider_construct_claim", []),
            "provider_construct_claim",
            ALLOWED_CONSTRUCT_CLAIM,
            allow_empty=True,
        ),
        "facets": facets,
        "headline_projection": as_string(parsed.get("headline_projection")),
        "projection_rationale": as_string(parsed.get("projection_rationale")),
        "review_status": as_string(parsed.get("review_status")),
        "rationale": as_string(parsed.get("rationale")),
    }

    if normalized["headline_projection"] not in ALLOWED_HEADLINE_PROJECTION:
        raise ValueError(f"Invalid headline_projection: {normalized['headline_projection']}")
    if normalized["review_status"] not in ALLOWED_REVIEW_STATUS:
        raise ValueError(f"Invalid review_status: {normalized['review_status']}")
    if not normalized["projection_rationale"]:
        raise ValueError("Missing projection_rationale")
    if not normalized["rationale"]:
        raise ValueError("Missing rationale")

    derived_projection = derive_projection_from_response(normalized)
    normalized["derived_headline_projection"] = derived_projection

    if minimum_confidence(facets) < 0.7 or has_weight_sum_issue(facets):
        normalized["review_status"] = "needs_review"
    if normalized["headline_projection"] != derived_projection and normalized["headline_projection"] != "Long Context Projection":
        normalized["review_status"] = "needs_review"

    return normalized


def gemini_generate(api_key: str, model: str, prompt: str) -> str:
    try:
        from google import genai
    except ImportError as e:
        raise RuntimeError("Missing dependency: google-genai. Install with `pip install google-genai`.") from e

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("Empty text response from Gemini")
    return text


def classify_row(row: Dict[str, str], api_key: str, model: str, retries: int) -> Dict[str, object]:
    prompt = build_prompt(row)

    last_error = ""
    for _ in range(retries + 1):
        try:
            raw = gemini_generate(api_key, model, prompt)
            parsed = extract_json(raw)
            return validate_and_normalize_v3(parsed, row)
        except Exception as e:
            last_error = str(e)
            time.sleep(1.5)

    raise RuntimeError(last_error or "Classification failed")


def load_or_init_legacy_rows(args: argparse.Namespace) -> List[Dict[str, str]]:
    if args.init_only:
        source_rows = read_csv(args.input)
        rows = build_initial_rows(source_rows)
        write_legacy_csv(args.output, rows)
        return rows

    if not os.path.exists(args.output):
        source_rows = read_csv(args.input)
        rows = build_initial_rows(source_rows)
        write_legacy_csv(args.output, rows)
        return rows

    existing = read_csv(args.output)
    rows = normalize_existing(existing)
    write_legacy_csv(args.output, rows)
    return rows


def infer_output_format(args: argparse.Namespace) -> str:
    if args.output_format:
        return args.output_format
    suffix = Path(args.output).suffix.casefold()
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".csv":
        return "candidate-facets-csv"
    raise ValueError("Cannot infer output format; use --output-format")


def ensure_safe_output_path(output: str, output_format: str) -> None:
    path = Path(output)
    if output_format != "legacy-csv" and path.name in CANONICAL_OUTPUT_FILENAMES:
        raise ValueError(
            f"Refusing to write review candidates directly to canonical data file {output!r}; "
            "choose a candidate output path instead."
        )


def candidate_key(row: Mapping[str, str]) -> Tuple[str, str, str, str, str]:
    return (
        row.get("benchmark_name", "").strip().casefold(),
        row.get("reference_link", "").strip(),
        row.get("provider", "").strip().casefold(),
        row.get("model_name", "").strip().casefold(),
        row.get("release_page_url", "").strip(),
    )


def existing_candidate_keys(path: str, output_format: str) -> Set[Tuple[str, str, str, str, str]]:
    if not os.path.exists(path):
        return set()

    keys: Set[Tuple[str, str, str, str, str]] = set()
    if output_format == "jsonl":
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                input_row = record.get("input", {})
                if isinstance(input_row, dict):
                    keys.add(candidate_key({key: as_string(value) for key, value in input_row.items()}))
        return keys

    if output_format == "candidate-facets-csv":
        for row in read_csv(path):
            keys.add(candidate_key(row))
        return keys

    return keys


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_candidate_record(row: Mapping[str, str], classification: Mapping[str, object], model: str) -> Dict[str, object]:
    try:
        legacy_projection: object = legacy_row_from_classification(row, classification)
    except ValueError as e:
        legacy_projection = {"error": str(e)}

    return {
        "schema_version": "benchmark_classification_v3_candidate",
        "generated_at": now_utc(),
        "generated_by_model": model,
        "input": dict(row),
        "classification": classification,
        "legacy_projection": legacy_projection,
    }


def facet_review_status(global_status: str, confidence: float) -> str:
    if global_status in {"disputed", "deprecated"}:
        return global_status
    if confidence < 0.7:
        return "needs_review"
    return global_status


def claim_confidence_and_evidence(
    label: str,
    facets: Mapping[str, Sequence[Mapping[str, object]]],
) -> Tuple[float, str]:
    for entry in facets.get("construct_claim", []):
        if entry.get("label") == label:
            return float(entry["classification_confidence"]), str(entry["evidence"])
    return 0.7, "Top-level construct claim from v3 response."


def candidate_facet_rows(
    row: Mapping[str, str],
    classification: Mapping[str, object],
    model: str,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    facets = classification["facets"]
    if not isinstance(facets, dict):
        return rows

    base = {
        "benchmark_id": row.get("benchmark_id", ""),
        "benchmark_name": row.get("benchmark_name", ""),
        "reference_link": row.get("reference_link", ""),
        "source_author": row.get("source_author", ""),
        "provider": row.get("provider", ""),
        "model_name": row.get("model_name", ""),
        "release_page_url": row.get("release_page_url", ""),
        "evidence_id": "",
        "rationale": str(classification.get("rationale", "")),
        "headline_projection": str(classification.get("headline_projection", "")),
        "derived_headline_projection": str(classification.get("derived_headline_projection", "")),
        "projection_rationale": str(classification.get("projection_rationale", "")),
        "generated_by_model": model,
    }

    for axis in ["benchmark_construct_claim", "provider_construct_claim"]:
        labels = classification.get(axis, [])
        if not isinstance(labels, list):
            continue
        for label in labels:
            confidence, evidence = claim_confidence_and_evidence(str(label), facets)
            rows.append(
                {
                    **base,
                    "facet_axis": axis,
                    "facet_label": str(label),
                    "label_weight": str(round(1.0 / len(labels), 6)) if labels else "1.0",
                    "classification_confidence": str(confidence),
                    "evidence": evidence,
                    "review_status": facet_review_status(str(classification.get("review_status", "")), confidence),
                }
            )

    for axis in PROMPT_FACET_AXES:
        entries = facets.get(axis, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            confidence = float(entry["classification_confidence"])
            rows.append(
                {
                    **base,
                    "facet_axis": axis,
                    "facet_label": str(entry["label"]),
                    "label_weight": str(entry["label_weight"]),
                    "classification_confidence": str(confidence),
                    "evidence": str(entry["evidence"]),
                    "review_status": facet_review_status(str(classification.get("review_status", "")), confidence),
                }
            )
    return rows


def primary_domain(facets: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    domains = list(facets.get("domain", []))
    if not domains:
        return ""
    return str(max(domains, key=lambda entry: float(entry["label_weight"]))["label"])


def collapse_domain_to_legacy(domain: str) -> str:
    if domain in {"General/Commonsense", "STEM/Math", "Coding/Engineering"}:
        return domain
    return "Specialized (Law/Bio/Finance)"


def legacy_task_mode_from_projection(classification: Mapping[str, object]) -> str:
    projection = str(classification.get("headline_projection", ""))
    derived_projection = str(classification.get("derived_headline_projection", ""))
    if projection == "needs_review" and derived_projection in HEADLINE_TO_LEGACY_TASK_MODE:
        projection = derived_projection
    task_mode = HEADLINE_TO_LEGACY_TASK_MODE.get(projection)
    if task_mode not in ALLOWED_TASK_MODE:
        raise ValueError(f"Cannot derive legacy task_mode from headline_projection: {projection}")
    return task_mode


def legacy_row_from_classification(
    row: Mapping[str, str],
    classification: Mapping[str, object],
) -> Dict[str, str]:
    facets = classification.get("facets", {})
    if not isinstance(facets, dict):
        raise ValueError("Cannot derive legacy row without facets")

    task_mode = legacy_task_mode_from_projection(classification)
    task_domain = collapse_domain_to_legacy(primary_domain(facets))
    if task_domain not in ALLOWED_TASK_DOMAIN:
        raise ValueError(f"Cannot derive legacy task_domain: {task_domain}")

    return {
        "benchmark_name": row.get("benchmark_name", ""),
        "reference_link": row.get("reference_link", ""),
        "source_author": row.get("source_author", ""),
        "task_mode": task_mode,
        "task_domain": task_domain,
        "rationale": str(classification.get("rationale", "")),
    }


def main() -> int:
    args = parse_args()
    try:
        output_format = infer_output_format(args)
        ensure_safe_output_path(args.output, output_format)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    if output_format == "legacy-csv":
        rows = load_or_init_legacy_rows(args)
        if args.init_only:
            print(f"Initialized legacy schema file: {args.output} ({len(rows)} rows)")
            return 0
    else:
        if args.init_only:
            if output_format == "jsonl":
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text("", encoding="utf-8")
            else:
                init_candidate_csv(args.output)
            print(f"Initialized {output_format} candidate file: {args.output}")
            return 0
        rows = build_input_rows(read_csv(args.input))

    try:
        with open(args.api_key_file, "r", encoding="utf-8") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        print(f"API key file not found: {args.api_key_file}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"Failed to read API key file {args.api_key_file}: {e}", file=sys.stderr)
        return 2

    if not api_key:
        print(f"API key file is empty: {args.api_key_file}", file=sys.stderr)
        return 2

    completed_keys = set() if args.force else existing_candidate_keys(args.output, output_format)
    processed = 0
    for i, row in enumerate(rows):
        if output_format == "legacy-csv":
            is_pending = not row.get("task_mode") or not row.get("task_domain") or not row.get("rationale")
            if not is_pending and not args.force:
                continue
        elif candidate_key(row) in completed_keys:
            continue

        try:
            classification = classify_row(row, api_key=api_key, model=args.model, retries=args.retries)
            if output_format == "jsonl":
                append_jsonl(args.output, make_candidate_record(row, classification, args.model))
                headline = classification["headline_projection"]
            elif output_format == "candidate-facets-csv":
                append_candidate_csv(args.output, candidate_facet_rows(row, classification, args.model))
                headline = classification["headline_projection"]
            else:
                rows[i] = legacy_row_from_classification(row, classification)
                write_legacy_csv(args.output, rows)
                headline = rows[i]["task_mode"]

            print(f"[{processed + 1}] {row['benchmark_name']} -> done ({headline})")
            if output_format != "legacy-csv":
                completed_keys.add(candidate_key(row))
        except RuntimeError as e:
            print(f"[{processed + 1}] {row['benchmark_name']} -> error: {e}", file=sys.stderr)
        except ValueError as e:
            print(f"[{processed + 1}] {row['benchmark_name']} -> invalid response: {e}", file=sys.stderr)

        processed += 1

        if args.max_rows > 0 and processed >= args.max_rows:
            break
        time.sleep(max(args.sleep, 0.0))

    print(f"Done. processed={processed}, output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
