from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from matplotlib.offsetbox import AnnotationBbox

from analysis.benchmark_evolution.analyze import (
    _draw_timeline,
    assign_collision_lanes,
    generate_graph,
    process_data,
    select_name_labels,
)
from scripts.plot_utils import MODE_ORDER


EVENT_COLUMNS = ["model_key", "Category", "Weight", "resolved_mentions_on_release"]


class BenchmarkEvolutionTimelineTests(unittest.TestCase):
    def test_inventory_rows_dates_and_conditional_projection_coverage_are_retained(self):
        models = pd.DataFrame([
            {"Provider": "Lab", "Model name": "Empty", "release date": "2026-01-01", "benchmarks": ""},
            {"Provider": "Lab", "Model name": "No projection", "release date": "2026-01-02", "benchmarks": "Alpha"},
            {"Provider": "Lab", "Model name": "Partial", "release date": "2026-01-03", "benchmarks": "Alpha, Beta"},
            {"Provider": "Lab", "Model name": "Twin", "release date": "2026-01-04", "benchmarks": "Alpha"},
            {"Provider": "Lab", "Model name": "Twin", "release date": "2026-01-04", "benchmarks": "Alpha"},
            {"Provider": "Lab", "Model name": "Future", "release date": "2026-02-01", "benchmarks": "Alpha"},
        ])
        # Enriched frames must not move source dates or merge otherwise equal rows.
        models["release_date"] = pd.Timestamp("2030-01-01")
        models["model_key"] = "stale-shared-key"

        def annotated_events(scoped, facets, axes, cutoff, strict_resolution):
            self.assertEqual(scoped["model_key"].nunique(), 5)
            self.assertEqual(scoped["release_date"].max(), pd.Timestamp("2026-01-04"))
            rows = []
            for model in scoped.to_dict("records"):
                if model["Model name"] == "Partial":
                    rows.extend([
                        [model["model_key"], "Agentic", .4, 2],
                        [model["model_key"], "Generative Reasoning", .1, 2],
                    ])
                elif model["Model name"] == "Twin":
                    rows.append([model["model_key"], "Agentic", 1., 1])
            return pd.DataFrame(rows, columns=EVENT_COLUMNS)

        with patch("analysis.benchmark_evolution.analyze.build_model_facet_events", side_effect=annotated_events):
            frame, categories = process_data(models, pd.DataFrame(), pd.Timestamp("2026-01-10"), True)

        self.assertEqual(len(frame), 5)
        self.assertEqual(frame["Model"].tolist().count("Twin"), 2)
        self.assertEqual(frame["Status"].tolist(), ["empty", "unclassified", "partial", "projected", "projected"])
        self.assertEqual(frame["Date"].tolist(), pd.to_datetime(models.iloc[:5]["release date"]).tolist())
        partial = frame.loc[frame["Model"] == "Partial"].iloc[0]
        self.assertEqual(partial["RawMentionCount"], 2)
        self.assertAlmostEqual(partial["ProjectionCoverage"], .5)
        self.assertAlmostEqual(partial["Ratios"][categories.index("Agentic")], .8)
        self.assertAlmostEqual(partial["Ratios"][categories.index("Generative Reasoning")], .2)
        self.assertEqual(frame.loc[frame["Status"] == "empty", "ProjectionCoverage"].iloc[0], 0)

    def test_same_day_markers_use_distinct_vertical_lanes_and_keep_true_dates(self):
        frame = pd.DataFrame({
            "Provider": ["A", "A", "A", "A", "B"],
            "Model": ["Two", "One", "Later", "Next", "Other"],
            "Date": pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-08", "2026-01-20", "2026-01-01"]),
        })
        packed = assign_collision_lanes(frame, 10)
        pd.testing.assert_series_equal(packed["Date"].sort_index(), frame["Date"])
        same_day = packed.loc[(packed["Provider"] == "A") & (packed["Date"] == "2026-01-01")]
        self.assertEqual(same_day["Lane"].nunique(), 2)
        self.assertEqual(packed.loc[packed["Provider"] == "B", "Lane"].iloc[0], 0)
        for _, group in packed.groupby(["Provider", "Lane"]):
            differences = group["Date"].sort_values().diff().dropna().dt.days
            self.assertTrue((differences >= 10).all())
        selected = frame.loc[select_name_labels(frame), "Model"].tolist()
        self.assertEqual(set(selected), {"One", "Next", "Other"})
        reversed_frame = frame.iloc[::-1]
        self.assertEqual(set(reversed_frame.loc[select_name_labels(reversed_frame), "Model"]), set(selected))

    def test_rendered_markers_anchor_every_model_at_its_date_and_keep_fixed_area(self):
        frame = pd.DataFrame({
            "Provider": ["A", "A", "A"], "Model": ["One", "Two", "Empty"],
            "Date": pd.to_datetime(["2026-01-01", "2026-01-01", "2026-01-20"]),
            "Ratios": [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0] * 5],
            "Status": ["projected", "projected", "empty"], "ProjectionCoverage": [1, 1, 0],
        })
        for detail in [False, True]:
            with self.subTest(detail=detail):
                captured = []
                with patch("analysis.benchmark_evolution.analyze.save_figure", side_effect=lambda fig, path: captured.append(fig)):
                    _draw_timeline(frame, MODE_ORDER, pd.Timestamp("2026-01-20"), "unused.png", detail=detail)
                fig = captured[0]
                markers = [artist for artist in fig.axes[0].artists if isinstance(artist, AnnotationBbox)]
                self.assertEqual(len(markers), 3)
                self.assertEqual(sorted(pd.Timestamp(marker.xy[0]) for marker in markers), sorted(frame["Date"]))
                self.assertEqual(len({marker.xy[1] for marker in markers[:2]}), 2)
                self.assertEqual({(marker.offsetbox.width, marker.offsetbox.height) for marker in markers}, {(23, 23)})

    def test_empty_cutoff_replaces_both_outputs_with_explicit_empty_state(self):
        models = pd.DataFrame([{
            "Provider": "A", "Model name": "Future", "release date": "2026-01-01", "benchmarks": "",
        }])
        with tempfile.TemporaryDirectory() as directory:
            main = Path(directory) / "main.png"
            detail = Path(directory) / "detail.png"
            main.write_bytes(b"stale image")
            detail.write_bytes(b"stale image")
            with patch("analysis.benchmark_evolution.analyze.load_models", return_value=models), \
                 patch("analysis.benchmark_evolution.analyze.load_benchmark_facets", return_value=pd.DataFrame()), \
                 patch("analysis.benchmark_evolution.analyze.build_model_facet_events", return_value=pd.DataFrame(columns=EVENT_COLUMNS)):
                generate_graph(pd.Timestamp("2020-01-01"), str(main), True, detail_output=str(detail))
            for output in [main, detail]:
                self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertGreater(output.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
