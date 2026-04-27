# Data Directory Guide

This directory contains the source tables, generated normalized benchmark tables, and manual review layers for the benchmark evolution analysis. The project studies which benchmarks frontier model providers emphasize on public release pages. It does not claim to measure model capability directly.

## Data Flow

```text
models.csv
benchmarks.csv
benchmark_aliases.csv
benchmark_metadata_overrides.csv
benchmark_facet_overrides.csv
benchmark_review_queue.csv
        |
        v
scripts/build_normalized_data.py
        |
        v
evidence.csv
benchmark_facet_edges.csv
```

`models.csv` remains the source for model release rows and their benchmark lists. `benchmarks.csv` is the canonical benchmark source. Scripts that need mention-level data expand the comma-separated `benchmarks` field at runtime and resolve each raw benchmark label through canonical names plus `benchmark_aliases.csv`.

## Current Snapshot

| File | Rows | Role |
| --- | ---: | --- |
| `models.csv` | 37 | Source list of model release pages and benchmark names mentioned on them. |
| `benchmarks.csv` | 135 | Canonical benchmark table used by README, scraping catalog matching, evidence generation, and facet generation. |
| `benchmark_aliases.csv` | 46 | Source-backed mapping from release-page surface forms to canonical benchmark IDs. |
| `benchmark_metadata_overrides.csv` | 35 | Manual benchmark metadata corrections. |
| `benchmark_facet_overrides.csv` | 123 | Manual multi-facet classification corrections. |
| `benchmark_review_queue.csv` | 40 | Open identity, classification, and evidence review items. |
| `evidence.csv` | 135 | Generated evidence/source table for benchmark definitions. |
| `benchmark_facet_edges.csv` | 1,275 | Generated benchmark-to-facet long table. |
| `base_readme.md` | n/a | README template used by `scripts/update_readme.py`. |

Row counts describe the current repository snapshot and may change after regeneration.

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
- `scripts/build_normalized_data.py` reads this file to regenerate `evidence.csv` and `benchmark_facet_edges.csv`.
- Richer v3 classifications are represented in `benchmark_facet_edges.csv`.

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

### `benchmark_metadata_overrides.csv`

Manual metadata correction layer for canonical benchmarks.

Columns:

- `benchmark_name`: Canonical benchmark name from `benchmarks.csv`.
- `reference_link`: Replacement source URL, if the benchmark source URL needs correction.
- `source_author`: Replacement author/source label, if needed.
- `frontier_lab_author_affiliations`: Manual frontier-lab affiliation label.
- `evidence_notes`: Notes explaining the source-backed correction.

Notes:

- Use this file instead of editing generated `benchmarks.csv`.
- Blank override fields leave the benchmark source value or inferred value unchanged.
- These overrides also affect generated evidence notes in `evidence.csv`.

### `benchmark_facet_overrides.csv`

Manual v3 multi-facet classification layer.

Columns:

- `benchmark_name`: Canonical benchmark name.
- `facet_axis`: Facet dimension, such as `construct_claim`, `task_mechanism`, `domain`, `modality`, `interaction_pattern`, `metric_type`, `context_pressure`, `benchmark_lifecycle_risk`, or `headline_task_mode`.
- `facet_label`: Label within the selected facet axis.
- `label_weight`: Numeric contribution of the label for this benchmark and axis.
- `classification_confidence`: Reviewer confidence score.
- `review_status`: Classification state.
- `rationale`: Source-backed explanation for the override.

Notes:

- This is the preferred place to record audited classification decisions.
- A benchmark can have multiple labels on the same axis, with weights representing a split across labels.
- Overrides are used by `scripts/build_normalized_data.py` to produce `benchmark_facet_edges.csv`.

### `benchmark_review_queue.csv`

Manual queue for unresolved benchmark identity or classification issues.

Columns:

- `benchmark_name`: Benchmark or mention requiring review.
- `issue_type`: Type of issue, such as alias identity, subset identity, private eval review, or construct validity review.
- `priority`: Review priority.
- `reason`: Why the item needs review.
- `suggested_action`: Recommended next step.

Notes:

- Medium-priority review items can cause generated benchmark rows to be marked `needs_review`.
- This file is useful for preserving uncertainty instead of making unsupported classification decisions.

### `evidence.csv`

Generated evidence/source table for benchmark definitions.

Columns:

- `evidence_id`: Stable generated evidence ID.
- `benchmark_id`: Canonical benchmark ID.
- `evidence_type`: Type of evidence, currently focused on benchmark definitions.
- `title`: Human-readable evidence title.
- `url`: Source URL.
- `source_date`: Date of the source, when known.
- `accessed_date`: Date used when the evidence record was generated.
- `notes`: Source or override notes.

Notes:

- This table supports source-backed classification and review.
- It is generated from benchmark metadata and the configured accessed date.

### `benchmark_facet_edges.csv`

Generated long-form multi-facet taxonomy table.

Columns:

- `benchmark_id`: Canonical benchmark ID.
- `facet_axis`: Facet dimension.
- `facet_label`: Label within the facet dimension.
- `label_weight`: Numeric label contribution.
- `classification_confidence`: Confidence score for the classification.
- `evidence_id`: Evidence row supporting the classification.
- `review_status`: Review state.
- `rationale`: Explanation for the classification.

Notes:

- This is the most important table for v3 multi-facet analysis.
- A single benchmark can appear many times across axes and labels.
- `headline_task_mode` is a visualization projection; it should not be treated as the benchmark's exclusive identity.
- Most rows are seeded from legacy classifications unless overridden and audited.

### `base_readme.md`

Template for the generated top-level `README.md`.

Contents:

- Narrative framing for the repository.
- Image references for generated charts.
- Placeholder tokens such as `{{MODELS_TABLE}}` and `{{TAXONOMY_TABLE}}`.
- Regeneration instructions.

Notes:

- `scripts/update_readme.py` fills the placeholders with generated tables.
- Edit this template when changing the stable narrative or README structure.

## Common Conventions

### Review Status

Common review status values include:

- `accepted`: Source-backed and reviewed.
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
- `task_mechanism`
- `domain`
- `modality`
- `interaction_pattern`
- `metric_type`
- `context_pressure`
- `benchmark_lifecycle_risk`
- `headline_task_mode`

Use the facet table when a benchmark spans multiple capabilities or domains. Use headline projections only for readable charting.

## Regeneration

Run the standard pipeline from the repository root:

```bash
AS_OF=2026-04-23
ACCESSED_DATE=2026-04-26

python scripts/build_normalized_data.py --accessed-date "$ACCESSED_DATE"
python scripts/validate_data.py
python scripts/generate_visuals.py --as-of "$AS_OF" --strict-resolution
python scripts/generate_trend_graph_by_main_category.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python scripts/generate_trend_graph_by_all_category.py --as-of "$AS_OF" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
python scripts/generate_facet_trends.py --as-of "$AS_OF" --window-days 180
python scripts/update_readme.py
python scripts/validate_data.py
```

After adding new model releases or benchmark classifications, run validation before trusting the generated charts or README tables.
