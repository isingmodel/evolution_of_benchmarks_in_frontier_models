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

Local run summary: 422 release-page benchmark mentions resolved to 133 canonical benchmarks. The latest modeled release date is 2026-04-23. In the facet table, 999 rows are `needs_review`, 184 are `legacy_seed`, and 83 are `accepted`, so uncertainty should remain visible in publication charts.

## What The Prototypes Show

### Provider Strategy Fingerprints

`provider_strategy_fingerprints.png` uses the latest 365-day window, 2025-04-23 through 2026-04-23. Each model release receives equal total weight; multi-label facet axes split a benchmark mention equally across labels.

Useful readouts:

- Anthropic is most agentic-coded in headline projection: 53% Agentic, 35% Generative Reasoning.
- Google is more general-reasoning framed in this window: 49% Generative Reasoning, 23% Agentic.
- OpenAI is split between Agentic and Generative Reasoning: 43% and 40%.
- Coding/Engineering is highest for Anthropic at 34%, while Google leans General/Commonsense at 47%.
- Terminal/codebase interaction is a visible differentiator: Anthropic 25%, OpenAI 21%, Google 10%.

Recommendation: use this as the main "provider strategy" panel after the global trend charts. It turns the dataset into a market-positioning comparison without claiming model ability.

### Domain-To-Interaction Alluvial

`domain_interaction_alluvial.png` shows how multi-facet annotations prevent overclaiming. Instead of saying a benchmark "is" agentic, the chart asks which domains are being projected into which interaction patterns.

Top recent flows:

- General/Commonsense -> static prompt response: 22.4%.
- Coding/Engineering -> terminal or codebase interaction: 20.2%.
- STEM/Math -> static prompt response: 18.3%.
- General/Commonsense -> single-turn tool use: 5.7%.

Recommendation: place this immediately after any headline projection chart. It visually teaches the reader that headline categories are views over a multi-facet table, not exclusive benchmark identities.

### Review Leverage

`review_leverage_benchmarks.png` ranks benchmarks by recent model-normalized mention weight multiplied by the share of active facet rows that are not `accepted`.

Top review targets:

- `SWE-bench verified`
- `MMMU / MMMU Pro`
- `MMMLU`
- `GPQA Diamond`
- `AIME`
- `Terminal-bench`
- `HLE (Humanity's Last Exam)`
- `Terminal-Bench 2.0`

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
10. **Projection sensitivity bands**: plot headline trends under three inclusion rules: all facets, accepted-only facets, and accepted plus legacy seed. This would show how much the story depends on review debt.
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
- The latest-window charts use 365 days ending on 2026-04-23.
- Many facet rows are still `needs_review` or `legacy_seed`; publication charts should offer accepted-only or uncertainty-aware variants.
- Source-author labels and lifecycle-risk labels inherit the current local taxonomy and should be audited before strong claims.
