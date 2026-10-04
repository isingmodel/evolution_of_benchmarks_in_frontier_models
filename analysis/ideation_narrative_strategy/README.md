# Provider Narrative Strategy Prototypes

Worker 4 scope: creative analyses for benchmark-evolution data, focused on provider narrative strategy and release-page positioning. This is about benchmark mentions on public release pages, not model capability.

Run with:

```bash
.venv/bin/python analysis/ideation_narrative_strategy/analyze.py
```

The script uses `scripts/taxonomy_utils.py` / `CanonicalResolver` for exact canonicalization. It does not fuzzy match. Current run through `2026-09-30`: 791 resolved raw benchmark mentions across 55 benchmark-bearing model-release rows, with 0 unresolved mentions. Shared launch URLs can supply several model rows.

## Outputs

- `mention_inventory.csv`: resolved mention-level inventory with derived narrative flags.
- `launch_benchmark_density.csv`: benchmark mention counts by model release page.
- `provider_headline_portfolio.csv`: provider shares by `headline_task_mode`.
- `provider_signature_lift.csv`: provider-vs-global lift for headline task modes.
- `release_strategy_frames.csv`: per-release shares for static exams, work simulations, multimodal/UI evals, and specialized domains.
- `annual_strategy_frames.csv`: annual average of those release-level shares.
- `risk_private_usage_by_release.csv`: lifecycle-risk/private/provider-created measures by release.
- `risk_private_usage_by_provider.csv`: provider-level lifecycle-risk/private/provider-created measures.
- `provider_risk_portfolio.csv`: provider shares by `benchmark_lifecycle_risk`.
- `unresolved_mentions.csv`: empty in this run, with header retained.
- `provider_headline_portfolio_heatmap.png`
- `static_to_work_simulation_trend.png`
- `provider_created_or_private_escalation.png`

## Ideation Catalog

1. Provider signature portfolios: compare each provider's benchmark mix by headline task mode, then rank over/under-indexed categories by lift. Possible from current CSVs.
2. Static exams to work simulations: track the shift from static prompt-response exams to agentic, browser, terminal, codebase, and tool-use evaluations. Possible from current facets.
3. Provider-created/private benchmark escalation: measure use of provider-created, private/opaque, and explicitly internal-named benchmarks over time. Partly possible from lifecycle facets; stronger with release-page text.
4. Launch-page benchmark density: treat benchmark count as a positioning signal and control variable for "benchmark arms race" rhetoric. Possible from current CSVs.
5. Multimodal vs agentic messaging: compare modality-heavy portfolios against interaction-heavy portfolios to see whether a launch is sold as perception breadth or task execution. Possible from current facets.
6. Specialization vs generality: measure how often releases move from general exams toward law, bio/medicine, finance, cybersecurity, and other vertical work. Possible from current facets.
7. Capability claim packaging: cross-tab construct claim, task mechanism, domain, metric type, and lifecycle risk to find recurring "proof packages." Possible from current facets; rhetoric strength needs page text.
8. Benchmark novelty and churn: identify first-seen benchmarks, reused staples, and provider-specific new benchmark introductions. Possible from current CSVs.
9. Borrowed authority vs owned authority: contrast third-party/academic benchmarks with provider-authored or frontier-lab-affiliated benchmarks. Partly possible from `source_author` and `frontier_lab_author_affiliations`.
10. Internal benchmark opacity ladder: distinguish public, versioned, proprietary, partner, and explicitly internal evals. Partly possible now; release-page text needed for caveats and access claims.
11. Prominence and ordering: score whether benchmarks appear in headlines, first tables, footnotes, appendices, or late detail sections. Requires release-page text/HTML parsing.
12. Rhetorical caveat analysis: detect phrases like "internal eval," "not directly comparable," "verified," "expert," "hard," "pro," and "real-world." Requires release-page text parsing.

## Prototype Findings

The following figures come from the regenerated local outputs through `2026-09-30`. They describe benchmark-selection framing, not observed page rhetoric or model capability.

### 1. Provider Signature Portfolios

Release-normalized headline projection from `provider_headline_portfolio.csv`:

| Provider | Agentic | Generative reasoning | Multimodal perception |
| --- | ---: | ---: | ---: |
| Anthropic | 51.5% | 24.6% | 15.9% |
| Google | 51.5% | 14.7% | 21.5% |
| OpenAI | 41.0% | 23.7% | 16.6% |

Use `provider_signature_lift.csv` for comparisons with the global portfolio. These are projections over facet annotations, not stable provider identities.

### 2. Static Exams to Work Simulations

Mean release-normalized shares from `annual_strategy_frames.csv`:

| Year | Static exam | Work simulation | Specialized domain | Benchmarked rows |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 82.4% | 12.0% | 53.7% | 3 |
| 2024 | 70.7% | 18.0% | 28.0% | 8 |
| 2025 | 54.4% | 39.1% | 48.7% | 14 |
| 2026 YTD | 12.2% | 70.2% | 37.2% | 30 |

2026 YTD ends on `2026-09-30`. Static and work flags are operationalized from taxonomy facets; provider mix and review status can affect the trend. Use the README-story sensitivity outputs for confidence and extraction-granularity checks.

### 3. Provider-Created, Private, and Internal Signals

Release-normalized shares from `risk_private_usage_by_provider.csv`:

| Provider | Provider-created or private | Private/opaque | Explicit internal name |
| --- | ---: | ---: | ---: |
| Anthropic | 31.4% | 13.5% | 1.1% |
| Google | 19.9% | 8.2% | 0.0% |
| OpenAI | 42.4% | 28.8% | 4.0% |

The combined flag includes public frontier-lab-authored benchmarks and should not be interpreted as an opacity measure. See the release-level risk CSV for current examples and preserve the distinction between authorship, private access, and internal naming.

### 4. Launch-Page Benchmark Density

Current densest model-release rows from `launch_benchmark_density.csv`:

| Model-release row | Resolved raw mentions |
| --- | ---: |
| GPT-5.6 | 42 |
| GPT-6 Astra | 42 |
| GPT-5.5 | 34 |
| Claude 4.7 (Opus) | 31 |
| GPT-5.4 | 26 |

Density counts names per tracked model row. Shared launch pages and extraction coverage affect it, so it does not by itself measure rhetoric or a benchmark arms race.

## CSV-Only vs Text-Parsing Boundary

Possible with current CSVs:

- Benchmark density by release, year, and provider.
- Provider portfolio shares and lift by facet axis.
- Static vs work-simulation framing using interaction, mechanism, construct, modality, and domain facets.
- Provider-created/private/opaque lifecycle-risk accounting.
- Specialization/generalization, multimodal/agentic balance, and benchmark novelty/reuse.

Requires release-page text or HTML parsing:

- Actual rhetoric, adjectives, claim verbs, caveats, disclaimers, and "real-world" language.
- Benchmark prominence, order, table section, hero placement, footnote status, and whether a benchmark is used as a headline claim.
- Result values, score deltas, human-baseline framing, competitor comparisons, and whether metrics are normalized or cherry-picked.
- Whether private/internal benchmark descriptions imply auditability, reproducibility, or marketing opacity beyond the taxonomy label.

## Caveats

- Release-normalized weights treat each benchmark-bearing model-release row as one portfolio. This avoids letting long benchmark lists dominate provider strategy, but raw mention counts are also retained in the CSVs.
- Pages with zero benchmark mentions are included in density outputs but omitted from portfolio shares because they have no benchmark portfolio to normalize.
- Multi-label facet axes split a mention's normalized weight across labels on that axis.
- Facets with `needs_review` are included unless deprecated; this is exploratory, not a final taxonomy audit.
- `provider_created_benchmark` means authored by a frontier lab/provider or provider-affiliated source in the taxonomy. It is broader than "same provider's internal eval."
- These analyses infer positioning from benchmark selection and taxonomy facets. They do not infer actual model capability.

## Recommended Next Steps

1. Add a release-page text extraction layer with section, heading, table, footnote, and paragraph offsets.
2. Add prominence features: first benchmark mention rank, in-title/in-heading flags, table position, and whether result numbers are present.
3. Split lifecycle risk into same-provider-authored, other-provider-authored, third-party private, explicitly internal, and opaque-metric subtypes.
4. Add benchmark novelty/churn outputs: first-seen globally, first-seen by provider, reused staples, and one-off launch-specific benchmarks.
5. Pair narrative portfolios with result-text parsing only after preserving the project's boundary: this is release-page rhetoric, not capability measurement.
