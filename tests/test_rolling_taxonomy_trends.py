from __future__ import annotations

import unittest
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import warnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import pandas as pd

from analysis.benchmark_taxonomy_trends import facet_trends, separate_axis_trends, task_mode_trend
from scripts.plot_utils import build_rolling_share_trend, draw_rolling_composition, set_rolling_date_limits
from scripts.taxonomy_utils import CanonicalBenchmark, CanonicalResolver


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

    def test_first_covered_date_is_visible_in_all_three_plotters_without_singular_limits(self):
        # This is the actual first benchmark-bearing source date, so the test
        # crosses the loader, resolution, projection and rendering boundaries.
        date = pd.Timestamp("2023-03-14")
        for module, generate in [
            (task_mode_trend, task_mode_trend.generate_trend_graph),
            (separate_axis_trends, separate_axis_trends.generate_trend_graph),
            (facet_trends, facet_trends.generate_facet_trends),
        ]:
            with self.subTest(plotter=module.__name__):
                captured = []
                with patch.object(module, "save_figure", side_effect=lambda fig, path: captured.append(fig)), \
                     warnings.catch_warnings(record=True) as raised:
                    generate(as_of=date, output_path="unused.png", strict_resolution=True)
                self.assertEqual(len(captured), 1)
                fig = captured[0]
                fig.canvas.draw()
                for ax in fig.axes:
                    segments = [segment for collection in ax.collections if isinstance(collection, LineCollection)
                                for segment in collection.get_segments()]
                    self.assertTrue(segments, "A singleton area must have visible snapshot glyphs.")
                    self.assertTrue(all(segment[0, 0] == mdates.date2num(date) == segment[1, 0] for segment in segments))
                    self.assertAlmostEqual(sum(segment[1, 1] - segment[0, 1] for segment in segments), 1)
                    self.assertLess(ax.get_xlim()[0], mdates.date2num(date))
                    self.assertGreater(ax.get_xlim()[1], mdates.date2num(date))
                    self.assertTrue(any("Snapshot · 2023-03-14" in text.get_text() for text in ax.texts))
                self.assertFalse(any("identical" in str(warning.message).lower() for warning in raised))

    def test_one_day_windows_render_every_isolated_date_without_filling_missing_days(self):
        trend, first = build_rolling_share_trend(
            events(("2026-01-01", "A", .25), ("2026-01-01", "B", .75),
                   ("2026-01-04", "A", 1.0)),
            pd.Timestamp("2026-01-06"), 1, ["A", "B"],
        )
        before = trend.copy()
        fig, ax = plt.subplots()
        draw_rolling_composition(ax, trend, ["A", "B"], ["red", "blue"])
        set_rolling_date_limits(ax, first, pd.Timestamp("2026-01-06"))
        fig.canvas.draw()
        segments = [segment for collection in ax.collections if isinstance(collection, LineCollection)
                    for segment in collection.get_segments()]
        self.assertEqual([segment.tolist() for segment in segments], [
            [[mdates.date2num(pd.Timestamp("2026-01-01")), 0], [mdates.date2num(pd.Timestamp("2026-01-01")), .25]],
            [[mdates.date2num(pd.Timestamp("2026-01-01")), .25], [mdates.date2num(pd.Timestamp("2026-01-01")), 1]],
            [[mdates.date2num(pd.Timestamp("2026-01-04")), 0], [mdates.date2num(pd.Timestamp("2026-01-04")), 1]],
        ])
        pd.testing.assert_frame_equal(trend, before)
        self.assertTrue(trend.loc[["2026-01-02", "2026-01-03", "2026-01-05", "2026-01-06"]].isna().all().all())
        last_annotation = next(text for text in ax.texts if "2026-01-04" in text.get_text())
        self.assertEqual(last_annotation.get_ha(), "right")
        plt.close(fig)

    def test_facet_normalization_keeps_separate_same_named_source_rows_equal(self):
        resolver = CanonicalResolver([
            CanonicalBenchmark(f"benchmark_{name.lower()}", name, "fixture", index)
            for index, name in enumerate(["Alpha", "Beta", "Gamma"], 1)
        ])
        models = pd.DataFrame([
            {"Provider": "A", "Model name": name, "release date": "2026-01-01",
             "link": f"https://a.example/{benchmark}", "benchmarks": benchmark}
            for name, benchmark in [("Same", "Alpha"), ("Same", "Beta"), ("Other", "Gamma")]
        ])
        facets = pd.DataFrame([
            {"benchmark_id": f"benchmark_{name.lower()}", "facet_axis": "domain",
             "facet_label": name, "review_status": "accepted"}
            for name in ["Alpha", "Beta", "Gamma"]
        ])
        mentions = facet_trends.build_model_mentions(models, resolver, strict_resolution=True)
        weighted = facet_trends.normalize_mentions(mentions, pd.Timestamp("2026-01-01"))
        self.assertEqual(weighted["model_row_id"].nunique(), 3)
        self.assertEqual(weighted.groupby("model_row_id")["normalized_model_weight"].sum().tolist(), [1, 1, 1])
        axis_events = facet_trends.events_for_axis(weighted, facets, "domain", 8)
        trend, _ = build_rolling_share_trend(axis_events, pd.Timestamp("2026-01-01"), 180)
        for label in ["Alpha", "Beta", "Gamma"]:
            self.assertAlmostEqual(trend.iloc[0][label], 1 / 3)

    def test_facet_scope_excludes_future_unknown_before_strict_resolution(self):
        resolver = CanonicalResolver([CanonicalBenchmark("benchmark_alpha", "Alpha", "fixture", 1)])
        models = pd.DataFrame([
            {"Provider": "A", "Model name": "Known", "release date": "2026-01-01", "benchmarks": "Alpha"},
            {"Provider": "A", "Model name": "Future", "release date": "2027-01-01", "benchmarks": "Future Unknown"},
        ])
        models["release_date"] = pd.Timestamp("2030-01-01")
        facets = pd.DataFrame([{"benchmark_id": "benchmark_alpha", "facet_axis": "domain",
                                "facet_label": "Alpha", "review_status": "accepted"}])
        with tempfile.TemporaryDirectory() as directory, \
            patch.object(facet_trends, "load_inputs", return_value=(models, facets, resolver)):
            output = Path(directory) / "facet.png"
            for cutoff in ["2020-01-01", "2026-01-31"]:
                output.write_bytes(b"previous-cutoff-image")
                facet_trends.generate_facet_trends(as_of=pd.Timestamp(cutoff), axes=["domain"],
                                                   output_path=str(output), strict_resolution=True)
                self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            with self.assertRaisesRegex(ValueError, "Future Unknown"):
                facet_trends.generate_facet_trends(as_of=pd.Timestamp("2027-01-01"), axes=["domain"],
                                                   output_path=str(output), strict_resolution=True)


if __name__ == "__main__":
    unittest.main()
