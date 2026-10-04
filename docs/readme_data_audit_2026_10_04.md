# Source-data audit for the README revision

This targeted audit checks source fidelity and interpretation after the release refresh and lifecycle analysis. It is not a fresh extraction of every historical page.

## Corrections applied

### XBOW visual-acuity evaluation

The [Claude Opus 4.7 announcement](https://www.anthropic.com/news/claude-opus-4-7), in Oege de Moor's XBOW testimonial, names a visual-acuity benchmark and reports 98.5% for Opus 4.7 against 54.5% for Opus 4.6. The earlier affiliation audit excluded it solely because it was a private partner evaluation. That exclusion conflicts with the current [release-page appearance policy](release_page_extraction_workflow.md), which includes identifiable partner and private evaluations.

The stable `benchmark_visual_acuity_benchmark` identity is restored as `Visual-acuity benchmark`, with `source_author=Others(XBOW)`, affiliation `none`, and identity status `needs_review`. The exact lowercase page label is appended to the Opus 4.7 model row and resolved through one narrow case alias.

The testimonial does not disclose task instances, interaction protocol or metric definition. All eight new facets remain provisional. Image/perception labels are tentative; static-response and visual-question-answering labels are low-confidence schema placeholders, not verified task definitions. Metric type is `unknown`; the evaluation is marked private/opaque. No computer-control or cybersecurity task claim is inferred from XBOW's product description.

### GPQA author affiliation

The [primary GPQA paper](https://arxiv.org/html/2311.12022v1) explicitly lists an Anthropic author affiliation and defines Diamond as a subset of GPQA. Both catalog affiliation fields are corrected from `none` to `Anthropic`. Their identity and facet statuses are not promoted.

### Real Toxicity Prompts omission

The stored [Gemini 1.0 announcement](https://blog.google/innovation-and-ai/technology/ai/google-gemini-ai/) explicitly names Real Toxicity Prompts in its safety section and credits the Allen Institute for AI. Its link resolves to the [official dataset](https://huggingface.co/datasets/allenai/real-toxicity-prompts); the [official repository](https://github.com/allenai/real-toxicity-prompts) documents text generation and toxicity scoring. The omitted name is now appended to that inventory row and recorded as `benchmark_real_toxicity_prompts`, with `source_author=Others(Allen Institute for AI)`, affiliation `none`, and eight conservative provisional facets. Google release-page hosting does not establish Google benchmark authorship. Exact Gemini task settings and scoring remain undisclosed.

### MTOB identity and task classification

The [MTOB repository](https://github.com/lukemelas/mtob) defines Machine Translation from One Book: English/Kalamang translation using language-reference materials. The catalog's math-optimization description and its image-generation facet rationales were incorrect. The [Gemini 1.5 announcement](https://blog.google/innovation-and-ai/products/google-gemini-next-generation-model-february-2024/) explicitly uses it to demonstrate learning from a long grammar-manual prompt. The [paper author block](https://arxiv.org/html/2309.16575v1) lists Google and academic affiliations, so the existing `Academia, Google` source author is retained and frontier-lab affiliation is corrected from `none` to `Google`.

The stable identity is unchanged and accepted after two independent primary-source checks. Sixteen incorrect facets are replaced with ten source-grounded rows. Seven directly documented labels are accepted: textual translation generation, Multilingual domain, static translation responses, long-context-primary framing, known chrF scoring represented by the vocabulary's `unknown` metric label, and a documented contamination concern with mitigation. The three long-context construct/mechanism mappings remain provisional because the vocabulary has no translation-learning construct. Shorter and retrieval-based experimental variants also exist; the long-context label does not describe every run. The legacy domain remains `General/Commonsense` because that older schema has no Multilingual option.

MTOB appears in the two-name Gemini 1.5 source row. Correcting its context label therefore changes Google's 2024 release-weighted context shares materially, without adding a benchmark mention. Regenerated summaries replace the earlier values.

## Unresolved metadata

The [Michelangelo paper](https://arxiv.org/html/2409.12640v1) introduces MRCR with Google DeepMind/Google Research authors. The [OpenAI MRCR dataset card](https://huggingface.co/datasets/openai/mrcr) describes a more difficult OpenAI implementation inspired by that original evaluation. The prior catalog mixed these histories: MRCR entries carried OpenAI source authorship and Google/DeepMind affiliation, and v2 aliases mapped both OpenAI and GDM-prefixed labels to one identity. Both rows now explicitly use `needs_review` for source author, affiliation and identity status. Stable IDs and aliases remain pending implementation-level adjudication; neither blanket attribution nor an automatic split is justified by this audit.

Downstream source-author classification must treat unresolved sentinels as unknown, not as an independent organization or another frontier lab. Linked-author shares describe identified attribution within a full mention denominator; they are not a complete measure of influence.

HLE's affiliation field includes contributor institutions from several frontier labs. The existing [affiliation audit](frontier_lab_author_affiliation_review.md) explicitly leaves open whether contributors should count alongside organizers and maintainers. Source-author influence claims therefore depend on unresolved attribution policy as well as mention counts.

## Historical extraction limits

A spot check of the stored [Gemini 1.0 announcement](https://blog.google/innovation-and-ai/technology/ai/google-gemini-ai/) found the Real Toxicity Prompts omission corrected above. It also names plain MMLU and MMMU, while the inventory stores combined family labels. This focused correction does not re-extract the historical series. Historical version identities need a separate page-level pass; current combined identities describe legacy family normalization, not universally verbatim joint chart labels or exact version histories. The earlier blanket assertion in [the audit notes](benchmark_audit_notes.md) is corrected accordingly.

## README interpretation requirements

- The source is a selected release-page series, including restricted and cyber launches. It is not an exhaustive model or evaluation history.
- A recorded association means a named evaluation appears on the page. Comparison-only names, suite components, footnotes and partner testimonials count; prominence and model-specific scores are not recorded.
- Shared-page model rows each inherit the full page set. Existing portfolio measures weight those model rows separately; lifecycle measures collapse provider/date/normalized-URL launches.
- Aggregate indices and their named components can both appear. Counts describe named evaluation identities, not independent statistical evidence.
- Release pages can be edited. The October refresh fully inspected new pages and selectively rechecked older ones; launch dates do not identify when every mention first appeared online. No per-mention historical snapshot is stored.
- Identity acceptance is separate from facet review. Before this targeted audit, only 29 of 4,042 facet rows were accepted, all belonging to HumanEval and GSM8K. The MTOB correction adds seven accepted facets; most facets remain provisional. High numerical confidence alone does not mean a facet was accepted.
- First and last tracked mentions delimit observed reporting spans. They do not establish creation, retirement, saturation or replacement, and omission does not establish non-use.

## Stale synthesis resolved

The audit initially found `analysis/SYNTHESIS.md` presenting an earlier July snapshot as current. That finding is resolved: the [current synthesis](../analysis/SYNTHESIS.md) now points to generated evidence without duplicating changing headline numbers, and the [historical meta-review](../analysis/meta_review/README.md) explicitly archives earlier numerical quotations and editorial judgments. Regenerated CSVs, with their documented denominators and sensitivity checks, supply current README claims.

The full pipeline was regenerated after these corrections; all 793 raw mentions resolve, and all 60 tests pass. Current counts, tables, and figures use the corrected inputs.
