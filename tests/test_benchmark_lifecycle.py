from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

import pandas as pd

from analysis.benchmark_lifecycle.analyze import plot_timeline
from analysis.benchmark_lifecycle.lifecycle import build_lifecycle_tables
from scripts.taxonomy_utils import (
    AliasEntry,
    CanonicalBenchmark,
    CanonicalResolver,
    benchmark_id,
)


def catalog(*names: str, aliases: dict[str, str] | None = None):
    """Use a tiny independent catalog rather than the repository's changing data."""
    records = [
        {
            "benchmark_id": benchmark_id(name),
            "benchmark_name": name,
            "reference_link": "https://benchmarks.example/reference",
            "source_author": "Academia",
            "frontier_lab_author_affiliations": "none",
            "legacy_task_mode": "Agentic",
            "legacy_task_domain": "General/Commonsense",
            "legacy_rationale": "Synthetic lifecycle fixture.",
            "review_status": "needs_review",
        }
        for name in names
    ]
    resolver = CanonicalResolver(
        [
            CanonicalBenchmark(benchmark_id(name), name, "fixture.csv", i)
            for i, name in enumerate(names, start=2)
        ],
        [
            AliasEntry(surface, benchmark_id(target), "exact", "Fixture alias.", "aliases.csv", i)
            for i, (surface, target) in enumerate((aliases or {}).items(), start=2)
        ],
    )
    return pd.DataFrame(records), resolver


def models(*rows: tuple[str, str, str, str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["Provider", "Model name", "release date", "link", "benchmarks"],
    )


class BenchmarkLifecycleTests(unittest.TestCase):
    def build(self, model_rows, *names, aliases=None, as_of="2026-01-31", recent_window_days=180):
        benchmarks, resolver = catalog(*names, aliases=aliases)
        return build_lifecycle_tables(
            model_rows,
            benchmarks,
            resolver,
            as_of=as_of,
            recent_window_days=recent_window_days,
        )

    def lifecycle(self, table, name):
        matches = table.loc[table["benchmark_name"] == name]
        self.assertEqual(len(matches), 1)
        return matches.iloc[0]

    def provider_lifecycle(self, table, name, provider):
        matches = table.loc[(table["benchmark_name"] == name) & (table["provider"] == provider)]
        self.assertEqual(len(matches), 1)
        return matches.iloc[0]

    def assert_fields(self, row, expected):
        for column, value in expected.items():
            with self.subTest(column=column):
                self.assertEqual(row[column], value)

    def test_aliases_and_repeated_names_count_once_per_model_and_launch(self):
        _, _, launches, mentions, _ = self.build(
            models(("A", "Model", "2026-01-01", "https://a.example/launch", "Alpha, Alias Alpha, Alpha, Beta")),
            "Alpha", "Beta", aliases={"Alias Alpha": "Alpha"},
        )

        self.assertEqual(len(launches), 1)
        self.assertEqual(launches.iloc[0]["benchmark_count"], 2)
        self.assertEqual(len(mentions), 2)
        self.assertEqual(mentions.set_index("benchmark_name")["model_row_count"].to_dict(), {"Alpha": 1, "Beta": 1})

    def test_two_models_on_one_page_have_one_launch_and_two_model_rows(self):
        lifecycles, providers, launches, mentions, _ = self.build(
            models(
                ("A", "Sol", "2026-01-01", "https://a.example/joint", "Alpha, Beta"),
                ("A", "Luna", "2026-01-01", "https://a.example/joint", "Alias Alpha"),
            ),
            "Alpha", "Beta", aliases={"Alias Alpha": "Alpha"},
        )

        self.assertEqual(len(launches), 1)
        launch = launches.iloc[0]
        self.assertEqual(launch["model_row_count"], 2)
        self.assertEqual(launch["model_names"], "Luna; Sol")
        self.assertEqual(launch["benchmark_count"], 2)
        indexed = mentions.set_index("benchmark_name")
        self.assertEqual(indexed.loc["Alpha", "model_row_count"], 2)
        self.assertEqual(indexed.loc["Alpha", "model_names"], "Luna; Sol")
        self.assertEqual(indexed.loc["Beta", "model_row_count"], 1)
        self.assertEqual(indexed.loc["Beta", "model_names"], "Sol")
        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {"launch_count": 1, "model_row_count": 2})
        self.assert_fields(self.provider_lifecycle(providers, "Alpha", "A"), {"launch_count": 1, "model_row_count": 2})

    def test_url_tracking_fragments_and_trailing_slash_do_not_split_a_page(self):
        _, _, launches, mentions, _ = self.build(
            models(
                ("A", "M1", "2026-01-01", "https://a.example/launch/?utm_source=one#table", "Alpha"),
                ("A", "M2", "2026-01-01", "https://a.example/launch?UTM_campaign=two#footnote", "Alpha"),
                ("A", "M3", "2026-01-01", "https://a.example/launch?edition=old", "Alpha"),
                ("A", "M4", "2026-01-01", "https://a.example/launch?edition=new", "Alpha"),
            ),
            "Alpha",
        )

        self.assertEqual(len(launches), 3)
        self.assertEqual(len(mentions), 3)
        by_url = launches.set_index("source_url")["model_row_count"].to_dict()
        self.assertEqual(by_url, {
            "https://a.example/launch": 2,
            "https://a.example/launch?edition=old": 1,
            "https://a.example/launch?edition=new": 1,
        })

    def test_provider_and_date_are_part_of_the_launch_identity(self):
        _, _, launches, mentions, _ = self.build(
            models(
                ("A", "M1", "2026-01-01", "https://shared.example/launch", "Alpha"),
                ("B", "M2", "2026-01-01", "https://shared.example/launch", "Alpha"),
                ("A", "M3", "2026-01-02", "https://shared.example/launch", "Alpha"),
            ),
            "Alpha",
        )

        self.assertEqual(len(launches), 3)
        self.assertEqual(launches["launch_id"].nunique(), 3)
        self.assertEqual(len(mentions), 3)

    def test_same_day_three_provider_adoption_keeps_all_first_providers(self):
        lifecycles, _, _, _, _ = self.build(
            models(
                ("C", "C1", "2026-01-10", "https://c.example/launch", "Alpha"),
                ("A", "A1", "2026-01-10", "https://a.example/launch", "Alpha"),
                ("B", "B1", "2026-01-10", "https://b.example/launch", "Alpha"),
            ),
            "Alpha",
        )

        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {
            "provider_count": 3,
            "launch_count": 3,
            "first_seen": "2026-01-10",
            "first_providers": "A; B; C",
            "second_provider_date": "2026-01-10",
            "third_provider_date": "2026-01-10",
            "second_provider_lag_days": 0,
            "third_provider_lag_days": 0,
        })

    def test_provider_diffusion_uses_dates_not_numbers_of_release_rows(self):
        lifecycles, _, _, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/one", "Alpha"),
                ("A", "A2", "2026-01-02", "https://a.example/two", "Alpha"),
                ("B", "B1", "2026-01-06", "https://b.example/one", "Alpha"),
                ("C", "C1", "2026-01-10", "https://c.example/one", "Alpha"),
            ),
            "Alpha",
        )

        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {
            "launch_count": 4,
            "provider_count": 3,
            "first_providers": "A",
            "second_provider_date": "2026-01-06",
            "second_provider_lag_days": 5,
            "third_provider_date": "2026-01-10",
            "third_provider_lag_days": 9,
        })

    def test_single_observation_has_zero_span_and_undefined_followup_share(self):
        lifecycles, providers, _, _, _ = self.build(
            models(("A", "A1", "2026-01-10", "https://a.example/one", "Alpha")),
            "Alpha",
        )

        row = self.lifecycle(lifecycles, "Alpha")
        self.assert_fields(row, {
            "first_seen": "2026-01-10",
            "last_seen": "2026-01-10",
            "observed_span_days": 0,
            "days_since_last_seen": 21,
            "adopter_followup_launches": 0,
            "adopter_followup_mention_launches": 0,
            "adopter_launches_after_last_seen": 0,
            "largest_within_provider_gap_launches": 0,
        })
        for field in ["followup_mention_share", "second_provider_lag_days", "third_provider_lag_days"]:
            self.assertTrue(pd.isna(row[field]), field)
        self.assertEqual(row["second_provider_date"], "")
        self.assertEqual(row["third_provider_date"], "")
        provider = self.provider_lifecycle(providers, "Alpha", "A")
        self.assert_fields(provider, {"followup_launches": 0, "followup_mention_launches": 0, "launches_after_last_seen": 0})
        self.assertTrue(pd.isna(provider["followup_mention_share"]))

    def test_unequal_provider_cadence_exposes_ten_versus_one_opportunities(self):
        # Both labs first mention Alpha on Jan 1. A has ten later launches;
        # B has one. Every later page is empty but remains an opportunity.
        rows = [
            ("A", "A0", "2026-01-01", "https://a.example/zero", "Alpha"),
            ("B", "B0", "2026-01-01", "https://b.example/zero", "Alpha"),
        ]
        rows.extend(
            ("A", f"A{day}", f"2026-01-{day:02}", f"https://a.example/{day}", "")
            for day in range(2, 12)
        )
        rows.append(("B", "B1", "2026-01-11", "https://b.example/one", ""))
        lifecycles, providers, launches, mentions, _ = self.build(models(*rows), "Alpha", as_of="2026-01-11")

        self.assertEqual(len(launches), 13)
        self.assertEqual(len(mentions), 2)
        self.assertEqual(int(launches["has_benchmark_mentions"].sum()), 2)
        self.assertEqual(int((launches["benchmark_count"] == 0).sum()), 11)
        for provider, opportunities in [("A", 10), ("B", 1)]:
            row = self.provider_lifecycle(providers, "Alpha", provider)
            self.assert_fields(row, {
                "followup_launches": opportunities,
                "followup_mention_launches": 0,
                "launches_after_last_seen": opportunities,
                "followup_mention_share": 0.0,
            })
        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {
            "adopter_followup_launches": 11,
            "adopter_followup_mention_launches": 0,
            "adopter_launches_after_last_seen": 11,
            "followup_mention_share": 0.0,
        })

    def test_followup_share_excludes_initial_adoption_and_includes_empty_pages(self):
        lifecycles, providers, _, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/one", "Alpha"),
                ("A", "A2", "2026-01-02", "https://a.example/two", ""),
                ("A", "A3", "2026-01-03", "https://a.example/three", "Alpha"),
                ("A", "A4", "2026-01-04", "https://a.example/four", ""),
            ),
            "Alpha", as_of="2026-01-04",
        )

        row = self.provider_lifecycle(providers, "Alpha", "A")
        self.assert_fields(row, {"followup_launches": 3, "followup_mention_launches": 1, "launches_after_last_seen": 1})
        self.assertAlmostEqual(row["followup_mention_share"], 1 / 3)
        global_row = self.lifecycle(lifecycles, "Alpha")
        self.assert_fields(global_row, {"adopter_followup_launches": 3, "adopter_followup_mention_launches": 1})
        self.assertAlmostEqual(global_row["followup_mention_share"], 1 / 3)

    def test_intermention_gap_and_postlast_opportunities_use_provider_history(self):
        # A's bounded gaps have 2 then 3 empty launches. A's Jan 21 page is
        # after its own last mention, but before B's global last mention.
        # C never adopts Alpha, so its Jan 27 page is not an adopter opportunity.
        lifecycles, providers, _, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/1", "Alpha"),
                ("A", "A2", "2026-01-02", "https://a.example/2", ""),
                ("A", "A3", "2026-01-03", "https://a.example/3", ""),
                ("A", "A10", "2026-01-10", "https://a.example/10", "Alpha"),
                ("A", "A11", "2026-01-11", "https://a.example/11", ""),
                ("A", "A12", "2026-01-12", "https://a.example/12", ""),
                ("A", "A13", "2026-01-13", "https://a.example/13", ""),
                ("A", "A20", "2026-01-20", "https://a.example/20", "Alpha"),
                ("A", "A21", "2026-01-21", "https://a.example/21", ""),
                ("B", "B25", "2026-01-25", "https://b.example/25", "Alpha"),
                ("A", "A26", "2026-01-26", "https://a.example/26", ""),
                ("C", "C27", "2026-01-27", "https://c.example/27", ""),
                ("B", "B28", "2026-01-28", "https://b.example/28", ""),
            ),
            "Alpha",
        )

        self.assert_fields(self.provider_lifecycle(providers, "Alpha", "A"), {
            "observed_span_days": 19,
            "largest_gap_launches": 3,
            "launches_after_last_seen": 2,
            "days_since_last_seen": 11,
            "followup_launches": 9,
            "followup_mention_launches": 2,
        })
        self.assert_fields(self.provider_lifecycle(providers, "Alpha", "B"), {
            "observed_span_days": 0,
            "largest_gap_launches": 0,
            "launches_after_last_seen": 1,
            "days_since_last_seen": 6,
        })
        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {
            "first_seen": "2026-01-01",
            "last_seen": "2026-01-25",
            "observed_span_days": 24,
            "largest_within_provider_gap_launches": 3,
            "adopter_launches_after_last_seen": 2,
            "days_since_last_seen": 6,
            "adopter_followup_launches": 10,
            "adopter_followup_mention_launches": 2,
        })

    def test_recent_window_is_inclusive_and_deduplicates_launches(self):
        lifecycles, _, _, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/one", "Alpha"),
                ("A", "A2", "2026-01-02", "https://a.example/two", "Alpha"),
                ("A", "A4", "2026-01-04", "https://a.example/four", "Alpha"),
                ("A", "A4 Variant", "2026-01-04", "https://a.example/four#table", "Alpha"),
            ),
            "Alpha", as_of="2026-01-04", recent_window_days=3,
        )

        # Three days ending Jan 4 means Jan 2 through Jan 4, inclusive.
        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {"launch_count": 3, "model_row_count": 4, "recent_launch_count": 2})

    def assert_unobserved(self, row):
        self.assert_fields(row, {"launch_count": 0, "model_row_count": 0, "provider_count": 0, "recent_launch_count": 0})
        for field in ["first_seen", "last_seen", "first_providers", "second_provider_date", "third_provider_date"]:
            self.assertEqual(row[field], "", field)
        for field in [
            "observed_span_days", "days_since_last_seen", "second_provider_lag_days",
            "third_provider_lag_days", "adopter_followup_launches", "adopter_followup_mention_launches",
            "followup_mention_share", "adopter_launches_after_last_seen", "largest_within_provider_gap_launches",
        ]:
            self.assertTrue(pd.isna(row[field]), field)

    def test_future_and_never_observed_catalog_entries_remain_with_unknown_spans(self):
        lifecycles, _, launches, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/one", "Alpha"),
                ("B", "B1", "2026-02-01", "https://b.example/one", "Beta"),
            ),
            "Alpha", "Beta", "Gamma", as_of="2026-01-15",
        )

        self.assertEqual(set(lifecycles["benchmark_name"]), {"Alpha", "Beta", "Gamma"})
        self.assertEqual(len(launches), 1)
        self.assert_unobserved(self.lifecycle(lifecycles, "Beta"))
        self.assert_unobserved(self.lifecycle(lifecycles, "Gamma"))

    def test_cutoff_before_first_release_returns_full_catalog_and_empty_inventories(self):
        lifecycles, providers, launches, mentions, cutoff = self.build(
            models(("A", "A1", "2026-01-10", "https://a.example/one", "Unknown")),
            "Alpha", "Beta", as_of="2026-01-01",
        )

        self.assertEqual(cutoff, pd.Timestamp("2026-01-01"))
        self.assertEqual(len(lifecycles), 2)
        # The provider table keeps the unscoped catalog/provider matrix, but
        # excluded future releases cannot become observations or opportunities.
        self.assertEqual(set(zip(providers["benchmark_name"], providers["provider"])), {("Alpha", "A"), ("Beta", "A")})
        for _, row in providers.iterrows():
            self.assert_fields(row, {"launch_count": 0, "model_row_count": 0, "first_seen": "", "last_seen": ""})
            for field in [
                "observed_span_days", "days_since_last_seen", "followup_launches",
                "followup_mention_launches", "followup_mention_share", "launches_after_last_seen",
                "largest_gap_launches",
            ]:
                self.assertTrue(pd.isna(row[field]), field)
        self.assertTrue(launches.empty)
        self.assertTrue(mentions.empty)
        self.assertIn("launch_id", launches.columns)
        self.assertIn("benchmark_id", mentions.columns)
        for _, row in lifecycles.iterrows():
            self.assert_unobserved(row)

    def test_default_cutoff_includes_the_latest_empty_release_page(self):
        lifecycles, providers, launches, _, cutoff = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/one", "Alpha"),
                ("A", "A10", "2026-01-10", "https://a.example/ten", ""),
            ),
            "Alpha", as_of=None,
        )

        self.assertEqual(cutoff, pd.Timestamp("2026-01-10"))
        self.assertEqual(len(launches), 2)
        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {
            "last_seen": "2026-01-01", "days_since_last_seen": 9,
            "adopter_followup_launches": 1, "adopter_launches_after_last_seen": 1,
        })
        self.assert_fields(self.provider_lifecycle(providers, "Alpha", "A"), {"followup_launches": 1})

    def test_same_day_pages_are_not_ordered_as_followup_or_bounded_gaps(self):
        lifecycles, providers, launches, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/first", "Alpha"),
                ("A", "A1 Empty", "2026-01-01", "https://a.example/second", ""),
                ("A", "A3", "2026-01-03", "https://a.example/third", "Alpha"),
                ("A", "A3 Empty", "2026-01-03", "https://a.example/fourth", ""),
            ),
            "Alpha", as_of="2026-01-03",
        )

        self.assertEqual(len(launches), 4)
        self.assert_fields(self.provider_lifecycle(providers, "Alpha", "A"), {
            "launch_count": 2, "followup_launches": 2, "followup_mention_launches": 1,
            "followup_mention_share": 0.5, "largest_gap_launches": 0, "launches_after_last_seen": 0,
        })
        self.assert_fields(self.lifecycle(lifecycles, "Alpha"), {
            "adopter_followup_launches": 2, "largest_within_provider_gap_launches": 0,
        })

    def test_empty_dataset_needs_a_cutoff_and_then_retains_catalog(self):
        with self.assertRaises(ValueError):
            self.build(models(), "Alpha", as_of=None)

        lifecycles, providers, launches, mentions, cutoff = self.build(models(), "Alpha", as_of="2026-01-31")
        self.assertEqual(cutoff, pd.Timestamp("2026-01-31"))
        self.assert_unobserved(self.lifecycle(lifecycles, "Alpha"))
        self.assertTrue(providers.empty)
        self.assertTrue(launches.empty)
        self.assertTrue(mentions.empty)

    def test_recent_window_must_have_a_positive_number_of_days(self):
        for window in [0, -1]:
            with self.subTest(window=window), self.assertRaises(ValueError):
                self.build(
                    models(("A", "A1", "2026-01-01", "https://a.example/one", "Alpha")),
                    "Alpha", recent_window_days=window,
                )

    def test_explicit_versions_are_separate_without_inferred_replacement(self):
        lifecycles, _, _, _, _ = self.build(
            models(
                ("A", "A1", "2026-01-01", "https://a.example/one", "Suite v1"),
                ("A", "A3", "2026-01-03", "https://a.example/three", "Suite v1"),
                ("A", "A20", "2026-01-20", "https://a.example/twenty", "Suite v2"),
            ),
            "Suite v1", "Suite v2",
        )

        self.assertEqual(len(lifecycles), 2)
        self.assert_fields(self.lifecycle(lifecycles, "Suite v1"), {
            "launch_count": 2, "first_seen": "2026-01-01", "last_seen": "2026-01-03", "observed_span_days": 2,
        })
        self.assert_fields(self.lifecycle(lifecycles, "Suite v2"), {
            "launch_count": 1, "first_seen": "2026-01-20", "last_seen": "2026-01-20", "observed_span_days": 0,
        })
        for _, row in lifecycles.iterrows():
            self.assertNotIn(str(row["reporting_pattern"]).casefold(), {"retired", "replaced", "superseded"})

    def test_resolution_is_strict_for_included_unknown_mentions(self):
        with self.assertRaisesRegex(ValueError, "Unresolved.*Unknown"):
            self.build(
                models(("A", "M1", "2026-01-01", "https://a.example/launch", "Alpha, Unknown")),
                "Alpha",
            )

    def test_an_excluded_future_unknown_does_not_fail_resolution(self):
        _, _, launches, mentions, cutoff = self.build(
            models(
                ("A", "M1", "2026-01-01", "https://a.example/old", "Alpha"),
                ("A", "M2", "2026-02-01", "https://a.example/future", "Unknown"),
            ),
            "Alpha", as_of="2026-01-01",
        )

        self.assertEqual(cutoff, pd.Timestamp("2026-01-01"))
        self.assertEqual(len(launches), 1)
        self.assertEqual(len(mentions), 1)

    def test_meaningful_unicode_source_urls_remain_distinct(self):
        _, _, launches, _, _ = self.build(
            models(
                ("A", "Width", "2026-01-01", "https://a.example/Ａ", "Alpha"),
                ("A", "ASCII", "2026-01-01", "https://a.example/A", "Alpha"),
                ("A", "Circled", "2026-01-01", "https://a.example/page?edition=①", "Alpha"),
                ("A", "Digit", "2026-01-01", "https://a.example/page?edition=1", "Alpha"),
                ("A", "Encoded", "2026-01-01", "https://a.example/page?edition=%E2%91%A0", "Alpha"),
            ),
            "Alpha",
        )

        self.assertEqual(len(launches), 4)
        counts = launches.set_index("source_url")["model_row_count"].to_dict()
        self.assertEqual(counts["https://a.example/Ａ"], 1)
        self.assertEqual(counts["https://a.example/A"], 1)
        self.assertEqual(counts["https://a.example/page?edition=1"], 1)
        self.assertEqual(counts["https://a.example/page?edition=%E2%91%A0"], 2)

    def test_canonical_display_labels_preserve_catalog_unicode(self):
        name = "τ³-Banking Leaderboard"
        lifecycles, providers, _, mentions, _ = self.build(
            models(("A", "A1", "2026-01-01", "https://a.example/one", name)),
            name,
        )

        for table in [lifecycles, providers, mentions]:
            self.assertEqual(table["benchmark_name"].tolist(), [name])

    def test_undated_inventory_rows_cannot_disappear_during_scoping(self):
        for missing_date in ["", None, pd.NaT]:
            with self.subTest(date=missing_date), self.assertRaisesRegex(ValueError, "valid release date"):
                self.build(
                    models(
                        ("A", "Known", "2026-01-01", "https://a.example/known", "Alpha"),
                        ("A", "Undated", missing_date, "https://a.example/undated", "Unknown"),
                    ),
                    "Alpha",
                )

    def test_scoped_launches_require_a_provider_and_absolute_source_url(self):
        for provider in ["", None]:
            with self.subTest(provider=provider), self.assertRaisesRegex(ValueError, "nonempty Provider"):
                self.build(
                    models((provider, "A1", "2026-01-01", "https://a.example/one", "Alpha")),
                    "Alpha",
                )
        for url in ["", None, "#chart", "/relative", "ftp://a.example/page"]:
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, r"HTTP\(S\) source URL"):
                self.build(models(("A", "A1", "2026-01-01", url, "Alpha")), "Alpha")

    def test_excluded_future_identifiers_do_not_create_an_empty_provider(self):
        _, providers, launches, mentions, _ = self.build(
            models(
                ("A", "Known", "2026-01-01", "https://a.example/known", "Alpha"),
                ("", "Future", "2026-02-01", "", "Unknown"),
            ),
            "Alpha", as_of="2026-01-01",
        )

        self.assertEqual(providers["provider"].tolist(), ["A"])
        self.assertEqual(len(launches), 1)
        self.assertEqual(len(mentions), 1)

    def test_chart_counts_same_provider_date_pages_without_shifting_dates(self):
        lifecycles, _, _, mentions, cutoff = self.build(
            models(
                ("OpenAI", "O1", "2026-01-01", "https://o.example/one", "GSM8K"),
                ("OpenAI", "O2", "2026-01-01", "https://o.example/two", "GSM8K"),
                ("Google", "G1", "2026-01-01", "https://g.example/one", "GSM8K"),
            ),
            "GSM8K",
        )

        with patch("analysis.benchmark_lifecycle.analyze.save_figure") as save:
            selected = plot_timeline(lifecycles, mentions, cutoff, Path("unused.png"))
        self.assertEqual(selected, [benchmark_id("GSM8K")])
        figure = save.call_args.args[0]
        axes = figure.axes[0]
        counts = [text for text in axes.texts if text.get_text().startswith("×")]
        self.assertEqual([text.get_text() for text in counts], ["×2"])
        self.assertEqual(counts[0].xy[0], pd.Timestamp("2026-01-01"))
        self.assertEqual(sum(len(collection.get_offsets()) for collection in axes.collections), 2)
        self.assertIn("×N = distinct pages", " ".join(text.get_text() for text in figure.texts))

    def test_cli_before_the_first_release_exports_complete_unobserved_catalog(self):
        root = Path(__file__).resolve().parents[1]
        source_catalog = pd.read_csv(root / "data/benchmarks.csv", keep_default_na=False)
        source_models = pd.read_csv(root / "data/models.csv", keep_default_na=False)
        catalog_ids = set(source_catalog["benchmark_id"])
        inventory_providers = set(source_models["Provider"])
        self.assertGreater(pd.to_datetime(source_models["release date"]).min(), pd.Timestamp("2020-01-01"))

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            assets = output / "assets"
            result = subprocess.run(
                [
                    sys.executable, "analysis/benchmark_lifecycle/analyze.py",
                    "--as-of", "2020-01-01", "--output-dir", str(output),
                    "--asset-dir", str(assets),
                ],
                cwd=root, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in [
                "benchmark_lifecycles.csv", "provider_lifecycles.csv",
                "launch_events.csv", "launch_mentions.csv", "summary.json", "report.md",
            ]:
                with self.subTest(filename=filename):
                    self.assertGreater((output / filename).stat().st_size, 0)
            image = assets / "benchmark_lifecycle.png"
            self.assertGreater(image.stat().st_size, 100)
            self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

            lifecycles = pd.read_csv(output / "benchmark_lifecycles.csv", keep_default_na=False)
            providers = pd.read_csv(output / "provider_lifecycles.csv", keep_default_na=False)
            self.assertEqual(set(lifecycles["benchmark_id"]), catalog_ids)
            self.assertEqual(len(lifecycles), len(catalog_ids))
            self.assertEqual(set(lifecycles["reporting_pattern"]), {"unobserved"})
            for column in ["launch_count", "model_row_count", "provider_count", "recent_launch_count"]:
                self.assertTrue(lifecycles[column].eq(0).all(), column)
            for column in ["first_seen", "last_seen", "observed_span_days", "days_since_last_seen"]:
                self.assertTrue(lifecycles[column].eq("").all(), column)
            self.assertEqual(
                set(zip(providers["benchmark_id"], providers["provider"])),
                {(identity, provider) for identity in catalog_ids for provider in inventory_providers},
            )
            self.assertEqual(len(providers), len(catalog_ids) * len(inventory_providers))
            self.assertTrue(providers["launch_count"].eq(0).all())
            self.assertTrue(providers["observed_span_days"].eq("").all())
            self.assertTrue(pd.read_csv(output / "launch_events.csv").empty)
            self.assertTrue(pd.read_csv(output / "launch_mentions.csv").empty)

            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["as_of"], "2020-01-01")
            self.assertEqual(summary["catalog_benchmarks"], len(catalog_ids))
            self.assertEqual(summary["unobserved_benchmarks"], len(catalog_ids))
            self.assertEqual(summary["selected_timeline_ids"], [])
            for metric in [
                "model_rows", "launch_events", "benchmark_bearing_launch_events", "observed_benchmarks",
                "single_launch_benchmarks", "multiple_launch_benchmarks", "shared_benchmarks",
                "model_row_mentions", "launch_mentions",
            ]:
                self.assertEqual(summary[metric], 0, metric)
            report = (output / "report.md").read_text(encoding="utf-8")
            self.assertIn("2020-01-01", report)
            self.assertIn("not retirement", report)
            methodology_link = report.split("[methodology](", 1)[1].split(")", 1)[0]
            self.assertEqual(
                (output / unquote(methodology_link)).resolve(),
                root / "analysis/benchmark_lifecycle/README.md",
            )


if __name__ == "__main__":
    unittest.main()
