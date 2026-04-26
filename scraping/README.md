# Benchmark Scraping Workflow

This directory contains an experimental scraper for extracting benchmark mentions from public model release pages.

The key design choice is to avoid asking an LLM to read an arbitrary web page from scratch. Release pages often spread benchmark names across normal text, tables, JavaScript-rendered tabs, image alt text, and serialized page data. The scraper therefore uses a staged pipeline:

1. Collect as much page evidence as possible from static HTML.
2. Optionally render the page with Playwright and click benchmark-like tabs/buttons.
3. Optionally run OCR over benchmark/performance-like images.
4. Match a canonical benchmark catalog built from `data/benchmarks.csv` and the small, curated `data/benchmark_aliases.csv` seed list.
5. Optionally ask Gemini to perform evidence-first extraction: identify raw benchmark mentions from text/rendered/OCR evidence, accept only exact or explicitly curated catalog mappings, and route uncertain or new names to review fields.
6. Evaluate extraction quality against the existing `data/models.csv` `benchmarks` column.

The current implementation treats `data/models.csv` as an answer key. That makes it useful for regression tests before applying the scraper to new model release links.

## Methodology

The scraper deliberately avoids broad generated aliases as the main solution. Alias expansion can inflate recall on a fixed gold file while creating brittle false positives for future benchmark names. The safer workflow is:

1. Collect high-coverage evidence from static HTML, reader markdown, Playwright-rendered text, image metadata, and OCR.
2. Use deterministic catalog matching only for exact canonical names and explicitly curated aliases.
3. Use Gemini, when requested, as a conservative evidence-grounded extractor rather than as a post-hoc synonym generator.
4. Automatically accept only exact canonical names and explicitly curated aliases from `data/benchmark_aliases.csv`.
5. Put semantic mappings, family/variant rollups, OCR corrections, low-confidence mappings, and catalog-missing names into `review_required_mentions`.
6. Keep catalog-missing benchmark-like names in `llm_unknown_mentions` as candidates for `data/benchmarks.csv`.

This makes the pipeline more useful for new release pages: a new benchmark should surface as an unknown candidate instead of being silently forced into the nearest existing alias.

## Multi-Agent Review Framework

For new model releases, use the scraper as an evidence generator rather than a fully automatic writer. The recommended review split is:

1. **Source extractor**: recover every benchmark-like, evaluation-like, suite-component, and aggregate-index-component name from prose, rendered tabs, images, alt text, captions, footnotes, and OCR.
2. **False-positive auditor**: reject only clear non-benchmark artifacts such as cost/speed/price metrics, source platforms, chart subtitles, UI labels, descriptions, model-family names, and wrong variants.
3. **Catalog mapper**: map only exact canonical names or explicit source-backed aliases; propose new benchmark rows or review-queue entries for unresolved variants.
4. **Data-integrity auditor**: verify model name, release date, row order, `AS_OF`, generated files, and validation commands.

For requested release pages, inclusion wins: if the page names a benchmark-like or evaluation-like item, keep it for `data/models.csv` even when it appears only as a footnote, aggregate-index component, suite member, comparison item, or OCR-only chart label. Do not split the same benchmark into multiple model-row mentions only because the page reports different run settings such as with-tools/no-tools, tiers, context ranges, prompt settings, or metric variants.

Generate a reusable review packet from one extraction JSON:

```bash
python scraping/review_packet.py scraping/output/new_release_extract.json
```

See `docs/release_page_extraction_workflow.md` for the full adjudication rules.

## Acceptance Policy

The scraper separates extracted mentions into two lanes:

| Lane | Meaning | Examples |
| --- | --- | --- |
| `accepted_mentions` | Safe to count as extracted benchmark mentions. | `GPQA Diamond -> GPQA Diamond`, `HLE -> HLE (Humanity's Last Exam)` when `HLE` is an explicit alias. |
| `review_required_mentions` | Evidence-backed but not safe to auto-map. | `GPQA (diamond) -> GPQA Diamond`, `MRCR v2 -> MRCR`, OCR-corrected names, or a new `NewAgentBench`. |
| `llm_unknown_mentions` | Subset of review items that do not map to any current catalog row. | A newly introduced benchmark absent from `data/benchmarks.csv`. |

This policy intentionally sacrifices some automatic recall. The goal is to avoid silent data corruption when a new benchmark resembles an existing one.

## Commands

Evaluate static HTML extraction against all rows with a non-empty benchmark answer:

```bash
python scraping/benchmark_scraper.py evaluate
```

Evaluate a small sample:

```bash
python scraping/benchmark_scraper.py evaluate --max-pages 5
```

Use Playwright rendering and tab/button clicks:

```bash
python scraping/benchmark_scraper.py evaluate --rendered --max-pages 5
```

Use image OCR for benchmark charts:

```bash
python scraping/benchmark_scraper.py evaluate --rendered --ocr-images --max-pages 5
```

Extract one page:

```bash
python scraping/benchmark_scraper.py extract \
  --url https://www.anthropic.com/news/claude-opus-4-6 \
  --provider Anthropic \
  --model-name "Claude 4.6 (Opus)" \
  --rendered \
  --ocr-images
```

Use Gemini as the evidence-first extractor and conservative catalog mapper:

```bash
python scraping/benchmark_scraper.py evaluate --rendered --ocr-images --use-gemini --max-pages 3
```

Gemini uses `secrets/gemini_api_key.txt` by default, matching the existing classification scripts.

## Output

Evaluation reports are written under `scraping/output/` by default and are ignored by git. The report includes page-level recall, precision, missing benchmark names, extra extracted benchmark names, accepted mentions, review-required mentions, LLM-added catalog names, raw LLM mentions, accepted raw-to-canonical LLM mappings, LLM unknown mentions, and fetch errors.

Strict exact-match metrics can still flag legitimate granularity differences, such as a page saying `GPQA (diamond)` while the current answer key uses `GPQA`. Those should be treated as review cases, not patched over with broad aliases.

## Limitations

This is a high-recall candidate extractor, not a fully automatic canonical data writer. OCR quality varies sharply by chart resolution, font size, and image format. The optional LLM stage can reason over OCR, text, metadata, and image alt/caption fragments, but final canonical updates should still be reviewed before writing to `data/models.csv` or adding rows to `data/benchmarks.csv`.
