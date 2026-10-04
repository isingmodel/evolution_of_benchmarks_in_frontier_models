# Benchmark Authorship and Affiliation Links

This exploratory analysis describes identified authorship and affiliation links
among evaluations named on public model launch pages. The historical folder name
is retained for compatibility; the data does not establish benchmark hegemony,
provider influence, institutional ownership, or causal adoption.

## Method and units

```bash
.venv/bin/python analysis/frontier_lab_benchmark_hegemony/analyze.py --as-of 2026-09-30
```

The shared canonical resolver accepts only exact names and explicit aliases.
This module counts resolved raw label occurrences within model rows. Repeated
aliases and models launched together can therefore contribute more than once.
Pages with longer lists also contribute more weight. These raw shares differ
from the main [overview's](../project_overview/README.md) announcement-weighted
composition shares and the [README story module's](../readme_story/README.md)
model-row-normalized attribution sensitivity.

Two metadata fields remain separate:

- `source_author`: the recorded benchmark author or publishing organization.
- `frontier_lab_author_affiliations`: identified frontier-lab affiliations of
  authors, including multi-affiliated collaborations.

The OpenAI-source-or-affiliated flag is the union of an identified OpenAI token
in either field. Affiliation-only outputs answer a different question. Google
and DeepMind are grouped for provider comparisons. Multi-affiliation matrices
are nonexclusive; provider-position shares use mutually exclusive categories.

Unknown or unresolved authorship remains in the full mention denominator.
Linked shares therefore measure **identified links**, not all influence.
A missing link is not proof of independence. Unresolved affiliation has its own
`unknown_affiliation` provider-position category and an `Unknown affiliation`
matrix target. Known-lab flags use only recognized frontier-lab names. The
`neutral_or_non_frontier` category covers recorded `none` affiliations, which
still should not be interpreted as a verified neutrality judgment.

Provider-created and private/opaque flags are separate lifecycle-risk facets.
They must not be conflated: a provider-authored benchmark can be public, and a
private partner evaluation need not be provider-authored.

## Current evidence tables

Use regenerated outputs rather than a manually copied period comparison:

| Output | Purpose |
| --- | --- |
| [mentions_enriched.csv](mentions_enriched.csv) | Source-linked raw occurrences and metadata flags |
| [provider_period_author_shares.csv](provider_period_author_shares.csv) | Mutually exclusive provider-position categories |
| [provider_year_author_shares.csv](provider_year_author_shares.csv) | Annual categories with observation counts |
| [openai_adoption_period_comparison.csv](openai_adoption_period_comparison.csv) | Separate source, affiliation, and union comparisons |
| [cross_lab_adoption_matrix.csv](cross_lab_adoption_matrix.csv) | Nonexclusive provider-to-lab identified links |
| [provider_period_lifecycle_shares.csv](provider_period_lifecycle_shares.csv) | Provider-created and private/opaque facet flags |
| [benchmark_first_adoption_lags.csv](benchmark_first_adoption_lags.csv) | First owner/later-provider reporting dates within this sample |
| [high_signal_benchmarks.csv](high_signal_benchmarks.csv) | Benchmark examples and observed provider counts |

Compare provider-specific results before pooling labs, and compare raw shares
with the model-row-normalized
[attribution table](../readme_story/borrowed_benchmark_authority.csv). A pooled
change can reflect sample composition or longer evaluation lists. Neither a
rising nor falling share establishes changes in authority or competitiveness.

## Attribution corrections and unresolved lineage

`GPQA` and `GPQA Diamond` now record Anthropic author affiliation. Their
source-author strings also include academic and other collaborators. Source
authorship is not equivalent to exclusive institutional ownership.

`MRCR` and `MRCR v2` retain historical stable identities, but both
`source_author` and `frontier_lab_author_affiliations` are explicitly
`needs_review`. The original evaluation has Google DeepMind/Google Research
authors; OpenAI publishes an expanded implementation inspired by it. Existing
generic, OpenAI-prefixed, and GDM-prefixed aliases mix implementation labels.
Do not attribute every mapped observation to a single creator or infer version
continuity while this remains unresolved.

See the [affiliation review](../../docs/frontier_lab_author_affiliation_review.md)
and [preface source audit](../../docs/readme_data_audit_2026_10_04.md). These
corrections supersede earlier attribution examples and copied numeric claims.

## Limits and next steps

Release-page first sightings are not publication dates or true adoption dates.
Negative or missing owner-to-competitor lags often reflect the selected launch
sample. Private/opaque and provider-created facets remain provisional where
their source review is incomplete.

Audit implementation-specific attribution, author affiliations, and benchmark
families before interpreting dependence. Publication dates, archived source
versions, citation metadata, and mention prominence would support stronger
questions than name presence alone permits. Extending the provider inventory
would also change which links count as own-lab or cross-lab.
