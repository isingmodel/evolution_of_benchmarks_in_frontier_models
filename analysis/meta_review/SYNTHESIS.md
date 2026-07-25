# Meta-Review Synthesis

This document integrates the five result reviews. The goal is to decide which exploratory outputs should become core project material, which should be shown as case studies or appendix material, and which need more data work before publication.

## Overall Ranking

| Priority | Result | Project Fit | Recommended Treatment | Best Display |
| ---: | --- | --- | --- | --- |
| 1 | Static exams to work simulations | Very high | Main README section | Revised line chart plus compact annual table |
| 2 | Gemini 1.5 long-context emphasis | High | Bounded case study | Bar chart plus 2024 driver table |
| 3 | Review leverage / review debt | Very high | Methodology caveat and audit roadmap | Top-10 table or current review leverage chart |
| 4 | Provider framing fingerprints | High | Main section after redesign and sensitivity checks | Simplified heatmap/small multiples |
| 5 | Public benchmark diffusion | Medium-high | Secondary README section | Compact cascade table plus annotated similarity chart |
| 6 | Borrowed benchmark authority | Medium-high | Short caveated callout | Compact period comparison table |
| 7 | Provider-created/private escalation | Medium | Appendix until metric is split | Caveated table, not headline chart |
| 8 | Domain-interaction alluvial | Medium | Methods appendix or replace | Domain-interaction matrix |
| 9 | Source-author dependency/import-export | Medium-low for now | Backlog/appendix | Needs metadata audit and publication dates |

## Best Main Story

The most project-fit and reader-friendly story is:

> Public frontier-model release pages are shifting from static exam-style benchmarks toward work-simulation benchmarks.

Why this should lead:

- It directly answers the project's benchmark-evolution question.
- It is easy to understand without assuming provider intent.
- It extends the existing README beyond task-mode trend charts.
- It can be shown with one chart and one small table.

Use:

- `analysis/ideation_narrative_strategy/static_to_work_simulation_trend.png`, after relabeling `2026` as `2026 YTD` and adding `n=` release counts.
- `analysis/ideation_narrative_strategy/annual_strategy_frames.csv`, reduced to static exam share, work simulation share, specialized domain share, and release-page count.

Needed before README:

- Add top-contributor table for the work-simulation rise.
- Add provider-balanced sensitivity or at least a note about provider/release mix.
- Caption every chart as benchmark mentions on public release pages, not capability.

## Best Case Study

The Gemini 1.5 long-context result is ideal as a bounded case study:

- Google 2024 broad long-context share: 39.3%.
- OpenAI 2024: 2.4%.
- Anthropic 2024: 5.8%.

Use:

- `analysis/provider_strategy_long_context/provider_long_context_share.png`.
- A compact table from `provider_hypothesis_period_summary.csv` and `long_context_benchmark_drivers.csv`.

Needed before README:

- Reword causal language: "consistent with release-page emphasis" rather than "because long context was differentiating."
- Add release counts and note that Google 2024 has only two benchmarked releases.
- Add broad versus primary-only sensitivity.
- Review `context_pressure` for high-impact rows such as `Needle In A Haystack`, `MRCR`, `MRCR v2`, and `EgoSchema`.

## Best Methodology/Caveat Artifact

The review-leverage output should become a visible methodology artifact, not a hidden caveat.

Use:

- `analysis/ideation_methodology_visuals/review_leverage_benchmarks.csv`.
- Either `review_leverage_benchmarks.png` or a compact top-10 table.

Recommended framing:

> These are the high-impact benchmark facets to audit first. This is not a quality score; it is an uncertainty roadmap.

Top review targets include `SWE-bench verified`, `MMMU / MMMU Pro`, `MMMLU`, `GPQA Diamond`, `AIME`, `Terminal-bench`, `HLE`, and `Terminal-Bench 2.0`.

## Useful Secondary Section

Public benchmark diffusion is promising, but should avoid "import/export" and "first mover" language.

Use:

- A compact "fastest cross-provider public mention cascades" table from `analysis/ideation_network_dynamics/cascade_metrics.csv`.
- A revised and annotated `portfolio_similarity_over_time.png`.

Recommended framing:

> Across tracked public launch pages, some benchmark vocabulary becomes shared quickly across providers, while many benchmarks remain single-provider in the observed window.

Needed before README:

- Replace "first mover/import/export" with "first tracked public mention/later public mention."
- Add low-denominator notes to the similarity chart.
- Keep source-author dependency and provider role balances in appendix until metadata is audited.

## Cautious Callout

The frontier-lab benchmark hegemony result is valuable, but the public-facing title should be softer.

Use:

- `analysis/frontier_lab_benchmark_hegemony/openai_adoption_period_comparison.csv`.

Recommended title:

- "Borrowed Benchmark Authority"
- "Lab-Authored Benchmarks in the Shared Evaluation Vocabulary"

Do not use as a headline "hegemony" claim yet. The result is best as a short counterintuitive callout:

> Anthropic and Google did not move away from OpenAI-linked benchmarks in this dataset; OpenAI-authored-or-affiliated mentions rose from 14.5% in 2023-2024 to 20.8% in 2025-2026.

Needed before README:

- Add release-normalized shares.
- Add strict sensitivity excluding multi-affiliated or ambiguous cases.
- Audit high-impact `source_author` and `frontier_lab_author_affiliations` rows.

## What To Keep Out Of The Main README For Now

- Provider-created/private escalation as a headline chart. The current metric blends public provider-created benchmarks with private or opaque evaluations.
- Domain-interaction alluvial in current form. The idea is good, but a matrix will be clearer and less likely to imply temporal flow.
- Source-author dependency and import/export balances. These need source-author audit and benchmark publication dates.
- Benchmark first-adoption lag. Current lag is first tracked public release-page mention, not benchmark creation or true adoption.

## Recommended README Flow

1. Scope note: release-page benchmark mentions are public framing signals, not capability measurements.
2. Existing global timeline and headline projection chart.
3. New main section: **From Static Exams to Work Simulations**.
4. Case study: **Gemini 1.5 and Long Context**.
5. Provider framing: simplified provider fingerprint after sensitivity checks.
6. Benchmark diffusion: compact cascade table and similarity chart.
7. Borrowed benchmark authority: short OpenAI-linked benchmark callout.
8. Review debt and review leverage: visible methodology caveat and audit roadmap.

## Immediate Action List

1. Regenerate `static_to_work_simulation_trend.png` with `2026 YTD` and `n=` labels.
2. Create a top-contributor table for work-simulation growth.
3. Create broad-vs-primary long-context sensitivity chart/table.
4. Create OpenAI-linked release-normalized shares and strict sensitivity table.
5. Rename public-facing "strategy" to "framing" or "benchmark emphasis" unless text evidence is added.
6. Add accepted-only or high-confidence sensitivity for provider fingerprints and domain-interaction views.
7. Replace current domain-interaction alluvial with a matrix.
8. Audit high-leverage facet/authorship rows before publication-level claims.
