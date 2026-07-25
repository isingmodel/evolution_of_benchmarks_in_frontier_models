# Review: Ideation Methodology Visuals

Reviewer: 5

Source folder reviewed: `analysis/ideation_methodology_visuals/`

## Verdict

Strong project fit, but not publication-ready as-is. The folder is valuable because it turns the project's core themes into concrete artifacts: provider framing fingerprints, projection-vs-identity structure, review debt, and a lifecycle seed table. The strongest path is to foreground a tightened provider-framing figure and the review leverage view, while treating the alluvial and lifecycle table as methodology/appendix material until they are simplified and sensitivity-tested.

The current README is appropriately careful that these are release-page benchmark mentions, not model capability. The remaining risk is mostly visual and rhetorical: phrases like "provider strategy" and "market-positioning comparison" can be read as stronger evidence of intent than the current data supports, especially with high taxonomy review debt and a small recent-window provider sample.

## Fit Score

Overall project fit: **8/10**

Current README/publication readiness: **6/10**

| Criterion | Score | Rationale |
| --- | ---: | --- |
| Fit to research question | 9 | Directly analyzes public release-page benchmark mentions and provider framing. |
| Novelty | 8 | Adds multi-facet, provider-comparative, and uncertainty-action views beyond basic trend charts. |
| Visual clarity | 6 | Review leverage is clear; provider heatmap is useful but crowded; alluvial is conceptually good but visually busy. |
| Data support | 6 | Reproducible from local CSVs, but many conclusions rely on unaccepted facet rows. |
| Reproducibility | 8 | Single script, named source CSVs, no fuzzy matching, and summary stats are included. |
| Risk of overclaiming | 5 | Manageable if renamed as framing/mentions; risky if presented as provider intent, capability, or market strategy. |
| Audience value | 8 | Gives readers a strategic comparison, a taxonomy lesson, and an actionable review roadmap. |

## What Works

- `provider_strategy_fingerprints.png` is the best story artifact. It makes provider differences legible in the project's own language: headline projection, domain, interaction pattern, context pressure, and lifecycle risk.
- `review_leverage_benchmarks.png` is the most immediately useful output. It converts uncertainty into an audit queue rather than burying review debt in a caveat.
- `domain_interaction_alluvial.png` advances the projection-vs-identity theme by showing that benchmarks should not be collapsed into one exclusive label.
- `benchmark_lifecycle_table.csv` is a good seed for a future adoption/diffusion figure because it already contains first seen, last seen, provider count, mention intensity, source author, and lifecycle-risk fields.
- `summary_stats.csv` is exactly the right reproducibility anchor: latest release date, resolved mentions, unique benchmarks, recent-window counts, and facet review status counts.
- The script normalizes each model release to equal total benchmark weight and splits multi-label facet contributions fractionally, which matches the project boundary better than raw benchmark counts alone.

## Risks

- The recent provider comparison rests on small denominators: `provider_strategy_fingerprints.csv` shows recent axis totals of 5 OpenAI releases, 3 Google releases, and 7 Anthropic releases. This is useful but volatile.
- Taxonomy dependency is high. `summary_stats.csv` shows 29 accepted facet rows out of 3,384 canonical facet rows, with 3,291 `needs_review` and 64 `legacy_seed`. Publication figures need accepted-only or high-confidence sensitivity views.
- The biggest flows in `domain_interaction_flow.csv` have low accepted-pair shares: for example, General/Commonsense -> static prompt response is about 22.4% of flow with accepted-pair share about 1.9%; Coding/Engineering -> terminal or codebase interaction is about 20.2% with accepted-pair share about 8.5%; STEM/Math -> static prompt response is about 18.3% with accepted-pair share 0%.
- The word "alluvial" visually implies movement or causality. Here the figure is a co-classification view across facet axes, not a temporal flow.
- "Provider strategy fingerprints" is a compelling title, but "strategy" can overstate intent. "Provider framing fingerprints" or "benchmark-emphasis fingerprints" would better match the data.
- The provider heatmap has crowded x-axis labels, especially in the Domain, Interaction, and Lifecycle Risk panels. It works for exploration but needs cleaner small multiples or fewer facets for a README.
- The lifecycle table depends on source-author and lifecycle-risk fields that should be audited before being used for stronger claims about benchmark hegemony or provider-created eval influence.

## Best Presentation

Use `provider_strategy_fingerprints.png` as the conceptual basis for a main README panel, but rebuild it before foregrounding. Recommended chart: a narrower "Recent Provider Framing Fingerprints" figure with only three panels from `provider_strategy_fingerprints.csv`: `headline_task_mode`, `domain`, and `interaction_pattern`. Put `OpenAI n=6`, `Google n=7`, and `Anthropic n=10` in row labels or a caption. Move `context_pressure` and `benchmark_lifecycle_risk` to an appendix table or secondary figure.

Use `review_leverage_benchmarks.png` near the methodology caveats or review-debt section. It is clear enough to use now, but a compact top-10 table from `review_leverage_benchmarks.csv` may be more README-friendly: benchmark, providers, recent weighted mentions, nonaccepted share, and review leverage. This should be framed as "what to audit next," not as a substantive finding about benchmark quality.

Do not foreground `domain_interaction_alluvial.png` in its current form. The idea is excellent, but the chart is too visually dense and can be misread as causal flow. Better publication chart: build a `domain_interaction_matrix.png` heatmap from `domain_interaction_flow.csv`, with rows as `source_domain`, columns as `target_interaction`, cell values as share, and a visual marker or subtitle for accepted-pair coverage. Keep the current alluvial as an appendix or methods visual if space allows.

Do not foreground `benchmark_lifecycle_table.csv` yet. Convert it into a lifecycle/adoption map first: x-axis `first_seen`, y-axis `provider_count` or `mentions_per_active_month`, bubble size `raw_mentions` or `model_normalized_mentions`, and color by audited `source_author` or lifecycle risk. Suggested output name: `benchmark_lifecycle_map.png`.

Use `summary_stats.csv` as a methods footnote or reproducibility box, not as a main result.

## Needed Improvements

1. Rename public-facing language from "strategy" to "framing" unless the text explicitly says this is inferred from benchmark mentions rather than provider intent.
2. Add accepted-only and high-confidence sensitivity outputs for the provider fingerprint and domain-interaction views. Suggested files: `provider_framing_fingerprints_sensitivity.csv`, `provider_framing_fingerprints_high_confidence.png`, and `domain_interaction_matrix_sensitivity.csv`.
3. Add release/sample denominators directly to figures and captions: recent window, provider release counts, resolved mention count, and unique benchmark count.
4. Simplify `provider_strategy_fingerprints.png`: fewer panels for the main README, larger labels, and less horizontal crowding.
5. Replace or supplement `domain_interaction_alluvial.png` with a matrix/table that is easier to read and less likely to imply temporal flow.
6. Keep `review_leverage_benchmarks.png`, but add a short caption explaining that orange/blue/red/green segments are facet review statuses, not benchmark quality scores.
7. Audit the high-leverage benchmarks in `review_leverage_benchmarks.csv` before using their facet labels to support strong narrative claims. Start with SWE-bench verified, MMMU / MMMU Pro, MMMLU, GPQA Diamond, AIME, Terminal-bench, HLE, and Terminal-Bench 2.0.
8. Add a weighting sensitivity appendix comparing equal-release weighting with raw mention counts, because equal-release weighting is defensible but hides differences in benchmark-list length.
9. For the lifecycle idea, generate the chart and audit `source_author` before making source-influence or hegemony claims.

## Suggested README Placement

Place this result package after the global benchmark-evolution timeline and any headline projection trend. It should not lead the README, because readers first need the project boundary and time trend.

Recommended order:

1. Scope note: release-page benchmark mentions are provider-framing signals, not capability measurements.
2. Global trend or projection chart from the main analysis.
3. Main figure: rebuilt "Recent Provider Framing Fingerprints" using `provider_strategy_fingerprints.csv`.
4. Method callout: projection-vs-identity explanation using a new domain-interaction matrix derived from `domain_interaction_flow.csv`.
5. Caveat/action box: `review_leverage_benchmarks.png` or a top-10 table from `review_leverage_benchmarks.csv`.
6. Appendix/future work: `benchmark_lifecycle_table.csv`, current `domain_interaction_alluvial.png`, and sensitivity views.

Strongest recommendation: **make review debt visible in the main README, but do not publish the provider or domain-interaction story without accepted-only sensitivity checks.**
