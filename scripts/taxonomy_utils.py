#!/usr/bin/env python3
"""Utilities for exact benchmark canonicalization.

This module deliberately does not implement fuzzy matching or substring
fallback. A raw mention resolves only when it is an exact canonical name or an
explicit row in data/benchmark_aliases.csv.
"""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


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

ALLOWED_ALIAS_MATCH_TYPE = {
    "exact",
    "case_variant",
    "provider_abbreviation",
    "version_alias",
    "legacy_name",
}

ALLOWED_REVIEW_STATUS = {
    "accepted",
    "needs_review",
    "disputed",
    "deprecated",
}

ALLOWED_FACET_AXIS = {
    "construct_claim",
    "benchmark_construct_claim",
    "provider_construct_claim",
    "task_mechanism",
    "domain",
    "modality",
    "interaction_pattern",
    "metric_type",
    "context_pressure",
    "benchmark_lifecycle_risk",
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
    "factuality_verification",
    "free_form_generation",
    "math_problem_solving",
    "code_generation",
    "code_repair",
    "repository_issue_resolution",
    "unit_test_passing",
    "sql_generation",
    "security_challenge_solving",
    "browser_navigation",
    "terminal_operation",
    "tool_calling",
    "computer_control_task",
    "visual_question_answering",
    "visual_grounding",
    "video_question_answering",
    "document_parsing",
    "speech_or_audio_translation",
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
    "none_identified",
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

REQUIRED_FACET_AXES = {
    "construct_claim",
    "task_mechanism",
    "domain",
    "modality",
    "interaction_pattern",
    "metric_type",
}


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    """Read a CSV into dictionaries with UTF-8 and newline-safe defaults."""
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def exact_key(value: str) -> str:
    """Return the exact-match key used by the resolver.

    This normalizes Unicode width/compatibility, trims leading/trailing space,
    and collapses internal whitespace. It intentionally preserves case and
    punctuation so case variants and shorthand names remain explicit aliases.
    """
    normalized = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", normalized.strip())


def identity_key(value: str) -> str:
    """Return the key used to detect duplicate canonical identities."""
    return exact_key(value).casefold()


def slugify(value: str) -> str:
    """Make a deterministic ASCII slug from a display name."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()
    return slug or stable_hash(value)


def stable_hash(value: str, length: int = 10) -> str:
    """Return a short deterministic hash for ID fallbacks."""
    return hashlib.sha1((value or "").encode("utf-8")).hexdigest()[:length]


def benchmark_id(benchmark_name: str) -> str:
    """Create a deterministic benchmark ID from a canonical benchmark name."""
    return f"benchmark_{slugify(benchmark_name)}"


def model_id(provider: str, model_name: str) -> str:
    """Create a deterministic model ID from provider and model display name."""
    return f"model_{slugify(provider)}_{slugify(model_name)}"


def mention_id(provider: str, model_name: str, release_date: str, mention_index: int, benchmark_id_value: str) -> str:
    """Create a deterministic mention ID for an exploded release mention."""
    base = f"{model_id(provider, model_name)}_{exact_key(release_date)}_{int(mention_index):03d}_{benchmark_id_value}"
    return f"mention_{slugify(base)}"


def benchmark_name_column(fieldnames: Optional[Sequence[str]]) -> str:
    """Return the benchmark-name column for either legacy or v2 taxonomy CSVs."""
    fields = set(fieldnames or [])
    if "benchmark_name" in fields:
        return "benchmark_name"
    if "Benchmark" in fields:
        return "Benchmark"
    raise ValueError("Expected taxonomy CSV to contain benchmark_name or Benchmark")


@dataclass(frozen=True)
class CanonicalBenchmark:
    benchmark_id: str
    benchmark_name: str
    source_path: str
    line_number: int


@dataclass(frozen=True)
class AliasEntry:
    alias: str
    benchmark_id: str
    match_type: str
    notes: str
    source_path: str
    line_number: int


@dataclass(frozen=True)
class Resolution:
    raw_mention: str
    benchmark_id: str
    benchmark_name: str
    match_source: str
    match_type: str


class CanonicalResolver:
    """Exact canonical resolver backed by canonical names and explicit aliases."""

    def __init__(self, benchmarks: Iterable[CanonicalBenchmark], aliases: Iterable[AliasEntry] = ()):
        self.benchmarks_by_id: Dict[str, CanonicalBenchmark] = {}
        self.canonical_by_exact: Dict[str, CanonicalBenchmark] = {}
        self.alias_by_exact: Dict[str, AliasEntry] = {}

        for benchmark in benchmarks:
            existing_id = self.benchmarks_by_id.get(benchmark.benchmark_id)
            if existing_id and existing_id.benchmark_name != benchmark.benchmark_name:
                raise ValueError(
                    f"Duplicate benchmark_id {benchmark.benchmark_id!r} for "
                    f"{existing_id.benchmark_name!r} and {benchmark.benchmark_name!r}"
                )
            self.benchmarks_by_id[benchmark.benchmark_id] = benchmark

            canonical_key = exact_key(benchmark.benchmark_name)
            existing_canonical = self.canonical_by_exact.get(canonical_key)
            if existing_canonical and existing_canonical.benchmark_id != benchmark.benchmark_id:
                raise ValueError(
                    f"Duplicate canonical benchmark key {canonical_key!r} for "
                    f"{existing_canonical.benchmark_id!r} and {benchmark.benchmark_id!r}"
                )
            self.canonical_by_exact[canonical_key] = benchmark

        for alias in aliases:
            alias_key = exact_key(alias.alias)
            existing_alias = self.alias_by_exact.get(alias_key)
            if existing_alias and existing_alias.benchmark_id != alias.benchmark_id:
                raise ValueError(
                    f"Duplicate alias key {alias_key!r} for "
                    f"{existing_alias.benchmark_id!r} and {alias.benchmark_id!r}"
                )
            canonical = self.canonical_by_exact.get(alias_key)
            if canonical and canonical.benchmark_id != alias.benchmark_id:
                raise ValueError(
                    f"Alias {alias.alias!r} shadows canonical benchmark "
                    f"{canonical.benchmark_name!r} with target {alias.benchmark_id!r}"
                )
            self.alias_by_exact[alias_key] = alias

    @classmethod
    def from_files(cls, taxonomy_path: Path, alias_path: Optional[Path] = None) -> "CanonicalResolver":
        benchmarks = load_canonical_benchmarks(taxonomy_path)
        aliases = load_aliases(alias_path) if alias_path and alias_path.exists() else []
        return cls(benchmarks, aliases)

    def resolve(self, raw_mention: str) -> Optional[Resolution]:
        key = exact_key(raw_mention)
        if not key:
            return None

        alias = self.alias_by_exact.get(key)
        if alias:
            benchmark = self.benchmarks_by_id.get(alias.benchmark_id)
            if benchmark:
                return Resolution(
                    raw_mention=raw_mention,
                    benchmark_id=benchmark.benchmark_id,
                    benchmark_name=benchmark.benchmark_name,
                    match_source="alias",
                    match_type=alias.match_type,
                )
            return None

        benchmark = self.canonical_by_exact.get(key)
        if benchmark:
            return Resolution(
                raw_mention=raw_mention,
                benchmark_id=benchmark.benchmark_id,
                benchmark_name=benchmark.benchmark_name,
                match_source="canonical",
                match_type="exact",
            )

        return None


def load_canonical_benchmarks(taxonomy_path: Path) -> List[CanonicalBenchmark]:
    with taxonomy_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        name_column = benchmark_name_column(reader.fieldnames)
        rows = []
        for line_number, row in enumerate(reader, start=2):
            name = exact_key(row.get(name_column, ""))
            if not name:
                continue
            rows.append(
                CanonicalBenchmark(
                    benchmark_id=benchmark_id(name),
                    benchmark_name=name,
                    source_path=str(taxonomy_path),
                    line_number=line_number,
                )
            )
    return rows


def load_aliases(alias_path: Path) -> List[AliasEntry]:
    with alias_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for line_number, row in enumerate(reader, start=2):
            rows.append(
                AliasEntry(
                    alias=exact_key(row.get("alias", "")),
                    benchmark_id=exact_key(row.get("benchmark_id", "")),
                    match_type=exact_key(row.get("match_type", "")),
                    notes=exact_key(row.get("notes", "")),
                    source_path=str(alias_path),
                    line_number=line_number,
                )
            )
    return rows


def split_benchmark_mentions(benchmarks_value: str) -> List[str]:
    """Split the current comma-separated models.csv benchmark field."""
    return [exact_key(part) for part in (benchmarks_value or "").split(",") if exact_key(part)]


def derive_headline_projection(facet_labels_by_axis: Mapping[str, Iterable[str]]) -> Optional[str]:
    """Derive the v3 headline projection from already assigned facets.

    The projection is intentionally simple and deterministic. It is a validator
    sanity check, not a replacement for reviewed facet annotations.
    """
    labels = {
        axis: {identity_key(label) for label in label_values if exact_key(label)}
        for axis, label_values in facet_labels_by_axis.items()
    }

    construct = labels.get("construct_claim", set()) | labels.get("benchmark_construct_claim", set()) | labels.get(
        "provider_construct_claim", set()
    )
    mechanism = labels.get("task_mechanism", set())
    modality = labels.get("modality", set())
    interaction = labels.get("interaction_pattern", set())
    context = labels.get("context_pressure", set())

    if context & {"long_context_primary"}:
        return "Long Context Projection"

    if construct & {"agentic_task_completion", "tool_use", "web_navigation", "computer_use"}:
        return "Agentic / Environment Interaction"
    if mechanism & {"browser_navigation", "terminal_operation", "tool_calling", "repository_issue_resolution"}:
        return "Agentic / Environment Interaction"
    if interaction & {
        "single_turn_tool_use",
        "multi_step_planning",
        "environment_interaction",
        "browser_or_web_interaction",
        "terminal_or_codebase_interaction",
        "computer_control",
        "human_in_the_loop",
    }:
        return "Agentic / Environment Interaction"

    if construct & {"multimodal_understanding", "document_understanding"}:
        return "Multimodal / Perceptual Understanding"
    if mechanism & {"visual_question_answering", "video_question_answering", "document_parsing"}:
        return "Multimodal / Perceptual Understanding"
    if modality - {"text", "code", "tool_api"}:
        return "Multimodal / Perceptual Understanding"

    if construct & {"instruction_following", "safety_or_refusal"}:
        return "Constraint / Safety / Control"
    if mechanism & {"format_constrained_output", "adversarial_refusal"}:
        return "Constraint / Safety / Control"

    if construct & {
        "reasoning",
        "mathematical_reasoning",
        "scientific_reasoning",
        "coding",
        "software_engineering",
        "domain_expertise",
    }:
        return "Generative or Deliberative Reasoning"
    if mechanism & {
        "free_form_generation",
        "math_problem_solving",
        "code_generation",
        "code_repair",
        "unit_test_passing",
        "long_context_synthesis",
    }:
        return "Generative or Deliberative Reasoning"

    if construct & {"factual_knowledge", "long_context_retrieval", "preference_or_human_judgment"}:
        return "Knowledge / Retrieval"
    if mechanism & {"multiple_choice_qa", "short_answer_qa", "long_context_retrieval", "human_preference_comparison"}:
        return "Knowledge / Retrieval"
    if context & {"long_context_supporting"}:
        return "Knowledge / Retrieval"

    return None
