from __future__ import annotations

import unittest

import pandas as pd

from analysis.benchmark_evolution.benchmark_count_trend import (
    build_release_counts,
    smooth_counts,
)
from scripts.taxonomy_utils import CanonicalBenchmark, CanonicalResolver


class BenchmarkCountTrendTests(unittest.TestCase):
    def test_release_counts_keep_zero_benchmark_releases_and_smooth_full_date_range(self) -> None:
        models = pd.DataFrame(
            [
                {
                    "Provider": "TestLab",
                    "Model name": "No Bench Model",
                    "release date": "2024-01-01",
                    "benchmarks": "",
                },
                {
                    "Provider": "TestLab",
                    "Model name": "Bench Model",
                    "release date": "2024-01-10",
                    "benchmarks": "Alpha, Alpha, Beta",
                },
            ]
        )
        resolver = CanonicalResolver(
            [
                CanonicalBenchmark("benchmark_alpha", "Alpha", "fixture", 1),
                CanonicalBenchmark("benchmark_beta", "Beta", "fixture", 2),
            ]
        )
        as_of = pd.Timestamp("2024-01-12")

        counts = build_release_counts(models, as_of, resolver=resolver, strict_resolution=True)
        counts = counts.sort_values("Date").reset_index(drop=True)
        trend = smooth_counts(counts, as_of, window_days=90)

        self.assertEqual(counts.loc[0, "BenchmarkCount"], 0)
        self.assertEqual(counts.loc[1, "BenchmarkCount"], 2)
        self.assertEqual(counts.loc[1, "ResolvedMentionCount"], 3)
        self.assertEqual(len(trend), (as_of - pd.Timestamp("2024-01-01")).days + 1)
        self.assertAlmostEqual(trend.iloc[-1]["SmoothedBenchmarkCount"], 1.0)


if __name__ == "__main__":
    unittest.main()
