# Exploratory README Story Analysis

This module retains the older story analyses. The
[project overview](../project_overview/README.md) now generates the root preface
with announcement-level counts and a narrower interaction-label measure.

Raw labels resolve only through exact canonical names or explicit aliases.
Within each model row, canonical identities are deduplicated. Every
benchmark-bearing model row contributes one unit, divided evenly across its
identities. A page jointly launching several named models can contribute several
units here; the overview and [lifecycle analysis](../benchmark_lifecycle/README.md)
union those identities into one provider/date/normalized-URL announcement.

## Broad software/tool proxy

The historical `is_work_simulation` field combines positive labels from three
axes: interaction pattern, task mechanism, and construct claim. It includes
planning and human involvement, as well as unit-test passing, code repair, SQL
generation, and software-engineering claims. A static coding benchmark such as
HumanEval can therefore qualify without requiring tool or environment interaction.

Read this field as a **broad software/tool proxy**, not evidence that the task
simulates work or that a model operates in an environment. The historical CSV
column and chart filenames are retained for continuity. The static-exam flag
also explicitly excludes benchmarks matching this proxy, so the two shares do
not independently establish a transition between natural task categories.

## Run and outputs

```bash
.venv/bin/python analysis/readme_story/analyze.py --as-of 2026-09-30
```

Outputs include:

- [static_work_sensitivity.csv](static_work_sensitivity.csv): broad-proxy shares,
  extraction filters, confidence-selected positive weight, and coverage-conditioned estimates.
- [work_simulation_top_contributors.csv](work_simulation_top_contributors.csv): pooled
  contributions across the selected period, not a decomposition of a particular year's change.
- [borrowed_benchmark_authority.csv](borrowed_benchmark_authority.csv): source-author
  and affiliation links under raw and model-row-normalized conventions.
- [public_benchmark_diffusion_cascades.csv](public_benchmark_diffusion_cascades.csv):
  selected first/later-provider sequences among identities with observed sharing.
- [review_leverage_benchmarks.csv](review_leverage_benchmarks.csv): recent reporting
  weight multiplied by nonaccepted facet-row share.
- Historical chart assets `assets/static_to_work_simulation_trend.png`,
  `assets/gemini_long_context_case.png`, and
  `assets/review_leverage_benchmarks.png`.

Repeat `--exclude-lifecycle-risk LABEL` and use `--min-mentions N` for ad hoc
filters. These filters renormalize surviving identities within each model row;
rows with none remaining leave the composition cohort. Minimum mention counts
refer to canonical model-row appearances, not distinct announcements.

Confidence sensitivity retains nondeprecated facets with ratings at least 0.70.
A rating is not a probability or acceptance decision. Broad-proxy coverage
requires a retained label on each of `construct_claim`, `task_mechanism`, and
`interaction_pattern`. Coverage-conditioned outputs restrict and renormalize
the surviving rows, so their denominator and cohort differ from the fixed-base
positive share. The overview instead reports interaction-axis coverage with
original weights, plus accepted-only sensitivity.

The old cascade tables condition on later observed reporting and do not estimate
field-wide adoption. Review leverage is a facet-row prioritization proxy, rather
than an uncertainty score. These outputs remain exploratory; use the overview's
complete-window diffusion and explicit coverage tables for current preface claims.
