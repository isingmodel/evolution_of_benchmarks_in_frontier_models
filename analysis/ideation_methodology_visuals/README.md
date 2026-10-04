# Methodology Visuals and Creative Analyses

This folder prototypes ways to display benchmark reporting, multifacet
classification, and review priorities. It uses local inputs and exact canonical
resolution. These views do not measure model capability, benchmark quality,
provider intent, or actual page prominence.

```bash
.venv/bin/python analysis/ideation_methodology_visuals/analyze.py --as-of 2026-09-30
```

The [project overview](../project_overview/README.md) and
[complete lifecycle analysis](../benchmark_lifecycle/README.md) are the primary
current analyses. This folder preserves supporting prototypes.

## Outputs and methods

| Output | Purpose |
| --- | --- |
| [summary_stats.csv](summary_stats.csv) | Run counts, cutoff, and annotation-review inventory |
| [provider_strategy_fingerprints.csv](provider_strategy_fingerprints.csv) and corresponding PNG | Recent provider-by-facet reporting composition |
| [domain_interaction_flow.csv](domain_interaction_flow.csv) and `domain_interaction_alluvial.png` | Domain/interaction co-classification, with fractional weights and accepted-pair coverage |
| [review_leverage_benchmarks.csv](review_leverage_benchmarks.csv) and corresponding PNG | Recent reporting weight combined with nonaccepted facet-row share |
| [benchmark_lifecycle_table.csv](benchmark_lifecycle_table.csv) | Exploratory first/last-sighting and reporting-count seed table |

Read generated tables for current values and rankings. Copied summaries become
stale when source omissions, aliases, or classifications are corrected.

### Provider fingerprints

Each benchmark-bearing model row receives one total weight divided across raw
resolved occurrences. Joint model announcements can therefore contribute several
units. Each axis splits a mention's weight across its labels. The recent window
runs inclusively from the analysis endpoint minus 365 days through that endpoint;
the CSV exposes each provider's axis-weight denominator.

Compare headline projections, domains, and interaction patterns separately.
Coverage can differ across axes, and nondeprecated provisional labels remain
included. These are reporting-composition fingerprints, not stable provider
identities or evidence of strategy. Show sample sizes and label-review coverage
beside any presentation.

For announcement weighting and confidence-versus-acceptance sensitivity, use
[interaction_trends.csv](../project_overview/interaction_trends.csv) and
[provider_interaction_trends.csv](../project_overview/provider_interaction_trends.csv).
The overview's strict interaction flag is distinct from the broader
[software/tool proxy](../readme_story/README.md).

### Domain/interaction co-classification

The alluvial joins domain labels with interaction labels for the same mentioned
benchmark, splitting weight across label pairs. Its ribbons represent
co-classification, not temporal movement, task execution, or a transition from
one benchmark identity to another. A compact matrix can convey the same evidence
without implying a flow over time.

### Review leverage

Review leverage multiplies recent model-normalized reporting weight by the share
of active facet rows lacking acceptance. This is a prioritization proxy, not a
calibrated uncertainty estimate or benchmark-quality score. Its denominator mixes
facet axes; missing annotations and axis-specific coverage require separate
inspection. Catalog identity approval does not establish facet approval.

Read [review_leverage_benchmarks.csv](review_leverage_benchmarks.csv) for current
targets, and the overview's
[interaction classifications](../project_overview/interaction_classification.csv)
for explicit missing-versus-retained labels.

### Reporting-history seed

The older seed table does not replace the
[source-linked lifecycle report](../benchmark_lifecycle/report.md), which retains
the full catalog, announcement identity, same-day ties, and provider-specific
follow-up opportunities. Reporting spans and gaps do not prove retirement or
saturation.

## Further visualization ideas

- Use small multiples for provider-level changes, alongside cohort and annotation
  coverage counts.
- Compare all-active, confidence-selected, and accepted labels without treating
  ratings as probabilities.
- Show benchmark-family and version lineage after identity review, rather than
  infer family continuity from similar names.
- Build co-mention matrices with controls for long lists and jointly announced
  variants; named suites and components need not be independent tests.
- Display source-author and affiliation links only after attribution review,
  distinguishing unresolved metadata from identified non-frontier affiliations.
- Add source-linked mention prominence before describing influence or foregrounding.

These are proposals, not additional findings. The
[current synthesis](../SYNTHESIS.md) explains which evidence leads the preface;
the [meta-review archive](../meta_review/README.md) preserves earlier editorial
judgments.
