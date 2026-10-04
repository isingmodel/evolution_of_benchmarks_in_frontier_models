# Provider Strategy: Long-Context Showcase

This analysis concretizes idea #2: providers may differ in how they showcase
benchmarks over time, and Gemini/Google in 2024 may have emphasized
long-context benchmarks because long context was a differentiating release-page
theme versus OpenAI and Anthropic. The quantitative claim here is only about
benchmark mentions on public release pages, not about model capability or
provider intent.

Run from the repo root:

```bash
.venv/bin/python analysis/provider_strategy_long_context/analyze.py
```

The current scope uses local data through `2026-09-30`. Current resolved and
unresolved inventory counts are in the generated outputs. The weighted unit is
a benchmark-bearing model-release row; a shared launch URL can supply several
rows.

## Metrics

Primary shares are release-normalized: each benchmark-bearing model-release row
contributes 1.0 total weight, divided evenly across the resolved benchmarks on
that page. This keeps long benchmark tables from dominating the provider-period
comparison. Raw mention counts and raw long-context shares are also written to
the CSVs.

- Long context: `context_pressure` is `long_context_primary` or
  `long_context_supporting`; primary-only share is reported separately.
- Agentic: headline mode is `Agentic`, or the construct/interaction facets
  indicate tool use, web/computer use, environment interaction, or multi-step
  agent behavior.
- Multimodal: modality uses image, video, audio, document layout, mixed
  multimodal, browser UI, or desktop UI.
- Coding: coding domain, code modality, coding/software-engineering construct,
  or coding-oriented task mechanism.
- Axis tables split a benchmark's weight evenly when a benchmark has multiple
  active labels within the same facet axis.

## Reading Current Results

Use [provider_hypothesis_period_summary.csv](provider_hypothesis_period_summary.csv)
for the release-normalized 2024 versus 2025–2026 comparison, and
[provider_period_summary.csv](provider_period_summary.csv) for non-overlapping
periods. Each table reports both primary-only and broader long-context shares.
The broad measure includes supporting-context work benchmarks; it is not
restricted to retrieval tests.

Google's 2024 sample has only two benchmark-bearing model-release rows, so it
supports a limited case study. The Gemini 1.5 row contains just Needle In A
Haystack and MTOB. The October source audit corrected MTOB from an erroneous
image-generation classification to text translation from a long grammar-manual
prompt. Both names therefore matter to that row's context share. Use the
regenerated [long-context drivers](long_context_benchmark_drivers.csv) to inspect
their contributions rather than reusing the previous snapshot's percentages.

## Charts And Tables

![Long-context benchmark share by provider](provider_long_context_share.png)

![Provider showcase strategy heatmap](provider_strategy_heatmap.png)

Generated outputs:

- `provider_hypothesis_period_summary.csv`: direct 2024 versus 2025-2026 test.
- `provider_period_summary.csv`: non-overlapping provider-period strategy table.
- `provider_hypothesis_axis_shares.csv`: facet-axis distributions for the direct
  hypothesis periods.
- `provider_period_axis_shares.csv`: facet-axis distributions for 2022-2023,
  2024, 2025, and 2026 YTD.
- `long_context_benchmark_drivers.csv`: benchmark-level long-context drivers.
- `benchmark_drivers.csv`: all benchmark-level provider-period drivers with
  long-context, agentic, multimodal, and coding flags.
- `release_benchmark_mentions.csv`: mention-level resolved data.
- `facet_review_status_summary.csv`: review status mix for facet rows.
- `unresolved_mentions.csv`: currently header-only because all mentions resolve.

## Limitations

This supports a release-page showcase pattern, not a causal claim about why
Google highlighted long context or whether one model was objectively better.
Provider intent and competitive differentiation would need page prose, launch
context, and external positioning evidence.

Facet review debt is material. Check the current
[review-status summary](facet_review_status_summary.csv) for accepted,
provisional and legacy annotations. Domain and headline task mode also mix
reviewed facets with legacy seeds. Treat the shares as operationalized
indicators from the current taxonomy, not final ground truth.

The broad long-context metric includes supporting-context benchmarks such as
`EgoSchema`, `FACTS Benchmark suite`, and `GDPval`, not only pure long-context
retrieval tests. Use `long_context_primary_share` in the CSVs for the stricter
view.

Model-release rows without benchmarks are counted in `release_count` but do not
contribute to the share denominator. This is intentional because the analysis is
about the composition of named benchmark mentions when a page includes them.

## Follow-Up Analyses

- Manually review `context_pressure` for MRCR, EgoSchema, FACTS, GDPval, and
  other supporting-context labels before treating small differences as robust.
- Add release-page prose features such as "context window", token counts,
  headline placement, chart placement, and benchmark-table ordering.
- Split provider-created or private evaluations from external benchmarks to see
  whether showcase strategy increasingly depends on proprietary evals.
- Compare release-normalized shares with raw mention shares and page-level
  prominence weights.
