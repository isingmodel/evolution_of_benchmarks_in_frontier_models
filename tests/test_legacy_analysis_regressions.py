from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from analysis.frontier_lab_benchmark_hegemony import analyze as authorship
from analysis.ideation_network_dynamics.analyze import parse_lab_affiliations, source_author_group
from analysis.readme_story.analyze import write_diffusion_outputs, write_review_leverage_outputs


class LegacyAnalysisRegressionTests(unittest.TestCase):
    def test_first_day_provider_ties_are_retained_without_direction_between_coadopters(self):
        rows = [
            ("all_tied", "All tied", "C", "2026-01-01"),
            ("all_tied", "All tied", "A", "2026-01-01"),
            ("all_tied", "All tied", "B", "2026-01-01"),
            ("early_tie", "Early tie", "B", "2026-01-01"),
            ("early_tie", "Early tie", "A", "2026-01-01"),
            ("early_tie", "Early tie", "C", "2026-01-10"),
            ("later_tie", "Later tie", "A", "2026-01-01"),
            ("later_tie", "Later tie", "C", "2026-01-10"),
            ("later_tie", "Later tie", "B", "2026-01-10"),
        ]
        mentions = pd.DataFrame(rows, columns=["benchmark_id", "benchmark_name", "provider", "release_date"])
        mentions["release_date"] = pd.to_datetime(mentions["release_date"])
        mentions["source_author"] = "Academia"
        with tempfile.TemporaryDirectory() as directory:
            write_diffusion_outputs(mentions, Path(directory))
            cascades = pd.read_csv(Path(directory) / "public_benchmark_diffusion_cascades.csv").set_index("benchmark_id")
        self.assertEqual(set(cascades.index), {"all_tied", "early_tie", "later_tie"})
        self.assertEqual(cascades.loc["all_tied", "days_to_next_provider"], 0)
        self.assertEqual(cascades.loc["all_tied", "first_tracked_providers"], "A; B; C")
        self.assertEqual(cascades.loc["all_tied", "next_provider"], "A; B; C")
        self.assertEqual(cascades.loc["all_tied", "public_mention_path"], "A; B; C (2026-01-01)")
        self.assertEqual(cascades.loc["early_tie", "days_to_next_provider"], 0)
        self.assertEqual(cascades.loc["early_tie", "public_mention_path"], "A; B (2026-01-01) -> C (2026-01-10)")
        self.assertEqual(cascades.loc["later_tie", "days_to_next_provider"], 9)
        self.assertEqual(cascades.loc["later_tie", "next_provider"], "B; C")
        self.assertEqual(cascades.loc["later_tie", "public_mention_path"], "A (2026-01-01) -> B; C (2026-01-10)")

    def test_missing_annotations_have_full_uncertainty_in_review_leverage(self):
        mentions = pd.DataFrame({
            "benchmark_id": ["unannotated", "accepted"],
            "benchmark_name": ["Unannotated", "Accepted"],
            "provider": ["OpenAI", "OpenAI"],
            "release_date": pd.to_datetime(["2026-01-01", "2026-01-01"]),
            "release_weight": [0.5, 0.5], "raw_weight": [1.0, 1.0],
        })
        counts = pd.DataFrame({
            "benchmark_id": ["accepted"], "accepted": [2], "legacy_seed": [0],
            "needs_review": [0], "disputed": [0], "facet_rows_total": [2], "nonaccepted_share": [0.0],
        })
        with tempfile.TemporaryDirectory() as directory, patch("matplotlib.figure.Figure.savefig"):
            output = Path(directory)
            write_review_leverage_outputs(mentions, counts, output, output, pd.Timestamp("2026-01-31"))
            leverage = pd.read_csv(output / "review_leverage_benchmarks.csv").set_index("benchmark_id")
            write_review_leverage_outputs(mentions, pd.DataFrame(), output, output, pd.Timestamp("2026-01-31"))
            entirely_missing = pd.read_csv(output / "review_leverage_benchmarks.csv")
        self.assertEqual(leverage.loc["unannotated", "facet_rows_total"], 0)
        self.assertEqual(leverage.loc["unannotated", "nonaccepted_share"], 1)
        self.assertEqual(leverage.loc["unannotated", "review_leverage"], 0.5)
        self.assertEqual(leverage.loc["accepted", "review_leverage"], 0)
        self.assertTrue(entirely_missing["nonaccepted_share"].eq(1).all())
        self.assertTrue(entirely_missing["review_leverage"].eq(0.5).all())

    def test_unknown_provenance_is_not_an_invented_frontier_lab_in_network_groups(self):
        for value in [None, "", "needs_review", "UNKNOWN", "missing", "n/a"]:
            with self.subTest(value=value):
                self.assertEqual(parse_lab_affiliations(value), set())
                self.assertEqual(source_author_group("OpenAI", value, value), "Unknown")
        self.assertEqual(parse_lab_affiliations("OpenAI; needs_review; Google"), {"OpenAI", "Google"})
        self.assertEqual(source_author_group("OpenAI", "needs_review", "OpenAI"), "Self-affiliated frontier lab")
        self.assertEqual(source_author_group("OpenAI", "needs_review", "Google"), "Other frontier lab-affiliated")
        self.assertEqual(source_author_group("OpenAI", "Academia", "none"), "Academia")
        self.assertEqual(source_author_group("OpenAI", "Others(Vendor)", "none"), "Independent/industry")

    def test_authorship_unknown_affiliation_is_distinct_from_known_none_and_stays_in_denominators(self):
        names = ["MRCR", "Neutral", "Own", "Other"]
        ids = ["mrcr", "neutral", "own", "other"]
        mentions = pd.DataFrame({
            "benchmark_id": ids, "benchmark_name": names, "provider": ["OpenAI"] * 4,
            "model_name": ["Model"] * 4, "mention_id": ["m1", "m2", "m3", "m4"],
            "mention_index": [1, 2, 3, 4], "period": ["2025-2026"] * 4,
            "release_year": [2026] * 4, "release_date": pd.to_datetime(["2026-01-01"] * 4),
        })
        catalog = pd.DataFrame({
            "benchmark_id": ids,
            "source_author": ["needs_review", "Academia", "OpenAI", "DeepMind"],
            "frontier_lab_author_affiliations": ["needs_review", "none", "OpenAI", "DeepMind"],
            "reference_link": ["https://example.org"] * 4, "legacy_task_mode": ["Agentic"] * 4,
            "legacy_task_domain": ["General/Commonsense"] * 4, "review_status": ["needs_review"] * 4,
        })
        lifecycle = pd.DataFrame(columns=["benchmark_id", "lifecycle_labels"])
        enriched = authorship.add_provenance_columns(mentions, catalog, lifecycle)
        by_id = enriched.set_index("benchmark_id")
        self.assertEqual(by_id.loc["mrcr", "author_position"], "unknown_affiliation")
        self.assertEqual(by_id.loc["mrcr", "frontier_lab_affiliation_labs"], "unknown")
        self.assertFalse(by_id.loc["mrcr", "is_any_frontier_affiliated"])
        self.assertFalse(by_id.loc["mrcr", "is_openai_source_or_affiliated"])
        self.assertEqual(by_id.loc["neutral", "author_position"], "neutral_or_non_frontier")
        self.assertEqual(by_id.loc["own", "author_position"], "own_lab_only")
        self.assertEqual(by_id.loc["other", "author_position"], "competitor_lab_only")
        with tempfile.TemporaryDirectory() as directory, patch.object(authorship, "OUT_DIR", Path(directory)):
            shares = authorship.write_provider_period_author_shares(enriched).iloc[0]
            matrix = authorship.write_cross_lab_matrix(enriched)
            signals = authorship.write_high_signal_benchmarks(enriched).set_index("benchmark_id")
        self.assertEqual(shares["total_mentions"], 4)
        self.assertEqual(shares["unknown_affiliation_mentions"], 1)
        self.assertEqual(shares["unknown_affiliation_share"], 0.25)
        self.assertEqual(shares["neutral_or_non_frontier_share"], 0.25)
        self.assertEqual(set(matrix["target_lab_group"]), {"Unknown affiliation", "Neutral/no frontier lab", "OpenAI", "Google/DeepMind"})
        self.assertEqual(int(matrix["mentions"].sum()), 4)
        self.assertEqual(signals.loc["mrcr", "high_signal_reason"], "unknown_affiliation")
        self.assertEqual(authorship.split_semicolon_labels("needs_review"), set())
        self.assertEqual(authorship.split_semicolon_labels("unknown; OpenAI; Invented lab"), {"OpenAI"})


if __name__ == "__main__":
    unittest.main()
