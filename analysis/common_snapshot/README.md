# Common Data Snapshot

This folder contains lightweight baseline tables for the experimental analyses under `analysis/`.
The numbers are derived only from local CSVs and use exact canonical benchmark resolution plus explicit aliases.

## Baseline Counts

- Resolved benchmark mentions: 582
- Providers: Anthropic=212, Google=139, OpenAI=231
- Years: 2023=24, 2024=84, 2025=168, 2026=306
- Legacy task-mode mentions: Agentic=239, Generative Reasoning=233, Multimodal Perception=80, Constraint Satisfaction=18, Knowledge Retrieval=12
- Legacy domain mentions: General/Commonsense=227, Coding/Engineering=155, STEM/Math=107, Specialized (Law/Bio/Finance)=93

## Top Benchmarks

| Mentions | Benchmark |
| ---: | --- |
| 22 | MMMU / MMMU Pro |
| 18 | SWE-bench verified |
| 16 | HLE (Humanity's Last Exam) |
| 15 | AIME |
| 14 | GPQA |
| 14 | GPQA Diamond |
| 13 | MMMLU |
| 12 | SWE-bench Pro |
| 10 | MMLU / MMLU-Pro |
| 10 | BrowseComp |

## Output Tables

- `resolved_mentions.csv`
- `provider_year_mentions.csv`
- `top_benchmarks.csv`
- `provider_year_task_mix.csv`
- `facet_review_debt.csv`

## Interpretation Caveat

These tables describe what providers foregrounded on public release pages. They do not measure all evaluations, hidden evals, or model capability.
