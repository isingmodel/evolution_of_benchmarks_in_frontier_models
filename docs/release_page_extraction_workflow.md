# Release Page Benchmark Extraction Workflow

This project tracks benchmarks that providers choose to emphasize on public model launch pages. The goal is not to recover every benchmark from system cards or technical reports; it is to preserve public launch-page positioning as a research signal.

## Why Use A Multi-Agent Review

Benchmark extraction from release pages is not a pure scraping problem. Benchmark names can appear in prose, image tables, JavaScript tabs, captions, methodology links, or OCR-only chart text. At the same time, release pages contain many benchmark-adjacent items that should not become canonical rows: latency metrics, price metrics, chart subtitles, source platforms, task descriptions, model variants, and benchmark family names.

The recommended workflow therefore uses independent reviewers/subagents as an adjudication layer. The scraper provides candidate evidence; reviewers challenge the candidates from different failure-mode perspectives; the foreground maintainer makes the final source-backed data edit.

## Scope Rule

Include a benchmark only when it is emphasized on the public release page itself. Public page images, tables, captions, alt text, and rendered tab content count as release-page evidence. System cards, technical reports, API docs, and methodology PDFs can verify identity or definitions, but they should not introduce additional benchmarks that the public release page did not foreground.

## Reviewer Roles

| Role | Responsibility | Typical Output |
| --- | --- | --- |
| Source Extractor | Recover all raw benchmark-like and leaderboard-like names from text, rendered content, image metadata, and OCR evidence. | Exact raw names, source locations, and explicit non-benchmark metrics. |
| False-Positive Auditor | Remove cost, speed, pricing, source datasets, descriptive row labels, model families, and wrong variants. | Accepted candidates, rejected candidates, and variant warnings. |
| Catalog Mapper | Map candidates to exact canonical rows or curated aliases; propose new benchmark rows only when needed. | Canonical mappings, narrow alias proposals, new-row proposals, review-queue items. |
| Data Integrity Auditor | Check release date, model name, row order, AS_OF, generated files, and validation commands. | Expected file diffs and validation checklist. |

## Final Adjudication Rules

- Do not use broad generated aliases to improve recall.
- Do not collapse a new benchmark variant into an existing benchmark unless the identity is source-backed.
- Preserve variant words such as `Pro`, `Verified`, `v2`, track names, and leaderboard names.
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
- `data/benchmark_taxonomy_v2.csv` for new canonical benchmark rows.
- `data/benchmark_aliases.csv` for narrow source-backed aliases.
- `data/benchmark_review_queue.csv` for unresolved identity, subset, or construct concerns.

Then regenerate and validate:

```bash
AS_OF=YYYY-MM-DD
ACCESSED_DATE=YYYY-MM-DD

python scripts/build_v3_data.py --accessed-date "$ACCESSED_DATE"
python scripts/validate_data.py
python scripts/apply_mention_prominence.py --dry-run
python scripts/generate_visuals.py --as-of "$AS_OF" --strict-resolution
python scripts/generate_trend_graph_by_main_category.py --as-of "$AS_OF" --window-days 180 --strict-resolution
python scripts/generate_trend_graph_by_all_category.py --as-of "$AS_OF" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution
python scripts/generate_v3_facet_trends.py --as-of "$AS_OF" --window-days 180
python scripts/update_readme.py
python scripts/validate_data.py
```
