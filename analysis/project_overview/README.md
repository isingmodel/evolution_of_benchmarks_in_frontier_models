# Project overview: evidence behind the preface

This module generates the main README's counts, evidence tables, and two overview
figures. It uses the source CSVs directly and the shared lifecycle builder for
announcement identity, cutoff handling, and canonical resolution.

```bash
.venv/bin/python analysis/project_overview/analyze.py --as-of 2026-09-30
```

`--output-dir` and `--asset-dir` support isolated runs. `--readme-path README.md`
also renders the repository preface from `README.template.md`; the full pipeline
passes this explicitly. Custom analysis runs do not overwrite the root README.

## Observation and weighting

An announcement is a provider/date/normalized-URL event. Canonical identities
are unioned across jointly announced model rows. This is the same definition as
the [lifecycle analysis](../benchmark_lifecycle/README.md).

Presence counts retain every distinct benchmark–announcement pair. Composition
shares give every benchmark-bearing announcement one unit divided across its
identities. Empty pages are counted in the inventory but have no composition
denominator. A parallel model-row calculation tests sensitivity to jointly
announced variants. Neither convention weights scores, prominence, or quality.

## Outputs

| Output | Definition |
| --- | --- |
| `summary.json` | Cutoff, inventory, catalog, shared-core, singleton and facet-review counts |
| `coverage_by_provider.csv` | Model rows, distinct announcements, benchmark-bearing pages, observed identities and date coverage |
| `annual_inventory.csv` | Yearly observation counts and first-seen identities |
| `sharing_summary.csv` | Catalog shares, observation shares and equal-announcement shares by number of reporting providers |
| `diffusion_horizons.csv` | Complete-follow-up denominators and second-provider sightings within 30, 90 and 180 days |
| `interaction_classification.csv` | Full catalog crossed with label variants; exact retained labels, positive flags and coverage |
| `interaction_trends.csv` | Annual positive/coverage shares under announcement and model-row weighting |
| `provider_interaction_trends.csv` | The same classification sensitivity within each provider |
| `../../assets/benchmark_shared_core.png` | Shared versus provider-specific identities and their reporting weight |
| `../../assets/interaction_taxonomy_sensitivity.png` | Positive interaction shares alongside annotation coverage |

### Shared core

The sharing classification uses each identity's provider count through the chosen
cutoff. The identity denominator contains only observed benchmarks; catalog
identities without sightings remain in the catalog and summary. Sharing is
defined over the full available history, not just a recent window. Versions and
legacy combined identities follow the catalog; no benchmark-family merge is
inferred.

### Diffusion with complete calendar follow-up

For horizon H days, an identity is eligible when `first_seen <= cutoff - H`.
It counts as shared within the window when its second provider's first sighting
is on or before `first_seen + H`. Both boundaries are inclusive. Same-day
first-provider ties have lag zero. Recent identities are excluded, rather than
counted as failures before their window ends.

Each horizon has a different eligible cohort. The rows are descriptive fractions,
not one survival curve or a field-wide adoption probability. Eligibility does not
ensure another provider had a tracked launch in the window. First seen is entry
into this selected sample, not benchmark publication. The conditional median lag
among benchmarks that ever become shared is reported separately.

### Strict interaction tags and missing classifications

Only `interaction_pattern` labels are used. Positive labels are:

- `single_turn_tool_use`
- `environment_interaction`
- `browser_or_web_interaction`
- `terminal_or_codebase_interaction`
- `computer_control`

No inference is made from task-domain names, unit-test scoring, code generation,
planning, human involvement, or construct claims alone. This narrower measure
replaces the older broad “work simulation” proxy in the project preface; it does
not purport to cover all forms of agentic or real-world work.

Variants retain all nondeprecated interaction labels, only labels with rating
at least 0.70, or only labels with `review_status=accepted`. Confidence is a filter,
not a count weight or calibrated probability. Acceptance is independent of the
rating threshold. Coverage means at least one retained label on this axis, not
that the whole taxonomy or all possible labels have been reviewed.

For each variant, `positive_share` counts positively tagged weight against the
full original denominator. Missing labels contribute no positive weight but
remain unknown: classification `positive` is missing, `covered` is false, and
`coverage_share` exposes the gap. `positive_share_among_covered` divides positive
weight by covered weight and is missing when coverage is zero. Labels are not
renormalized separately within each surviving announcement. A zero fixed-base
positive share under zero coverage is not evidence of non-interaction.

## Quality and reproducibility

Source corrections and outstanding identity issues are recorded in the
[preface audit](../../docs/readme_data_audit_2026_10_04.md). This module does not
silently reclassify source facets or promote confidence ratings to accepted rows.
Independent fixtures check joint announcements, weighting, follow-up boundaries,
same-day ties, unknown labels, accepted-versus-rated labels and empty cutoffs.
CI regenerates both evidence tables and the root README to catch numerical drift.
