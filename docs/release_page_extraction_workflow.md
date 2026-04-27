# Release Page Benchmark Extraction Workflow

This project tracks benchmark and evaluation names that appear on public model launch pages. The goal is not to recover every benchmark from system cards or technical reports; it is to preserve the public launch-page surface itself as a research signal.

When ingesting a requested release page, every benchmark-like or evaluation-like named item on that page must be captured in the model row. Appearance on the requested page is sufficient; the item does not need to be a primary chart row, a direct model-score row, or a provider-authored benchmark.

Non-negotiable rule: if the requested release page names a benchmark-like or evaluation-like item, include it. Include it even if it appears only once, even if it is in a footnote, even if it is inside an aggregate index, even if it is only a component of another benchmark suite, even if it is shown only in an image/OCR extraction, and even if the maintainer suspects it may later need review. Do not omit first and review later; include first, then normalize or review.

De-duplication rule: the same benchmark run under different settings is still one benchmark mention in `data/models.csv`. Do not create separate model-row mentions for score-setting variants such as with-tools/no-tools, reasoning-effort settings, prompt adjustments, context-length slices, tier slices, needle ranges, pass repeats, or metric display labels when they are clearly runs of the same benchmark. Keep one clean release-page benchmark label and capture setting details only in review notes or future mention-level metadata if needed.

Image/OCR safety rule: do not trust a single OCR pass for benchmark-bearing images. Every image, chart, table screenshot, carousel slide, tab-rendered image, or other same-page JavaScript-revealed visual state that may contain benchmarks should be inspected with multiple independent OCR/review passes, preferably by separate subagents. If any pass finds a benchmark-like/evaluation-like name, include it or move it to review; reject it only after foreground adjudication shows it is clearly not a benchmark or evaluation.

## Why Use A Multi-Agent Review

Benchmark extraction from release pages is not a pure scraping problem. Benchmark names can appear in prose, image tables, JavaScript tabs, captions, methodology links, aggregate-index component lists, suite descriptions, comparison sections, footnotes, or OCR-only chart text. At the same time, release pages contain non-benchmark artifacts that should not become canonical rows: latency metrics, price metrics, chart subtitles, source platforms, task descriptions, model variants, and UI labels.

The recommended workflow therefore uses independent reviewers/subagents as an adjudication layer. The scraper provides candidate evidence; reviewers challenge the candidates from different failure-mode perspectives; the foreground maintainer makes the final source-backed data edit.

## Scope Rule

The requested release page is the source of truth. Include every benchmark-like or evaluation-like named item that appears on the public release page itself. Public page images, tables, captions, alt text, rendered tab content, OCR text, footnotes, comparison text, aggregate-index component lists, and benchmark-suite constituent lists all count as release-page evidence.

Same-page interactive content counts. If a normal reader can reveal content on the requested release page by clicking tabs, carousel next/previous controls, thumbnails, accordions, "show more" controls, or other JavaScript UI without leaving the release page, inspect those states and include benchmark-like/evaluation-like names found there. External links can verify identity, but benchmark names that appear only after navigating to a different page are not added unless the requested release page itself also names them.

The inclusion bar is appearance, not prominence. Do not exclude a benchmark-like named item merely because it is:

- part of an aggregate or intelligence index rather than a direct score row,
- a component benchmark in a suite or methodology list,
- used for comparison, context, or contrast,
- shown only in an image, OCR result, footnote, tab, or secondary section,
- owned by a third party rather than the model provider.

If the page names both a broad suite/index and its constituent benchmarks, include every named benchmark-like item. Store the release-page label in `data/models.csv`; use aliases and canonical taxonomy rows to normalize identity afterward.

This rule is intentionally strict: every benchmark-like/evaluation-like release-page mention is included in the model row unless it is clearly not a benchmark or evaluation at all. Direct evaluation rows, aggregate-index components, suite members, comparison-only benchmark names, and OCR-only benchmark names are all included. When there is uncertainty, inclusion wins.

However, do not double-count repeated mentions or run settings for the same benchmark within one model row. For example, `MMMU Pro (no tools)` and `MMMU Pro (with tools)` should resolve to one `MMMU Pro` mention; `FrontierMath Tier 1-3` and `FrontierMath Tier 4` should resolve to one `FrontierMath` mention; multiple `OpenAI MRCR v2 8-needle` context ranges should resolve to one `OpenAI MRCR v2` mention.

System cards, technical reports, API docs, methodology PDFs, and external benchmark pages can verify identity or definitions, but they should not introduce additional benchmarks that the requested release page itself did not name.

## Image And OCR Review

Images are high-risk evidence because chart labels, footnotes, and comparison rows often exist only inside bitmap assets or JavaScript-controlled slides. Treat each image or interactive visual state as its own extraction unit.

For every potentially benchmark-bearing image:

- capture the visible state or image file and record enough location context to revisit it,
- run at least two independent OCR/review passes, preferably with separate subagents,
- use three passes or a manual zoomed visual inspection for dense, low-resolution, cropped, carousel, or table-heavy images,
- reconcile disagreements in the foreground before editing source CSVs,
- preserve every benchmark-like/evaluation-like name found by any pass unless it is clearly a non-benchmark artifact,
- record uncertainty, OCR ambiguity, or possible chart-label false positives in `data/benchmark_review_queue.csv`.

The output of image reviewers should be image-scoped: image URL or screenshot name, interaction state such as tab/slide label, raw transcribed text, benchmark-like candidates, and rejected non-benchmark labels. Do not merge image OCR candidates into nearest existing benchmarks unless there is an exact canonical match or a source-backed alias.

## Reviewer Roles

| Role | Responsibility | Typical Output |
| --- | --- | --- |
| Source Extractor | Recover all raw benchmark-like, evaluation-like, leaderboard-like, suite-component, and aggregate-index-component names from text, rendered content, image metadata, and OCR evidence. | Exact raw names, source locations, and explicit non-benchmark metrics. |
| Image/OCR Reviewers | Independently inspect each benchmark-bearing or possibly benchmark-bearing image and each same-page interactive visual state. Use multiple reviewers/subagents per image so OCR misses can be caught by disagreement. | Image-scoped transcriptions, candidate benchmark names, interaction-state notes, and OCR ambiguity warnings. |
| False-Positive Auditor | Remove only clear non-benchmark artifacts such as cost, speed, pricing, UI labels, source platforms, descriptive row labels, model families, and wrong variants. Ambiguous benchmark-like names stay included and move to review. | Accepted candidates, rejected candidates, and variant warnings. |
| Catalog Mapper | Map candidates to exact canonical rows or curated aliases; propose new benchmark rows only when needed. | Canonical mappings, narrow alias proposals, new-row proposals, review-queue items. |
| Data Integrity Auditor | Check release date, model name, row order, AS_OF, generated files, and validation commands. | Expected file diffs and validation checklist. |

## Final Adjudication Rules

- Do not use broad generated aliases to improve recall.
- Do not collapse a new benchmark variant into an existing benchmark unless the identity is source-backed.
- Preserve variant words such as `Pro`, `Verified`, `v2`, track names, and leaderboard names.
- If a benchmark-like or evaluation-like name appears on the requested page, include it in `data/models.csv` even when it is only an aggregate-index component, suite constituent, comparison item, footnote item, or OCR-only item.
- Never reject a benchmark-like/evaluation-like page mention solely because it is indirect, secondary, component-level, third-party, low-prominence, or not a model-score table row.
- Do not split the same benchmark into multiple model-row mentions solely because the page reports different run settings, tool settings, context windows, tiers, prompt settings, or metric variants.
- When unsure whether a page item is a benchmark/evaluation or a descriptive label, include it first and record the uncertainty in `data/benchmark_review_queue.csv`.
- Do not rely on one OCR pass for an image. Multiple independent image/OCR passes are required for benchmark-bearing images, and any benchmark-like item found by any pass must be adjudicated.
- Exclude cost, latency, throughput, token price, and the source of those measurements unless the project explicitly adds an efficiency-metric axis later.
- Treat unknown benchmark-like names as review candidates, not as nearest-neighbor matches.
- Record unresolved subset or variant decisions in `data/benchmark_review_queue.csv`.

## Local Workflow

Run the extractor on a single release page:

```bash
python scraping/benchmark_scraper.py extract \
  --url "$URL" \
  --provider "$PROVIDER" \
  --model-name "$MODEL_NAME" \
  --rendered \
  --ocr-images \
  --use-gemini > scraping/output/new_release_extract.json
```

Generate a review packet for subagents or human reviewers:

```bash
python scraping/review_packet.py scraping/output/new_release_extract.json
```

After the independent reviews are reconciled, edit only the source CSVs:

- `data/models.csv` for release-page benchmark mentions.
- `data/benchmarks.csv` for new canonical benchmark rows.
- `data/benchmark_aliases.csv` for narrow source-backed aliases.
- `data/benchmark_review_queue.csv` for unresolved identity, subset, or construct concerns.
- `data/benchmark_metadata_overrides.csv` for source-backed link or author-affiliation corrections.
- `data/benchmark_facet_overrides.csv` for audited multi-facet benchmark annotations.

Then regenerate and validate:

```bash
AS_OF=YYYY-MM-DD
ACCESSED_DATE=YYYY-MM-DD

python scripts/build_normalized_data.py --accessed-date "$ACCESSED_DATE"
python scripts/validate_data.py
python scripts/generate_visuals.py --as-of "$AS_OF" --strict-resolution
python scripts/generate_trend_graph_by_main_category.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python scripts/generate_trend_graph_by_all_category.py --as-of "$AS_OF" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
python scripts/generate_facet_trends.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python scripts/update_readme.py
python scripts/validate_data.py
```
