# Common Data Snapshot

This folder contains lightweight baseline tables for the experimental analyses under `analysis/`.
The numbers are derived only from local CSVs and use exact canonical benchmark resolution plus explicit aliases.

## Baseline Counts

- Resolved benchmark mentions: 422
- Providers: Anthropic=146, Google=92, OpenAI=184
- Years: 2023=24, 2024=84, 2025=168, 2026=146
- Legacy task-mode mentions: Generative Reasoning=199, Agentic=126, Multimodal Perception=72, Constraint Satisfaction=13, Knowledge Retrieval=12
- Legacy domain mentions: General/Commonsense=182, STEM/Math=102, Coding/Engineering=94, Specialized (Law/Bio/Finance)=44

## Top Benchmarks

| Mentions | Benchmark |
| ---: | --- |
| 25 | MMMU / MMMU Pro |
| 18 | SWE-bench verified |
| 15 | AIME |
| 14 | GPQA |
| 13 | MMMLU |
| 13 | GPQA Diamond |
| 11 | HLE (Humanity's Last Exam) |
| 10 | MMLU / MMLU-Pro |
| 10 | TAU-2 bench |
| 9 | MATH |

## Output Tables

- `resolved_mentions.csv`
- `provider_year_mentions.csv`
- `top_benchmarks.csv`
- `provider_year_task_mix.csv`
- `facet_review_debt.csv`

## Interpretation Caveat

These tables describe what providers foregrounded on public release pages. They do not measure all evaluations, hidden evals, or model capability.
