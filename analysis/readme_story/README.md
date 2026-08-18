# README Story Analysis

This analysis generates the tables and chart assets used by the README story sections.
It uses the same exact canonical benchmark resolver as the validation pipeline: a raw release-page mention counts only when it matches a canonical benchmark name or an explicit alias.

The evidence source is a public release page, while the weighted analysis unit is a benchmark-bearing model-release row. A page that launches several named variants can therefore supply several rows. Each row contributes one unit in share-based analyses, divided evenly across its benchmark list, so long evaluation tables do not dominate provider-period comparisons.

## Run

```bash
.venv/bin/python analysis/readme_story/analyze.py --as-of 2026-08-13
```

## Outputs

- `analysis/readme_story/*.csv`
- `analysis/readme_story/static_work_sensitivity.csv` with extraction-granularity filters plus confidence-threshold lower-bound and coverage-conditioned variants
- `assets/static_to_work_simulation_trend.png`
- `assets/gemini_long_context_case.png`
- `assets/review_leverage_benchmarks.png`

The generated outputs summarize public release-page benchmark mentions. They are not model capability measurements or complete evaluation records.

For ad hoc sensitivity runs, repeat `--exclude-lifecycle-risk LABEL` as needed and use `--min-mentions N`. The script recomputes weights after filtering so each model-release row with surviving mentions still contributes one unit. The committed confidence sensitivity also reports coverage across the three work-classification axes (`construct_claim`, `task_mechanism`, and `interaction_pattern`).
