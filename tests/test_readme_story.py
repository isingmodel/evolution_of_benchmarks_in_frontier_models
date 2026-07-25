from __future__ import annotations

import unittest

import pandas as pd

from analysis.readme_story.analyze import (
    add_metadata_and_flags,
    renormalize_release_weights,
)


class ReadmeStorySensitivityTests(unittest.TestCase):
    def test_work_classification_requires_all_three_axes_for_coverage(self) -> None:
        mentions = pd.DataFrame(
            [
                {
                    "provider": "TestLab",
                    "model_name": "Test Model",
                    "link": "https://example.com/model",
                    "release_date": pd.Timestamp("2026-01-01"),
                    "release_year": 2026,
                    "model_key": "TestLab|Test Model|2026-01-01",
                    "raw_mention": "TestBench",
                    "benchmark_id": "benchmark_test",
                    "benchmark_name": "TestBench",
                    "release_weight": 1.0,
                    "raw_weight": 1.0,
                    "resolved_benchmark_count_for_release": 1,
                }
            ]
        )
        benchmarks = pd.DataFrame(
            [
                {
                    "benchmark_id": "benchmark_test",
                    "source_author": "Academia",
                    "frontier_lab_author_affiliations": "none",
                    "legacy_task_mode": "Agentic",
                    "legacy_task_domain": "Coding/Engineering",
                    "review_status": "accepted",
                }
            ]
        )
        partial_map = {
            "benchmark_test": {
                "interaction_pattern": {"multi_step_planning"},
                "task_mechanism": {"tool_calling"},
            }
        }

        partial = add_metadata_and_flags(mentions, benchmarks, partial_map).iloc[0]

        self.assertTrue(partial["is_work_simulation"])
        self.assertEqual(partial["work_classification_axes_covered"], 2)
        self.assertFalse(partial["work_classification_complete"])

        complete_map = {
            "benchmark_test": {
                **partial_map["benchmark_test"],
                "construct_claim": {"agentic_task_completion"},
            }
        }
        complete = add_metadata_and_flags(mentions, benchmarks, complete_map).iloc[0]
        self.assertEqual(complete["work_classification_axes_covered"], 3)
        self.assertTrue(complete["work_classification_complete"])

    def test_renormalization_gives_each_surviving_release_one_unit(self) -> None:
        frame = pd.DataFrame(
            [
                {"model_key": "release-a", "benchmark_id": "a"},
                {"model_key": "release-a", "benchmark_id": "b"},
                {"model_key": "release-b", "benchmark_id": "c"},
            ]
        )

        normalized = renormalize_release_weights(frame)
        totals = normalized.groupby("model_key")["release_weight"].sum()

        self.assertEqual(totals.to_dict(), {"release-a": 1.0, "release-b": 1.0})
        self.assertEqual(
            normalized["resolved_benchmark_count_for_release"].tolist(),
            [2, 2, 1],
        )


if __name__ == "__main__":
    unittest.main()
