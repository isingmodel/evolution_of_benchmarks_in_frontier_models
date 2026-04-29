# Benchmark Facet Review Guidelines

This guide defines how to convert `needs_review` rows in `data/benchmark_facets.csv` into reviewed facet annotations.

The main rule is simple: review facets by benchmark, not row by row. A facet row can be accepted only when the label, confidence, and rationale are source-backed enough to survive review.

## Scope

Use this guide when reviewing `benchmark_facets.csv`, especially rule-seeded rows with `classification_confidence=0.6`.

Do not use this workflow to canonicalize benchmark identities. If the benchmark identity, alias, or source URL is wrong, fix `data/benchmarks.csv` or `data/benchmark_aliases.csv` first, then return to facet review.

`review_status` has table-local meaning. In `data/benchmarks.csv`, `accepted` means the canonical benchmark identity is accepted. In `data/benchmark_facets.csv`, `accepted` means the specific axis label has been reviewed with enough evidence. Do not promote facet rows only because the benchmark identity row is accepted.

## Review Unit

The review unit is one `benchmark_id`.

For each benchmark, inspect:

- the canonical row in `data/benchmarks.csv`,
- all current rows for that `benchmark_id` in `data/benchmark_facets.csv`,
- the benchmark paper or official benchmark page,
- provider release-page context from `data/models.csv` when release framing matters.

When editing a facet axis, replace the full set of labels for that `benchmark_id + facet_axis`. Do not add one label to an axis without checking whether the old labels still represent the intended interpretation.

## Status Rules

Use `accepted` when:

- the label is supported by an official benchmark page, paper, model card, technical report, or reliable secondary source,
- the axis-level interpretation is not materially contested,
- `classification_confidence >= 0.7`,
- the rationale names the specific evidence used.

Use `needs_review` when:

- the label was inferred mostly from the benchmark name,
- the source URL is missing, unavailable, or too vague for that axis,
- an internal/private benchmark has enough evidence for identity but not enough evidence for the specific facet,
- the complete label set for that axis would be arbitrary,
- the benchmark format appears to vary across versions or provider implementations,
- a source suggests the row may be a metric, subset, setting, or chart label rather than a benchmark-level facet.

Provider-created or private benchmarks can have accepted benchmark identities while still having `needs_review` facet rows. Promote those facet rows only when the public source gives enough axis-level evidence, or mark the lifecycle risk with `provider_created_benchmark` or `private_or_opaque_eval` as appropriate.

Use `disputed` when:

- two plausible source-backed interpretations conflict,
- reviewers disagree on the construct or mechanism,
- provider framing and benchmark documentation make materially different capability claims that cannot both be represented cleanly.

Use `deprecated` when:

- the facet row belongs to a removed canonical benchmark,
- the axis no longer applies after identity cleanup,
- the row represents a release-page surface label that has been remapped to another canonical benchmark.

Do not manually write `legacy_seed` during review. Treat it as a generated status for rows that have not received v3 facet review.

## Confidence Scale

Use confidence as evidence quality, not benchmark importance.

| Confidence | Meaning | Status |
| ---: | --- | --- |
| `0.95` | Official benchmark paper/card gives explicit task format, domain, modality, and scoring. | `accepted` |
| `0.85` | Official source is clear; only minor interpretation is needed. | `accepted` |
| `0.75` | Public source plus release-page context supports the label, but details are partial. | `accepted` or `needs_review` |
| `0.65` | Partial evidence or notable ambiguity remains. | `needs_review` |
| `0.60` | Rule-seeded from legacy fields, benchmark name, or broad rationale. | `needs_review` |
| `<0.60` | Name-only guess or weak source. | `needs_review` or `disputed` |

Validation requires low-confidence rows below `0.7` to remain `needs_review` or `disputed`.

## Multi-Label Rules

Within a single `benchmark_id + facet_axis`, include each supported label once. Do not store per-label weights. Downstream trend scripts divide a benchmark's contribution equally across labels within the same axis.

Avoid more than three labels on one axis unless the benchmark is explicitly a composite suite or aggregate index. If equal sharing would badly misrepresent the benchmark, keep the axis in `needs_review` and explain the issue in `rationale`.

## Axis Rules

### `construct_claim`

Use this for the capability the benchmark is intended or used to measure. Prefer the benchmark creator's claim unless the row exists only because a provider release page uses it in a different way.

If the benchmark creator's claim and provider claim differ materially, preserve the distinction in the rationale. Optional `benchmark_construct_claim` and `provider_construct_claim` axes may be introduced later for high-value disputed cases, but the current reviewed table should remain compact unless the distinction changes analysis.

### `task_mechanism`

Use this for what the model actually does. This axis should be more operational than `construct_claim`.

Examples:

- SWE-style issue repair: `repository_issue_resolution`
- static coding prompt: `code_generation`
- terminal benchmark: `terminal_operation`
- browser benchmark: `browser_navigation`
- document parsing benchmark: `document_parsing`
- safety refusal benchmark: `adversarial_refusal` or `format_constrained_output`, depending on the actual task.

### `domain`

Use the domain needed to perform the benchmark, not the provider's marketing category.

Use fine-grained labels such as `Law`, `Bio/Medicine`, `Finance`, `Cybersecurity`, and `Visual/Document` when evidence supports them. Use `Other Specialized` only when the domain is specialized but does not fit a more precise allowed label.

### `modality`

Use this for the input/output medium or interface.

Use `multimodal_mixed` when multiple modalities are central and cannot be reduced to one primary modality. Use interface labels such as `browser_ui`, `desktop_ui`, and `tool_api` when the benchmark evaluates interaction with that interface.

### `interaction_pattern`

Use this for the interaction structure.

Do not label every tool-using benchmark as fully agentic. Distinguish:

- `static_prompt_response`: no external environment interaction,
- `single_turn_tool_use`: one-shot or bounded tool/API use,
- `multi_step_planning`: multi-step plan without a persistent external environment,
- `environment_interaction`: broader external environment interaction,
- `browser_or_web_interaction`: browser or live web tasks,
- `terminal_or_codebase_interaction`: terminal, repository, or command-line work,
- `computer_control`: desktop/OS control.

### `metric_type`

Use the scoring method reported by the source.

Use `unknown` only after checking the source and failing to find a scoring method. Pair `unknown` with `benchmark_lifecycle_risk=unclear_metric` when the missing metric affects interpretability.

Do not infer `accuracy` as a default merely because a benchmark reports a percentage.

### `context_pressure`

Use `long_context_primary` only when long context is the core bottleneck, such as needle retrieval or long-document reasoning where the task is designed around context length.

Use `long_context_supporting` when long documents or long trajectories are present but the main construct is agentic task completion, document understanding, coding, or domain reasoning.

Use `none` only when context length is not a meaningful part of the benchmark design.

### `benchmark_lifecycle_risk`

Use this axis to preserve limitations, not to punish a benchmark.

Common choices:

- `provider_created_benchmark`: authored or primarily controlled by a frontier lab or benchmark vendor,
- `private_or_opaque_eval`: internal benchmark or insufficiently public task/scoring details,
- `version_instability`: benchmark has changing tasks, verified splits, live sites, or moving leaderboards,
- `contamination_risk`: static public data is likely to appear in training corpora,
- `saturation_risk`: benchmark is known or likely to be near-saturated,
- `unclear_metric`: scoring is not public or is hard to interpret,
- `construct_validity_risk`: benchmark-to-claim mapping is weak or contested,
- `distribution_shift_risk`: deployment target differs materially from benchmark data.

Use `none_identified` only after a real review. Do not preserve rule-seeded `none_identified` by inertia.

### `headline_task_mode`

This is a visualization projection, not a benchmark identity.

The canonical `benchmark_facets.csv` no longer stores `headline_task_mode`
rows. Chart scripts derive a single-label projection at runtime from the
reviewed v3 axes when they need a readable headline category.

Runtime projections use the legacy chart labels:

- `Agentic`
- `Multimodal Perception`
- `Constraint Satisfaction`
- `Generative Reasoning`
- `Knowledge Retrieval`

Derive this projection only after reviewing the other axes. Use the priority from the main methodology:

1. long-context projection, represented in this CSV as `Knowledge Retrieval`, only when `context_pressure=long_context_primary`,
2. `Agentic`,
3. `Multimodal Perception`,
4. `Constraint Satisfaction`,
5. `Generative Reasoning`,
6. `Knowledge Retrieval`.

If the projection feels wrong, revisit the underlying facets first rather than
adding a permanent headline row.

## Editing Workflow

Preferred workflow:

1. Select a batch of benchmark IDs.
2. Review all axes for each benchmark.
3. Write proposed rows to temporary `data/benchmark_facet_manual.csv`.
4. Include every row for each touched `benchmark_id + facet_axis`, not only changed labels.
5. Run `python scripts/build_normalized_data.py`.
6. Run `python scripts/validate_data.py`.
7. Inspect the diff in `data/benchmark_facets.csv`.
8. Remove `data/benchmark_facet_manual.csv` after integration.

Only edit `data/benchmark_facets.csv` directly for small foreground corrections where the full axis replacement is obvious.

## Reviewer Output Contract

When asking humans or subagents to review facets, request this output per benchmark:

| Field | Meaning |
| --- | --- |
| `benchmark_id` | Canonical benchmark ID. |
| `source_checked` | Official page, paper, release page, or other source reviewed. |
| `facet_rows` | Complete replacement rows for every reviewed axis. |
| `status_decision` | Which axes can become `accepted`, remain `needs_review`, or become `disputed`. |
| `confidence_notes` | Why each confidence is above or below `0.7`. |
| `open_questions` | Remaining uncertainty that should not be hidden. |

Do not ask reviewers to return a status-only patch.

## Batch Strategy

Recommended order:

1. Public, well-documented benchmarks whose `benchmarks.csv` rows are already `accepted`.
2. Public, classic `legacy_seed` benchmarks with official papers/pages.
3. Composite suites and aggregate indexes.
4. Provider-created or private benchmarks.
5. Ambiguous release-page labels and variants.

This order reduces review debt quickly without converting the hardest ambiguous cases by force.
