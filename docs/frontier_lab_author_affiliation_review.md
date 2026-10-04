# Frontier Lab Author Affiliation Review

This note records the difference between the first local-metadata pass and the later direct-source verification pass for `frontier_lab_author_affiliations` in `data/benchmarks.csv`.

The target labels are:

- `OpenAI`
- `Anthropic`
- `Google`
- `DeepMind`
- `Microsoft`
- `xAI`
- `Meta`

`Google DeepMind` is represented as `Google; DeepMind`. Labels describe benchmark author, creator, maintainer, or evaluator affiliation only. Model providers that merely mention a benchmark, sponsors, funders, backers, and business partners are not counted.

## Changed Rows

| benchmark_id | first_value | source_verified_value |
| --- | --- | --- |
| `benchmark_aime` | `none` | `needs_review` |
| `benchmark_activitynet` | `none` | `needs_review` |
| `benchmark_artificial_analysis_coding_index` | `none` | `needs_review` |
| `benchmark_biology_olympiad` | `none` | `none` |
| `benchmark_bird_sql` | `none` | `needs_review` |
| `benchmark_critpt` | `none` | `needs_review` |
| `benchmark_erqa` | `Google` | `needs_review` |
| `benchmark_facts_grounding` | `Google` | `needs_review` |
| `benchmark_fleurs` | `Google; Meta` | `Google` |
| `benchmark_gpqa` | `Anthropic` | `none` |
| `benchmark_gpqa_diamond` | `Anthropic` | `none` |
| `benchmark_hle_humanity_s_last_exam` | `none` | `OpenAI; Anthropic; Google; DeepMind; Microsoft` |
| `benchmark_hiddenmath` | `Google` | `needs_review` |
| `benchmark_lmarena` | `none` | `needs_review` |
| `benchmark_m3exam` | `none` | `needs_review` |
| `benchmark_mgsm` | `Google` | `needs_review` |
| `benchmark_mrcr` | `OpenAI` | `Google; DeepMind` |
| `benchmark_mrcr_v2` | `OpenAI` | `Google; DeepMind` |
| `benchmark_mtob_benchmark` | `Google` | `none` |
| `benchmark_mathvista` | `none` | `Microsoft` |
| `benchmark_natural2code` | `Google` | `Google; DeepMind` |
| `benchmark_needle_in_a_haystack` | `Microsoft` | `none` |
| `benchmark_omnidocbench` | `none` | `needs_review` |
| `benchmark_omnidocbench_1_5` | `none` | `needs_review` |
| `benchmark_swe_lancer` | `OpenAI` | `needs_review` |
| `benchmark_swe_bench_multimodal` | `Anthropic` | `none` |
| `benchmark_screenspot_pro` | `none` | `needs_review` |
| `benchmark_structural_biology` | `Anthropic` | `Anthropic` |
| `benchmark_tau_bench` | `none` | `needs_review` |
| `benchmark_terminal_bench_2_0` | `none` | `needs_review` |
| `benchmark_terminal_bench` | `none` | `needs_review` |
| `benchmark_toolathlon` | `none` | `needs_review` |
| `benchmark_vatex` | `none` | `needs_review` |
| `benchmark_vibe_eval` | `none` | `needs_review` |
| `benchmark_video_mmmu` | `none` | `needs_review` |
| `benchmark_webvoyager` | `none` | `needs_review` |
| `benchmark_visual_acuity_benchmark` | `none` | removed |

## Rows To Manually Check

### `benchmark_hle_humanity_s_last_exam`

The direct-source pass found dataset contributor affiliations including target labs. Review whether contributor institutions should count as benchmark author affiliations, or whether only organizers/maintainers should count.

Current source-verified value:

```text
OpenAI; Anthropic; Google; DeepMind; Microsoft
```

### `benchmark_gpqa` and `benchmark_gpqa_diamond`

The earlier direct-source pass did not establish an affiliation and conservatively stored `none`. The 2026-10-04 recheck of the primary paper's author block establishes Anthropic affiliation for GPQA and its Diamond subset, superseding that value.

Current source-verified value:

```text
Anthropic
```

### `benchmark_mrcr` and `benchmark_mrcr_v2`

The earlier direct-source pass found the MRCR/Michelangelo paper author affiliations as Google DeepMind and Google Research. The 2026-10-04 audit found that the canonical rows and aliases also cover an expanded OpenAI implementation, so attributing every mapped occurrence to the original paper's authors is not established. Stable identities and aliases remain pending implementation-level adjudication; source authorship, affiliation and identity review are explicitly `needs_review`.

Current source-verified value:

```text
needs_review
```

### `benchmark_fleurs`

The first pass inferred `Google; Meta`, but the direct-source pass treated the Hugging Face `google/fleurs` source as establishing Google only. Review whether the cited FLEURS paper or original dataset history justifies retaining Meta.

Current source-verified value:

```text
Google
```

### `benchmark_swe_lancer`

The direct-source pass could not verify the OpenAI source because the page was blocked by a Cloudflare challenge. The related `benchmark_swe_lancer_ic_diamond` source did verify OpenAI authorship, so this may be a conservative false `needs_review`.

Current source-verified value:

```text
OpenAI
```

### `benchmark_structural_biology`

The Claude Opus 4.7 system card has a life-sciences section that describes the evaluations as internally developed by domain experts and not publicly released. It includes a Structural Biology subsection with multiple-choice and open-ended variants, so this row now counts as an Anthropic internal/private evaluation.

Current source-verified value:

```text
Anthropic
```

### Anthropic Release-Page Internal/Partner Evaluations

Several Anthropic release-page rows require careful distinction between Anthropic-created internal evaluations and third-party partner benchmarks quoted on the page.

Examples:

- `benchmark_swe_bench_multimodal`: changed from `Anthropic` to `none`
- `benchmark_structural_biology`: kept as `Anthropic` after system-card review
- `benchmark_visual_acuity_benchmark`: the earlier removal because it was an external partner's private test was superseded on 2026-10-04. The launch-page appearance policy includes identifiable partner evaluations; the row is restored with XBOW authorship, no frontier-lab author affiliation, and provisional identity/facets.

The key question is whether the source establishes benchmark creation/evaluation ownership, not merely that Anthropic reported the result.

## Follow-Up: Paper-Link Correction

After the direct-source pass, several `needs_review` rows were rechecked for more precise paper links. When a reliable paper or canonical benchmark source was found, `data/benchmarks.csv` was updated with that link and the affiliation was recomputed from the paper/source rather than the stale landing page.

### Resolved By Paper Or Canonical Source

| benchmark_id | updated_reference_link | updated_affiliation |
| --- | --- | --- |
| `benchmark_bird_sql` | `https://arxiv.org/abs/2305.03111` | `none` |
| `benchmark_critpt` | `https://arxiv.org/abs/2509.26574` | `none` |
| `benchmark_erqa` | `https://github.com/embodiedreasoning/ERQA` | `Google; DeepMind` |
| `benchmark_facts_grounding` | `https://storage.googleapis.com/deepmind-media/FACTS/FACTS_grounding_paper.pdf` | `Google; DeepMind` |
| `benchmark_hiddenmath` | `https://storage.googleapis.com/deepmind-media/gemini/gemini_v1_5_report.pdf` | `Google; DeepMind` |
| `benchmark_lmarena` | `https://arxiv.org/abs/2403.04132` | `none` |
| `benchmark_m3exam` | `https://arxiv.org/abs/2306.05179` | `none` |
| `benchmark_mgsm` | `https://openreview.net/forum?id=fR3wGCk-IXp` | `Google` |
| `benchmark_omnidocbench` | `https://arxiv.org/abs/2412.07626` | `none` |
| `benchmark_omnidocbench_1_5` | `https://github.com/opendatalab/OmniDocBench` | `none` |
| `benchmark_swe_lancer` | `https://arxiv.org/abs/2502.12115` | `OpenAI` |
| `benchmark_screenspot_pro` | `https://arxiv.org/abs/2504.07981` | `none` |
| `benchmark_structural_biology` | `https://www.anthropic.com/claude-opus-4-7-system-card` | `Anthropic` |
| `benchmark_tau_bench` | `https://arxiv.org/abs/2406.12045` | `none` |
| `benchmark_terminal_bench_2_0` | `https://arxiv.org/abs/2601.11868` | `Anthropic` |
| `benchmark_terminal_bench` | `https://arxiv.org/abs/2601.11868` | `Anthropic` |
| `benchmark_toolathlon` | `https://arxiv.org/abs/2510.25726` | `none` |
| `benchmark_vatex` | `https://arxiv.org/abs/1904.03493` | `none` |
| `benchmark_vibe_eval` | `https://arxiv.org/abs/2405.02287` | `none` |
| `benchmark_video_mmmu` | `https://arxiv.org/abs/2501.13826` | `none` |
| `benchmark_webvoyager` | `https://arxiv.org/abs/2401.13919` | `none` |

### Removed Rows

| benchmark_id | reason |
| --- | --- |
| `benchmark_visual_acuity_benchmark` | Historical removal, superseded on 2026-10-04: the source explicitly names XBOW's visual-acuity benchmark. Its private partner ownership does not justify exclusion under the current appearance policy. |

## 2026-10-04 Source Corrections

The [Opus 4.7 launch page](https://www.anthropic.com/news/claude-opus-4-7) includes XBOW's visual-acuity benchmark in its CEO testimonial. The restored canonical identity is `Visual-acuity benchmark`, with `source_author=Others(XBOW)` and `frontier_lab_author_affiliations=none`. Its identity and facet rows remain `needs_review`: the source reports percentages but does not disclose a task protocol or metric definition. The surrounding computer-use product description is insufficient to classify the benchmark as a full computer-control task.

Both `GPQA` and its `GPQA Diamond` subset now have `frontier_lab_author_affiliations=Anthropic`. The [primary GPQA paper](https://arxiv.org/html/2311.12022v1) explicitly lists an Anthropic author affiliation and defines Diamond as a subset of GPQA. This supersedes the earlier conservative `none` values; it does not promote identity or facet review statuses.

`MTOB benchmark` now has `frontier_lab_author_affiliations=Google`, retaining `source_author=Academia, Google`. The [primary paper's author block](https://arxiv.org/html/2309.16575v1) explicitly identifies Google alongside universities. Its stable identity denotes Machine Translation from One Book; incorrect mathematical-optimization and image-generation descriptions are superseded by the focused source audit in [the README data audit](readme_data_audit_2026_10_04.md).

MRCR and MRCR v2 now explicitly carry unresolved attribution. The [Michelangelo paper](https://arxiv.org/html/2409.12640v1) establishes the original Google evaluation, while the [OpenAI dataset card](https://huggingface.co/datasets/openai/mrcr) describes an expanded implementation inspired by it. Neither source settles every generic or versioned label mapped by the current catalog. Keep the stable IDs and aliases pending further source review rather than forcing one lab attribution across them.

### Remaining `needs_review`

The historical pass ended with no `frontier_lab_author_affiliations=needs_review` rows. That statement is superseded by the 2026-10-04 MRCR audit: MRCR and MRCR v2 now use `needs_review` for unresolved implementation-level attribution.
