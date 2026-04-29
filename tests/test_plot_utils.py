from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from plot_utils import add_derived_headline_task_mode, build_model_facet_events  # noqa: E402
from taxonomy_utils import (  # noqa: E402
    CanonicalBenchmark,
    CanonicalResolver,
    REVIEW_CONFIDENCE_THRESHOLD,
)


FACET_COLUMNS = [
    "benchmark_id",
    "facet_axis",
    "facet_label",
    "classification_confidence",
    "review_status",
    "rationale",
]


def facets_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=FACET_COLUMNS).fillna("")


class PlotUtilsFacetTests(unittest.TestCase):
    def test_derived_headline_confidence_uses_projection_axes_only(self) -> None:
        facets = facets_frame(
            [
                {
                    "benchmark_id": "benchmark_alpha",
                    "facet_axis": "construct_claim",
                    "facet_label": "agentic_task_completion",
                    "classification_confidence": 0.95,
                    "review_status": "accepted",
                    "rationale": "Projection driver.",
                },
                {
                    "benchmark_id": "benchmark_alpha",
                    "facet_axis": "metric_type",
                    "facet_label": "unknown",
                    "classification_confidence": 0.2,
                    "review_status": "needs_review",
                    "rationale": "Not consulted by headline projection.",
                },
            ]
        )

        output = add_derived_headline_task_mode(facets)
        derived = output[output["facet_axis"] == "headline_task_mode"].iloc[0]

        self.assertEqual(derived["facet_label"], "Agentic")
        self.assertAlmostEqual(float(derived["classification_confidence"]), 0.95)

    def test_derived_headline_confidence_falls_back_to_shared_threshold(self) -> None:
        facets = facets_frame(
            [
                {
                    "benchmark_id": "benchmark_alpha",
                    "facet_axis": "construct_claim",
                    "facet_label": "agentic_task_completion",
                    "classification_confidence": "",
                    "review_status": "needs_review",
                    "rationale": "Projection driver with missing confidence.",
                }
            ]
        )

        output = add_derived_headline_task_mode(facets)
        derived = output[output["facet_axis"] == "headline_task_mode"].iloc[0]

        self.assertAlmostEqual(
            float(derived["classification_confidence"]),
            REVIEW_CONFIDENCE_THRESHOLD,
        )

    def test_build_model_facet_events_splits_release_and_axis_label_weights(self) -> None:
        models = pd.DataFrame(
            [
                {
                    "Provider": "TestLab",
                    "Model name": "Test Model",
                    "release date": "2024-01-01",
                    "benchmarks": "Alpha, Beta",
                }
            ]
        )
        facets = facets_frame(
            [
                {
                    "benchmark_id": "benchmark_alpha",
                    "facet_axis": "domain",
                    "facet_label": "Law",
                    "classification_confidence": 1.0,
                    "review_status": "accepted",
                    "rationale": "Fixture.",
                },
                {
                    "benchmark_id": "benchmark_alpha",
                    "facet_axis": "domain",
                    "facet_label": "Finance",
                    "classification_confidence": 1.0,
                    "review_status": "accepted",
                    "rationale": "Fixture.",
                },
                {
                    "benchmark_id": "benchmark_beta",
                    "facet_axis": "domain",
                    "facet_label": "STEM/Math",
                    "classification_confidence": 1.0,
                    "review_status": "accepted",
                    "rationale": "Fixture.",
                },
            ]
        )
        resolver = CanonicalResolver(
            [
                CanonicalBenchmark("benchmark_alpha", "Alpha", "fixture", 1),
                CanonicalBenchmark("benchmark_beta", "Beta", "fixture", 2),
            ]
        )

        events = build_model_facet_events(
            models,
            facets,
            ["domain"],
            pd.Timestamp("2024-01-31"),
            resolver=resolver,
        )
        weights = events.groupby("Category")["Weight"].sum().to_dict()

        self.assertEqual(events["resolved_mentions_on_release"].unique().tolist(), [2])
        self.assertAlmostEqual(weights["Law"], 0.25)
        self.assertAlmostEqual(weights["Finance"], 0.25)
        self.assertAlmostEqual(weights["STEM/Math"], 0.5)
        self.assertAlmostEqual(events["Weight"].sum(), 1.0)


if __name__ == "__main__":
    unittest.main()
