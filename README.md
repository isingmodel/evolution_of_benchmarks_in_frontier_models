# The Evolution of Benchmarks in Frontier Models

**A release-page dataset of the benchmarks used to introduce frontier AI models.**

[![Providers](https://img.shields.io/badge/providers-OpenAI%20%C2%B7%20Google%20%C2%B7%20Anthropic-2f6f8f)](#dataset)
[![Snapshot](https://img.shields.io/badge/snapshot-2026--07--24-555)](#dataset)
[![License](https://img.shields.io/badge/license-Apache--2.0-3b7d44)](LICENSE)

This project tracks benchmark and evaluation names published on the launch pages
for frontier models from OpenAI, Google, and Anthropic. It follows how those
benchmark portfolios have changed over time: from academic tests and static
question sets toward coding environments, tool use, computer interaction, and
other work-like tasks.

**45 tracked releases · 41 benchmark-bearing rows · 557 raw mentions · 197 catalog entries**

## Dataset

The unit of evidence is a benchmark mention on a public model-release page. A
benchmark is associated with a model when it appears on that page. Technical
reports, system cards, and benchmark papers are used to verify catalog metadata
such as authorship, aliases, and task design.

| Provider | Releases | First release | Latest release |
| --- | ---: | --- | --- |
| OpenAI | 16 | 2022-11-30 | GPT-5.6 — 2026-07-09 |
| Google | 11 | 2023-12-06 | Gemini variants — 2026-07-21 |
| Anthropic | 18 | 2023-03-14 | Claude 5 Opus — 2026-07-24 |

Every model-release row carries the same total weight. If a launch page lists
ten resolved benchmarks, each receives one tenth of that release's weight. This
keeps releases with long benchmark tables from dominating the time series.

The main files are:

| File | Contents |
| --- | --- |
| [`data/models.csv`](data/models.csv) | Model releases, dates, source URLs, and raw benchmark mentions |
| [`data/benchmarks.csv`](data/benchmarks.csv) | Canonical benchmark catalog and provenance |
| [`data/benchmark_aliases.csv`](data/benchmark_aliases.csv) | Exact alias-to-benchmark mappings |
| [`data/benchmark_facets.csv`](data/benchmark_facets.csv) | Multi-label taxonomy assignments and review status |
| [`data/benchmark_distinctness.csv`](data/benchmark_distinctness.csv) | Benchmark-family and distinctness decisions |

## Main findings

### Release pages are moving from exams toward work simulations

Static question answering still appears frequently, but the mix changed sharply
after 2024. The active taxonomy assigns 73.2% of the weighted 2026 YTD portfolio
to work-simulation characteristics, up from 12.0% in 2023.

![Weighted shift from static evaluation to work simulation](assets/static_to_work_simulation_trend.png)

| Release year | Static evaluation | Work simulation | Specialized context | Releases |
| ---: | ---: | ---: | ---: | ---: |
| 2023 | 82.4% | 12.0% | 53.7% | 3 |
| 2024 | 70.7% | 18.0% | 28.0% | 8 |
| 2025 | 54.4% | 39.1% | 48.7% | 14 |
| 2026 YTD | 17.4% | 73.2% | 44.8% | 16 |

The 2026 estimate is sensitive to taxonomy review coverage. It is 73.2% across
all active labels, 37.7% under a fixed-denominator lower bound, and 60.1% among
mentions with complete high-confidence coverage.

| Release year | All active labels | Fixed-denominator lower bound | Fully covered mentions | High-confidence coverage |
| ---: | ---: | ---: | ---: | ---: |
| 2023 | 12.0% | 12.0% | 12.0% | 100.0% |
| 2024 | 18.0% | 18.0% | 18.1% | 99.1% |
| 2025 | 39.1% | 38.6% | 37.9% | 97.9% |
| 2026 YTD | 73.2% | 37.7% | 60.1% | 56.6% |

SWE-bench Verified, OSWorld-Verified, SWE-bench Pro, HumanEval, and the TAU
family account for much of the work-simulation signal. Full sensitivity tables
are available in
[`analysis/readme_story/static_work_sensitivity.csv`](analysis/readme_story/static_work_sensitivity.csv).

### New public benchmarks spread quickly between labs

Several recent benchmarks appeared on another provider's release page within
days of their first observed use in this dataset.

| Benchmark | First provider | Next provider | Lag |
| --- | --- | --- | ---: |
| MMMLU | Anthropic | OpenAI | 2 days |
| Terminal-Bench 2.0 | Google | Anthropic | 6 days |
| OfficeQA Pro | Anthropic | OpenAI | 7 days |
| Finance Agent v2 | Google | Anthropic | 9 days |
| GDPval-AA v2 | Anthropic | OpenAI | 9 days |
| Terminal-Bench 2.1 | Google | Anthropic | 9 days |

These dates measure adoption on the release pages covered here.

### Gemini made long context part of the launch narrative

Long-context evaluations formed 39.3% of Google's weighted benchmark portfolio
in 2024. The comparable shares were 2.4% for OpenAI and 5.8% for Anthropic.
Needle In A Haystack was Google's main driver in this period.

![Gemini long-context benchmark case](assets/gemini_long_context_case.png)

| Provider | Broad share | Primary-only share | Main 2024 driver | Releases |
| --- | ---: | ---: | --- | ---: |
| OpenAI | 2.4% | 2.4% | EgoSchema | 3 |
| Google | 39.3% | 35.7% | Needle In A Haystack | 2 |
| Anthropic | 5.8% | 2.1% | SWE-bench Verified | 3 |

### OpenAI-linked benchmarks have become shared reference points

On Google's release pages, the release-normalized share of OpenAI-authored or
OpenAI-affiliated benchmarks rose from 6.1% to 22.1%. The combined
Anthropic–Google share rose from 16.9% to 21.2%, while Anthropic stayed close to
its earlier level.

| Portfolio | 2023–24 raw | 2023–24 normalized | 2025–26 raw | 2025–26 normalized |
| --- | ---: | ---: | ---: | ---: |
| Anthropic + Google | 14.5% | 16.9% | 20.8% | 21.2% |
| Anthropic | 19.0% | 25.0% | 18.8% | 20.6% |
| Google | 8.8% | 6.1% | 24.7% | 22.1% |

## Other charts

The repository includes several complementary views of the same release-page
history.

### Category mix by release

The release-level view shows how the benchmark portfolio changes from one model
launch to the next.

![Benchmark category mix by model release](assets/benchmark_evolution.png)

### Rolling category trend

A rolling window makes the longer-term shift in headline benchmark categories
easier to see.

![Rolling trend in benchmark categories](assets/benchmark_growth.png)

### Benchmark count per release

The number of benchmark mentions on each launch page varies substantially across
providers and releases.

![Benchmark count per model release](assets/benchmark_count_per_release.png)

### Category trends on separate axes

Separating the category series avoids compressing smaller but still meaningful
trends.

![Benchmark category trends shown on separate axes](assets/benchmark_growth_by_all_category.png)

### Multi-facet taxonomy trend

The facet view follows labels across interaction pattern, task mechanism,
construct claim, and context rather than reducing each benchmark to one class.

![Trends across the multi-facet benchmark taxonomy](assets/benchmark_facet_trends.png)

### Review debt by facet

Taxonomy coverage is uneven, so this view makes the remaining review workload
visible alongside the substantive trends.

![Taxonomy review debt by benchmark facet](assets/benchmark_review_debt.png)

### Benchmarks with the highest review leverage

These benchmarks affect the most release-page evidence and therefore offer the
largest payoff from manual taxonomy review.

![Benchmarks with the highest taxonomy review leverage](assets/review_leverage_benchmarks.png)

## Method

| Stage | Rule |
| --- | --- |
| Extraction | Record benchmark names and variants shown on each public launch page |
| Resolution | Match exact canonical names or reviewed aliases |
| Weighting | Give every release one unit of total weight, split across its resolved benchmarks |
| Classification | Assign multiple facets across interaction pattern, task mechanism, construct claim, and context |
| Review | Store confidence, provenance, and review status with each facet assignment |

The charts use a concise headline projection built from the multi-label taxonomy.
The facet table currently contains 3,330 rows: 29 accepted, 3,268 awaiting
review, and 33 legacy rows. Of these, 1,462 have confidence below 0.70. Review
priority is driven by both uncertainty and the number of release-page mentions
affected by a benchmark.

Detailed documentation:

- [`docs/release_page_extraction_workflow.md`](docs/release_page_extraction_workflow.md)
- [`docs/benchmark_classification_methodology_v3.md`](docs/benchmark_classification_methodology_v3.md)
- [`docs/benchmark_classification_prompt.md`](docs/benchmark_classification_prompt.md)
- [`docs/facet_review_guidelines.md`](docs/facet_review_guidelines.md)
- [`docs/frontier_lab_author_affiliation_review.md`](docs/frontier_lab_author_affiliation_review.md)

## Reproduce the analysis

Install the project and run the full pipeline:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
bash scripts/run_pipeline.sh
```

The pipeline consumes the committed facet table. Reclassification follows the
public prompt contract in
[`docs/benchmark_classification_prompt.md`](docs/benchmark_classification_prompt.md);
the current authoring script also uses a maintainer-local OpenAI OAuth client.

## Add a release

1. Add the release metadata and raw benchmark names to
   [`data/models.csv`](data/models.csv).
2. Add new canonical benchmarks to
   [`data/benchmarks.csv`](data/benchmarks.csv).
3. Add spelling and display variants to
   [`data/benchmark_aliases.csv`](data/benchmark_aliases.csv).
4. Add taxonomy rows to
   [`data/benchmark_facets.csv`](data/benchmark_facets.csv).
5. Run `bash scripts/run_pipeline.sh` and review the generated diffs.

The extraction checklist and evidence requirements are documented in
[`docs/release_page_extraction_workflow.md`](docs/release_page_extraction_workflow.md).

## Limitations

- Launch-page detail varies by provider and release, so the dataset also reflects
  publication choices.
- Comparisons use benchmark presence and release-level weighting. Score scales
  and evaluation protocols vary across sources.
- Taxonomy coverage is still under review, with the largest confidence gap in
  2026 releases.
- Release-page edits can change the public record after the original launch date.

## License

Released under the [Apache License 2.0](LICENSE).
