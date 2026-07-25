<div align="center">

# Benchmark Evolution in Frontier Models

**How frontier AI labs choose to measure—and market—model capability on public launch pages**

[Explore the data](data/) · [Read the methodology](docs/benchmark_classification_methodology_v3.md) · [Review extraction rules](docs/release_page_extraction_workflow.md) · [Reproduce the analysis](#reproduce-the-analysis)

![Scope: release pages only](https://img.shields.io/badge/scope-release%20pages%20only-6f42c1)
![Resolution: exact or explicit alias](https://img.shields.io/badge/resolution-exact%20or%20explicit%20alias-0f766e)
![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-2563eb)

</div>

{{PROJECT_SNAPSHOT}}

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

{{PROVIDER_COVERAGE_TABLE}}

The source unit is a **public release page**. When one page introduces several named model variants, the dataset may record separate model-release rows tied to that page. Each benchmark-bearing release row contributes equal total weight in share-based analyses, divided across its resolved benchmark mentions. This prevents launches with very long evaluation tables from dominating the trends.

## What the data shows

### 1. Public evaluation framing is moving from exams toward work

Earlier launch pages leaned heavily on static, exam-style tests. Recent launches foreground codebases, terminals, browsers, tools, professional workflows, and specialized work simulations. This is a shift in public benchmark selection—not evidence that models can fully perform the corresponding jobs.

![Static exams to work simulations](assets/static_to_work_simulation_trend.png)

{{STATIC_WORK_TABLE}}

> Multi-label shares can sum above 100% because a benchmark may represent more than one analytical frame.

Top contributors to the work-simulation signal:

{{WORK_SIMULATION_CONTRIBUTORS_TABLE}}

### 2. Benchmark vocabulary diffuses quickly between providers

The same evaluation names often move into the launch vocabulary of multiple providers. The table measures the time from the first tracked public mention to the next provider's first tracked mention. It does not identify benchmark creation dates, private adoption, or copying.

{{DIFFUSION_TABLE}}

### 3. Gemini 1.5 made long context unusually visible

Google's 2024 Gemini pages show a concentrated long-context emphasis under the current taxonomy. The evidence supports a narrow positioning claim: long context occupied an unusually large share of Google's public benchmark framing in that period.

![Gemini 1.5 long-context case study](assets/gemini_long_context_case.png)

{{LONG_CONTEXT_TABLE}}

### 4. Provider-authored benchmarks become shared competitive language

OpenAI-authored or OpenAI-affiliated benchmarks remain visible on Anthropic and Google pages. A cautious interpretation is that provider-linked evaluations can become part of a shared competitive vocabulary alongside academic and independent vendor benchmarks.

{{BORROWED_AUTHORITY_TABLE}}

## Visual atlas

### Release-by-release evolution

Each pie represents one benchmark-bearing release page. The chart uses a runtime `headline_task_mode` projection derived from the multi-facet taxonomy.

![Benchmark evolution by model release](assets/benchmark_evolution.png)

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
AS_OF=2026-07-24          # latest release date in data/models.csv
PY=.venv/bin/python       # or python, with project dependencies installed

$PY scripts/build_normalized_data.py
$PY scripts/validate_data.py
$PY analysis/benchmark_evolution/analyze.py --as-of "$AS_OF" --strict-resolution
$PY analysis/benchmark_taxonomy_trends/task_mode_trend.py --as-of "$AS_OF" --window-days 180 --strict-resolution
$PY analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of "$AS_OF" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
$PY analysis/benchmark_taxonomy_trends/facet_trends.py --as-of "$AS_OF" --window-days 180 --top-labels 8 --strict-resolution
$PY analysis/readme_story/analyze.py --as-of "$AS_OF"
$PY scripts/update_readme.py
$PY scripts/validate_data.py
```

The normalized-data build preserves reviewed facet assignments for existing benchmark IDs, seeds facets for new IDs, removes facets for deleted IDs, and integrates temporary manual corrections. Story tables are generated under `analysis/readme_story/`; chart assets are written to `assets/`.

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
