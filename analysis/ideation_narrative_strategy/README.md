# Provider Narrative Strategy Prototypes

Worker 4 scope: creative analyses for benchmark-evolution data, focused on provider narrative strategy and release-page positioning. This is about benchmark mentions on public release pages, not model capability.

Run with:

```bash
.venv/bin/python analysis/ideation_narrative_strategy/analyze.py
```

The script uses `scripts/taxonomy_utils.py` / `CanonicalResolver` for exact canonicalization. It does not fuzzy match. Current run: 582 resolved benchmark mentions across 43 benchmarked release pages, with 0 unresolved mentions.

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

### 1. Provider Signature Portfolios

Provider portfolios now lean more agentic under the runtime headline projection, but the signatures differ:

- Anthropic: 47.9% agentic and 27.4% generative reasoning. Agentic is 1.11x the global share.
- Google: 42.5% agentic and 25.4% multimodal perception. Knowledge retrieval is 2.16x the global share, from a 13.1% share.
- OpenAI: 38.4% agentic, 28.9% generative reasoning, and 19.7% multimodal. Generative reasoning is 1.17x the global share.

Interpretation: a reasonable first narrative cut is Anthropic as agentic/workflow-heavy, Google as multimodal/knowledge-heavy, and OpenAI as broad reasoning with a small but distinctive constraint/control signal.

### 2. Static Exams to Work Simulations

The release-page benchmark mix shows a clear shift toward work simulations:

- Mean static-exam share falls from 82.4% in 2023 to 70.7% in 2024, 54.4% in 2025, and 16.0% in 2026 YTD.
- Mean work-simulation share rises from 12.0% in 2023 to 18.0% in 2024, 39.1% in 2025, and 73.5% in 2026 YTD.
- Specialized-domain share is 42.4% in 2026 YTD.

Top work-simulation-heavy releases include Gemini 3.6 Flash, Gemini 3.5 Flash Cyber, and GPT-5.3-Codex at 100%, followed by Claude 4.8 Opus at 90.9%, Claude 5 Sonnet at 88.9%, and GPT-5.6-Cyber at 80.0%.

Interpretation: benchmark rhetoric appears to be moving from "can pass the exam" toward "can operate in work environments," especially coding, tools, terminal, browser, finance, legal, bio, and office-like workflows.

### 3. Provider-Created, Private, and Internal Signals

Provider-created or private/opaque benchmark share is high but differentiated across providers:

- Anthropic: 34.6% provider-created/private share; 14.6% private/opaque only; 1.0% explicitly internal-named.
- Google: 24.0% provider-created/private share; 8.7% private/opaque only; 0.0% explicitly internal-named.
- OpenAI: 40.6% provider-created/private share; 24.3% private/opaque only; 1.8% explicitly internal-named.

Recent releases show stronger opaque/internal signals. GPT-5.6-Cyber has 100.0% provider-created/private share; GPT-5.3-Codex has 71.4%; Gemini 3.5 Flash Cyber has 66.7%; and Claude 4.7 Opus has 61.3%. Explicit internal-named benchmarks appear on several recent pages, including GPT-5.4, Claude 4.7 Opus, GPT-5.5, and GPT-5.6.

Interpretation: the strongest signal is not many explicitly private benchmarks, but a growing reliance on frontier-lab/provider-created benchmark authority. This should be framed carefully because `provider_created_benchmark` does not necessarily mean same-provider or private.

### 4. Launch-Page Benchmark Density

Benchmark density also looks like a strategic signal:

- 2024 benchmarked releases average 10.5 resolved benchmark mentions.
- 2025 benchmarked releases average 12.0.
- 2026 benchmarked releases average 17.0.

The densest pages are GPT-5.6 with 42 mentions, GPT-5.5 with 34, Claude 4.7 Opus with 31, GPT-5.4 with 26, and Claude 5 Fable/Mythos with 25.

Interpretation: later releases increasingly package capability claims as broad benchmark portfolios rather than a few canonical scores.

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

- Release-normalized weights treat each benchmarked release page as one portfolio. This avoids letting long benchmark lists dominate provider strategy, but raw mention counts are also retained in the CSVs.
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
