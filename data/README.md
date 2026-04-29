# Data Directory Guide

This directory contains the source tables and integrated benchmark facet table for the benchmark evolution analysis. The project studies which benchmarks frontier model providers emphasize on public release pages. It does not claim to measure model capability directly.

## Data Flow

```text
models.csv
benchmarks.csv
benchmark_aliases.csv
benchmark_facets.csv
benchmark_facet_manual.csv   # temporary, optional
        |
        v
scripts/build_normalized_data.py
        |
        v
benchmark_facets.csv
```

`models.csv` remains the source for model release rows and their benchmark lists. `benchmarks.csv` is the canonical benchmark source. Scripts that need mention-level data expand the comma-separated `benchmarks` field at runtime and resolve each raw benchmark label through canonical names plus `benchmark_aliases.csv`.

`scripts/build_normalized_data.py` is an additive merge, not a destructive facet rebuild. It preserves existing `benchmark_facets.csv` rows for existing benchmark IDs, seeds facets only for new benchmark IDs, drops rows whose benchmark IDs no longer exist in `benchmarks.csv`, and applies temporary `benchmark_facet_manual.csv` rows by replacing the touched `benchmark_id + facet_axis` groups. Changing `benchmarks.csv` identity fields does not automatically rewrite already integrated facet rows.

## File Overview

| File | Current rows | Role |
| --- | ---: | --- |
| `models.csv` | ~37 | Source list of model release pages and benchmark names mentioned on them. |
| `benchmarks.csv` | ~134 | Canonical benchmark table used by scraping catalog matching and facet generation. |
| `benchmark_aliases.csv` | ~46 | Source-backed mapping from release-page surface forms to canonical benchmark IDs. |
| `benchmark_facets.csv` | ~2,826 | Integrated v3 benchmark-to-facet long table used by multi-facet analyses. |

Row counts are approximate orientation only. Run validation or inspect the CSVs directly for authoritative counts.

## File Reference

### `models.csv`

Source table for tracked model releases.

Columns:

- `Provider`: Model provider, such as `OpenAI`, `Google`, or `Anthropic`.
- `Model name`: Public model name used in the release page.
- `link`: Public launch or announcement URL.
- `release date`: Release date in `YYYY-MM-DD` format.
- `benchmarks`: Comma-separated benchmark names represented as release-page mentions.

Notes:

- This is the source of truth for model-level benchmark lists.
- Trend scripts expand `benchmarks` at runtime instead of reading a separate materialized mention table.
- Raw benchmark strings must resolve by exact canonical name or explicit alias.

### `benchmarks.csv`

Canonical benchmark table.

Columns:

- `benchmark_id`: Stable generated benchmark ID.
- `benchmark_name`: Canonical benchmark name.
- `reference_link`: Primary source or reference URL for the benchmark.
- `source_author`: Broad author/source label, such as `Academia`, `OpenAI`, `Google`, `Anthropic`, or another organization.
- `frontier_lab_author_affiliations`: Inferred or reviewed frontier-lab affiliation label.
- `legacy_task_mode`: Legacy headline task-mode classification.
- `legacy_task_domain`: Legacy headline domain classification.
- `legacy_rationale`: Short explanation for the legacy classification.
- `review_status`: Review state for the benchmark row.

Notes:

- This file is the canonical benchmark source.
- `scripts/build_normalized_data.py` reads this file when keeping `benchmark_facets.csv` aligned with current benchmark IDs.
- Richer v3 classifications are represented in `benchmark_facets.csv`.
- `review_status` in this file is about canonical benchmark identity, not completion of every facet review.

### `benchmark_aliases.csv`

Explicit alias table for resolving non-canonical benchmark mentions.

Columns:

- `alias`: Surface form found in release pages or source CSVs.
- `benchmark_id`: Canonical benchmark ID that the alias resolves to.
- `match_type`: Reason for the alias mapping.
- `notes`: Short explanation or source context.

Common `match_type` values:

- `exact`
- `case_variant`
- `provider_abbreviation`
- `version_alias`
- `legacy_name`

Notes:

- The resolver intentionally avoids fuzzy or substring matching.
- Add an alias here when a provider uses shorthand such as `MCP-Atlas` for `Scale MCP-Atlas`.
- Alias rows should be narrow and source-backed.

### `benchmark_facets.csv`

Integrated long-form multi-facet taxonomy table.

Columns:

- `benchmark_id`: Canonical benchmark ID.
- `facet_axis`: Facet dimension.
- `facet_label`: Label within the facet dimension.
- `classification_confidence`: Confidence score for the classification.
- `review_status`: Review state.
- `rationale`: Explanation for the classification.

Notes:

- This is the most important table for v3 multi-facet analysis.
- A single benchmark can appear many times across axes and labels.
- When multiple labels exist within the same benchmark and facet axis, trend scripts divide that benchmark's contribution equally across the labels at runtime.
- The table is v3-first and does not persist legacy `headline_task_mode` projection rows.
- Analysis scripts that need a single headline category derive it at runtime from the v3 facets.
- Model-generated candidate rows and human-reviewed rows live together here after review.
- During data updates, reviewers may temporarily create `benchmark_facet_manual.csv` with the same facet columns plus either `benchmark_id` or `benchmark_name`. Running `scripts/build_normalized_data.py` merges those rows into `benchmark_facets.csv` by replacing the touched `benchmark_id + facet_axis` rows. Remove the temporary file after integration; it is intentionally ignored by Git.

## Common Conventions

### Review Status

Common review status values include:

- `accepted`: Source-backed and reviewed for the table where it appears. In `benchmarks.csv`, this means the benchmark identity is accepted; in `benchmark_facets.csv`, this means the specific facet label is accepted.
- `needs_review`: Known uncertainty remains.
- `disputed`: Classification or identity is contested.
- `deprecated`: Row is retained for traceability but should not be active.
- `legacy_seed`: Generated from legacy taxonomy fields without full v3 review.

### Legacy Headline Categories

Legacy `task_mode` values:

- `Agentic`
- `Generative Reasoning`
- `Knowledge Retrieval`
- `Constraint Satisfaction`
- `Multimodal Perception`

Legacy `task_domain` values:

- `STEM/Math`
- `Coding/Engineering`
- `General/Commonsense`
- `Specialized (Law/Bio/Finance)`

### Multi-Facet Axes

The v3 taxonomy separates benchmark identity into multiple axes, including:

- `construct_claim`
- `benchmark_construct_claim`
- `provider_construct_claim`
- `task_mechanism`
- `domain`
- `modality`
- `interaction_pattern`
- `metric_type`
- `context_pressure`
- `benchmark_lifecycle_risk`

Use the facet table when a benchmark spans multiple capabilities or domains. Use headline projections only for readable charting.

## Regeneration

Run the standard pipeline from the repository root:

```bash
AS_OF=2026-04-23
PY=.venv/bin/python

$PY scripts/build_normalized_data.py
$PY scripts/validate_data.py
$PY analysis/benchmark_evolution/analyze.py --as-of "$AS_OF" --strict-resolution
$PY analysis/benchmark_evolution/benchmark_count_trend.py --as-of "$AS_OF" --window-days 90 --strict-resolution
$PY analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of "$AS_OF" --window-days 180 --strict-resolution
$PY analysis/benchmark_taxonomy_trends/facet_trends.py --as-of "$AS_OF" --window-days 180 --axes modality,interaction_pattern,context_pressure --top-labels 8 --strict-resolution
$PY analysis/readme_story/analyze.py --as-of "$AS_OF"
$PY scripts/validate_data.py
```

After adding new model releases or benchmark classifications, run validation before trusting the generated charts or analysis tables. The top-level `README.md` is maintained directly rather than generated from a data-directory template.
