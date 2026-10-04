# Frontier Lab Benchmark Hegemony Review

These are methodological review notes retained during the data refresh through `2026-09-30`. Numeric findings should be read from the linked regenerated CSVs; design scores and recommendations are qualitative review judgments.

## Verdict

This is a strong supporting analysis, but it should be framed more cautiously than the folder title suggests. It fits the project because it studies which benchmarks frontier providers choose to foreground on public release pages, and it adds a useful "borrowed benchmark authority" lens to the existing benchmark-evolution story.

The result is not ready to carry a main README headline about "hegemony" without edits. The refreshed combined inclusive share is nearly flat, while provider-specific and affiliation-only comparisons differ. That supports a mixed evaluation-vocabulary analysis rather than one rising or fading hegemony claim. It does not establish causal influence, true benchmark adoption, internal evaluation practice, or model capability.

## Fit Score

Overall project-fit score: **7.5/10**.

README-readiness now: **6.5/10**. Publication-readiness now: **5/10**.

The concept is on-theme and the outputs are reproducible from local CSVs, but the public-facing version needs release-normalized shares, a cleaner main visual/table, and a manual audit of high-impact authorship and affiliation fields.

## What Works

- The analysis directly engages the repository's themes: benchmark evolution, provider strategy, benchmark hegemony, and uncertainty around taxonomy fields.
- The unit of analysis is correctly bounded as release-page benchmark mentions, not capability or all eval usage.
- The period comparison tests the proposed hegemony narrative rather than treating it as an assumption.
- `openai_adoption_period_comparison.csv` exposes inclusive source/affiliation counts, affiliation-only counts, and their denominators.
- `provider_period_author_shares.csv` and `provider_period_author_mix.png` make an important balancing point visible: neutral / academic / vendor benchmarks remain the majority in every provider-period cell.
- `high_signal_benchmarks.csv` provides concrete examples that make the abstract claim easier to understand, especially `SWE-bench verified`, `MMMLU`, `BrowseComp`, `HumanEval`, `GSM8K`, `SimpleQA`, `Terminal-Bench 2.0`, `HLE (Humanity's Last Exam)`, and `MRCR v2`.
- The README already includes unusually helpful caveats about release-page lag, multi-affiliated benchmarks, and source-author versus affiliation differences.

## Risks

- The word "hegemony" is analytically interesting but rhetorically risky. Readers may infer causal control over the field, when the data only shows public release-page mentions.
- The main period comparison uses raw mention counts. This can be distorted by release pages with very long benchmark tables, especially in 2025-2026.
- The core comparison depends on authorship and affiliation labels. Join current benchmark `review_status` to the enriched mentions before making strong claims.
- `source_author` and `frontier_lab_author_affiliations` sometimes tell different stories. `MRCR` and `MRCR v2` have OpenAI as `source_author` but Google/DeepMind affiliation; `GPQA` has Anthropic in `source_author` but no frontier-lab affiliation; `HLE` is multi-affiliated across several labs.
- Inclusive results can depend on multi-affiliated or ambiguous benchmarks. Recompute a strict affiliation-only or single-lab sensitivity before presenting it; historical strict-sensitivity figures should not be carried forward.
- `benchmark_first_adoption_lags.csv` is useful for exploration but should not be foregrounded. It measures first mention inside this dataset, not benchmark publication or actual first use.
- Lifecycle-risk claims are valuable but should remain secondary until `benchmark_lifecycle_risk` review debt is reduced.

## Best Presentation

Use this as a **short narrative callout plus compact table**, not as the main visual spine of the project.

Best existing file to foreground:

- `analysis/frontier_lab_benchmark_hegemony/openai_adoption_period_comparison.csv`

Recommended main table: derive current provider-group counts and shares from `openai_adoption_period_comparison.csv`. Show both periods, their mention denominators, and an affiliation-only sensitivity alongside the inclusive source-or-affiliated measure.

Use `analysis/frontier_lab_benchmark_hegemony/provider_period_author_mix.png` only as an appendix or secondary figure. It is good for showing that neutral benchmarks remain the majority, but it does not make the headline OpenAI-adoption finding easy to see.

Use `analysis/frontier_lab_benchmark_hegemony/high_signal_benchmarks.csv` as an examples table in an appendix or hover/caption material. Suggested rows: `SWE-bench verified`, `MMMLU`, `BrowseComp`, `HumanEval`, `GSM8K`, `SimpleQA`, `Terminal-Bench 2.0`, `HLE (Humanity's Last Exam)`, `MRCR`, and `MRCR v2`.

Use `analysis/frontier_lab_benchmark_hegemony/cross_lab_adoption_matrix.csv` as appendix evidence only, or remake it as a heatmap for 2025-2026. The table is non-exclusive because multi-affiliated benchmarks count once for each target lab group, so it needs a prominent note.

Recommended better chart:

- Create `openai_adoption_period_slope.png`: a slope chart with Anthropic, Google, and Anthropic+Google, showing 2023-2024 versus 2025-2026 OpenAI source-or-affiliated share.
- Add a second, lighter line or annotation for strict OpenAI-only affiliation excluding multi-lab/ambiguous cases. This makes the robustness story visible without overclaiming.

## Needed Improvements

- Add release-normalized versions of the main shares, where each benchmark-bearing release page contributes equal total weight. This would align with the stronger normalization strategy used elsewhere in the project.
- Add sensitivity outputs that separate:
  - `source_author` contains OpenAI
  - `frontier_lab_author_affiliations` contains OpenAI
  - strict OpenAI-only affiliation
  - source-or-affiliated excluding `HLE`, `MRCR`, and `MRCR v2`
- Manually audit the high-impact `legacy_seed` benchmark authorship and affiliation rows before publication, especially `SWE-bench verified`, `MMMLU`, `HumanEval`, `GSM8K`, `BrowseComp`, `GraphWalks`, `SimpleQA`, `MRCR`, and `MRCR v2`.
- Add benchmark-family grouping for SWE-bench, MRCR, GPQA, MMLU/MMMLU, Terminal-Bench, and BrowseComp variants so version churn does not masquerade as independent adoption.
- Rename or reframe the public-facing section from "Benchmark Hegemony" to something less causal, such as "Borrowed Benchmark Authority" or "Lab-Authored Benchmarks in the Shared Evaluation Vocabulary."
- Keep `benchmark_first_adoption_lags.csv` out of the main README until benchmark publication dates or external citation metadata are added.
- Add a small confidence note to any table that uses authorship/affiliation fields, including counts by `review_status`.

## Suggested README Placement

Place this after the current "Battle for Hegemony" discussion as a caveated correction, not as a top-level hero chart.

Suggested framing:

> Through 2026-09-30, Anthropic and Google's combined OpenAI-source-or-affiliated mention share is nearly flat between 2023-2024 and 2025-2026. Individual providers and affiliation-only comparisons differ. Neutral academic and vendor benchmarks remain the majority by affiliation classification; these patterns describe public benchmark vocabulary, not causal influence or capability.

Recommended placement shape:

- Main README: one paragraph plus the compact table from `openai_adoption_period_comparison.csv`.
- Appendix or analysis page: `provider_period_author_mix.png`, `cross_lab_adoption_matrix.csv`, and selected rows from `high_signal_benchmarks.csv`.
- Not foregrounded yet: `benchmark_first_adoption_lags.csv`, unless real benchmark publication dates are added.
