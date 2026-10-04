# Current Analysis Synthesis

The project measures evaluations named on selected public model launch pages.
It records public reporting, not model capability, all internal evaluations,
benchmark quality, or provider intent. A name can appear in a result, comparison,
footnote, component list, or partner quotation.

The [project overview](project_overview/README.md) is the primary evidence source
for the repository preface. Its generated tables use the committed inputs and
the selected cutoff; this synthesis does not duplicate their changing numbers.
The [historical meta-review](meta_review/SYNTHESIS.md) preserves earlier editorial
judgments and hypotheses, rather than current findings.

## Evidence priorities

### A visual map of the sample

The [release/type timeline](benchmark_evolution/README.md) answers which model
row reported each task mix, and the [rolling category view](benchmark_taxonomy_trends/README.md)
summarizes changes over time. These views belong near the beginning of the
project preface because they orient the reader before the narrower findings.
Both retain named model rows and use a provisional headline projection; they
are descriptive context rather than proof of a change in model capability.
The five-category Agentic projection is broader than strict interaction tags.

These views complement the announcement-based concentration and lifecycle
analyses. Domain, multi-facet, count, attribution, and provider-network views
remain supporting analyses instead of a second undifferentiated chart gallery.

### Shared identities and a long tail

The most direct result compares how many canonical identities appear across
providers with how much reporting those identities account for. This requires
canonical resolution and announcement identity, but no provisional task taxonomy.

Use [sharing_summary.csv](project_overview/sharing_summary.csv) for observed
identity shares, benchmark–announcement counts, and equal-announcement weights.
The identity denominator excludes catalog entries without a sighting. The
weighted comparison gives each benchmark-bearing announcement one unit, so long
tables and jointly announced variants do not independently dominate it.

This is concentration among catalog identities, not among benchmark families or
independent tests. Explicit versions remain separate, some historical combined
identities remain, and a named suite and its components can all be recorded.

### Reporting histories and cross-provider sightings

The [lifecycle report](benchmark_lifecycle/report.md) follows every catalog
identity through first and last sightings, recurrence, provider-specific
opportunities, and reporting gaps. One announcement is a provider, release date,
and normalized source URL; model-row counts are retained separately. Empty
benchmark lists remain in opportunity counts.

[diffusion_horizons.csv](project_overview/diffusion_horizons.csv) compares second
provider sightings within complete calendar windows, including identities that
remain provider-specific. Each horizon has its own eligible cohort. Same-day
ties have zero lag. This is preferable to using only the fastest cases or only
identities that eventually become shared.

First seen means first recorded in this selected sample, not publication or true
adoption. A completed calendar window need not contain another provider's launch.
Last seen and a reporting gap do not establish retirement, saturation, or
replacement.

### Interaction-tag trends with annotation coverage

The overview uses five explicit interaction labels: single-turn tool use,
environment interaction, browser/web interaction, terminal/codebase interaction,
and computer control. Static code generation, unit-test scoring, planning, or a
construct claim alone do not qualify. This is a narrow reporting-composition
measure, not a measure of all agentic or real-world work.

[interaction_trends.csv](project_overview/interaction_trends.csv) retains original
weights while comparing all active labels, confidence-filtered labels, and
accepted labels. It reports positive shares and classification coverage together.
A confidence rating is neither a count weight nor evidence of completed review.
Unknown classifications remain missing; zero positive weight under zero coverage
is not evidence that interaction is absent. See the
[exact retained labels](project_overview/interaction_classification.csv) and
[provider-level sensitivity](project_overview/provider_interaction_trends.csv).

The older [README story analysis](readme_story/README.md) uses a broader
software/tool proxy and model-row weighting. It remains useful as an exploratory
sensitivity lens, but its “work simulation” field is not the overview's construct.

## Secondary analyses

- [Long-context analysis](provider_strategy_long_context/README.md) supports
  bounded release-page case studies. Compare broad and primary-only labels,
  annotation status, and the number of contributing announcements. Corrected
  source definitions, including MTOB's translation task, can change older
  summaries; use regenerated tables rather than historical numeric claims.
- [Benchmark attribution](frontier_lab_benchmark_hegemony/README.md) distinguishes
  source authorship from frontier-lab author affiliation. Identified links are
  descriptive metadata, not evidence of influence or benchmark ownership.
  Unresolved MRCR implementation lineage and multi-affiliated papers limit
  interpretation.
- [Network dynamics](ideation_network_dynamics/README.md) and
  [taxonomy trends](benchmark_taxonomy_trends/README.md) provide additional
  portfolio and classification views. Historical cascade rankings condition on
  observed sharing and should not replace complete-window denominators.

## Highest-value improvements

Review source evidence for influential provisional facets before strengthening
task-composition claims. Keep identity acceptance separate from facet acceptance.
The overview's coverage tables expose this distinction; older review-leverage
rankings are prioritization proxies, not calibrated uncertainty estimates.

Record benchmark-family and implementation lineage without silently merging
versions. Add mention-level evidence identifying direct results, comparisons,
components, and quotations before making claims about prominence. Publication
dates and archived launch-page versions would also support stronger timing
analysis than release dates and current page contents alone.

Reproduce the current tables with the
[pipeline](../scripts/run_pipeline.sh). See the
[analysis guide](README.md) for folder purposes and the
[overview methods](project_overview/README.md) for denominators and sensitivity
definitions.
