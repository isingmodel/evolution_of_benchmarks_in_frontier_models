# Analysis Synthesis

This synthesis collects the five subagent explorations plus the common data snapshot. The shared caveat remains central: these analyses measure benchmark mentions on public release pages, not hidden evaluations or model capability.

## Verification

All analysis scripts were rerun from the repository root with `.venv/bin/python`, and the source data validator still passes:

```bash
.venv/bin/python scripts/validate_data.py
```

Current baseline:

- 557 resolved benchmark mentions
- 195 canonical benchmarks mentioned at least once
- 3 providers: OpenAI, Google, Anthropic
- Latest modeled release date: 2026-07-24

## Main Findings

### 1. OpenAI benchmark hegemony did not fade in the simple sense

The first hypothesis was framed as: if OpenAI's early benchmark hegemony weakened as Google and Anthropic became more competitive, then Google/Anthropic release pages should use fewer OpenAI-authored or OpenAI-affiliated benchmarks in 2025-2026 than in 2023-2024.

The current data shows the opposite:

- Anthropic+Google OpenAI-authored-or-affiliated mentions rose from 11/76 in 2023-2024 (14.5%) to 53/255 in 2025-2026 (20.8%).
- Google drove most of the increase, from 8.8% to 24.7%.
- Anthropic stayed nearly flat, from 19.0% to 18.8%.

Better interpretation: OpenAI's benchmark vocabulary became more shared competitive currency even as the field grew more competitive. The more nuanced hegemony story is not "less OpenAI influence"; it is "more shared use of OpenAI-linked benchmarks alongside more self-authored/private/provider-created benchmarks."

Primary folder: `analysis/frontier_lab_benchmark_hegemony/`.

### 2. Google 2024 long-context showcase is strongly visible

The second hypothesis is supported descriptively. Using release-normalized benchmark shares:

- Google 2024 broad long-context share: 39.3%.
- OpenAI 2024 broad long-context share: 2.4%.
- Anthropic 2024 broad long-context share: 5.8%.

The signal is mostly Gemini 1.5 and `Needle In A Haystack`, with smaller 2024 support from Gemini 2.0 benchmarks such as `MRCR` and `EgoSchema`.

In 2025-2026, the long-context gap narrows:

- Google: 18.0%.
- OpenAI: 23.3%.
- Anthropic: 13.5%.

The later competition axis shifts more toward agentic/coding showcases. Anthropic has the strongest 2025-2026 agentic share at 61.8%, followed by Google at 54.7%.

Primary folder: `analysis/provider_strategy_long_context/`.

### 3. The strongest new story may be "exam to work simulation"

The narrative-strategy prototype found a major shift from static benchmark exams toward work simulations:

- Mean static-exam share falls from 82.4% in 2023 to 18.7% in 2026 YTD.
- Mean work-simulation share rises from 12.0% in 2023 to 18.0% in 2024, 39.1% in 2025, and 73.3% in 2026 YTD.
- Specialized-domain share is 46.2% in 2026 YTD.

This gives the project a strong broader thesis: frontier release-page benchmarking is moving from "can pass canonical exams" toward "can operate inside work environments."

Primary folder: `analysis/ideation_narrative_strategy/`.

### 4. Provider strategy fingerprints are publication-ready candidates

The recent-window fingerprint prototype suggests a clear provider contrast:

- Anthropic is most agentic-coded in headline projection and terminal/codebase interaction.
- Google leans more general-reasoning, multimodal, and knowledge retrieval.
- OpenAI is split between agentic and generative reasoning, with a smaller but distinctive constraint/control signal.

Recommended use: put this panel after the global trend charts to turn the dataset into a provider-positioning comparison without claiming capability differences.

Primary folder: `analysis/ideation_methodology_visuals/`.

### 5. Benchmark diffusion can become a new analysis section

The network-dynamics prototype found:

- 64 cross-provider benchmark cascades.
- 131 benchmarks remain single-provider in observed release pages.
- Latest cumulative portfolio similarity is highest for Anthropic-OpenAI at 0.282, followed by Anthropic-Google at 0.278 and Google-OpenAI at 0.258.
- Fast cascades include `MMMLU` (Anthropic to OpenAI in 2 days), `Terminal-Bench 2.0` (Google to Anthropic in 6 days), and `OfficeQA Pro` (Anthropic to OpenAI in 7 days).

This can support a "benchmark vocabulary diffusion" section, especially once benchmark publication dates are added.

Primary folder: `analysis/ideation_network_dynamics/`.

## Suggested Next Story Structure

1. Scope note: release-page benchmark mentions are public framing signals.
2. Existing global timeline and headline trend charts.
3. Add Google 2024 long-context case study as a concrete provider strategy example.
4. Add "exam to work simulation" as the major cross-provider historical shift.
5. Add provider strategy fingerprints for the latest 365-day window.
6. Add frontier-lab benchmark hegemony/source-author analysis.
7. Add benchmark diffusion/cascade analysis.
8. End with uncertainty: review leverage and review debt.

## Highest-Leverage Follow-Ups

1. Review high-impact facet rows before making strong claims: `SWE-bench verified`, `MMMU / MMMU Pro`, `MMMLU`, `GPQA Diamond`, `AIME`, `Terminal-bench`, `HLE`, and `Terminal-Bench 2.0`.
2. Add accepted-only versus all-facets sensitivity charts.
3. Add benchmark publication dates to replace release-page first-mention lag with real adoption lag.
4. Add release-page text/prominence features: heading placement, table order, footnote status, benchmark result presence, and claim language.
5. Group benchmark families such as SWE-bench, MRCR, GPQA, MMLU/MMMLU, Terminal-Bench, ARC-AGI, and BrowseComp to separate family adoption from version churn.
