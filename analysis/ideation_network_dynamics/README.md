# Network, Diffusion, and Competitive Dynamics Ideation

This folder prototypes analyses over benchmark mentions on public frontier model
release pages. The unit of observation is a public mention/adoption signal, not
a direct measurement of model capability.

Run from the repository root:

```bash
.venv/bin/python analysis/ideation_network_dynamics/analyze.py
```

The script uses `scripts/taxonomy_utils.py` and `CanonicalResolver` for exact
canonical names plus explicit aliases. It does not fuzzy match benchmark names.
Latest local release date in this run: `2026-09-30`.

## Ideation Catalog

| Idea | Core question | Persuasive evidence | Current data gaps | Publishable chart or section |
|---|---|---|---|---|
| Benchmark import/export ledger | Which providers first surface benchmarks, and which later import them? | Clear first-provider ordering, cross-provider adoption lags, role balance by provider. | Public pages may omit quiet internal eval use; benchmark creation dates are absent. | Provider import/export bar chart plus case-study table of exported benchmarks. |
| Adoption cascade speed | Which benchmarks become shared competitive currency fastest? | Days from first mention to second and third provider, split by benchmark family/facet. | Only three providers; same-day releases are coarse at daily resolution. | Lollipop chart of cascade lag, colored by task mode or source author. |
| Attention half-life | Do benchmarks get most public attention immediately or after long diffusion? | Time from first mention to 50% of observed mentions and active-span days. | Right-censoring for recent benchmarks; release cadence differs by provider. | Scatter of active span vs time-to-half-attention with labels for outliers. |
| Strategic convergence clock | Are providers' benchmark portfolios getting more similar? | Pairwise cumulative Jaccard over time, with release annotations for big jumps. | Jaccard treats all mentions equally and ignores benchmark prominence on pages. | Time-series panel of provider-pair similarity. |
| Differentiation releases | Which releases introduce novel public eval framing instead of repeating consensus benchmarks? | Per-release share of globally new, new-to-provider, self-repeat, and already-other-provider benchmarks. | No weighting by page placement, table size, or headline emphasis. | Release scatter: novelty share vs follower share, sized by benchmark count. |
| Co-mention communities | Which benchmarks travel together as bundles on release pages? | Weighted co-occurrence network from same-release benchmark sets. | Large release tables create dense cliques; needs thresholding or backbone extraction. | Network map or clustered matrix of benchmark bundles. |
| Benchmark bridges | Which benchmarks connect otherwise distinct evaluation communities? | High weighted degree or betweenness in the co-mention graph. | Robust betweenness needs a richer graph and possibly more providers/releases. | "Bridge benchmark" ranked table with neighboring communities. |
| Source-author dependency | How much public eval attention depends on academia, independent vendors, or frontier-lab-authored benchmarks? | Mention shares by source group and provider, plus provider-created lifecycle-risk flags. | Authorship labels need periodic review; affiliation does not equal control. | Stacked source-author mix bars and a section on evaluation supply chains. |
| Cross-provider follower graph | Whose benchmark vocabulary does each provider appear to follow? | For each imported benchmark, edge from prior provider(s) to adopting provider weighted by lag. | Multiple first movers and common academic benchmarks complicate causal claims. | Directed provider graph with edge labels for median lag. |
| Facet-specific contagion | Do agentic, coding, multimodal, or long-context benchmarks diffuse at different rates? | Cascade-lag distributions by `legacy_task_mode`, domain, or v3 facets. | Some facets are still `needs_review`; sparse counts in newer categories. | Small multiples of cascade lag by facet. |
| Version/alias drift | Are providers converging on canonical benchmark versions or using variant names strategically? | Raw variant count per canonical benchmark and provider/date paths. | Alias table intentionally exact; unlisted variants remain unresolved until curated. | Timeline of canonical benchmark name variants. |
| Evaluation supply-chain concentration | Is attention concentrating around a few benchmark authors or vendors? | Herfindahl/entropy over source authors by year/provider. | Source-author names mix institutions and composite collaborations. | Stacked area or entropy trend by source group. |

## Prototype A: Cascades and First-Mover Roles

Outputs: `normalized_mentions.csv`, `cascade_metrics.csv`, `adoption_events.csv`, `provider_diffusion_roles.csv`, `provider_role_balance.png`, and `release_strategy_metrics.csv`.

The refreshed local outputs resolve 791 raw mentions to 286 canonical benchmarks. They identify 74 cross-provider cascades and 212 single-provider benchmarks.

Fastest observed second-provider mentions:

| Benchmark path | Days |
| --- | ---: |
| Terminal-Bench 4.0: Anthropic -> Google | 1 |
| MMMLU: Anthropic -> OpenAI | 2 |
| Terminal-Bench Science 0.1: Anthropic -> OpenAI | 2 |
| Terminal-Bench 2.0: Google -> Anthropic | 6 |
| OfficeQA Pro: Anthropic -> OpenAI | 7 |

These are first tracked public mentions, not benchmark creation or private adoption dates. Use `provider_diffusion_roles.csv` for current provider role counts and `release_strategy_metrics.csv` for novelty and reuse. Pair any diffusion claim with source-page evidence and benchmark publication dates.

## Prototype B: Portfolio Similarity and Strategic Convergence

Outputs: `provider_similarity_timeseries.csv`, `provider_similarity_latest.csv`, `portfolio_similarity_over_time.png`, and `release_strategy_metrics.csv`.

Cumulative portfolio overlap at `2026-09-30`:

| Provider pair | Jaccard similarity |
| --- | ---: |
| Anthropic - Google | 0.249 |
| Anthropic - OpenAI | 0.231 |
| Google - OpenAI | 0.219 |

The time series can fluctuate when portfolios are small. Similarity describes shared benchmark vocabulary and does not establish copying, provider intent, or capability. Use the release-level strategy CSV for current novelty counts rather than inferring them from the overlap chart. Annotate major releases and portfolio sizes before foregrounding the chart.

## Prototype C: Source-Author Dependency

Outputs: `source_author_dependency_by_provider.csv`, `release_source_author_mix.csv`, and `source_author_mix_by_provider.png`.

Current raw-mention shares:

| Provider | Self-affiliated | Academia-sourced | Provider-created risk |
| --- | ---: | ---: | ---: |
| Anthropic | 20.2% | 31.9% | 25.1% |
| Google | 13.0% | 39.9% | 13.0% |
| OpenAI | 33.1% | 40.7% | 22.6% |

These flags are non-exclusive and inherit the taxonomy's source and affiliation annotations. Authorship does not establish benchmark control, and provider-created does not imply private. Audit composite authors and provisional lifecycle-risk labels before making evaluation-supply-chain claims.

## Generated Files

- `analyze.py`
- `manifest.json`
- `summary_metrics.csv`
- `normalized_mentions.csv`
- `cascade_metrics.csv`
- `adoption_events.csv`
- `provider_diffusion_roles.csv`
- `release_strategy_metrics.csv`
- `provider_similarity_timeseries.csv`
- `provider_similarity_latest.csv`
- `source_author_dependency_by_provider.csv`
- `release_source_author_mix.csv`
- `portfolio_similarity_over_time.png`
- `provider_role_balance.png`
- `source_author_mix_by_provider.png`
