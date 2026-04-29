# Benchmark Taxonomy Trends

This folder contains README-facing trend analyses for benchmark taxonomy projections.
The scripts here answer related but separate questions about how release-page benchmark framing changes over time.

## Scripts

- `task_mode_trend.py`: legacy standalone headline task-mode projection kept for ad hoc comparison.
- `separate_axis_trends.py`: separate headline task-mode and v3 domain facet trends used for `assets/benchmark_growth_by_all_category.png`.
- `facet_trends.py`: rolling trends over the richer multi-facet taxonomy used for `assets/benchmark_facet_trends.png`.

## Run

```bash
.venv/bin/python analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of 2026-04-23 --window-days 180 --strict-resolution
.venv/bin/python analysis/benchmark_taxonomy_trends/facet_trends.py --as-of 2026-04-23 --window-days 180 --top-labels 8 --strict-resolution
```

## Outputs

- `assets/benchmark_growth_by_all_category.png`
- `assets/benchmark_facet_trends.png`

All shares are release-page benchmark-framing views. Each release page contributes equal total weight; when a resolved benchmark has multiple labels within the plotted facet axis, that benchmark's contribution is divided equally across those labels. These charts should not be read as capability measurements.
