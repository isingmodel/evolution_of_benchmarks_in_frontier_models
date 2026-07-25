from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.validate_data import Report, validate_legacy


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
ALIAS_COLUMNS = ["alias", "benchmark_id", "match_type", "notes"]


def benchmark_row(benchmark_id: str, name: str) -> dict[str, str]:
    return {
        "benchmark_id": benchmark_id,
        "benchmark_name": name,
        "reference_link": "https://example.com",
        "source_author": "Academia",
        "frontier_lab_author_affiliations": "none",
        "legacy_task_mode": "Generative Reasoning",
        "legacy_task_domain": "General/Commonsense",
        "legacy_rationale": "Fixture.",
        "review_status": "accepted",
    }


class ValidateDataIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.models_path = self.root / "models.csv"
        self.benchmarks_path = self.root / "benchmarks.csv"
        self.aliases_path = self.root / "benchmark_aliases.csv"
        self.distinctness_path = self.root / "benchmark_distinctness.csv"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_fixture(
        self,
        benchmark_rows: list[dict[str, str]],
        mentions: str,
        alias_rows: list[dict[str, str]] | None = None,
    ) -> None:
        pd.DataFrame(
            [
                {
                    "Provider": "TestLab",
                    "Model name": "Test Model",
                    "link": "https://example.com/model",
                    "release date": "2025-01-01",
                    "benchmarks": mentions,
                }
            ]
        ).to_csv(self.models_path, index=False)
        pd.DataFrame(benchmark_rows, columns=BENCHMARK_COLUMNS).to_csv(
            self.benchmarks_path,
            index=False,
        )
        pd.DataFrame(alias_rows or [], columns=ALIAS_COLUMNS).to_csv(
            self.aliases_path,
            index=False,
        )

    def validate(self) -> Report:
        report = Report()
        validate_legacy(
            report,
            self.models_path,
            self.benchmarks_path,
            self.aliases_path,
            self.distinctness_path,
        )
        return report

    def test_alias_shadowing_is_an_error(self) -> None:
        self.write_fixture(
            [
                benchmark_row("benchmark_alpha", "Alpha"),
                benchmark_row("benchmark_beta", "Beta"),
            ],
            "Alpha",
            [
                {
                    "alias": "Alpha",
                    "benchmark_id": "benchmark_beta",
                    "match_type": "exact",
                    "notes": "Invalid fixture.",
                }
            ],
        )

        report = self.validate()

        self.assertTrue(
            any("Aliases shadow canonical benchmark names" in error for error in report.errors),
            report.errors,
        )

    def test_duplicate_normalized_identity_is_an_error(self) -> None:
        self.write_fixture(
            [
                benchmark_row("benchmark_alpha_bench", "Alpha Bench"),
                benchmark_row("benchmark_alpha_bench_duplicate", "alpha bench"),
            ],
            "Alpha Bench",
        )

        report = self.validate()

        self.assertTrue(
            any("Duplicate canonical benchmark names after normalization" in error for error in report.errors),
            report.errors,
        )

    def test_near_duplicate_identity_is_only_a_warning(self) -> None:
        self.write_fixture(
            [
                benchmark_row("benchmark_terminal_bench", "Terminal-Bench"),
                benchmark_row("benchmark_terminal_bench_2_0", "Terminal-Bench 2.0"),
            ],
            "Terminal-Bench, Terminal-Bench 2.0",
        )

        report = self.validate()

        self.assertEqual(report.errors, [])
        self.assertTrue(
            any("Near-duplicate canonical benchmark identities" in warning for warning in report.warnings),
            report.warnings,
        )

    def test_containment_near_duplicate_identity_is_only_a_warning(self) -> None:
        self.write_fixture(
            [
                benchmark_row("benchmark_firefox", "Firefox"),
                benchmark_row(
                    "benchmark_firefox_147_exploit_evaluation",
                    "Firefox 147 exploit evaluation",
                ),
            ],
            "Firefox, Firefox 147 exploit evaluation",
        )

        report = self.validate()

        self.assertEqual(report.errors, [])
        warning = next(
            (
                warning
                for warning in report.warnings
                if "Near-duplicate canonical benchmark identities" in warning
            ),
            "",
        )
        self.assertIn("'Firefox' (benchmark_firefox)", warning)
        self.assertIn(
            "'Firefox 147 exploit evaluation' "
            "(benchmark_firefox_147_exploit_evaluation)",
            warning,
        )


if __name__ == "__main__":
    unittest.main()
