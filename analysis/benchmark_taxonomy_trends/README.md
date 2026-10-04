# Benchmark Taxonomy Composition Over Time

These charts show the composition of evaluations named on public release pages,
using active taxonomy annotations. They describe recorded appearances, not model
capability, benchmark publication, or the birth of new benchmark identities.

## Scripts

- `task_mode_trend.py`: standalone task-mode projection for comparison with older charts.
- `separate_axis_trends.py`: task-mode projection and domain composition on separate axes.
- `facet_trends.py`: composition of selected non-domain facet axes; labels outside the selected top labels are grouped as `Other`.

## Run

```bash
.venv/bin/python analysis/benchmark_taxonomy_trends/task_mode_trend.py --as-of 2026-09-30 --window-days 180 --strict-resolution
.venv/bin/python analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of 2026-09-30 --window-days 180 --strict-resolution
.venv/bin/python analysis/benchmark_taxonomy_trends/facet_trends.py --as-of 2026-09-30 --window-days 180 --axes modality,interaction_pattern,context_pressure --top-labels 8 --strict-resolution
```

## Outputs

- `assets/benchmark_growth_by_all_category.png`
- `assets/benchmark_growth.png`
- `assets/benchmark_facet_trends.png`

## Units and denominators

Every benchmark-bearing model row contributes one unit before missing annotations
are removed. That unit is split evenly across its recorded, resolved mentions and
then across the active labels assigned to each mention within a facet axis.
Repeated appearances on later rows count again. Raw labels that resolve to the
same identity within one row retain their separate contributions for continuity
with these older analyses. Jointly announced named model variants also contribute
separately. This differs from the announcement union and canonical deduplication
used by the [project overview](../project_overview/README.md).

A mention without an active annotation on the plotted axis contributes no covered
weight on that axis. Each chart normalizes the remaining covered weight to 100%
within its calendar window. Thus these are **covered composition shares**, not
fixed-denominator positive shares or evidence of complete taxonomy coverage.
`Other` groups known labels; it does not represent missing classifications.

## Calendar windows and gaps

An N-day trailing window includes the plotted day and the preceding N−1 calendar
days. Values change when recorded rows enter or leave that window. There is no
additional smoothing. When a window contains no covered weight, its shares stay
undefined and the plot leaves a gap; it does not carry earlier composition forward.
The early part of the series has only the observed history available so far.
If no covered mentions precede the selected cutoff, each command writes an
explicit empty-state figure, replacing any image from a previous run.

## Projection and annotation limits

Task mode assigns one priority category derived from existing facets. It is a
visual projection, not an exclusive benchmark identity. In particular, `Agentic`
can be selected by a construct claim or planning label and does not require one
of the overview's five strict tool/environment interaction labels. Task-mode and
domain plots answer different questions and should not be combined as disjoint
natural categories.

These views retain all nondeprecated labels, including provisional annotations;
confidence is not a count weight. The overview's
[interaction sensitivity and coverage](../project_overview/interaction_trends.csv)
provides confidence-filtered and accepted-label checks with a fixed denominator.
Sparse periods and changing provider/model coverage also limit comparisons over
time. A smooth-looking portfolio trend must not be interpreted as capability
progress, intent, or a field-wide adoption rate.
