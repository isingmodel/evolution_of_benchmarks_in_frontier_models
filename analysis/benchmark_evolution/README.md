# Benchmark Evolution Timeline

This analysis shows when tracked model rows were released and how their reported benchmark lists map to the legacy task-mode projection. The compact timeline retains every model row, including models sharing an announcement page and rows with an empty benchmark list. It labels the first row per provider/calendar year and the latest row per provider; model name breaks same-day ties. The [detail image](../../assets/benchmark_evolution_detail.png) labels every row.

All marker centers and release-date anchors use the actual source date. Vertical lanes separate nearby markers and have no quantitative meaning. Pies have a fixed area, so their size does not represent benchmark counts. Empty lists use hollow circles; nonempty lists with no usable projection use gray hatched circles. Partial projection coverage is printed beside a labeled model.

The slices preserve the historical model-row calculation: resolve each raw inventory mention, assign equal weight to surviving resolved mentions, then normalize the weights with a headline projection. Repeated surface forms remain repeated mentions. Missing projection labels are excluded from the pie denominator, so colors describe the classified portion of that row, rather than silently treating unclassified mentions as a task mode. Active labels include provisional annotations. The projection is a deterministic priority rule across facets, not a disjoint natural taxonomy or a direct measure of interaction: a long-context-primary label takes priority, while planning and construct claims can trigger the Agentic category. The [data guide](../../data/README.md#benchmark_facetscsv) describes the facet axes and review process.

The count trend is a separate view of unique resolved canonical benchmarks per model row, including zero-benchmark rows. Neither chart measures model capability. The [project overview](../project_overview/README.md) and [benchmark lifecycle](../benchmark_lifecycle/README.md) use announcement events for their primary calculations; this timeline intentionally keeps the historical model-row unit.

## Run

```bash
.venv/bin/python -m analysis.benchmark_evolution.analyze --as-of 2026-09-30 --strict-resolution --detail-output assets/benchmark_evolution_detail.png
.venv/bin/python analysis/benchmark_evolution/benchmark_count_trend.py --as-of 2026-09-30 --window-days 90 --strict-resolution
```

## Outputs

- `assets/benchmark_evolution.png`
- `assets/benchmark_evolution_detail.png` (with `--detail-output`)
- `assets/benchmark_count_per_release.png`

An early cutoff with no inventory rows writes an explicit empty-state image, including the optional detail output. Dates after the cutoff are excluded. The default cutoff is the latest source release date; `--output` changes the compact image destination.
