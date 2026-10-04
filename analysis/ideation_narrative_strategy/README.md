# Provider Narrative Strategy Prototypes

This folder explores benchmark selection and task-composition patterns on public
launch pages. Names and taxonomy labels can suggest reporting emphasis, but they
do not establish provider intent, page rhetoric, evaluation prominence, or model
capability. The [project overview](../project_overview/README.md) supplies current
preface evidence; this module retains exploratory measures.

```bash
.venv/bin/python analysis/ideation_narrative_strategy/analyze.py --as-of 2026-09-30
```

Resolution uses exact canonical names and explicit aliases, without fuzzy
matching. The inventory retains resolved raw label occurrences within model
rows. Composition shares divide one unit across each benchmark-bearing model
row's mentions; jointly announced model variants can contribute several units,
and repeated aliases can retain weight. Multiple labels on an axis divide a
mention's weight across those labels. These conventions differ from the
overview's canonical, announcement-level weighting.

## Generated evidence

Use the generated tables for the selected run's values, rather than copied
numeric summaries:

| Output | Purpose |
| --- | --- |
| [mention_inventory.csv](mention_inventory.csv) | Resolved raw occurrences and derived flags |
| [launch_benchmark_density.csv](launch_benchmark_density.csv) | Mention counts by model row, including rows with empty lists |
| [provider_headline_portfolio.csv](provider_headline_portfolio.csv) | Model-row-normalized headline projections |
| [provider_signature_lift.csv](provider_signature_lift.csv) | Provider shares relative to the pooled portfolio |
| [release_strategy_frames.csv](release_strategy_frames.csv) | Per-row static, broad software/tool, multimodal/UI, and domain flags |
| [annual_strategy_frames.csv](annual_strategy_frames.csv) | Annual means and benchmark-bearing row counts |
| [risk_private_usage_by_release.csv](risk_private_usage_by_release.csv) | Release-level provider-created, private/opaque, and internal-name flags |
| [risk_private_usage_by_provider.csv](risk_private_usage_by_provider.csv) | Provider-level versions of those measures |
| [provider_risk_portfolio.csv](provider_risk_portfolio.csv) | Lifecycle-risk label composition |
| [unresolved_mentions.csv](unresolved_mentions.csv) | Resolution failures requiring curation |

The heatmap and historical `static_to_work_simulation_trend.png` and
`provider_created_or_private_escalation.png` visualize these tables. Values,
cohorts, and rankings can change after source corrections or taxonomy review.

## Definitions and limits

The historical `is_work_simulation` field is a **broad software/tool proxy**:
a qualifying interaction pattern, mechanism, or construct claim is sufficient.
It includes planning, human involvement, unit-test passing, code repair, SQL
generation, and software-engineering claims. Static coding tests can qualify;
the flag does not demonstrate operation in a work environment. The static-exam
flag excludes anything matching this proxy, so the two shares are not independent
natural categories.

For the narrower five-label interaction measure, original-weight confidence
sensitivity, and accepted-label coverage, use the
[overview methods](../project_overview/README.md) and
[interaction trends](../project_overview/interaction_trends.csv). The
[older story module](../readme_story/README.md) documents additional broad-proxy
filters and their changing denominators.

Headline task modes are derived projections over a multifacet annotation table,
not exclusive identities or stable provider characteristics. Nondeprecated
provisional facets are included. Source-definition corrections such as MTOB's
translation task can alter earlier portfolio summaries.

Provider-created does not mean private, same-provider-authored, or internal.
The combined provider-created/private flag must not be interpreted as an opacity
measure. Keep authorship, restricted access, and internal naming separate.

Density counts recorded labels per model row. Shared pages, named components,
comparison mentions, and extraction coverage affect the count. Empty lists stay
in density outputs but cannot contribute to normalized composition.

## Useful questions and additional evidence

The local tables can support descriptive comparisons of task portfolios, domain
mixes, first-seen/reused names, and annotation-risk flags. Check sample sizes and
provider-specific trends before interpreting pooled changes.

Stronger narrative questions require mention-level source evidence:

- Page sections, heading placement, table order, footnotes, and result presence
  can distinguish prominence from incidental appearance.
- Claim verbs, adjectives, caveats, and “real-world” wording can test actual
  rhetoric rather than infer it from taxonomy.
- Score values, baselines, and comparison protocols require separate extraction;
  name presence alone cannot establish a performance claim.
- Access and reproducibility statements can distinguish provider authorship from
  private or opaque evaluation design.

Add source offsets and source-linked review before presenting these ideas as
findings about positioning. Benchmark-family lineage and announcement-level
sensitivity would also help separate version changes from portfolio change.
