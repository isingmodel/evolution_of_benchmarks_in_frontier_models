# README Story Analysis

This analysis generates the tables and chart assets used by the README story sections.
It uses the same exact canonical benchmark resolver as the validation pipeline: a raw release-page mention counts only when it matches a canonical benchmark name or an explicit alias.

Each benchmark-bearing release page contributes one unit of weight in share-based analyses, divided evenly across the benchmarks listed on that page. This keeps long benchmark tables from dominating provider-period comparisons.

## Run

```bash
.venv/bin/python analysis/readme_story/analyze.py --as-of 2026-04-23
```

## Outputs

- `analysis/readme_story/*.csv`
- `assets/static_to_work_simulation_trend.png`
- `assets/gemini_long_context_case.png`
- `assets/review_leverage_benchmarks.png`

The generated outputs summarize public release-page benchmark mentions. They are not model capability measurements or complete evaluation records.
