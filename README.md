# Benchmark Evolution in Frontier Models
This repository tracks how major AI providers (OpenAI, Google, Anthropic, etc.) select and position benchmarks on their frontier model release pages over time. It is not a measurement of model capability progress.

The unit of analysis is the public launch page — what a provider shows to customers, developers, and journalists. A benchmark appearing there signals which capability the provider chose to foreground, not merely that the model was evaluated on it.

The charts summarize how providers frame capability claims in launch material. Under the v3 methodology each benchmark carries multiple facets, so any single headline category in a chart is a projection chosen for visualization, not an exclusive label.

## Evolution Graph
The release-page pies project `headline_task_mode` at runtime from `benchmark_facets.csv`. Each release page contributes equal total weight, split across its resolved benchmark mentions and then across multiple labels on the same facet axis.
![Benchmark Evolution](assets/benchmark_evolution.png)

## Benchmark Landscape Growth
This graph keeps headline task mode and v3 domain facets on separate axes, so a single denominator never has to mix unlike taxonomy dimensions. Where a benchmark carries multiple domain labels, its contribution splits equally within the domain axis.
![Benchmark Growth by Separate Axes](assets/benchmark_growth_by_all_category.png)

## Multi-Facet Trends
This graph expands `models.csv` at runtime and joins it to `benchmark_facets.csv`. When a benchmark carries multiple labels on a single facet axis, its contribution is split equally across them.
![Benchmark Facet Trends](assets/benchmark_facet_trends.png)

## Story Analyses

These analyses come from `analysis/readme_story/analyze.py`, which reuses the validation pipeline's benchmark resolver: a release-page mention counts only when it matches a canonical name or an explicit alias. In share-based analyses each release page contributes one unit of weight, divided evenly across the benchmarks it lists, so long benchmark tables don't dominate provider-period comparisons.

### From Static Exams to Work Simulations

The clearest pattern is a shift in public benchmark framing. Earlier release pages leaned on static, exam-style benchmarks; recent ones foreground work simulations across codebases, terminals, browsers, tools, professional workflows, and specialized domains. The claim is about how providers choose to advertise their models, not whether the models can actually do those jobs.

![Static Exams to Work Simulations](assets/static_to_work_simulation_trend.png)

| Year     | Static exam-style   | Work simulation   | Specialized domains   |   Benchmarked releases |
|:---------|:--------------------|:------------------|:----------------------|-----------------------:|
| 2023     | 82.4%               | 12.0%             | 53.7%                 |                      3 |
| 2024     | 70.7%               | 18.0%             | 28.0%                 |                      8 |
| 2025     | 54.4%               | 39.1%             | 48.7%                 |                     14 |
| 2026 YTD | 30.5%               | 61.5%             | 55.9%                 |                      7 |

Under the multi-label projection, shares can exceed 100% because a benchmark can sit in more than one frame. That is a counting change, not a change in the underlying release-page data.

Top contributors to the work-simulation signal:

| Benchmark          |   Weighted mentions |   Raw mentions | Providers                 |
|:-------------------|--------------------:|---------------:|:--------------------------|
| SWE-bench verified |                1.6  |             18 | Anthropic; Google; OpenAI |
| HumanEval          |                0.75 |              7 | Anthropic; Google; OpenAI |
| Tau-bench          |                0.65 |              6 | Anthropic; OpenAI         |
| TAU-2 bench        |                0.65 |             10 | Anthropic; Google; OpenAI |
| Terminal-bench     |                0.6  |              6 | Anthropic                 |
| OSWorld            |                0.47 |              5 | Anthropic                 |
| Terminal-Bench 2.0 |                0.43 |              7 | Anthropic; Google; OpenAI |
| Codeforces         |                0.42 |              4 | OpenAI                    |

### Case Study: Gemini 1.5 and Long Context

Google's 2024 Gemini release pages show a clear long-context emphasis under the current taxonomy, supporting the narrower claim that Gemini's public framing leaned into long context that year. On its own it says nothing about provider intent or comparative model capability.

![Gemini Long Context Case Study](assets/gemini_long_context_case.png)

| Provider   | Broad long-context share   | Primary-only share   | Main 2024 driver                      |   Benchmarked releases |
|:-----------|:---------------------------|:---------------------|:--------------------------------------|-----------------------:|
| OpenAI     | 2.4%                       | 2.4%                 | EgoSchema (GPT-4o)                    |                      3 |
| Google     | 39.3%                      | 35.7%                | Needle In A Haystack (Gemini 1.5)     |                      2 |
| Anthropic  | 5.8%                       | 2.1%                 | SWE-bench verified (Claude 3.5 Haiku) |                      3 |

### Public Benchmark Diffusion

Some benchmark names move into shared public evaluation vocabulary quickly. The table below ranks the fastest cross-provider cascades, measured from the first tracked release-page mention to the next provider's first tracked mention. These are not benchmark creation dates, internal adoption dates, or evidence that one provider copied another.

| Benchmark          | First tracked public mention   | Next provider          | Lag     |
|:-------------------|:-------------------------------|:-----------------------|:--------|
| MMMLU              | Anthropic (2025-02-25)         | OpenAI (2025-02-27)    | 2 days  |
| Terminal-Bench 2.0 | Google (2025-11-18)            | Anthropic (2025-11-24) | 6 days  |
| OfficeQA Pro       | Anthropic (2026-04-16)         | OpenAI (2026-04-23)    | 7 days  |
| APEX-Agents        | Google (2026-02-19)            | OpenAI (2026-03-05)    | 14 days |
| GDPval-AA          | Anthropic (2026-02-05)         | Google (2026-02-19)    | 14 days |
| Scale MCP-Atlas    | Anthropic (2025-11-24)         | OpenAI (2025-12-11)    | 17 days |

### Borrowed Benchmark Authority

OpenAI-linked benchmark influence does not fade from the release pages. On Anthropic and Google pages, mentions of OpenAI-authored or OpenAI-affiliated benchmarks rise in 2025–2026 under both raw and release-normalized views. The cautious reading: those benchmarks have entered a shared competitive vocabulary, even as neutral academic and vendor benchmarks remain central.

| Provider group   | 2023-2024                           | 2025-2026                           |
|:-----------------|:------------------------------------|:------------------------------------|
| Anthropic+Google | 14.5% raw; 16.9% release-normalized | 24.8% raw; 26.0% release-normalized |
| Anthropic        | 19.0% raw; 25.0% release-normalized | 22.3% raw; 23.7% release-normalized |
| Google           | 8.8% raw; 6.1% release-normalized   | 29.3% raw; 30.6% release-normalized |

### Benchmark Analysis Methodology
The analysis focuses on benchmarks featured on model release pages, not the full set listed in technical reports, system cards, or API documentation. Those detailed sources answer what was evaluated; the question here is narrower — which benchmarks did providers choose to emphasize in launch messaging, and how did that emphasis shift over time? See the [v3 benchmark classification methodology](docs/benchmark_classification_methodology_v3.md) for the multi-facet rules.

The headline category is a visualization projection, not the benchmark's full identity. A coding benchmark can keep its `Coding/Engineering` domain facet while being headline-projected as `Agentic` when the release page emphasizes autonomous environment interaction. The canonical facet table is v3-first, and scripts derive any single-label projection at runtime when a chart needs one.

The normalized facet table has been regenerated as a reviewable v3 multi-label table. See [benchmark audit notes](docs/benchmark_audit_notes.md) for source-backed decisions and the open caveats on high-impact benchmarks already audited.

## Models Data
See [`data/models.csv`](data/models.csv) for the full model-release inventory and benchmark mentions.

## Benchmark Taxonomy
See [`data/`](data/) for the benchmark catalog, aliases, and normalized multi-facet taxonomy files.

## Categorization Logic
The normalized benchmark files keep source metadata alongside legacy headline fields for audit and backward compatibility:
1. **frontier_lab_author_affiliations**: whether benchmark authors include the tracked frontier labs (OpenAI, Anthropic, Google, DeepMind, Microsoft, xAI).
2. **task_mode**: how the task is solved (Agentic, Generative Reasoning, Knowledge Retrieval, Constraint Satisfaction, Multimodal Perception).
3. **task_domain**: what subject expertise is required (STEM/Math, Coding/Engineering, General/Commonsense, Specialized).

Under v3, these fields are projections from richer benchmark facets — construct claim, task mechanism, domain, modality, interaction pattern, metric type, context pressure, and lifecycle risk.

## Auto-Update
To regenerate the normalized benchmark data, current chart assets, and README, run:
```bash
AS_OF=2026-04-23          # latest release date included in data/models.csv
PY=.venv/bin/python       # or python, if your environment is already activated

$PY scripts/build_normalized_data.py
$PY scripts/validate_data.py
$PY analysis/benchmark_evolution/analyze.py --as-of "$AS_OF" --strict-resolution
$PY analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of "$AS_OF" --window-days 180 --strict-resolution
$PY analysis/benchmark_taxonomy_trends/facet_trends.py --as-of "$AS_OF" --window-days 180 --top-labels 8 --strict-resolution
$PY analysis/readme_story/analyze.py --as-of "$AS_OF"
$PY scripts/update_readme.py
$PY scripts/validate_data.py
```

The build keeps `data/benchmark_facets.csv` aligned with the canonical benchmark source. Curated facet corrections are merged into that final table after review; `data/benchmark_facet_manual.csv` is only a temporary staging file during updates. Trend analyses stay headline-compatible by projecting a single label at runtime, while the normalized facet table preserves the full multi-facet labels for quantitative and qualitative analysis. Story-analysis tables land under `analysis/readme_story/`, and README chart assets under `assets/`.

## Release-Page Extraction Workflow
For new model launches, treat the scraper as a source extractor and review its output through separate roles: source extraction, false-positive audit, catalog mapping, and data-integrity audit. Generate a handoff packet with `python scraping/review_packet.py scraping/output/new_release_extract.json`, then apply only source-backed CSV edits and rerun the validation pipeline above. See [release-page extraction workflow](docs/release_page_extraction_workflow.md) and [scraping workflow](scraping/README.md) for details.
