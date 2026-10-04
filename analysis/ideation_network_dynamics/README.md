# Network and Reporting Dynamics Prototypes

This folder explores shared benchmark vocabulary, repeated names, portfolio
overlap, and source-author links on public frontier-model launch pages. The
observation is a recorded mention, not proof of internal use, true adoption,
provider influence, or model capability.

```bash
.venv/bin/python analysis/ideation_network_dynamics/analyze.py --as-of 2026-09-30
```

Resolution uses exact canonical names and explicit aliases. This module retains
raw occurrences within model rows. Joint announcements and repeated aliases can
therefore contribute multiple observations. Set-based portfolio similarity uses
distinct canonical identities, while raw-count outputs retain those repetitions.

Use generated tables for the selected run's counts and rankings. The
[project overview](../project_overview/README.md) supplies canonical
announcement-level concentration and complete-window cross-provider estimates;
the [lifecycle report](../benchmark_lifecycle/report.md) supplies full reporting
histories and provider opportunity counts.

## Cascades and first/later reporting roles

| Output | Purpose |
| --- | --- |
| [normalized_mentions.csv](normalized_mentions.csv) | Resolved raw occurrences and source metadata |
| [cascade_metrics.csv](cascade_metrics.csv) | First/last sightings, provider reach, and later-provider lags |
| [adoption_events.csv](adoption_events.csv) | Per-provider first reporting dates; historical field name retained |
| [provider_diffusion_roles.csv](provider_diffusion_roles.csv) | First/later-reporting role counts |
| [release_strategy_metrics.csv](release_strategy_metrics.csv) | New-to-sample, new-to-provider, reused, and previously elsewhere names |
| `provider_role_balance.png` | Role-count visualization |

The historical “originated,” “imported,” and “exported” terms describe ordering in
this selected sample, not creation, copying, causal diffusion, or private use.
First tracked reporting need not be the first public use of a benchmark.

The prototype's later-provider lag looks for a provider outside the group tied
on the earliest date. If several providers first report on that day, they belong
to the first group; they are not a sequential chain. This differs from the
overview's second-provider lag, where a simultaneous second provider has lag zero.
Within-day ordering is unknown.

Fastest-case rankings select successful observed sharing. Recent benchmarks have
less follow-up, and provider launch cadence differs. For estimates retaining
provider-specific identities, use
[diffusion_horizons.csv](../project_overview/diffusion_horizons.csv): each horizon
admits its own complete calendar cohort. A calendar window still need not contain
an opportunity from another provider.

The prototype's time-to-half-of-observed-mentions and first/last span are summaries
of the recorded sample. They are not attention decay, complete lifetimes,
retirement, or saturation measures. Prefer provider-specific lifecycle gaps when
asking how many later tracked launches omitted a benchmark.

## Portfolio similarity

[provider_similarity_timeseries.csv](provider_similarity_timeseries.csv),
[provider_similarity_latest.csv](provider_similarity_latest.csv), and
`portfolio_similarity_over_time.png` describe cumulative pairwise Jaccard overlap.

Similarity compares sets of named identities, without weighting scores,
prominence, or evaluation quality. Early portfolios can be small, and later
cumulative sets retain old identities. Changes need not represent current
provider convergence or copying. Inspect portfolio sizes and source coverage
alongside the time series.

Versions remain separate where the catalog distinguishes them; historical
combined identities also remain. Family-level similarity requires explicit
lineage decisions before regrouping.

## Source-author composition

[source_author_dependency_by_provider.csv](source_author_dependency_by_provider.csv),
[release_source_author_mix.csv](release_source_author_mix.csv), and
`source_author_mix_by_provider.png` summarize raw-mention source groups and
affiliation/risk flags.

Flags can overlap. Authorship and author affiliation do not establish control or
influence; provider-created does not imply private. When no known lab link is
identified, unresolved source or affiliation metadata uses an `Unknown` grouping
rather than assigning an institution by guess. Unknown mentions remain in full
denominators, so identified link shares are not total-influence estimates.

Review composite authors, MRCR implementation lineage, and provisional
lifecycle-risk labels before interpreting these outputs. See the
[attribution methods](../frontier_lab_benchmark_hegemony/README.md) and
[preface audit](../../docs/readme_data_audit_2026_10_04.md).

## Additional research ideas

| Question | Needed analysis or evidence |
| --- | --- |
| Which names appear together? | Co-mention matrix or graph, controlling long-list cliques and joint model rows |
| Which identities connect reporting bundles? | Robust network structure, sensitivity to components and canonical versions |
| How do task-specific sharing patterns differ? | Reviewed facets, cohort sizes, and complete-follow-up denominators |
| Are benchmark families shared while versions change? | Source-backed family/implementation lineage |
| How prominent are authors or benchmarks on a page? | Mention placement, section, result/comparison role, and source text |
| How long after publication does reporting begin? | Publication dates and archived launch-page evidence |
| Does source supply become more concentrated? | Audited author groups and explicit treatment of collaborations/unknowns |

These remain descriptive hypotheses and extensions. The
[manifest](manifest.json) and [summary_metrics.csv](summary_metrics.csv) record
the local run. The [current synthesis](../SYNTHESIS.md) explains evidence priorities;
historical editorial rankings are preserved in the
[meta-review archive](../meta_review/README.md).
