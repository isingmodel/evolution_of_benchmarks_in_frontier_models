# Frontier Lab Benchmark Hegemony

This analysis concretizes idea #1: frontier labs may shape model-development direction by publishing, popularizing, and repeatedly using benchmarks that other labs then adopt on public release pages.

The quantitative unit is a benchmark mention on a public model release page in `data/models.csv`. It is not a measure of model capability, benchmark quality, or all evaluations used by a lab.

## Hypothesis

If OpenAI had early benchmark hegemony that weakened as competition became more even, then Anthropic and Google release pages should show a higher share of OpenAI-authored or OpenAI-affiliated benchmark mentions in 2023-2024 than in 2025-2026.

Through `2026-09-30`, the combined OpenAI-source-or-affiliated share for Anthropic and Google is nearly flat across the two periods. Provider-specific patterns and the affiliation-only measure differ, so the data does not establish a single fading or rising hegemony story.

## Methodology

Run:

```bash
.venv/bin/python analysis/frontier_lab_benchmark_hegemony/analyze.py
```

The script uses `scripts/taxonomy_utils.py::CanonicalResolver`, so every raw mention resolves only through an exact canonical benchmark name or explicit alias.

Measured concepts:

- Own-lab benchmark usage: release provider mentions a benchmark whose `frontier_lab_author_affiliations` contains that provider's lab group. Google includes `Google` and `DeepMind`.
- Competitor-lab benchmark adoption: release provider mentions a benchmark affiliated with another frontier lab.
- Neutral / academic / vendor adoption: the benchmark has no frontier-lab author affiliation.
- Mixed own + competitor: multi-affiliation benchmarks such as HLE that include both the release provider and other frontier labs.
- OpenAI-authored-or-affiliated adoption: `source_author` contains OpenAI or `frontier_lab_author_affiliations` contains OpenAI. The output also separates those two fields.
- Provider-created/private/opaque lifecycle share: mentions whose `benchmark_lifecycle_risk` facet includes `provider_created_benchmark` or `private_or_opaque_eval`.
- Release-page lag: first competitor mention date minus first owner-lab mention date inside this dataset only.

## Outputs

- `mentions_enriched.csv`: mention-level resolved data with authorship, affiliation, lifecycle, period, and provider-position labels.
- `provider_period_author_shares.csv`: main period-level author-position shares.
- `provider_year_author_shares.csv`: yearly author-position shares.
- `openai_adoption_period_comparison.csv`: Anthropic/Google use of OpenAI-authored and/or OpenAI-affiliated benchmarks.
- `cross_lab_adoption_matrix.csv`: non-exclusive provider-to-lab mention matrix.
- `provider_period_lifecycle_shares.csv` and `provider_year_lifecycle_shares.csv`: lifecycle-risk shares.
- `benchmark_first_adoption_lags.csv`: release-page lag calculations where possible.
- `high_signal_benchmarks.csv`: benchmark-level examples with provider counts.
- `provider_period_author_mix.png`: stacked bar chart of provider/period author-position shares.

## Findings

Current raw-mention comparison from `openai_adoption_period_comparison.csv`, through `2026-09-30`:

| Provider group | OpenAI source/affiliated 2023-2024 | OpenAI source/affiliated 2025-2026 |
| --- | ---: | ---: |
| Anthropic+Google | 11/76 (14.5%) | 60/410 (14.6%) |
| Anthropic | 8/42 (19.0%) | 35/221 (15.8%) |
| Google | 3/34 (8.8%) | 25/189 (13.2%) |

The combined inclusive share is nearly flat. Anthropic's share falls while Google's rises. Counting only frontier-lab affiliation gives a different combined comparison: 10/76 (13.2%) versus 51/410 (12.4%). These are raw mention shares; pages with long lists and shared model rows can affect the denominator.

Neutral / academic / vendor benchmarks remain the majority by the affiliation classification in every provider-period cell. Current own-lab and competitor shares are in `provider_period_author_shares.csv` and `cross_lab_adoption_matrix.csv`; the latter is non-exclusive for multi-affiliated benchmarks. Provider-created and private/opaque flags are reported separately in `provider_period_lifecycle_shares.csv` and should remain provisional until their facet review debt is reduced.

## High-Signal Examples

`SWE-bench verified` is the clearest OpenAI-affiliated cross-provider signal: 18 mentions across OpenAI, Google, and Anthropic release pages.

`HumanEval`, `GSM8K`, `MMMLU`, `BrowseComp`, `GraphWalks`, and `SimpleQA` are OpenAI-authored or OpenAI-affiliated benchmarks that appear outside OpenAI pages.

`Terminal-Bench 2.0` is a useful counterexample: `source_author` is Academia, but `frontier_lab_author_affiliations` is Anthropic, and it appears across providers in 2025-2026.

`HLE (Humanity's Last Exam)` is multi-affiliated with OpenAI, Anthropic, Google, DeepMind, and Microsoft. It is counted as mixed own + competitor in author-position shares, not as a clean competitor-only adoption.

`MRCR` and `MRCR v2` show why `source_author` and `frontier_lab_author_affiliations` must stay separate: their `source_author` is OpenAI, while the affiliation field lists Google/DeepMind.

`GPQA` and `GPQA Diamond` also need care: `source_author` includes Anthropic, but `frontier_lab_author_affiliations` is `none`, so this analysis treats them as neutral by affiliation while preserving the source-author field.

## Limitations

This measures release-page benchmark mentions, not all internal evaluations or model capability.

The time-lag table uses first mention in this dataset, not benchmark publication date. Negative or blank lags often mean the owner lab did not mention the benchmark on an earlier release page captured here.

Lifecycle facets include many `needs_review` rows. Treat provider-created/private/opaque counts as a structured signal to review, not as a final transparency audit.

Multi-affiliated benchmarks are counted once per target lab in `cross_lab_adoption_matrix.csv`, so that table is intentionally non-exclusive. The author-position share table is mutually exclusive.

The current provider universe is OpenAI, Google, and Anthropic. Adding Meta, xAI, Mistral, or other labs could change asymmetry estimates.

## Next Analysis Ideas

Add benchmark publication dates and paper-level citation metadata to estimate real adoption lag instead of release-page lag.

Cluster benchmark variants into families, such as SWE-bench, MRCR, GPQA, and MMLU/MMMLU, to separate family hegemony from version churn.

Manually review divergent rows where `source_author` and `frontier_lab_author_affiliations` tell different stories.

Normalize by release-page length or table density so mention shares are not dominated by long appendix-style releases.
