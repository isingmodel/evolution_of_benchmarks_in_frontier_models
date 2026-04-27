# Benchmark Evolution in Frontier Models
This repository analyzes the evolution of benchmarks mentioned on public frontier-model launch pages from major AI providers (OpenAI, Google, Anthropic, etc.). It tracks provider benchmark selection and release-page positioning over time; it should not be interpreted as a direct measurement of model capability progress.

The unit of analysis is the public launch page written for a general audience: the page a provider presents to customers, developers, journalists, and the broader market. When a benchmark appears there, this repository treats it as a signal of the capability the provider chose to foreground, not simply as evidence that the model was evaluated on that benchmark.

The current normalized data covers 36 model-release rows, 32 rows with captured benchmark mentions, 422 resolved benchmark mentions, 135 canonical benchmark rows, and 1,275 benchmark-facet edges. The latest included release is OpenAI GPT-5.5 on 2026-04-23. The charts summarize how providers frame capability claims in public launch material; any single headline category shown in a chart is a visualization projection, not an exclusive benchmark identity.

## How To Read This README
- **Scope:** counts come from public launch-page benchmark mentions, not full technical reports, system cards, model cards, API docs, or independent benchmark runs.
- **Headline projection:** some charts assign each benchmark one readable task-mode category so the trend is plottable. That category is not the benchmark's full identity.
- **Weighting:** rolling trend charts normalize each release's resolved mentions before applying a 180-day rolling window and 30-day exponentially weighted moving average smoothing, so prolific release pages do not outweigh others only because they list more benchmarks.
- **Uncertainty:** row-level review status is still mixed. A facet edge is one benchmark-to-label row in the multi-facet taxonomy; most facet edges still need review.
- **Zero-count model rows:** a `0` mention count or "No public launch-page benchmark mentions captured" entry means no benchmark mentions were captured for that release row; it is not a claim that the model was unevaluated.

## Main Findings
- Recent launch pages emphasize agentic task completion, coding environments, tool use, professional workflows, and safety/alignment evaluations more than early static exam-style benchmark lists.
- In the raw latest-window count, Agentic and Generative Reasoning are the largest captured categories; in the rolling charts, the same categories are shown as release-normalized shares so releases with long benchmark lists do not overwhelm the trend.
- The most important limitation is not missing counts but unresolved review debt: most multi-facet rows still need manual audit, and prominence, quote-level release evidence, composite-index rollups, and benchmark-family sensitivity analyses remain future work.

## Source & Evidence Status
{{SOURCE_EVIDENCE_SUMMARY_TABLE}}

## Category Quick Reference
Task modes used in the headline charts:

- **Agentic:** tasks requiring autonomous tool use, environment interaction, or multi-step task completion.
- **Generative Reasoning:** answer, code, or text generation that primarily tests reasoning without an external task loop.
- **Knowledge Retrieval:** factual recall, search, long-context retrieval, or grounded question answering.
- **Constraint Satisfaction:** instruction following, safety/alignment behavior, control, or format compliance.
- **Multimodal Perception:** image, document, chart, GUI, audio, or video understanding.

Domains used in the separate-axis chart:

- **Coding/Engineering:** software, terminal, systems, cybersecurity, or engineering work.
- **STEM/Math:** mathematics, science, and technical reasoning outside software work.
- **General/Commonsense:** broad consumer, factual, visual, or commonsense tasks.
- **Specialized (Law/Bio/Finance):** professional or domain-specialist work such as law, biology, finance, and office deliverables.

## Evolution Graph
Each release is plotted on its provider row. Pie slices show the release-normalized headline projection for resolved benchmark mentions; a gray dot marks a release row with no resolved benchmark mentions captured. The pies are intentionally equal-sized, so they show composition rather than volume. To avoid overplotting, only spaced release labels are shown; the number in a shown label is the count of resolved mentions for that release.
![Benchmark Evolution](assets/benchmark_evolution.png)

## Benchmark Landscape Growth
The following graph shows the headline task-mode projection over time. It uses release-normalized mention weights, a rolling 180-day window, and 30-day exponentially weighted smoothing. This is a readable projection from the taxonomy, not an exclusive benchmark identity.
![Benchmark Growth](assets/benchmark_growth.png)

## Separate Axis Trends
The following graph keeps task mode and domain as separate axes, using the same release-normalized rolling window as the headline trend. Keeping the axes separate avoids a single denominator that mixes unlike taxonomy dimensions.
![Benchmark Growth by Separate Axes](assets/benchmark_growth_by_all_category.png)

## Classification Review Debt
The following graph summarizes low-confidence or review-needed facet rows in the generated normalized data. It is a data-quality dashboard: high bars mean the corresponding facet axis needs more manual audit before strong conclusions should be drawn from that axis.
![Benchmark Review Debt](assets/benchmark_review_debt.png)

{{REVIEW_DEBT_TABLE}}

## Multi-Facet Trends
The following graph uses `release_mentions.csv` and `benchmark_facet_edges.csv` directly. It plots the default facet axes `domain`, `modality`, `interaction_pattern`, and `context_pressure`; each panel has its own denominator. A single benchmark can contribute to multiple labels within a facet axis through `label_weight`, the fraction of that benchmark's contribution assigned to a label. The top 10 labels per axis are shown while smaller labels are grouped into `Other`. Because 1,008 of 1,275 facet rows still need review, treat this figure as experimental rather than final.
![Benchmark Facet Trends](assets/benchmark_facet_trends.png)

## Review Status And Caveats
The current normalized data has 5 accepted benchmark rows, 38 `needs_review` benchmark rows, and 92 `legacy_seed` rows. The accepted multi-facet benchmark rows are `BrowseComp Long Context`, `GDPval`, `GDPval-AA`, `TAU-2 bench`, and `Vending-Bench 2`; `FACTS Benchmark suite` and `BioPipelineBench` remain review-needed. At the facet level, 1,008 of 1,275 rows are `needs_review`, so the multi-facet charts should be treated as an evolving seed layer rather than a final taxonomy.

{{REVIEW_STATUS_SUMMARY_TABLE}}

Review-status terms:

- `accepted`: manually reviewed under the current multi-facet methodology.
- `needs_review`: present in the normalized tables but still awaiting manual audit or higher-confidence evidence.
- `legacy_seed`: inherited from the older single-projection catalog or rule-seeded pipeline output; useful for continuity, but not yet audited as a v3 multi-facet classification.

Several modern release-page patterns require special caution:

- Composite-index double counting: GPT-5.5 lists both Artificial Analysis composite indices and component benchmarks.
- Versioned benchmark replacement: successor rows such as SWE-bench Pro, Terminal-Bench 2.0, OSWorld-Verified, MRCR v2, and ARC-AGI-2 are not independent of their predecessors.
- Private, provider-created, and partner-branded evals: some rows are launch-page labels without public item sets or full scoring methodology.
- Release-page mentions are positioning signals, not capability measurements.

Open follow-up audits:

- Add quote-level, page-section, and OCR provenance for release-page mentions.
- Audit mention prominence so counts can be compared with page-position-weighted views.
- Run rollup-aware sensitivity analyses for composite indices and version families such as SWE-bench, Terminal-Bench, MRCR, ARC-AGI, and OSWorld.
- Promote high-impact `legacy_seed` and `needs_review` rows into accepted multi-facet rows through source-backed review.

## Preliminary Analysis & Observations

### Current Picture
The benchmark landscape has moved from mostly static exam, reasoning, and multimodal tasks toward agentic task completion, coding environments, tool use, professional workflows, and safety/alignment evaluations. In the raw latest-window count, from 2025-10-25 through 2026-04-23, Agentic is the largest headline projection at 43.5% of resolved mentions (87 of 200), followed by Generative Reasoning at 39.5% (79 of 200). This raw count is separate from the rolling chart shares, which normalize each release before smoothing.

The shift is not simply "more benchmarks." The release-page set is being refreshed by hardened successors and variants: SWE-bench Verified gives way to SWE-bench Pro, Terminal-bench to Terminal-Bench 2.0/Hard, OSWorld to OSWorld-Verified, MRCR to MRCR v2, ARC-AGI to ARC-AGI-2, SimpleQA to SimpleQA Verified, and OmniDocBench to OmniDocBench 1.5. Trend charts should therefore be read as a record of benchmark positioning, not as a clean longitudinal test suite.

Two new release-page patterns are especially visible in 2026. First, composite and third-party indices enter the captured benchmark list: GPT-5.5's first two captured benchmark entries are Artificial Analysis's Coding Index and Artificial Analysis Intelligence Index, and the same row also lists several component benchmarks. Second, provider-internal and partner-branded evaluations become common launch-page material, especially in GPT-5.5 and Claude Opus 4.7.

### Latest Frontier Release Snapshot
| Release | Mentions | Headline Pattern |
|---|---:|---|
| OpenAI GPT-5.5, 2026-04-23 | 34 | 15 Generative Reasoning, 14 Agentic, plus knowledge, safety/constraint, and multimodal mentions; includes third-party composites, internal evals, professional work, cybersecurity, and science. |
| Anthropic Claude 4.7 Opus, 2026-04-16 | 31 | 19 Agentic mentions; strong SWE-bench family concentration, partner/private coding evals, professional work, structural biology, and safety/alignment rows. |
| OpenAI GPT-5.4, 2026-03-05 | 26 | Balanced between Agentic and Generative Reasoning, with finance, office, law, web-agent, coding, and CoT-control evaluations. |
| Google Gemini 3.1 Pro, 2026-02-19 | 16 | Split between Agentic and Generative Reasoning, with SWE-bench Pro, Terminal-Bench 2.0, APEX-Agents, GDPval-AA, BrowseComp, and MRCR v2. |
| Google Gemini 3.1 Flash-Lite, 2026-03-03 | 11 | No Agentic headline projection; focuses on LMArena, factuality, multimodal reasoning, multilingual evaluation, and MRCR v2. |
| OpenAI GPT-5.3-Codex, 2026-02-05 | 7 | Coding-specialized release: 5 Agentic mentions and 6 Coding/Engineering domain mentions. |

### Provider Positioning
OpenAI still contributes many benchmark rows with OpenAI authorship or affiliation, but GPT-5.5 differs from earlier OpenAI rows: its first two captured benchmark entries are third-party Artificial Analysis composite indices, followed by both component benchmarks and OpenAI internal evaluations. The release-page signal is no longer only provider-created benchmarks; it also includes external rollups and internal professional-work evals.

Anthropic's Opus 4.5-4.7 releases show a strong concentration in software-engineering agents, partner/customer-oriented benchmarks, and safety evaluation. Claude Opus 4.7 in particular combines SWE-bench variants, partner-branded coding rows such as CursorBench, Rakuten-SWE-Bench, and Qodo's real-world code review benchmark, plus internal research-agent and behavioral-audit evaluations.

Google's Gemini 3.x releases emphasize a different mix from the latest OpenAI and Anthropic pages. Gemini 3.0 and 3.1 emphasize factuality, multimodal reasoning, multilingual evaluation, long-context/retrieval style tasks, and user-facing quality signals such as LMArena and SimpleQA Verified, while Gemini 3.1 Pro also joins the common agentic/coding comparison set.

### Methodology
This analysis focuses on benchmarks mentioned on public model launch pages, rather than every benchmark listed in technical reports, system cards, model cards, or API documentation. Those detailed sources are useful for verification and safety analysis, but they answer a different question: what was evaluated? Here, the narrower question is: which benchmarks did providers choose to mention in public launch messaging, and how did that selection change over time?

Prominence is not yet audited. All rows in `release_mentions.csv` currently have `mention_prominence=release_page_unspecified` and `mention_weight=1.0`, so the current analysis should be read as mention-count analysis rather than page-position-weighted analysis.

Release-page evidence is not yet normalized into quote-level or section-level provenance. `release_mentions.csv` records the source URL, raw mention label, and mention index, while `evidence.csv` currently stores benchmark-definition evidence seeded from reference links. Mention locations, surrounding quotes, OCR provenance, and page-section metadata remain future work.

The data flow is:

```text
models.csv + benchmark_aliases.csv
  -> release_mentions.csv

benchmark_catalog.csv
  + benchmark_metadata_overrides.csv
  + benchmark_facet_overrides.csv
  + benchmark_review_queue.csv
  -> benchmarks.csv
  -> evidence.csv
  -> benchmark_facet_edges.csv
```

`benchmark_catalog.csv` is the source catalog with one chart-compatible task mode and domain. `benchmarks.csv` is generated normalized benchmark metadata with stable IDs, canonical names, frontier-lab author affiliations, legacy projection fields, and review status. `benchmark_facet_edges.csv` is the multi-facet taxonomy table: each benchmark can contribute multiple labels within axes such as construct claim, task mechanism, domain, modality, interaction pattern, metric type, context pressure, and lifecycle risk.

Headline category is a visualization projection, not an exclusive benchmark identity. For example, a coding benchmark can retain a `Coding/Engineering` domain facet while being headline-projected as `Agentic` when the release-page emphasis is autonomous environment interaction. See the [v3 benchmark classification methodology](docs/benchmark_classification_methodology_v3.md) for the multi-facet classification rules.

## Models Data
The compact table below shows the latest release rows and captured mention counts. The all-release-row summary is kept in a collapsible block; use `data/models.csv` for raw benchmark-list strings and `data/release_mentions.csv` for normalized mention-level analysis.

{{LATEST_RELEASE_SUMMARY_TABLE}}

<details>
<summary>All release rows summary</summary>

{{MODELS_TABLE}}

</details>

## Benchmark Projection Table
The summaries below show chart-compatible projection fields by review status. Use `data/benchmarks.csv` for benchmark-level rows, reference links, source authors, and rationales, and `data/benchmark_facet_edges.csv` for long-form facet annotations.

{{PROJECTION_SUMMARY_TABLES}}

## Categorization Logic
The generated projection table currently exposes the normalized source metadata plus the headline fields used by existing scripts:
1. **frontier_lab_author_affiliations**: whether benchmark authors include the tracked frontier labs (OpenAI, Anthropic, Google, DeepMind, Microsoft, xAI).
2. **task_mode**: how the task is solved (Agentic, Generative Reasoning, Knowledge Retrieval, Constraint Satisfaction, Multimodal Perception).
3. **task_domain**: what subject expertise is required (STEM/Math, Coding/Engineering, General/Commonsense, Specialized).

Under the v3 methodology, these fields should be treated as projections from richer benchmark facets such as construct claim, task mechanism, domain, modality, interaction pattern, metric type, context pressure, and lifecycle risk.

## Auto-Update
To regenerate the normalized benchmark data, current chart assets, and README, run:
```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt

AS_OF=2026-04-23          # latest release date included in data/models.csv
ACCESSED_DATE=2026-04-26  # date used for seeded evidence records

python3 scripts/build_normalized_data.py --accessed-date "$ACCESSED_DATE"
python3 scripts/validate_data.py
python3 scripts/apply_mention_prominence.py --dry-run
python3 scripts/generate_visuals.py --as-of "$AS_OF" --strict-resolution
python3 scripts/generate_trend_graph_by_main_category.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python3 scripts/generate_trend_graph_by_all_category.py --as-of "$AS_OF" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
python3 scripts/generate_facet_trends.py --as-of "$AS_OF" --window-days 180
python3 scripts/update_readme.py
python3 scripts/validate_data.py
```

The normalized-data build seeds canonical benchmark, evidence, facet-edge, and release-mention tables from source CSVs. Curated corrections live in `data/benchmark_metadata_overrides.csv` and `data/benchmark_facet_overrides.csv` rather than in the build script. Mention prominence is deterministic and manual: `data/mention_prominence_overrides.csv` is validated and applied by the build, but no release-page scraping is performed by default. The generated README taxonomy table and trend scripts remain headline-compatible while the normalized tables preserve richer multi-facet labels for quantitative and qualitative analysis.

## Release-Page Extraction Workflow
For new model launches, run the scraper as an evidence generator and review the result with independent roles: source extraction, false-positive audit, catalog mapping, and data-integrity audit. Generate a handoff packet with `python scraping/review_packet.py scraping/output/new_release_extract.json`, then apply only source-backed CSV edits and rerun the validation pipeline above. See [release-page extraction workflow](docs/release_page_extraction_workflow.md) and [scraping workflow](scraping/README.md) for details.
