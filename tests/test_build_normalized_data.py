import unittest

import pandas as pd

from scripts.build_normalized_data import normalize_benchmarks, validate_benchmark_source
from scripts.taxonomy_utils import benchmark_id


class UnicodeBenchmarkIdentityTests(unittest.TestCase):
    def test_builder_accepts_shared_unicode_identity_and_preserves_it(self):
        names = ["Pokémon Red", "τ³-Banking Leaderboard", "ExploitBench (June–August 2026)"]
        source = pd.DataFrame([
            {
                "benchmark_id": benchmark_id(name),
                "benchmark_name": name,
                "reference_link": "https://example.com/evaluation",
                "source_author": "Academia",
                "frontier_lab_author_affiliations": "none",
                "legacy_task_mode": "Agentic",
                "legacy_task_domain": "General/Commonsense",
                "legacy_rationale": "Fixture.",
                "review_status": "needs_review",
            }
            for name in names
        ])
        validate_benchmark_source(source)
        normalized = normalize_benchmarks(source)
        self.assertEqual(
            normalized.set_index("benchmark_name")["benchmark_id"].to_dict(),
            source.set_index("benchmark_name")["benchmark_id"].to_dict(),
        )
