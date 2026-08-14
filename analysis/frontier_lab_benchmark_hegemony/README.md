# Frontier Lab Benchmark Hegemony

This analysis concretizes idea #1: frontier labs may shape model-development direction by publishing, popularizing, and repeatedly using benchmarks that other labs then adopt on public release pages.

The quantitative unit is a benchmark mention on a public model release page in `data/models.csv`. It is not a measure of model capability, benchmark quality, or all evaluations used by a lab.

## Hypothesis

If OpenAI had early benchmark hegemony that weakened as competition became more even, then Anthropic and Google release pages should show a higher share of OpenAI-authored or OpenAI-affiliated benchmark mentions in 2023-2024 than in 2025-2026.

The data does not support that specific fading-hegemony version. In this release-page dataset, Anthropic and Google mention OpenAI-authored-or-affiliated benchmarks more often in 2025-2026 than in 2023-2024.

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

OpenAI-authored-or-affiliated mentions by non-OpenAI labs rose, rather than fell. Anthropic+Google went from 11/76 mentions in 2023-2024 (14.5%) to 54/275 in 2025-2026 (19.6%). Using only `frontier_lab_author_affiliations`, the share rose from 10/76 (13.2%) to 46/275 (16.7%).

Google changed the most: OpenAI-authored-or-affiliated mentions rose from 3/34 (8.8%) in 2023-2024 to 22/105 (21.0%) in 2025-2026. Anthropic was nearly flat, from 8/42 (19.0%) to 32/170 (18.8%).

Own-lab benchmark visibility increased, especially for OpenAI. OpenAI's own-only plus mixed own/competitor share rose from 2/32 mentions (6.3%) to 60/199 (30.2%). Anthropic rose from 0/42 to 33/170 (19.4%). Google declined from 7/34 (20.6%) to 17/105 (16.2%).

Neutral / academic / vendor benchmarks remain the majority in every provider-period cell. In 2025-2026, neutral shares were OpenAI 125/199 (62.8%), Anthropic 108/170 (63.5%), and Google 72/105 (68.6%).

Competitor-lab adoption is asymmetric. In 2025-2026, Anthropic mentions OpenAI-affiliated benchmarks 31 times and Google/DeepMind-affiliated benchmarks 9 times. Google mentions OpenAI-affiliated benchmarks 15 times and Anthropic-affiliated benchmarks 11 times. OpenAI mentions Google/DeepMind-affiliated benchmarks 13 times and Anthropic-affiliated benchmarks 9 times.

Provider-created or private/opaque lifecycle mentions became more common. The combined lifecycle share rose from 12.5% to 44.7% for OpenAI, 16.7% to 41.2% for Anthropic, and 8.8% to 26.7% for Google. This supports the weaker claim that frontier release pages increasingly mix public neutral benchmarks with lab-shaped or less transparent evaluation surfaces.

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
