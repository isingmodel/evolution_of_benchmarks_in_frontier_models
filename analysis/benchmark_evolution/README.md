# Benchmark Evolution Timeline

This analysis generates the top-level benchmark evolution timeline and benchmark-count trend shown in the repository README. It resolves release-page benchmark mentions through the shared canonical benchmark utilities and projects them onto the legacy task-mode categories for a compact visual overview.

## Run

```bash
.venv/bin/python analysis/benchmark_evolution/analyze.py --as-of 2026-04-23 --strict-resolution
.venv/bin/python analysis/benchmark_evolution/benchmark_count_trend.py --as-of 2026-04-23 --window-days 90 --strict-resolution
```

## Outputs

- `assets/benchmark_evolution.png`
- `assets/benchmark_count_per_release.png`

The charts visualize benchmark framing on public release pages, not a direct measurement of model capability.
