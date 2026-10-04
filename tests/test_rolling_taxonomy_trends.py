from __future__ import annotations

import unittest
from pathlib import Path
import subprocess
import sys
import tempfile

import pandas as pd

from scripts.plot_utils import build_rolling_share_trend


def events(*rows: tuple[str, str, float]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["Date", "Category", "Weight"])
    frame["Date"] = pd.to_datetime(frame["Date"])
    return frame


class RollingTaxonomyTrendTests(unittest.TestCase):
    def test_boundary_expiry_changes_composition_without_smoothing_or_carry_forward(self):
        # A three-day window retains Jan 1 through Jan 3, but not Jan 4.
        # The second release enters on Jan 4 and expires on Jan 7.
        trend, first_date = build_rolling_share_trend(
            events(("2026-01-01", "A", .5), ("2026-01-01", "B", .5),
                   ("2026-01-04", "A", 1.0)),
            pd.Timestamp("2026-01-08"), 3, ["A", "B"],
        )
        self.assertEqual(first_date, pd.Timestamp("2026-01-01"))
        for day in ["2026-01-01", "2026-01-02", "2026-01-03"]:
            self.assertEqual(trend.loc[day].tolist(), [.5, .5])
        for day in ["2026-01-04", "2026-01-05", "2026-01-06"]:
            self.assertEqual(trend.loc[day].tolist(), [1.0, 0.0])
        self.assertTrue(trend.loc["2026-01-07":"2026-01-08"].isna().all().all())

    def test_new_recorded_row_after_an_empty_window_restarts_at_its_own_composition(self):
        trend, _ = build_rolling_share_trend(
            events(("2026-02-01", "A", 1.0), ("2026-02-07", "B", 1.0)),
            pd.Timestamp("2026-02-07"), 2, ["B", "A", "Absent"],
        )
        self.assertEqual(trend.columns.tolist(), ["B", "A", "Absent"])
        self.assertTrue(trend.loc["2026-02-03":"2026-02-06"].isna().all().all())
        self.assertEqual(trend.loc["2026-02-07"].tolist(), [1.0, 0.0, 0.0])

    def test_repeated_category_weight_counts_again_and_normalizes_only_covered_weight(self):
        # One row has .4 covered A weight and .1 covered B weight; its missing
        # half is not an annotated category. A later A appearance contributes
        # another unit. This is composition among covered weight, not first use.
        trend, _ = build_rolling_share_trend(
            events(("2026-03-01", "A", .4), ("2026-03-01", "B", .1),
                   ("2026-03-02", "A", 1.0)),
            pd.Timestamp("2026-03-02"), 2, ["A", "B"],
        )
        self.assertAlmostEqual(trend.loc["2026-03-01", "A"], .8)
        self.assertAlmostEqual(trend.loc["2026-03-01", "B"], .2)
        self.assertAlmostEqual(trend.loc["2026-03-02", "A"], 14 / 15)
        self.assertAlmostEqual(trend.loc["2026-03-02", "B"], 1 / 15)

    def test_no_events_retains_requested_categories_without_inventing_dates(self):
        trend, first_date = build_rolling_share_trend(
            pd.DataFrame(columns=["Date", "Category", "Weight"]),
            pd.Timestamp("2026-03-31"), 180, ["A", "B"],
        )
        self.assertTrue(trend.empty)
        self.assertEqual(trend.columns.tolist(), ["A", "B"])
        self.assertIsNone(first_date)

    def test_empty_cutoff_cli_replaces_previous_images_for_every_taxonomy_view(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            for name in ["task_mode_trend", "separate_axis_trends", "facet_trends"]:
                with self.subTest(script=name):
                    output = Path(directory) / f"{name}.png"
                    output.write_bytes(b"previous-cutoff-image")
                    result = subprocess.run(
                        [sys.executable, str(root / "analysis/benchmark_taxonomy_trends" / f"{name}.py"),
                         "--as-of", "2020-01-01", "--output", str(output), "--strict-resolution"],
                        cwd=root, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
                    self.assertGreater(output.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
