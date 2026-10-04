# Analysis Guide

These analyses describe evaluations named on selected public frontier-model
launch pages. They do not measure model capability or every evaluation used by a
provider. The [project overview](project_overview/README.md) supplies the evidence
for the root README; [SYNTHESIS.md](SYNTHESIS.md) explains the current priorities.
Generated CSVs are the source for numeric findings at each selected cutoff.

## Primary analyses

| Folder | Purpose |
| --- | --- |
| [project_overview](project_overview/README.md) | Preface counts, shared-core concentration, complete-window cross-provider sightings, and strict interaction-label sensitivity |
| [benchmark_lifecycle](benchmark_lifecycle/README.md) | Complete catalog reporting histories, source-linked announcement observations, recurrence, and provider-cadence gaps |
| [benchmark_evolution](benchmark_evolution/README.md) | Model-release dates and benchmark task-mode composition; benchmark-count view |
| [benchmark_taxonomy_trends](benchmark_taxonomy_trends/README.md) | Rolling taxonomy composition and annotation-review context |

The overview and lifecycle use a provider/date/normalized-URL announcement unit,
unioning identities across jointly announced model rows. The overview also
retains model-row sensitivity. Empty benchmark lists remain in launch inventory
and lifecycle opportunity counts, but contribute no benchmark-composition unit.

## Exploratory and supporting analyses

| Folder | Purpose and reading guidance |
| --- | --- |
| [common_snapshot](common_snapshot/README.md) | Shared resolved mentions and review context for the exploratory analyses |
| [readme_story](readme_story/README.md) | Older model-row-weighted story tables, including a broad software/tool proxy; distinct from the overview's strict interaction tags |
| [frontier_lab_benchmark_hegemony](frontier_lab_benchmark_hegemony/README.md) | Identified source-author and affiliation links; the historical folder name does not imply demonstrated hegemony |
| [provider_strategy_long_context](provider_strategy_long_context/README.md) | Provider-period long-context case studies; check source definitions, label coverage, and small cohorts |
| [ideation_network_dynamics](ideation_network_dynamics/README.md) | Portfolio similarity and public-mention networks; conditional cascades are not population adoption probabilities |
| [ideation_narrative_strategy](ideation_narrative_strategy/README.md) | Exploratory framing proxies and presentation ideas |
| [ideation_methodology_visuals](ideation_methodology_visuals/README.md) | Taxonomy views and review-priority proposals |
| [meta_review](meta_review/README.md) | Historical qualitative reviews and editorial proposals, not current numeric evidence |

The README selects four complementary views: release/type orientation, rolling
type composition, shared-identity concentration, and individual reporting histories.
The interaction sensitivity plot and annual values remain in an expandable
section. Additional charts remain useful for specific questions:

| Question | Chart and interpretation |
| --- | --- |
| Which model is each point in the release overview? | [Fully labeled timeline](../assets/benchmark_evolution_detail.png); all inventory rows at their actual dates |
| Which subject domains change alongside task types? | [Task-mode and domain panels](../assets/benchmark_growth_by_all_category.png); model-row-weighted taxonomy composition |
| What does the five-category projection hide? | [Multi-facet trends](../assets/benchmark_facet_trends.png); modality, interaction, and context axes |
| How much reporting does each release contain? | [Benchmark counts](../assets/benchmark_count_per_release.png); mention counts, not evaluation quality |
| Where would source review have the most effect? | [Review-leverage table](readme_story/review_leverage_top.csv); prioritization using exposure and unaccepted labels |

Weighting differs between modules. Some exploratory outputs count raw labels
within model rows; others divide one unit across each benchmark-bearing model
row. These are not interchangeable with announcement counts or equal-announcement
shares. Consult the folder methods before comparing tables.

Run scripts from the repository root with `.venv/bin/python`. The
[full pipeline](../scripts/run_pipeline.sh) regenerates committed outputs; use
`AS_OF=YYYY-MM-DD` for a selected cutoff. Each folder documents its command and
outputs. Taxonomy authoring and source review are separate from reproduction.
