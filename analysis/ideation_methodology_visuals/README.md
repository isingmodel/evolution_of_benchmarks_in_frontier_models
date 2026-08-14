# Ideation: Methodology Visuals and Creative Analyses

This folder prototypes additional analysis ideas for the benchmark-evolution project. The project studies benchmark mentions on public frontier-model release pages: it is about provider framing and benchmark selection, not direct model capability.

Generated with:

```bash
.venv/bin/python analysis/ideation_methodology_visuals/analyze.py
```

The script uses `scripts/taxonomy_utils.py` and `CanonicalResolver` against `data/benchmarks.csv` plus `data/benchmark_aliases.csv`. It does not fuzzy match mentions.

## Prototype Outputs

| Output | Purpose |
| --- | --- |
| `provider_strategy_fingerprints.png` / `.csv` | Recent provider-by-facet heatmaps for strategy contrast. |
| `domain_interaction_alluvial.png` / `domain_interaction_flow.csv` | Alluvial flow from domain facets to interaction-pattern facets. |
| `review_leverage_benchmarks.png` / `.csv` | Prioritized uncertainty view: which high-impact mentioned benchmarks have unaccepted facet rows. |
| `benchmark_lifecycle_table.csv` | Seed table for a future benchmark lifecycle/adoption map. |
| `summary_stats.csv` | Reproducibility stats for the local data run. |

Local run summary: 582 release-page benchmark mentions resolved to 207 canonical benchmarks. The latest modeled release date is 2026-08-13. The canonical facet frame contains 3,339 rows marked `needs_review`, 42 `legacy_seed` rows, and 29 `accepted` rows out of 3,410, so uncertainty should remain visible in publication charts.

## What The Prototypes Show

### Provider Strategy Fingerprints

`provider_strategy_fingerprints.png` uses the latest 365-day window, 2025-08-13 through 2026-08-13. Each model release receives equal total weight; multi-label facet axes split a benchmark mention equally across labels.

Useful readouts:

- Anthropic is most agentic-coded in headline projection at 69%.
- Google is 60% Agentic and 18% Multimodal Perception in this window.
- OpenAI is 65% Agentic, with Generative Reasoning and Multimodal Perception each near 12%.
- Coding/Engineering is highest for OpenAI at 43%, followed by Google at 33% and Anthropic at 30%.
- Terminal/codebase interaction is 12% for Google, 10% for Anthropic, and 7% for OpenAI; environment interaction is the larger work-like differentiator.

Recommendation: use this as the main "provider strategy" panel after the global trend charts. It turns the dataset into a market-positioning comparison without claiming model ability.

### Domain-To-Interaction Alluvial

`domain_interaction_alluvial.png` shows how multi-facet annotations prevent overclaiming. Instead of saying a benchmark "is" agentic, the chart asks which domains are being projected into which interaction patterns.

Top recent flows:

- Coding/Engineering -> environment interaction: 16.5%.
- General/Commonsense -> static prompt response: 9.1%.
- Coding/Engineering -> terminal or codebase interaction: 8.4%.
- STEM/Math -> static prompt response: 8.2%.

Recommendation: place this immediately after any headline projection chart. It visually teaches the reader that headline categories are views over a multi-facet table, not exclusive benchmark identities.

### Review Leverage

`review_leverage_benchmarks.png` ranks benchmarks by recent model-normalized mention weight multiplied by the share of active facet rows that are not `accepted`.

Top review targets:

- `OSWorld-Verified`
- `SWE-bench Pro`
- `HLE (Humanity's Last Exam)`
- `SWE-bench verified`
- `MRCR v2`
- `MMMLU`
- `GPQA Diamond`
- `GDPval-AA v2`

Recommendation: include this near the methodology caveats or as a review roadmap. It makes uncertainty actionable: reviewers should not audit randomly; they should focus on high-leverage benchmarks that shape current claims.

## Idea Catalog

1. **Domain-to-interaction alluvial**: flow from `domain` to `interaction_pattern`, weighted by release-page mentions. This makes projection vs identity tangible.
2. **Provider strategy fingerprints**: heatmap rows for providers and columns for selected facet labels, with a recent-window toggle.
3. **Review leverage Pareto**: rank benchmarks by current influence times unaccepted facet share.
4. **Benchmark lifecycle map**: x-axis first mention, y-axis provider spread or mentions per active month, bubble size by raw mentions, color by source author or lifecycle risk.
5. **Source-author influence map**: track whether public release pages foreground academia, OpenAI, Google, Anthropic, Scale AI, Artificial Analysis, or other benchmark authors.
6. **Benchmark family diffusion**: group variants such as SWE-bench, Terminal-Bench, BrowseComp, ARC-AGI, MMMU, MMLU, and GPQA; show how families split into variants over time.
7. **Novelty and churn index**: per release, show share of first-time benchmark mentions, returning mentions, and deprecated/no-longer-mentioned benchmarks.
8. **Provider contrast small multiples**: rolling facet shares per provider, not just global rolling trends.
9. **Timeline annotation layer**: annotate releases where the public framing shifts: long context surge, multimodal plateau, coding-agent expansion, professional-task benchmarks.
10. **Projection sensitivity bands**: plot headline trends under three inclusion rules: all active facets, accepted-only facets, and high-confidence facets. This would show how much the story depends on review debt.
11. **Internal/private benchmark exposure index**: track `private_or_opaque_eval`, internal benchmark naming, and provider-created benchmark mentions over time.
12. **Co-mention network**: connect benchmarks that appear on the same release page; cluster into "reasoning suite", "coding-agent suite", "multimodal suite", and "professional workflow suite".

## Recommended Dashboard Story

1. **Scope note**: release-page benchmark mentions are provider-framing signals, not capability measurements.
2. **Global timeline**: keep the existing evolution timeline to orient the reader.
3. **Headline growth chart**: keep the readable projection, but label it explicitly as a projection.
4. **Multi-facet correction**: add the domain-to-interaction alluvial to show how benchmark identity is multi-dimensional.
5. **Provider strategy**: add provider strategy fingerprints for the most recent 365-day period.
6. **Lifecycle/adoption**: convert `benchmark_lifecycle_table.csv` into a bubble lifecycle map; annotate fast diffusers such as MMMLU, HLE, TAU-2 bench, Terminal-Bench 2.0, Scale MCP-Atlas, MRCR v2, and SWE-bench Pro.
7. **Source influence**: add source-author influence or provider-created benchmark share to support the "battle for hegemony" thesis.
8. **Uncertainty and review debt**: end with review leverage plus the existing review debt chart, so caveats are not hidden in prose.
9. **Method appendix**: document exact resolution, equal-release weighting, multi-label fractional allocation, and accepted-only sensitivity views.

## Caveats

- The prototypes are local-data only; no web lookup was used.
- The charts analyze public release-page mentions, not benchmark scores, model capability, or scientific validity.
- A model release with more benchmark mentions is normalized to the same total weight as another release with fewer mentions.
- Facet labels are fractional when a benchmark has multiple labels on the same axis.
- The latest-window charts use 365 days ending on 2026-08-13.
- Many facet rows are still `needs_review`; publication charts should offer accepted-only or uncertainty-aware variants.
- Source-author labels and lifecycle-risk labels inherit the current local taxonomy and should be audited before strong claims.
