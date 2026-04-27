# Benchmark Evolution in Frontier Models
This repository analyzes the evolution of benchmarks emphasized on frontier model release pages from major AI providers (OpenAI, Google, Anthropic, etc.). It tracks provider benchmark selection and positioning over time; it should not be interpreted as a direct measurement of model capability progress.

The unit of analysis is the public launch page written for a general audience: the page a provider presents to customers, developers, journalists, and the broader market. When a benchmark appears there, this repository treats it as a signal of the capability the provider chose to foreground, not simply as evidence that the model was evaluated on that benchmark.

The charts summarize how providers frame capability claims in public launch material. Benchmark categories are multi-facet in the v3 methodology; any single headline category shown in a chart is a visualization projection, not an exclusive benchmark identity.

## Evolution Graph
![Benchmark Evolution](assets/benchmark_evolution.png)

## Benchmark Landscape Growth
The following graph shows the headline task-mode projection over time (rolling 6-month window). This is a readable projection from the taxonomy, not an exclusive benchmark identity.
![Benchmark Growth](assets/benchmark_growth.png)

## Separate Axis Trends
The following graph keeps task mode and domain as separate axes, avoiding a single denominator that mixes unlike taxonomy dimensions.
![Benchmark Growth by Separate Axes](assets/benchmark_growth_by_all_category.png)

## Classification Review Debt
The following graph summarizes low-confidence or review-needed facet rows in the generated normalized data.
![Benchmark Review Debt](assets/benchmark_review_debt.png)

## Multi-Facet Trends
The following graph expands the benchmark list in `models.csv` at runtime and joins it to `benchmark_facet_edges.csv`. A single benchmark can contribute to multiple labels within a facet axis through `label_weight`, so this chart is closer to the multi-facet methodology than the headline projection charts above.
![Benchmark Facet Trends](assets/benchmark_facet_trends.png)

## Analysis & Observations

### Case Study: Gemini 1.5
When Gemini 1.5 was released in February 2024, GPT-4 was the market leader. Lacking significant performance advantages in other areas compared to GPT-4, Google focused heavily on promoting its **Long Context** capabilities. While competitors like GPT and Llama were limited to tens of thousands of tokens, Gemini 1.5 boasted support for hundreds of thousands, making Long Context the highlight of its release page.

### Benchmark Analysis Methodology
This analysis therefore focuses on benchmarks featured prominently on model release pages, rather than every benchmark listed in technical reports, system cards, model cards, or API documentation. Those detailed sources are useful for verification and safety analysis, but they answer a different question: what was evaluated? Here, the question is narrower: which benchmarks did providers choose to emphasize in public launch messaging, and how did that emphasis change over time? See the [v3 benchmark classification methodology](docs/benchmark_classification_methodology_v3.md) for the multi-facet classification rules.

Headline category is a visualization projection, not an exclusive benchmark identity. For example, a coding benchmark can retain a `Coding/Engineering` domain facet while being headline-projected as `Agentic` when the release-page emphasis is autonomous environment interaction.

The current normalized seed includes evidence-audited multi-facet annotations for `TAU-2 bench`, `Vending-Bench 2`, `GDPval`, `GDPval-AA`, `BrowseComp Long Context`, `FACTS Benchmark suite`, and `BioPipelineBench`. See [benchmark audit notes](docs/benchmark_audit_notes.md) for the source-backed decisions and remaining review queue.

### Evolution of Benchmarks
*   **Early GPT (3, 3.5)**: Focused on simple knowledge-based QA benchmarks (e.g., Biology Olympiad), reflecting the limitations of early LLMs.
*   **Expansion**: The landscape shifted towards **Multimodal** and **Coding** benchmarks as model capabilities matured.
*   **Current Trend**: **Agentic** benchmarks are rapidly increasing. We anticipate a surge in agent-related benchmarks for the upcoming frontier models in the first half of this year.

### The Battle for Hegemony
Observations from these public release pages reveal a strategic battle:
*   **Google's Catch-up**: As a fast follower in the LLM product space, Google's early Gemini releases heavily adopted benchmarks established by OpenAI.
*   **OpenAI's Lead**: OpenAI often created new benchmarks to define the direction of the field. Google followed suit, and the landscape has now become highly competitive with comparable performance metrics.

## Models Data
The following table lists the models and their associated benchmarks.

{{MODELS_TABLE}}

## Benchmark Taxonomy
Classification of various benchmarks by category.

{{TAXONOMY_TABLE}}

## Categorization Logic
The generated taxonomy table currently exposes the normalized source metadata plus the headline fields used by existing scripts:
1. **frontier_lab_author_affiliations**: whether benchmark authors include the tracked frontier labs (OpenAI, Anthropic, Google, DeepMind, Microsoft, xAI).
2. **task_mode**: how the task is solved (Agentic, Generative Reasoning, Knowledge Retrieval, Constraint Satisfaction, Multimodal Perception).
3. **task_domain**: what subject expertise is required (STEM/Math, Coding/Engineering, General/Commonsense, Specialized).

Under the v3 methodology, these fields should be treated as projections from richer benchmark facets such as construct claim, task mechanism, domain, modality, interaction pattern, metric type, context pressure, and lifecycle risk.

## Auto-Update
To regenerate the normalized benchmark data, current chart assets, and README, run:
```bash
AS_OF=2026-04-23          # latest release date included in data/models.csv
ACCESSED_DATE=2026-04-26  # date used for seeded evidence records

python scripts/build_normalized_data.py --accessed-date "$ACCESSED_DATE"
python scripts/validate_data.py
python scripts/generate_visuals.py --as-of "$AS_OF" --strict-resolution
python scripts/generate_trend_graph_by_main_category.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python scripts/generate_trend_graph_by_all_category.py --as-of "$AS_OF" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
python scripts/generate_facet_trends.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python scripts/update_readme.py
python scripts/validate_data.py
```

The normalized-data build seeds canonical benchmark, evidence, and facet-edge tables from source CSVs. Curated corrections live in `data/benchmark_metadata_overrides.csv` and `data/benchmark_facet_overrides.csv` rather than in the build script. The generated README taxonomy table and trend scripts remain headline-compatible while the normalized facet table preserves richer multi-facet labels for quantitative and qualitative analysis.

## Release-Page Extraction Workflow
For new model launches, run the scraper as an evidence generator and review the result with independent roles: source extraction, false-positive audit, catalog mapping, and data-integrity audit. Generate a handoff packet with `python scraping/review_packet.py scraping/output/new_release_extract.json`, then apply only source-backed CSV edits and rerun the validation pipeline above. See [release-page extraction workflow](docs/release_page_extraction_workflow.md) and [scraping workflow](scraping/README.md) for details.
