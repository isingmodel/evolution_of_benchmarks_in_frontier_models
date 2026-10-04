from __future__ import annotations

import json
from pathlib import Path
import unittest

import pandas as pd

from analysis.project_overview.metrics import build_overview_tables
from analysis.project_overview.analyze import readme_values, render_readme, sharing_title
from scripts.taxonomy_utils import AliasEntry, CanonicalBenchmark, CanonicalResolver, benchmark_id


def catalog(*names: str, aliases: dict[str, str] | None = None):
    records = [
        {"benchmark_id": benchmark_id(name), "benchmark_name": name, "review_status": "needs_review"}
        for name in names
    ]
    resolver = CanonicalResolver(
        [CanonicalBenchmark(benchmark_id(name), name, "fixture.csv", i) for i, name in enumerate(names, 2)],
        [
            AliasEntry(surface, benchmark_id(target), "exact", "Fixture alias", "aliases.csv", i)
            for i, (surface, target) in enumerate((aliases or {}).items(), 2)
        ],
    )
    return pd.DataFrame(records), resolver


def models(*rows: tuple[str, str, str, str, str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Provider", "Model name", "release date", "link", "benchmarks"])


def facets(*rows: tuple[str, str, str, float, str]) -> pd.DataFrame:
    return pd.DataFrame(
        [(benchmark_id(name), axis, label, confidence, status) for name, axis, label, confidence, status in rows],
        columns=["benchmark_id", "facet_axis", "facet_label", "classification_confidence", "review_status"],
    )


class ProjectOverviewTests(unittest.TestCase):
    def build(self, model_rows, names, facet_rows=(), *, aliases=None, as_of="2026-07-01"):
        benchmarks, resolver = catalog(*names, aliases=aliases)
        return build_overview_tables(model_rows, benchmarks, facets(*facet_rows), resolver, as_of=as_of)

    def trend(self, tables, *, unit="announcement", variant="all_active", year=2026):
        frame = tables["interaction_trends"]
        selected = frame[(frame["unit"] == unit) & (frame["variant"] == variant) & (frame["release_year"] == year)]
        self.assertEqual(len(selected), 1)
        return selected.iloc[0]

    def classification(self, tables, name, variant="all_active"):
        frame = tables["interaction_classification"]
        selected = frame[(frame["benchmark_name"] == name) & (frame["variant"] == variant)]
        self.assertEqual(len(selected), 1)
        return selected.iloc[0]

    def test_joint_page_is_one_announcement_but_retains_model_row_sensitivity(self):
        tables, _ = self.build(
            models(
                ("A", "Large", "2026-01-01", "https://a.example/joint/?utm_source=x#table", "Alpha, Beta, Alias Alpha"),
                ("A", "Small", "2026-01-01", "https://a.example/joint", "Alias Alpha"),
                ("B", "Other", "2026-01-02", "https://b.example/other", "Beta"),
            ),
            ["Alpha", "Beta", "Unobserved"],
            [
                ("Alpha", "interaction_pattern", "single_turn_tool_use", .9, "needs_review"),
                ("Beta", "interaction_pattern", "static_prompt_response", .9, "needs_review"),
            ],
            aliases={"Alias Alpha": "Alpha"},
        )
        announcement = self.trend(tables)
        model_row = self.trend(tables, unit="model_row")
        self.assertEqual(announcement["benchmark_bearing_units"], 2)
        self.assertAlmostEqual(announcement["positive_share"], .25)
        self.assertEqual(model_row["benchmark_bearing_units"], 3)
        self.assertAlmostEqual(model_row["positive_share"], .5)
        self.assertEqual(len(tables["launch_events"]), 2)
        self.assertEqual(len(tables["launch_mentions"]), 3)
        self.assertEqual(len(tables["canonical_model_mentions"]), 4)
        sharing = tables["sharing_summary"].set_index("provider_count")
        self.assertEqual(sharing.loc[1, "benchmark_count"], 1)
        self.assertEqual(sharing.loc[2, "benchmark_count"], 1)
        self.assertAlmostEqual(sharing.loc[1, "benchmark_share"], .5)
        self.assertAlmostEqual(sharing.loc[2, "mention_share"], 2 / 3)
        self.assertAlmostEqual(sharing.loc[1, "announcement_weight_share"], .25)
        self.assertAlmostEqual(sharing.loc[2, "announcement_weight_share"], .75)
        inventory = tables["annual_inventory"].set_index("release_year").loc[2026]
        self.assertEqual(inventory["model_rows"], 3)
        self.assertEqual(inventory["launch_events"], 2)
        self.assertEqual(inventory["benchmark_bearing_launches"], 2)
        self.assertEqual(inventory["launch_mentions"], 3)
        self.assertEqual(inventory["new_identities"], 2)

    def test_static_code_and_planning_only_are_outside_strict_interaction_flag(self):
        names = ["Code", "Planning", "Human", "Dialogue", "Tool", "Environment"]
        tables, _ = self.build(
            models(("A", "One", "2026-01-01", "https://a.example/one", ", ".join(names))),
            names,
            [
                ("Code", "interaction_pattern", "static_prompt_response", .9, "accepted"),
                ("Code", "task_mechanism", "unit_test_passing", .9, "accepted"),
                ("Code", "construct_claim", "software_engineering", .9, "accepted"),
                ("Planning", "interaction_pattern", "multi_step_planning", .9, "accepted"),
                ("Planning", "construct_claim", "agentic_task_completion", .9, "accepted"),
                ("Human", "interaction_pattern", "human_in_the_loop", .9, "accepted"),
                ("Dialogue", "interaction_pattern", "multi_turn_dialogue", .9, "accepted"),
                ("Tool", "interaction_pattern", "single_turn_tool_use", .9, "accepted"),
                ("Environment", "interaction_pattern", "environment_interaction", .9, "accepted"),
            ],
        )
        for name in names[:4]:
            row = self.classification(tables, name)
            self.assertTrue(row["covered"])
            self.assertFalse(row["positive"])
        for name in names[4:]:
            self.assertTrue(self.classification(tables, name)["positive"])
        self.assertAlmostEqual(self.trend(tables)["positive_share"], 1 / 3)

    def test_confidence_and_review_acceptance_are_independent_filters(self):
        names = ["High", "AcceptedLow", "Boundary", "Deprecated", "Static"]
        tables, _ = self.build(
            models(("A", "One", "2026-01-01", "https://a.example/one", ", ".join(names))),
            names,
            [
                ("High", "interaction_pattern", "browser_or_web_interaction", .9, "needs_review"),
                ("AcceptedLow", "interaction_pattern", "computer_control", .6, "accepted"),
                ("Boundary", "interaction_pattern", "terminal_or_codebase_interaction", .7, "needs_review"),
                ("Deprecated", "interaction_pattern", "environment_interaction", .99, "deprecated"),
                ("Static", "interaction_pattern", "static_prompt_response", .99, "accepted"),
            ],
        )
        expectations = {
            "all_active": (.6, .8, .75),
            "confidence_ge_0_7": (.4, .6, 2 / 3),
            "accepted": (.2, .4, .5),
        }
        for variant, (positive, covered, conditional) in expectations.items():
            row = self.trend(tables, variant=variant)
            self.assertAlmostEqual(row["positive_share"], positive)
            self.assertAlmostEqual(row["coverage_share"], covered)
            self.assertAlmostEqual(row["positive_share_among_covered"], conditional)
            self.assertFalse(self.classification(tables, "Deprecated", variant)["covered"])
        self.assertTrue(self.classification(tables, "Boundary", "confidence_ge_0_7")["positive"])
        self.assertTrue(pd.isna(self.classification(tables, "AcceptedLow", "confidence_ge_0_7")["positive"]))
        self.assertTrue(pd.isna(self.classification(tables, "High", "accepted")["positive"]))

    def test_partial_coverage_retains_original_weights_across_announcements(self):
        tables, _ = self.build(
            models(
                ("A", "Wide", "2026-01-01", "https://a.example/wide", "Tool, Unknown1, Unknown2, Unknown3"),
                ("A", "Narrow", "2026-01-02", "https://a.example/narrow", "Static"),
            ),
            ["Tool", "Static", "Unknown1", "Unknown2", "Unknown3"],
            [
                ("Tool", "interaction_pattern", "single_turn_tool_use", .8, "accepted"),
                ("Static", "interaction_pattern", "static_prompt_response", .8, "accepted"),
            ],
        )
        for variant in ["all_active", "confidence_ge_0_7", "accepted"]:
            row = self.trend(tables, variant=variant)
            self.assertEqual(row["benchmark_bearing_units"], 2)
            self.assertAlmostEqual(row["positive_share"], .125)
            self.assertAlmostEqual(row["coverage_share"], .625)
            self.assertAlmostEqual(row["positive_share_among_covered"], .2)

    def test_unclassified_mentions_and_benchmark_empty_year_keep_missing_conditional_rates(self):
        tables, summary = self.build(
            models(
                ("A", "Unknown", "2025-01-01", "https://a.example/unknown", "Alpha"),
                ("A", "Empty", "2026-01-01", "https://a.example/empty", ""),
            ),
            ["Alpha", "NeverSeen"],
        )
        self.assertEqual(len(tables["interaction_classification"]), 6)
        for variant in ["all_active", "confidence_ge_0_7", "accepted"]:
            classification = self.classification(tables, "Alpha", variant)
            self.assertFalse(classification["covered"])
            self.assertTrue(pd.isna(classification["positive"]))
            unknown = self.trend(tables, variant=variant, year=2025)
            self.assertEqual(unknown["benchmark_bearing_units"], 1)
            self.assertEqual(unknown["coverage_share"], 0)
            self.assertTrue(pd.isna(unknown["positive_share_among_covered"]))
            empty = self.trend(tables, variant=variant, year=2026)
            self.assertEqual(empty["benchmark_bearing_units"], 0)
            for field in ["positive_share", "coverage_share", "positive_share_among_covered"]:
                self.assertTrue(pd.isna(empty[field]))
        self.assertEqual(set(tables["annual_inventory"]["release_year"]), {2025, 2026})
        inventory = tables["annual_inventory"].set_index("release_year")
        self.assertEqual(inventory.loc[2026, "model_rows"], 1)
        self.assertEqual(inventory.loc[2026, "launch_events"], 1)
        self.assertEqual(inventory.loc[2026, "benchmark_bearing_launches"], 0)
        self.assertEqual(inventory.loc[2026, "launch_mentions"], 0)
        self.assertEqual(summary["latest_release_year"], 2026)
        json.dumps(summary, allow_nan=False)

    def test_diffusion_uses_complete_horizon_cohorts_and_inclusive_boundary_days(self):
        tables, _ = self.build(
            models(
                ("A", "First", "2026-01-01", "https://a.example/first", "Day30, Day90, Day180, Tied, Never"),
                ("B", "Tied", "2026-01-01", "https://b.example/tied", "Tied"),
                ("B", "Day30", "2026-01-31", "https://b.example/day30", "Day30"),
                ("B", "Day90", "2026-04-01", "https://b.example/day90", "Day90"),
                ("B", "Day180", "2026-06-30", "https://b.example/day180", "Day180"),
                ("A", "LateFirst", "2026-06-01", "https://a.example/late", "LateBoundary"),
                ("B", "LateSecond", "2026-07-01", "https://b.example/late", "LateBoundary"),
                ("A", "ImmatureFirst", "2026-06-15", "https://a.example/immature", "Immature"),
                ("B", "ImmatureSecond", "2026-06-16", "https://b.example/immature", "Immature"),
                ("B", "FutureSecond", "2026-07-02", "https://b.example/future", "Never"),
                ("C", "FutureOnly", "2027-01-01", "https://c.example/future", "FutureOnly"),
            ),
            ["Day30", "Day90", "Day180", "Tied", "Never", "LateBoundary", "Immature", "FutureOnly"],
        )
        horizons = tables["diffusion_horizons"].set_index("horizon_days")
        for horizon, eligible, diffused in [(30, 6, 3), (90, 5, 3), (180, 5, 4)]:
            self.assertEqual(horizons.loc[horizon, "eligible_benchmarks"], eligible)
            self.assertEqual(horizons.loc[horizon, "diffused_benchmarks"], diffused)
            self.assertAlmostEqual(horizons.loc[horizon, "diffusion_share"], diffused / eligible)
        lifecycle = tables["lifecycle"].set_index("benchmark_name")
        self.assertEqual(lifecycle.loc["Tied", "second_provider_lag_days"], 0)
        self.assertEqual(lifecycle.loc["Never", "provider_count"], 1)
        self.assertEqual(lifecycle.loc["FutureOnly", "launch_count"], 0)
        self.assertEqual(set(tables["launch_events"]["provider"]), {"A", "B"})

    def test_early_cutoff_keeps_unobserved_catalog_and_provider_inventory_without_nan_summary(self):
        tables, summary = self.build(
            models(("FutureProvider", "Future", "2026-01-10", "https://future.example/launch", "Alpha")),
            ["Alpha", "Beta"],
            as_of="2026-01-01",
        )
        self.assertEqual(len(tables["lifecycle"]), 2)
        self.assertEqual(len(tables["launch_events"]), 0)
        self.assertEqual(len(tables["launch_mentions"]), 0)
        self.assertEqual(len(tables["annual_inventory"]), 0)
        self.assertEqual(len(tables["interaction_trends"]), 0)
        self.assertEqual(set(tables["coverage_by_provider"]["provider"]), {"FutureProvider"})
        provider = tables["coverage_by_provider"].iloc[0]
        for field in ["model_rows", "launch_events", "benchmark_bearing_launches", "observed_benchmarks"]:
            self.assertEqual(provider[field], 0)
        self.assertEqual(provider["first_release"], "")
        self.assertEqual(provider["last_release"], "")
        self.assertEqual(tables["diffusion_horizons"]["eligible_benchmarks"].sum(), 0)
        self.assertTrue(tables["diffusion_horizons"]["diffusion_share"].isna().all())
        self.assertIsNone(summary["latest_release_year"])
        json.dumps(summary, allow_nan=False)

    def test_empty_models_need_explicit_cutoff_and_unresolved_scoped_mentions_fail(self):
        tables, summary = self.build(models(), ["Alpha"])
        self.assertTrue(tables["launch_events"].empty)
        self.assertEqual(len(tables["interaction_classification"]), 3)
        json.dumps(summary, allow_nan=False)
        with self.assertRaises(ValueError):
            self.build(models(), ["Alpha"], as_of=None)
        with self.assertRaises(ValueError):
            self.build(
                models(("A", "Bad", "2026-01-01", "https://a.example/bad", "Unresolved")),
                ["Alpha"],
            )

    def test_source_date_overrides_stale_derived_dates_for_both_observation_units(self):
        model_rows = models(("A", "Tool", "2026-01-01", "https://a.example/tool", "Tool"))
        model_rows["release_date"] = pd.to_datetime(["2027-01-01"])
        tables, summary = self.build(model_rows, ["Tool"], [
            ("Tool", "interaction_pattern", "single_turn_tool_use", .9, "accepted"),
        ], as_of="2026-01-31")
        for unit in ["announcement", "model_row"]:
            row = self.trend(tables, unit=unit)
            self.assertEqual(row["benchmark_bearing_units"], 1)
            self.assertEqual(row["positive_share"], 1)
        self.assertEqual(set(tables["canonical_model_mentions"]["release_year"]), {2026})
        self.assertEqual(summary["canonical_model_mentions"], 1)
        self.assertEqual(summary["raw_model_mentions"], 1)

    def test_future_cutoff_cannot_create_followup_beyond_the_source_series(self):
        model_rows = models(
            ("A", "First", "2025-12-01", "https://a.example/first", "Alpha"),
            ("B", "Empty", "2026-01-15", "https://b.example/empty", ""),
        )
        current, current_summary = self.build(model_rows, ["Alpha"], as_of="2026-01-15")
        future, future_summary = self.build(model_rows, ["Alpha"], as_of="2027-01-01")
        self.assertEqual(current_summary["diffusion_followup_end"], "2026-01-15")
        self.assertEqual(future_summary["diffusion_followup_end"], "2026-01-15")
        pd.testing.assert_frame_equal(current["diffusion_horizons"], future["diffusion_horizons"])
        self.assertEqual(current["diffusion_horizons"]["eligible_benchmarks"].tolist(), [1, 0, 0])
        _, past_summary = self.build(model_rows, ["Alpha"], as_of="2025-12-15")
        self.assertEqual(past_summary["diffusion_followup_end"], "2025-12-15")

    def test_readme_keeps_the_observation_year_when_cutoff_moves_forward(self):
        tables, summary = self.build(
            models(("A", "Old", "2026-01-01", "https://a.example/old", "Alpha")),
            ["Alpha"], as_of="2027-01-01",
        )
        values = readme_values(tables, summary)
        self.assertEqual(values["AS_OF"], "2027-01-01")
        self.assertEqual(values["LATEST_YEAR"], "2026")
        self.assertEqual(values["SINGLE_LAUNCH_FIRST_SEEN_LATEST_YEAR"], "1")
        self.assertNotIn("2026 YTD", values["INTERACTION_TABLE"])
        template = (Path(__file__).resolve().parents[1] / "analysis/project_overview/README.template.md").read_text()
        rendered = render_readme(template, values)
        self.assertNotIn("{{", rendered)
        self.assertIn("**1 first enter the sample in 2026**", rendered)

    def test_readme_renders_missing_rates_as_unknown_and_rejects_missing_values(self):
        tables, summary = self.build(models(), ["Alpha"])
        values = readme_values(tables, summary)
        self.assertEqual(values["SHARED_MENTION_SHARE"], "—")
        self.assertEqual(values["CONDITIONAL_MEDIAN_LAG"], "—")
        self.assertIn("undefined", values["SHARING_FINDING"])
        self.assertIn("undefined", values["INTERACTION_FINDING"])
        self.assertNotIn("most reporting", sharing_title(summary))
        with self.assertRaisesRegex(ValueError, "Missing README value"):
            render_readme("{{UNDEFINED_METRIC}}", values)

    def test_early_cutoff_does_not_inherit_later_majority_or_interaction_trend_claims(self):
        model_rows = models(
            ("A", "First", "2023-01-01", "https://a.example/first", "Shared, Own1, Own2, Own3"),
            ("B", "Second", "2023-07-01", "https://b.example/second", "Shared, Other1, Other2, Other3"),
            ("B", "Future", "2026-01-01", "https://b.example/future", "Own1, Own2, Own3"),
        )
        tables, summary = self.build(model_rows, ["Shared", "Own1", "Own2", "Own3", "Other1", "Other2", "Other3"], as_of="2024-01-01")
        self.assertAlmostEqual(summary["shared_mention_share"], .25)
        values = readme_values(tables, summary)
        template = (Path(__file__).resolve().parents[1] / "analysis/project_overview/README.template.md").read_text()
        rendered = render_readme(template, values)
        self.assertNotIn("most reporting", rendered)
        self.assertNotIn("majority", rendered)
        self.assertNotIn("rises", rendered)
        self.assertIn("a trend across years cannot be assessed", rendered)
        self.assertNotIn("most reporting", sharing_title(summary))
        _, later_summary = self.build(model_rows, ["Shared", "Own1", "Own2", "Own3", "Other1", "Other2", "Other3"])
        # The later snapshot crosses a reporting majority, but most identities
        # are now shared: it must not call that set a minority either.
        self.assertGreater(later_summary["shared_mention_share"], .5)
        self.assertNotIn("small shared set", sharing_title(later_summary))

    def test_interaction_narrative_follows_decreasing_and_flat_annual_shares(self):
        model_rows = models(
            ("A", "Tool", "2024-01-01", "https://a.example/tool", "Tool"),
            ("A", "Static", "2025-01-01", "https://a.example/static", "Static"),
        )
        for first_label, expected in [("single_turn_tool_use", "falls"), ("static_prompt_response", "unchanged")]:
            with self.subTest(first_label=first_label):
                tables, summary = self.build(model_rows, ["Tool", "Static"], [
                    ("Tool", "interaction_pattern", first_label, .9, "accepted"),
                    ("Static", "interaction_pattern", "static_prompt_response", .9, "accepted"),
                ])
                finding = readme_values(tables, summary)["INTERACTION_FINDING"]
                self.assertIn(expected, finding)
                self.assertNotIn("rises", finding)


if __name__ == "__main__":
    unittest.main()
