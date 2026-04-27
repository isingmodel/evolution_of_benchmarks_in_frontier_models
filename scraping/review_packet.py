#!/usr/bin/env python3
"""Generate a multi-agent review packet from one scraper extraction JSON.

The scraper extracts source-backed candidates; this script turns that raw
extraction into a stable handoff packet for independent reviewers/subagents.
It does not call any model API and does not modify canonical data files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROLE_BRIEFS = [
    (
        "Source Extractor",
        "Recover every benchmark-like, evaluation-like, leaderboard-like, suite-component, and aggregate-index-component name present on the public release page, including text, tables, image alt text, rendered tabs, footnotes, and OCR source context. Keep release-page names visible and explicitly mark cost, latency, price, and non-evaluation UI labels as non-benchmarks.",
    ),
    (
        "False-Positive Auditor",
        "Challenge each candidate, but inclusion wins for ambiguous benchmark-like names. Reject only clear non-benchmark artifacts such as source datasets, task descriptions, price/speed metrics, chart subtitles, model families, UI labels, and wrong variants. Do not reject a page mention solely because it is indirect, component-level, low-prominence, third-party, or not a direct score row.",
    ),
    (
        "Catalog Mapper",
        "Map only exact canonical names or explicit curated aliases to the local catalog. Propose new canonical rows for genuinely new benchmark names, and propose narrow aliases only when the source identity is source-backed.",
    ),
    (
        "Data Integrity Auditor",
        "Check the model name, release date, source URL, row order, AS_OF value, generated files, expected asset regeneration, and validation commands. Flag any change that would silently rewrite existing rows or broaden aliases.",
    ),
]


FINAL_ADJUDICATION_RULES = [
    "The requested public launch page is the source of truth; if it names a benchmark-like or evaluation-like item, include it.",
    "Images, JavaScript-rendered tabs, tables, captions, alt text, footnotes, aggregate-index component lists, and OCR text count when they are part of the public release page.",
    "Direct score rows, aggregate-index components, suite members, comparison-only benchmark names, and OCR-only benchmark names are included.",
    "Do not split the same benchmark into multiple model-row mentions solely because the page reports different run settings, tool settings, context windows, tiers, prompt settings, or metric variants.",
    "Do not count cost, latency, throughput, pricing, or the source of those measurements as capability benchmarks.",
    "Do not create broad semantic aliases to improve recall; unknown or variant names should become review items or new canonical rows.",
    "Keep raw mention wording visible when canonicalizing variants, especially Pro, Verified, v2, subset, track, and leaderboard names when they change benchmark identity rather than only run settings.",
    "Final data writes happen in the foreground after independent reviews are reconciled against the source page.",
]


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "\\|").strip()


def bullet_lines(values: Iterable[Any], empty: str = "_None._") -> list[str]:
    items = [str(value).strip() for value in values if str(value).strip()]
    if not items:
        return [empty]
    return [f"- `{md_escape(item)}`" for item in items]


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    if not rows:
        return ["_None._"]
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(md_escape(cell) for cell in row) + " |")
    return output


def benchmark_rows(data: Mapping[str, Any]) -> list[list[Any]]:
    rows = []
    for item in as_list(data.get("benchmarks")):
        rows.append(
            [
                item.get("benchmark_name", ""),
                item.get("raw_match", ""),
                item.get("source_kind", ""),
                item.get("source_label", ""),
                item.get("score", ""),
                item.get("snippet", ""),
            ]
        )
    return rows


def review_rows(data: Mapping[str, Any]) -> list[list[Any]]:
    rows = []
    for item in as_list(data.get("review_required_mentions")):
        rows.append(
            [
                item.get("raw_name", ""),
                item.get("canonical_name", ""),
                item.get("relationship", ""),
                item.get("confidence", ""),
                item.get("reason", ""),
                item.get("source_excerpt", item.get("evidence", "")),
            ]
        )
    return rows


def generate_packet(data: Mapping[str, Any], source_path: Path) -> str:
    lines: list[str] = []
    title = data.get("title") or data.get("model_name") or "Release Page"
    lines.extend(
        [
            f"# Multi-Agent Benchmark Review Packet: {title}",
            "",
            "This packet is generated from scraper output and is intended for independent review before editing canonical data.",
            "",
            "## Page Metadata",
            "",
            f"- Source JSON: `{source_path}`",
            f"- Provider: `{md_escape(data.get('provider', ''))}`",
            f"- Model name: `{md_escape(data.get('model_name', ''))}`",
            f"- URL: {md_escape(data.get('url', ''))}",
            f"- Final URL: {md_escape(data.get('final_url', ''))}",
            f"- Rendered: `{md_escape(data.get('rendered', ''))}`",
            f"- OCR images: `{md_escape(data.get('ocr_images', ''))}`",
            f"- Used Gemini extraction: `{md_escape(data.get('used_gemini', ''))}`",
            "",
            "## Accepted By Scraper",
            "",
        ]
    )
    lines.extend(bullet_lines(as_list(data.get("accepted_mentions"))))
    lines.extend(
        [
            "",
            "## Benchmark Source Hits",
            "",
            *table(
                ["canonical", "raw", "source_kind", "source_label", "score", "snippet"],
                benchmark_rows(data),
            ),
            "",
            "## Review-Required Mentions",
            "",
            *table(
                ["raw", "candidate canonical", "relationship", "confidence", "reason", "source_excerpt"],
                review_rows(data),
            ),
            "",
            "## Unknown Benchmark-Like Names",
            "",
        ]
    )
    lines.extend(bullet_lines(as_list(data.get("llm_unknown_mentions"))))
    lines.extend(["", "## Fetch / Extraction Errors", ""])
    lines.extend(bullet_lines(as_list(data.get("errors"))))

    lines.extend(["", "## Independent Reviewer Roles", ""])
    for role, brief in ROLE_BRIEFS:
        lines.extend([f"### {role}", "", brief, ""])

    lines.extend(["## Final Foreground Adjudication Rules", ""])
    for rule in FINAL_ADJUDICATION_RULES:
        lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "## Data Patch Checklist",
            "",
            "- Add or update `data/models.csv` only after raw mentions are reconciled.",
            "- Add new benchmark rows to `data/benchmarks.csv` only when the name is not safely represented by an existing canonical benchmark.",
            "- Add aliases to `data/benchmark_aliases.csv` only for exact, source-backed identity mappings.",
            "- Record unresolved variants or construct concerns directly in `data/benchmarks.csv` or temporary `data/benchmark_facet_manual.csv`.",
            "- Add audited multi-facet annotations to temporary `data/benchmark_facet_manual.csv`, then integrate them into `data/benchmark_facets.csv` with `scripts/build_normalized_data.py`.",
            "- Regenerate normalized data, README, and chart assets; then run validation.",
            "",
            "```bash",
            "AS_OF=YYYY-MM-DD",
            "",
            "python scripts/build_normalized_data.py",
            "python scripts/validate_data.py",
            "python scripts/generate_visuals.py --as-of \"$AS_OF\" --strict-resolution",
            "python scripts/generate_trend_graph_by_main_category.py --as-of \"$AS_OF\" --window-days 180 --strict-resolution",
            "python scripts/generate_trend_graph_by_all_category.py --as-of \"$AS_OF\" --window-days 180 --review-debt-output assets/benchmark_review_debt.png --strict-resolution",
            "python scripts/generate_facet_trends.py --as-of \"$AS_OF\" --window-days 180 --strict-resolution",
            "python scripts/update_readme.py",
            "python scripts/validate_data.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Extraction JSON produced by benchmark_scraper.py extract.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Markdown output path. Defaults to <input stem>.review_packet.md next to the input file.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8") as f:
        data = json.load(f)
    output = args.output or args.input.with_suffix(".review_packet.md")
    output.write_text(generate_packet(data, args.input), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
