# Common Data Snapshot

This folder contains lightweight baseline tables for the experimental analyses under `analysis/`.
The numbers are derived only from local CSVs and use exact canonical benchmark resolution plus explicit aliases.

The current snapshot includes tracked releases through `2026-09-30`. Counts below use resolved raw mentions; analyses that deduplicate canonical identities within a model-release row can have a smaller count.

## Baseline Counts

- Resolved benchmark mentions: 791
- Providers: Anthropic=263, Google=223, OpenAI=305
- Years: 2023=24, 2024=84, 2025=168, 2026=515
- Legacy task-mode mentions: Agentic=372, Generative Reasoning=265, Multimodal Perception=92, Constraint Satisfaction=45, Knowledge Retrieval=17
- Legacy domain mentions: General/Commonsense=313, Coding/Engineering=212, Specialized (Law/Bio/Finance)=146, STEM/Math=120

## Top Benchmarks

| Mentions | Benchmark |
| ---: | --- |
| 22 | MMMU / MMMU Pro |
| 20 | HLE (Humanity's Last Exam) |
| 18 | SWE-bench verified |
| 15 | AIME |
| 15 | GPQA Diamond |
| 14 | GPQA |
| 13 | MMMLU |
| 13 | SWE-bench Pro |
| 12 | MRCR v2 |
| 12 | DeepSWE v1.1 |

## Output Tables

- `resolved_mentions.csv`
- `provider_year_mentions.csv`
- `top_benchmarks.csv`
- `provider_year_task_mix.csv`
- `facet_review_debt.csv`

## Interpretation Caveat

These tables describe what providers foregrounded on public release pages. They do not measure all evaluations, hidden evals, or model capability.
