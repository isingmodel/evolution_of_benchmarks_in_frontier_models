from __future__ import annotations

import unittest

from scripts.taxonomy_utils import (
    AliasEntry,
    CanonicalBenchmark,
    CanonicalResolver,
    derive_headline_projection,
)


def benchmark(benchmark_id: str, name: str, line_number: int = 1) -> CanonicalBenchmark:
    return CanonicalBenchmark(benchmark_id, name, "fixture.csv", line_number)


def alias(name: str, benchmark_id: str, line_number: int = 1) -> AliasEntry:
    return AliasEntry(name, benchmark_id, "exact", "Fixture.", "aliases.csv", line_number)


class CanonicalResolverInvariantTests(unittest.TestCase):
    def test_rejects_duplicate_benchmark_id_for_different_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate benchmark_id"):
            CanonicalResolver(
                [
                    benchmark("benchmark_shared", "Alpha", 1),
                    benchmark("benchmark_shared", "Beta", 2),
                ]
            )

    def test_rejects_duplicate_canonical_key_for_different_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate canonical benchmark key"):
            CanonicalResolver(
                [
                    benchmark("benchmark_alpha", "Alpha", 1),
                    benchmark("benchmark_other", "Alpha", 2),
                ]
            )

    def test_rejects_duplicate_alias_key_for_different_targets(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate alias key"):
            CanonicalResolver(
                [benchmark("benchmark_alpha", "Alpha"), benchmark("benchmark_beta", "Beta")],
                [alias("Shared", "benchmark_alpha", 1), alias("Shared", "benchmark_beta", 2)],
            )

    def test_rejects_alias_that_shadows_another_canonical_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "shadows canonical benchmark"):
            CanonicalResolver(
                [benchmark("benchmark_alpha", "Alpha"), benchmark("benchmark_beta", "Beta")],
                [alias("Alpha", "benchmark_beta")],
            )


class HeadlineProjectionTests(unittest.TestCase):
    def test_each_projection_branch(self) -> None:
        cases = [
            (
                "long context primary",
                {"context_pressure": ["long_context_primary"]},
                "Long Context Projection",
            ),
            (
                "agentic construct",
                {"construct_claim": ["agentic_task_completion"]},
                "Agentic / Environment Interaction",
            ),
            (
                "agentic mechanism",
                {"task_mechanism": ["terminal_operation"]},
                "Agentic / Environment Interaction",
            ),
            (
                "agentic interaction",
                {"interaction_pattern": ["multi_step_planning"]},
                "Agentic / Environment Interaction",
            ),
            (
                "multimodal construct",
                {"construct_claim": ["document_understanding"]},
                "Multimodal / Perceptual Understanding",
            ),
            (
                "multimodal mechanism",
                {"task_mechanism": ["video_question_answering"]},
                "Multimodal / Perceptual Understanding",
            ),
            (
                "multimodal modality",
                {"modality": ["image"]},
                "Multimodal / Perceptual Understanding",
            ),
            (
                "constraint construct",
                {"construct_claim": ["safety_or_refusal"]},
                "Constraint / Safety / Control",
            ),
            (
                "constraint mechanism",
                {"task_mechanism": ["format_constrained_output"]},
                "Constraint / Safety / Control",
            ),
            (
                "reasoning construct",
                {"construct_claim": ["mathematical_reasoning"]},
                "Generative or Deliberative Reasoning",
            ),
            (
                "reasoning mechanism",
                {"task_mechanism": ["code_generation"]},
                "Generative or Deliberative Reasoning",
            ),
            (
                "knowledge construct",
                {"construct_claim": ["factual_knowledge"]},
                "Knowledge / Retrieval",
            ),
            (
                "knowledge mechanism",
                {"task_mechanism": ["multiple_choice_qa"]},
                "Knowledge / Retrieval",
            ),
            (
                "supporting long context",
                {"context_pressure": ["long_context_supporting"]},
                "Knowledge / Retrieval",
            ),
            ("no projection", {"modality": ["text"]}, None),
        ]
        for label, facets, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(derive_headline_projection(facets), expected)

    def test_priority_cascade(self) -> None:
        all_lower_priority_signals = {
            "construct_claim": [
                "agentic_task_completion",
                "multimodal_understanding",
                "safety_or_refusal",
                "reasoning",
                "factual_knowledge",
            ],
            "task_mechanism": ["multiple_choice_qa"],
            "modality": ["image"],
            "context_pressure": ["long_context_supporting"],
        }
        cases = [
            (
                "long context primary wins over everything",
                {
                    **all_lower_priority_signals,
                    "context_pressure": ["long_context_primary", "long_context_supporting"],
                },
                "Long Context Projection",
            ),
            (
                "agentic wins over multimodal and lower",
                all_lower_priority_signals,
                "Agentic / Environment Interaction",
            ),
            (
                "multimodal wins over constraint and lower",
                {
                    "construct_claim": ["multimodal_understanding", "safety_or_refusal", "reasoning"],
                    "task_mechanism": ["multiple_choice_qa"],
                },
                "Multimodal / Perceptual Understanding",
            ),
            (
                "constraint wins over reasoning and knowledge",
                {
                    "construct_claim": ["safety_or_refusal", "reasoning", "factual_knowledge"],
                },
                "Constraint / Safety / Control",
            ),
            (
                "reasoning wins over knowledge",
                {"construct_claim": ["reasoning", "factual_knowledge"]},
                "Generative or Deliberative Reasoning",
            ),
        ]
        for label, facets, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(derive_headline_projection(facets), expected)


if __name__ == "__main__":
    unittest.main()
