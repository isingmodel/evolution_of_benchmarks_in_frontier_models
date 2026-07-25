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
Latest local release date in this run: `2026-07-24`.

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

Outputs:

- `normalized_mentions.csv`
- `cascade_metrics.csv`
- `adoption_events.csv`
- `provider_diffusion_roles.csv`
- `provider_role_balance.png`
- `release_strategy_metrics.csv`

Headline results from the current local CSVs:

- 557 benchmark mentions resolve exactly to 196 canonical benchmarks.
- 65 benchmarks show cross-provider cascades; 131 remain single-provider in the observed pages.
- Fastest second-provider cascades:
  - `MMMLU`: Anthropic to OpenAI in 2 days.
  - `Terminal-Bench 2.0`: Google to Anthropic in 6 days.
  - `OfficeQA Pro`: Anthropic to OpenAI in 7 days.
  - `Finance Agent v2`: Google to Anthropic in 9 days.
  - `GDPval-AA v2`: Anthropic to OpenAI in 9 days.
- Slow cross-provider cascades include `ARC-AGI` at 624 days to second provider and `GPQA Diamond` at 484 days.
- Role balance by provider:
  - Anthropic: 68 first-tracked benchmarks, 24 later adopted, 32 imported, net export balance -8.
  - Google: 46 first-tracked benchmarks, 21 later adopted, 26 imported, net export balance -5.
  - OpenAI: 82 first-tracked benchmarks, 20 later adopted, 38 imported, net export balance -18.

Interpretation: OpenAI has the largest unique benchmark vocabulary in these
pages, but many of its first mentions remain provider-specific in the observed
window. Google looks closest to balanced between public benchmark export and
import. Anthropic exports several widely adopted benchmarks but also imports a
large shared evaluation vocabulary.

To make this persuasive, the strongest next step is to pair the lag table with
manual release-page screenshots or citations for the top cascades, then separate
public benchmark creation date from first release-page mention date.

## Prototype B: Portfolio Similarity and Strategic Convergence

Outputs:

- `provider_similarity_timeseries.csv`
- `provider_similarity_latest.csv`
- `portfolio_similarity_over_time.png`
- `release_strategy_metrics.csv`

Latest cumulative benchmark-portfolio Jaccard similarities:

- Anthropic - OpenAI: 0.282
- Anthropic - Google: 0.278
- Google - OpenAI: 0.258

The time series shows early spikes from small portfolio sizes, then a more
stable 2025-2026 band around 0.28-0.35. The `release_strategy_metrics.csv`
table also surfaces high-novelty releases: Google `gemini 1.0` introduced 16
globally new mentions out of 18, while OpenAI `GPT-5.6` introduced 27 of 42
and Anthropic `Claude 5 (Fable/Mythos)` introduced 16 of 25 in 2026.

To make this publishable, annotate major releases directly on the convergence
line chart and add a second panel showing novelty/follower shares per release.
The main caveat is that all mentions are unweighted: a benchmark in a large
appendix table counts the same as a headline benchmark.

## Prototype C: Source-Author Dependency

Outputs:

- `source_author_dependency_by_provider.csv`
- `release_source_author_mix.csv`
- `source_author_mix_by_provider.png`

Mention-share results:

- Self-affiliated frontier-lab source share:
  - OpenAI: 27.4%
  - Anthropic: 20.8%
  - Google: 20.2%
- Academia-sourced share:
  - Google: 47.1%
  - OpenAI: 45.1%
  - Anthropic: 34.9%
- Provider-created lifecycle-risk mention share:
  - Anthropic: 28.3%
  - OpenAI: 27.4%
  - Google: 19.3%

Interpretation: all providers still rely heavily on academic benchmarks, but a
substantial minority of public benchmark attention now flows through
frontier-lab-affiliated or provider-created evaluations. Anthropic's mentions
show the largest share of other-frontier-lab-affiliated benchmark sources in
this run.

To make this persuasive, the source-author labels should get a focused audit,
especially for composite authors and vendor-backed benchmarks. A publishable
section could frame this as an evaluation supply-chain analysis rather than as
a claim about benchmark quality.

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
