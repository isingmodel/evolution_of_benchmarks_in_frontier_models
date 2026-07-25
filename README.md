<div align="center">

# Benchmark Evolution in Frontier Models

**How frontier AI labs choose to measure—and market—model capability on public launch pages**

[Explore the data](data/) · [Read the methodology](docs/benchmark_classification_methodology_v3.md) · [Review extraction rules](docs/release_page_extraction_workflow.md) · [Reproduce the analysis](#reproduce-the-analysis)

![Scope: release pages only](https://img.shields.io/badge/scope-release%20pages%20only-6f42c1)
![Resolution: exact or explicit alias](https://img.shields.io/badge/resolution-exact%20or%20explicit%20alias-0f766e)
![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-2563eb)

</div>

<table>
  <tr>
    <td align="center"><strong>3</strong><br><sub>providers</sub></td>
    <td align="center"><strong>45</strong><br><sub>model releases</sub></td>
    <td align="center"><strong>196</strong><br><sub>canonical benchmarks</sub></td>
    <td align="center"><strong>557</strong><br><sub>release-page mentions</sub></td>
    <td align="center"><strong>2026-07-24</strong><br><sub>latest tracked launch</sub></td>
  </tr>
</table>

> [!IMPORTANT]
> **This is a study of public benchmark positioning, not a model leaderboard.** A benchmark is associated with a model only when it is named on that model's public release page—in page text, tables, images, captions, footnotes, or attributed partner evaluations. Technical reports, system cards, model cards, API documentation, and benchmark papers do not create model associations in this dataset.

## The question

Which evaluations do frontier-model providers choose to foreground when introducing a model to customers, developers, journalists, and the broader market?

That choice is informative. A benchmark appearing on a launch page signals which capabilities a provider wants its audience to notice. This project tracks that public evaluation vocabulary over time across OpenAI, Google, and Anthropic.

### What is—and is not—included

| Included | Excluded from model association |
| --- | --- |
| Named benchmarks and evaluation-like suites on public model launch pages | Evaluations found only in technical reports or papers |
| Labels in page text, tables, embedded images, captions, and footnotes | System cards, model cards, and API documentation |
| Explicitly named internal and partner evaluations, marked for review when opaque | Unnamed claims such as “better reasoning” or “state of the art” |
| Versioned surface forms exactly as presented, such as `Terminal-Bench 2.1` | Capability conclusions inferred from scores or marketing language |

Benchmark papers and official benchmark websites may be used to verify metadata in the canonical catalog. They never establish that a model used or emphasized a benchmark.

## Coverage

| Provider   |   Tracked releases | Coverage begins   | Latest tracked launch                                                        |
|:-----------|-------------------:|:------------------|:-----------------------------------------------------------------------------|
| OpenAI     |                 16 | 2022-11-30        | GPT-5.6 — 2026-07-09                                                         |
| Google     |                 11 | 2023-12-06        | Gemini 3.5 Flash Cyber, Gemini 3.5 Flash-Lite, Gemini 3.6 Flash — 2026-07-21 |
| Anthropic  |                 18 | 2023-03-14        | Claude 5 (Opus) — 2026-07-24                                                 |

The source unit is a **public release page**. When one page introduces several named model variants, the dataset may record separate model-release rows tied to that page. Each benchmark-bearing release row contributes equal total weight in share-based analyses, divided across its resolved benchmark mentions. This prevents launches with very long evaluation tables from dominating the trends.

## What the data shows

### 1. Public evaluation framing is moving from exams toward work

Earlier launch pages leaned heavily on static, exam-style tests. Recent launches foreground codebases, terminals, browsers, tools, professional workflows, and specialized work simulations. This is a shift in public benchmark selection—not evidence that models can fully perform the corresponding jobs.

![Static exams to work simulations](assets/static_to_work_simulation_trend.png)

| Year     | Static exam-style   | Work simulation   | Specialized domains   |   Benchmarked releases |
|:---------|:--------------------|:------------------|:----------------------|-----------------------:|
| 2023     | 82.4%               | 12.0%             | 53.7%                 |                      3 |
| 2024     | 70.7%               | 18.0%             | 28.0%                 |                      8 |
| 2025     | 54.4%               | 39.1%             | 48.7%                 |                     14 |
| 2026 YTD | 18.8%               | 73.2%             | 46.1%                 |                     16 |

> Multi-label shares can sum above 100% because a benchmark may represent more than one analytical frame.

Top contributors to the work-simulation signal:

| Benchmark          |   Weighted mentions |   Raw mentions | Providers                 |
|:-------------------|--------------------:|---------------:|:--------------------------|
| SWE-bench verified |                1.6  |             18 | Anthropic; Google; OpenAI |
| OSWorld-Verified   |                0.96 |             10 | Anthropic; Google; OpenAI |
| SWE-bench Pro      |                0.89 |             12 | Anthropic; Google; OpenAI |
| HumanEval          |                0.75 |              7 | Anthropic; Google; OpenAI |
| Tau-bench          |                0.65 |              6 | Anthropic; OpenAI         |
| TAU-2 bench        |                0.65 |             10 | Anthropic; Google; OpenAI |
| Terminal-bench     |                0.6  |              6 | Anthropic                 |
| GDPval-AA v2       |                0.58 |              5 | Anthropic; Google; OpenAI |

### 2. Benchmark vocabulary diffuses quickly between providers

The same evaluation names often move into the launch vocabulary of multiple providers. The table measures the time from the first tracked public mention to the next provider's first tracked mention. It does not identify benchmark creation dates, private adoption, or copying.

| Benchmark          | First tracked public mention   | Next provider          | Lag    |
|:-------------------|:-------------------------------|:-----------------------|:-------|
| MMMLU              | Anthropic (2025-02-25)         | OpenAI (2025-02-27)    | 2 days |
| Terminal-Bench 2.0 | Google (2025-11-18)            | Anthropic (2025-11-24) | 6 days |
| OfficeQA Pro       | Anthropic (2026-04-16)         | OpenAI (2026-04-23)    | 7 days |
| Finance Agent v2   | Google (2026-05-19)            | Anthropic (2026-05-28) | 9 days |
| GDPval-AA v2       | Anthropic (2026-06-30)         | OpenAI (2026-07-09)    | 9 days |
| Terminal-Bench 2.1 | Google (2026-05-19)            | Anthropic (2026-05-28) | 9 days |

### 3. Gemini 1.5 made long context unusually visible

Google's 2024 Gemini pages show a concentrated long-context emphasis under the current taxonomy. The evidence supports a narrow positioning claim: long context occupied an unusually large share of Google's public benchmark framing in that period.

![Gemini 1.5 long-context case study](assets/gemini_long_context_case.png)

| Provider   | Broad long-context share   | Primary-only share   | Main 2024 driver                      |   Benchmarked releases |
|:-----------|:---------------------------|:---------------------|:--------------------------------------|-----------------------:|
| OpenAI     | 2.4%                       | 2.4%                 | EgoSchema (GPT-4o)                    |                      3 |
| Google     | 39.3%                      | 35.7%                | Needle In A Haystack (Gemini 1.5)     |                      2 |
| Anthropic  | 5.8%                       | 2.1%                 | SWE-bench verified (Claude 3.5 Haiku) |                      3 |

### 4. Provider-authored benchmarks become shared competitive language

OpenAI-authored or OpenAI-affiliated benchmarks remain visible on Anthropic and Google pages. A cautious interpretation is that provider-linked evaluations can become part of a shared competitive vocabulary alongside academic and independent vendor benchmarks.

| Provider group   | 2023-2024                           | 2025-2026                           |
|:-----------------|:------------------------------------|:------------------------------------|
| Anthropic+Google | 14.5% raw; 16.9% release-normalized | 20.9% raw; 21.2% release-normalized |
| Anthropic        | 19.0% raw; 25.0% release-normalized | 18.9% raw; 20.6% release-normalized |
| Google           | 8.8% raw; 6.1% release-normalized   | 24.7% raw; 22.1% release-normalized |

## Visual atlas

### Release-by-release evolution

Each pie represents one benchmark-bearing release page. The chart uses a runtime `headline_task_mode` projection derived from the multi-facet taxonomy.

![Benchmark evolution by model release](assets/benchmark_evolution.png)

### Benchmarks per release

This chart counts unique resolved benchmark names for every tracked model release, including releases with no benchmark list, and overlays a 90-day moving average. It measures launch-page evaluation volume—not benchmark breadth or model quality.

![Benchmarks per model release](assets/benchmark_count_per_release.png)

### Task mode and domain over time

Task mode and domain are plotted as separate axes so unlike taxonomy dimensions do not share a denominator. Multi-label assignments split a benchmark's contribution equally within each axis.

![Benchmark landscape growth by separate axes](assets/benchmark_growth_by_all_category.png)

### Multi-facet trends

This view retains the richer taxonomy. When a benchmark has several labels within one facet axis, its contribution is divided equally among those labels at runtime.

![Multi-facet benchmark trends](assets/benchmark_facet_trends.png)

## How the data flows

```mermaid
flowchart LR
    A[Public model<br/>release page] --> B[Named benchmark or<br/>evaluation label]
    B --> C{Exact canonical<br/>name?}
    C -->|Yes| D[Canonical benchmark]
    C -->|No| E{Explicit,<br/>source-backed alias?}
    E -->|Yes| D
    E -->|No| F[Validation failure]
    D --> G[Multi-facet taxonomy]
    G --> H[Tables, trends,<br/>and charts]
```

The resolver does not silently fuzzy-match unresolved names. Surface forms must match a canonical benchmark name or a documented alias.

## Repository map

| Path | Purpose |
| --- | --- |
| [`data/models.csv`](data/models.csv) | Model release pages and the benchmark labels found on them |
| [`data/benchmarks.csv`](data/benchmarks.csv) | Canonical benchmark identities, references, provenance, and review status |
| [`data/benchmark_aliases.csv`](data/benchmark_aliases.csv) | Narrow, source-backed mappings from page wording to canonical IDs |
| [`data/benchmark_facets.csv`](data/benchmark_facets.csv) | Integrated multi-label taxonomy used by the analyses |
| [`analysis/readme_story/`](analysis/readme_story/) | Generated tables behind the narrative findings |
| [`assets/`](assets/) | Generated charts used in this README |
| [`scraping/`](scraping/) | Release-page extraction and review tooling |
| [`docs/`](docs/) | Classification methodology, audit notes, and contributor workflows |

## Methodology and guardrails

### Multi-facet classification

A benchmark can belong to several analytical facets at once. The v3 taxonomy records:

- **Construct claim** — the capability the benchmark is presented as measuring.
- **Task mechanism** — how the task is performed.
- **Domain** — the expertise or subject area required.
- **Modality and interaction pattern** — what the model receives and how it acts.
- **Metric, context pressure, and lifecycle risk** — how performance is measured and where interpretation needs care.

Charts that need one compact headline derive a projection at runtime. That projection is not the benchmark's exclusive identity. For example, a coding benchmark can retain a `Coding/Engineering` domain while being projected as `Agentic` when it requires autonomous environment interaction.

### Identity and review policy

- Explicit versions remain distinct when the release page distinguishes them.
- Run settings are deduplicated when they are only configurations of the same benchmark.
- Internal and partner evaluations are included when named, but opaque identities are marked `needs_review`.
- Every raw launch-page mention must resolve by exact canonical name or explicit alias.
- Prominence on a release page is not evidence of benchmark quality, score comparability, or model capability.

See the [classification methodology](docs/benchmark_classification_methodology_v3.md), [benchmark audit notes](docs/benchmark_audit_notes.md), and [facet review guidelines](docs/facet_review_guidelines.md) for the full rules.

## Reproduce the analysis

Run the pipeline from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

AS_OF=2026-07-24          # latest release date in data/models.csv
PY=.venv/bin/python       # or python, with project dependencies installed

$PY scripts/build_normalized_data.py
$PY scripts/validate_data.py
$PY analysis/benchmark_evolution/analyze.py --as-of "$AS_OF" --strict-resolution
$PY analysis/benchmark_evolution/benchmark_count_trend.py --as-of "$AS_OF" --window-days 90 --strict-resolution
$PY analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of "$AS_OF" --window-days 180 --strict-resolution
$PY analysis/benchmark_taxonomy_trends/facet_trends.py --as-of "$AS_OF" --window-days 180 --axes modality,interaction_pattern,context_pressure --top-labels 8 --strict-resolution
$PY analysis/readme_story/analyze.py --as-of "$AS_OF"
$PY scripts/validate_data.py
```

The normalized-data build preserves reviewed facet assignments for existing benchmark IDs, seeds facets for new IDs, removes facets for deleted IDs, and integrates temporary manual corrections. Story tables are generated under `analysis/readme_story/`; chart assets are written to `assets/`. The top-level README is maintained directly.

## Adding a model release

1. Extract benchmark-like names from the public launch page.
2. Audit false positives and distinguish benchmarks from ordinary capability claims.
3. Map each surface form to a canonical benchmark or add a narrow explicit alias.
4. Add source-backed metadata and mark opaque evaluations `needs_review`.
5. Rebuild normalized data, regenerate the analyses, and require strict validation to pass.

The scraper is a source extractor, not an authority. Generate a review packet with:

```bash
python scraping/review_packet.py scraping/output/new_release_extract.json
```

See the [release-page extraction workflow](docs/release_page_extraction_workflow.md) and [scraping guide](scraping/README.md) for the review process.

## Limitations

- The dataset captures **public launch-page emphasis**, not every evaluation a provider performed.
- Release pages differ in length, design, audience, and disclosure practices.
- Scores are not normalized or compared across models.
- Internal and partner evaluations may be incompletely documented.
- Taxonomy assignments are analytical interpretations and remain reviewable.

## License

Licensed under the [Apache License 2.0](LICENSE).
