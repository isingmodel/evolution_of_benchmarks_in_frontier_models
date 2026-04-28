# Provider Narrative Strategy Prototypes

Worker 4 scope: creative analyses for benchmark-evolution data, focused on provider narrative strategy and release-page positioning. This is about benchmark mentions on public release pages, not model capability.

Run with:

```bash
.venv/bin/python analysis/ideation_narrative_strategy/analyze.py
```

The script uses `scripts/taxonomy_utils.py` / `CanonicalResolver` for exact canonicalization. It does not fuzzy match. Current run: 422 resolved benchmark mentions across 32 benchmarked release pages, with 0 unresolved mentions.

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

All providers still center generative reasoning in their benchmark portfolios, but the signatures differ:

- Anthropic: 48.7% generative reasoning, 36.1% agentic. Agentic is 1.42x the global share.
- Google: 59.0% generative reasoning, 22.3% multimodal perception. Multimodal is 1.39x the global share; knowledge retrieval is 2.34x, but from a small 6.4% share.
- OpenAI: 54.9% generative reasoning, 22.4% agentic, 14.8% multimodal. Constraint/safety/control is small at 4.7%, but 1.87x global share.

Interpretation: a reasonable first narrative cut is Anthropic as agentic/workflow-heavy, Google as multimodal/knowledge-heavy, and OpenAI as broad reasoning with a small but distinctive constraint/control signal.

### 2. Static Exams to Work Simulations

The release-page benchmark mix shows a clear shift toward work simulations:

- Mean static-exam share peaks at 43.4% in 2024, then falls to 16.2% in 2026.
- Mean work-simulation share rises from 0.0% in 2023 to 7.5% in 2024, 32.0% in 2025, and 51.1% in 2026.
- Specialized-domain share rises to 24.4% in 2026.

Top work-simulation-heavy releases include GPT-5.3-Codex at 85.7%, Claude 4.7 Opus at 64.5%, Claude 4.6 Opus at 61.9%, and Claude 4.5 Opus at 61.5%.

Interpretation: benchmark rhetoric appears to be moving from "can pass the exam" toward "can operate in work environments," especially coding, tools, terminal, browser, finance, legal, bio, and office-like workflows.

### 3. Provider-Created, Private, and Internal Signals

Provider-created or private/opaque benchmark share is high and similar across providers:

- Anthropic: 39.9% provider-created/private share; 2.1% private/opaque only; 0.5% explicitly internal-named.
- Google: 39.6% provider-created/private share; 3.9% private/opaque only; 0.0% explicitly internal-named.
- OpenAI: 35.5% provider-created/private share; 3.2% private/opaque only; 1.0% explicitly internal-named.

Recent releases show stronger opaque/internal signals. GPT-5.3-Codex has 57.1% provider-created/private share; Gemini 3.1 Pro has 50.0%; Claude 4.7 Opus has 45.2%; GPT-5.5 has 38.2%. Explicit internal-named benchmarks appear only in the most recent releases here: GPT-5.4, Claude 4.7 Opus, and GPT-5.5.

Interpretation: the strongest signal is not many explicitly private benchmarks, but a growing reliance on frontier-lab/provider-created benchmark authority. This should be framed carefully because `provider_created_benchmark` does not necessarily mean same-provider or private.

### 4. Launch-Page Benchmark Density

Benchmark density also looks like a strategic signal:

- 2024 benchmarked releases average 10.5 resolved benchmark mentions.
- 2025 benchmarked releases average 11.2.
- 2026 benchmarked releases average 20.9.

The densest pages are GPT-5.5 with 34 mentions, Claude 4.7 Opus with 31, GPT-5.4 with 26, Gemini 3.0 and Claude 4.6 Opus with 21 each, and GPT-5.2 with 20.

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
