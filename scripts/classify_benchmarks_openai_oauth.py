#!/usr/bin/env python3
"""Classify benchmarks one-by-one with OpenAI OAuth using the v3 multi-facet contract.

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

from scripts.openai_oauth_client import (
    DEFAULT_OPENAI_OAUTH_BASE_URL,
    DEFAULT_OPENAI_OAUTH_MODEL,
    OpenAIOAuthClient,
    resolve_openai_oauth_dir,
)
from scripts.taxonomy_utils import (
    ALLOWED_CONSTRUCT_CLAIM,
    ALLOWED_FACET_LABELS,
    ALLOWED_HEADLINE_PROJECTION,
    ALLOWED_REVIEW_STATUS,
    ALLOWED_TASK_DOMAIN,
    ALLOWED_TASK_MODE,
    HEADLINE_TO_LEGACY_TASK_MODE,
    PROMPT_FACET_AXES,
    REQUIRED_FACET_AXES,
    benchmark_id,
    derive_headline_projection,
)

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
    "classification_confidence",
    "evidence",
    "review_status",
    "rationale",
    "headline_projection",
    "derived_headline_projection",
    "projection_rationale",
    "generated_by_model",
]

CANONICAL_OUTPUT_FILENAMES = {
    "benchmark_facets.csv",
    "benchmarks.csv",
}

LEGACY_DOMAIN_PRIORITY: Tuple[str, ...] = (
    "Coding/Engineering",
    "STEM/Math",
    "Law",
    "Bio/Medicine",
    "Finance",
    "Cybersecurity",
    "Visual/Document",
    "Multilingual",
    "Other Specialized",
    "General/Commonsense",
)
LEGACY_DOMAIN_PRIORITY_INDEX = {label: index for index, label in enumerate(LEGACY_DOMAIN_PRIORITY)}


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
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "task_mechanism": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "domain": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "modality": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "interaction_pattern": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "metric_type": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "context_pressure": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
    ],
    "benchmark_lifecycle_risk": [
      {{"label": "string", "classification_confidence": 0.0, "evidence": "short source note"}}
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
- When multiple labels apply within one facet axis, include each supported label once. Downstream analysis divides contribution equally across labels at runtime.
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
    p.add_argument("--model", default=DEFAULT_OPENAI_OAUTH_MODEL, help="OpenAI OAuth model name")
    p.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high", "xhigh"],
        default=None,
        help="Optional Responses reasoning effort to send through openai-oauth.",
    )
    p.add_argument("--openai-oauth-base-url", default=DEFAULT_OPENAI_OAUTH_BASE_URL)
    p.add_argument("--openai-oauth-dir", default=str(resolve_openai_oauth_dir()))
    p.add_argument(
        "--no-openai-oauth-start",
        action="store_true",
        help="Do not auto-start the local openai-oauth proxy.",
    )
    p.add_argument("--openai-oauth-timeout", type=float, default=120.0)
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

    if minimum_confidence(facets) < 0.7:
        normalized["review_status"] = "needs_review"
    if normalized["headline_projection"] != derived_projection and normalized["headline_projection"] != "Long Context Projection":
        normalized["review_status"] = "needs_review"

    return normalized


def classify_row(row: Dict[str, str], client: OpenAIOAuthClient, retries: int) -> Dict[str, object]:
    prompt = build_prompt(row)

    last_error = ""
    for _ in range(retries + 1):
        try:
            raw = client.generate_text(prompt)
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
                    "classification_confidence": str(confidence),
                    "evidence": str(entry["evidence"]),
                    "review_status": facet_review_status(str(classification.get("review_status", "")), confidence),
                }
            )
    return rows


def primary_domain(facets: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    domains = {
        str(entry.get("label", "")).strip()
        for entry in facets.get("domain", [])
        if isinstance(entry, Mapping) and str(entry.get("label", "")).strip()
    }
    if not domains:
        return ""
    return min(
        sorted(domains),
        key=lambda label: (LEGACY_DOMAIN_PRIORITY_INDEX.get(label, len(LEGACY_DOMAIN_PRIORITY_INDEX)), label),
    )


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

    completed_keys = set() if args.force else existing_candidate_keys(args.output, output_format)
    processed = 0
    client = OpenAIOAuthClient(
        base_url=args.openai_oauth_base_url,
        model=args.model,
        reasoning_effort=args.reasoning_effort or None,
        project_dir=Path(args.openai_oauth_dir),
        auto_start=not args.no_openai_oauth_start,
        timeout=args.openai_oauth_timeout,
    )
    try:
        for i, row in enumerate(rows):
            if output_format == "legacy-csv":
                is_pending = not row.get("task_mode") or not row.get("task_domain") or not row.get("rationale")
                if not is_pending and not args.force:
                    continue
            elif candidate_key(row) in completed_keys:
                continue

            try:
                classification = classify_row(row, client=client, retries=args.retries)
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
    finally:
        client.close()

    print(f"Done. processed={processed}, output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
