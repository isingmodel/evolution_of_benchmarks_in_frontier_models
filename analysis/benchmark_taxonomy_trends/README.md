# Benchmark Taxonomy Trends

This folder contains README-facing trend analyses for benchmark taxonomy projections.
The scripts here answer related but separate questions about how release-page benchmark framing changes over time.

## Scripts

- `task_mode_trend.py`: rolling task-mode projection used for `assets/benchmark_growth.png`.
- `separate_axis_trends.py`: separate task-mode and domain projections used for `assets/benchmark_growth_by_all_category.png`, with optional review-debt chart output.
- `facet_trends.py`: rolling trends over the richer multi-facet taxonomy used for `assets/benchmark_facet_trends.png`.

## Run

```bash
.venv/bin/python analysis/benchmark_taxonomy_trends/task_mode_trend.py --as-of 2026-04-23 --window-days 180 --strict-resolution
.venv/bin/python analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of 2026-04-23 --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
.venv/bin/python analysis/benchmark_taxonomy_trends/facet_trends.py --as-of 2026-04-23 --window-days 180 --strict-resolution
```

## Outputs

- `assets/benchmark_growth.png`
- `assets/benchmark_growth_by_all_category.png`
- `assets/benchmark_review_debt.png`
- `assets/benchmark_facet_trends.png`

All shares are release-page benchmark-framing views. They should not be read as capability measurements.
