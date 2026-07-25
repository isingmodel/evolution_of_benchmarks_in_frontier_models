# Ideation Narrative Strategy Review

## Verdict

This is one of the better-fitting exploratory outputs for the project. It stays mostly inside the repository's actual question: which benchmarks providers choose to mention on public launch pages, and how that selection changes over time. The strongest result is the static-exam to work-simulation transition, because it directly supports the project's benchmark-evolution theme without requiring claims about model capability.

README-worthy after small edits. Publication-worthy only after tightening denominators, labeling 2026 as year-to-date, and separating provider-created benchmarks from private or opaque benchmarks.

## Fit Score

**8/10 for project fit; 7/10 for current presentation readiness.**

The result aligns well with provider narrative strategy, benchmark evolution, launch-page benchmark density, and the shift from static exams to work simulations. Its main weakness is that several interpretations use narrative language while the current data only captures benchmark names and taxonomy facets, not release-page prominence, wording, caveats, score deltas, or placement.

## What Works

- `static_to_work_simulation_trend.png` is the clearest main finding. It shows benchmarked release pages moving from static exam framing toward work-simulation framing, with the supporting values in `annual_strategy_frames.csv`.
- `annual_strategy_frames.csv` has a readable denominator: release-normalized shares averaged across benchmarked release pages. The explicit counts by year are useful: 3 benchmarked pages in 2023, 8 in 2024, 14 in 2025, and 7 in 2026.
- `provider_headline_portfolio.csv` and `provider_signature_lift.csv` give a compact provider-positioning lens: Anthropic over-indexes on agentic benchmarks, Google on multimodal/knowledge retrieval, and OpenAI on broad reasoning with a small constraint/control signal.
- `launch_benchmark_density.csv` is useful because it includes zero-benchmark pages as well as dense benchmark-list pages. That makes it a good support file for the "benchmark density as launch-page packaging" theme.
- The script is reproducible and scoped: `analyze.py` uses the canonical resolver, emits all CSVs and PNGs, and reports 557 resolved mentions across 41 benchmarked release pages with 0 unresolved mentions.
- The README's caveats are unusually helpful. It already says provider-created does not mean same-provider or private, and it preserves the project boundary that this is not a model capability analysis.

## Risks

- **Overclaiming narrative intent:** The current outputs infer positioning from benchmark selection. They do not observe actual rhetoric, page prominence, headline placement, caveats, or score framing. Use "benchmark-selection framing" unless a text/HTML extraction layer is added.
- **2026 is year-to-date:** The trend chart shows 2026 as a normal annual point, but the data only runs through the latest listed release, Claude 5 Opus on 2026-07-24. The chart should label this as `2026 YTD` and show `n=16` benchmarked release pages.
- **Provider-created/private is too blended:** `provider_created_or_private_escalation.png` combines public frontier-lab-created benchmarks with private/opaque evaluations. This can look like an opacity claim even though much of the signal is provider-authored but public benchmark authority.
- **Small provider samples:** Provider signatures are based on 12 Anthropic, 7 Google, and 13 OpenAI benchmarked release pages. This is enough for an exploratory portfolio cut, not enough for a strong provider-identity claim.
- **Release mix affects year trends:** Later years have more releases and more benchmark-dense pages. The release-normalized method is reasonable, but a provider-balanced sensitivity view would make the trend more defensible.
- **Taxonomy dependency:** The static/work distinction depends on facet rules for interaction patterns, task mechanisms, and construct claims. The output should expose a small "top contributing benchmarks" table so readers can see what is driving the category shift.
- **Chart polish:** `provider_headline_portfolio_heatmap.png` is understandable but less persuasive than a table because it invites comparison across tiny shares and has cramped axis/colorbar labeling.

## Best Presentation

Foreground `static_to_work_simulation_trend.png`, revised with clearer labeling. The caption should say: "Mean share of benchmark mentions per benchmarked release page; 2026 is year-to-date through 2026-07-24." Pair it with a tiny table sourced from `annual_strategy_frames.csv` showing static exam share, work simulation share, specialized domain share, and release-page count.

Use `provider_signature_lift.csv` as a compact supporting table, not as a standalone major chart. Recommended table columns: `Provider`, `highest-lift task mode`, `share`, `lift_vs_global`, and `raw_mentions`. This is more README-friendly than the full heatmap.

Create a new density chart from `launch_benchmark_density.csv`: a lollipop or bar-over-time chart of `resolved_benchmark_mentions` by release page, including zero-mention launches. This would support the "benchmark arms race / benchmark density" idea better than a paragraph.

Keep `provider_created_or_private_escalation.png` out of the main README for now. Use `risk_private_usage_by_provider.csv`, `provider_risk_portfolio.csv`, and `risk_private_usage_by_release.csv` in an appendix or caveated callout titled something like "Frontier-lab-authored and opaque benchmark signals." Do not call this "private escalation" until provider-authored, same-provider, private, opaque, and explicitly internal benchmarks are split.

Use `mention_inventory.csv` and `unresolved_mentions.csv` as reproducibility appendix artifacts only.

## Needed Improvements

- Regenerate `static_to_work_simulation_trend.png` with `2026 YTD`, `n=` labels, and preferably direct point labels for the main static/work lines.
- Add a provider-balanced trend table or chart so 2025/2026 movement is not just a byproduct of changing provider/release mix.
- Add a top-contributors table for the work-simulation rise: benchmark name, first release year seen, task-mode/facet reason, and raw mention count.
- Split the current provider-created/private metric into same-provider-authored, other-frontier-lab-authored, third-party public, explicitly private/opaque, explicitly internal-named, and unclear-metric/version-risk categories.
- Add a release-page text layer before making claims about rhetoric: heading/table position, first mention rank, whether a score appears, whether the benchmark is in a headline/table/footnote, and nearby caveat wording.
- Add a density visualization from `launch_benchmark_density.csv` rather than relying on prose.
- Rename or caption charts so they describe launch-page benchmark mentions, not model performance.
- Add a short methods note explaining release-normalized weights and multi-label splitting wherever the figures appear.

## Suggested README Placement

Put this after the existing methodology discussion and before broader observations, as a new section titled **From Exams to Work Simulations**. Use the revised `static_to_work_simulation_trend.png` as the main figure and include a short paragraph that says benchmarked launch pages increasingly foreground work-like environments such as codebases, terminals, browsers, tools, finance, legal, bio, and office workflows.

Follow with a small **Provider Portfolio Signatures** callout table sourced from `provider_signature_lift.csv`. Keep it exploratory and avoid saying providers "are" agentic or multimodal; say their release-page benchmark portfolios "over-index" on those modes.

Place the provider-created/private material in an appendix or an **Uncertainty and Benchmark Authority** section, not the main storyline. It is valuable, but its current blended metric needs one more pass before it can carry a headline claim.
