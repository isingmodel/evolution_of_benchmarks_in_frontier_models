#!/usr/bin/env python3
"""Extract benchmark mentions from public model release pages.

The scraper is intentionally staged:

1. Gather static page source context from HTML, tables, metadata, scripts, and image
   alt/title text.
2. Optionally render with Playwright and click benchmark-like tabs/buttons.
3. Optionally run OCR over benchmark/performance-like images.
4. Match a canonical benchmark catalog from local CSV data.
5. Optionally use the local OpenAI OAuth proxy for source-first LLM extraction.
6. Evaluate against data/models.csv as a gold answer key.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from openai_oauth_client import (  # noqa: E402
    DEFAULT_OPENAI_OAUTH_BASE_URL,
    DEFAULT_OPENAI_OAUTH_MODEL,
    OpenAIOAuthClient,
    resolve_openai_oauth_dir,
)
from taxonomy_utils import exact_key, identity_key, split_benchmark_mentions  # noqa: E402


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

TEXT_HINT_RE = re.compile(
    r"benchmark|eval|evaluation|score|performance|leaderboard|"
    r"벤치마크|평가|성능|MMLU|MMMU|GPQA|AIME|SWE|TAU|Terminal|OSWorld",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s|)>\"]+")
READER_URL_PREFIX = "https://r.jina.ai/http://"
TAB_HINT_RE = re.compile(
    r"benchmark|eval|evaluation|score|performance|compare|comparison|"
    r"reasoning|coding|agent|intelligence|chart|table|"
    r"벤치마크|평가|성능|비교|추론|코딩",
    re.IGNORECASE,
)
SAFE_LLM_RELATIONSHIPS = {"exact", "abbreviation"}
ACCEPT_MIN_CONFIDENCE = 0.75


@dataclass(frozen=True)
class PageFragment:
    source_kind: str
    label: str
    text: str


@dataclass
class PageDocument:
    url: str
    final_url: str
    title: str = ""
    fragments: List[PageFragment] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_fragment(self, source_kind: str, label: str, text: str, max_chars: int = 250_000) -> None:
        cleaned = collapse_ws(text)
        if not cleaned:
            return
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
        self.fragments.append(PageFragment(source_kind=source_kind, label=label, text=cleaned))


@dataclass(frozen=True)
class AliasPattern:
    alias: str
    benchmark_id: str
    benchmark_name: str
    source: str
    pattern: re.Pattern[str]
    priority: int


@dataclass
class BenchmarkHit:
    benchmark_id: str
    benchmark_name: str
    raw_match: str
    alias: str
    alias_source: str
    source_kind: str
    source_label: str
    snippet: str
    score: float


@dataclass(frozen=True)
class LLMExtractionItem:
    raw_name: str
    canonical_name: str
    relationship: str
    confidence: float
    source_excerpt: str
    source_block: str


@dataclass(frozen=True)
class ReviewMention:
    raw_name: str
    canonical_name: str
    relationship: str
    confidence: float
    reason: str
    source_excerpt: str
    source_block: str


@dataclass
class ExtractionResult:
    url: str
    final_url: str
    title: str
    provider: str = ""
    model_name: str = ""
    rendered: bool = False
    used_openai_oauth: bool = False
    hits: List[BenchmarkHit] = field(default_factory=list)
    llm_added: List[str] = field(default_factory=list)
    llm_unknown_mentions: List[str] = field(default_factory=list)
    review_required_mentions: List[ReviewMention] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def benchmark_ids(self) -> Set[str]:
        return {hit.benchmark_id for hit in self.hits}

    @property
    def benchmark_names(self) -> List[str]:
        return sorted({hit.benchmark_name for hit in self.hits}, key=str.casefold)


class BenchmarkCatalog:
    def __init__(self, benchmarks: Mapping[str, str], aliases: Mapping[str, Tuple[str, str]]):
        self.benchmarks = dict(benchmarks)
        self.name_to_id = {exact_key(name): benchmark_id for benchmark_id, name in self.benchmarks.items()}
        self.alias_to_id = {exact_key(alias): benchmark_id for alias, (benchmark_id, _) in aliases.items()}
        self.alias_notes = {exact_key(alias): source for alias, (_, source) in aliases.items()}
        self.patterns = self._build_patterns()

    @classmethod
    def from_files(cls, benchmarks_path: Path, aliases_path: Path) -> "BenchmarkCatalog":
        benchmarks: Dict[str, str] = {}
        with benchmarks_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                benchmark_id = exact_key(row.get("benchmark_id", ""))
                benchmark_name = exact_key(row.get("benchmark_name", ""))
                if benchmark_id and benchmark_name:
                    benchmarks[benchmark_id] = benchmark_name

        aliases: Dict[str, Tuple[str, str]] = {}
        if aliases_path.exists():
            with aliases_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    alias = exact_key(row.get("alias", ""))
                    benchmark_id = exact_key(row.get("benchmark_id", ""))
                    if alias and benchmark_id in benchmarks:
                        aliases[alias] = (benchmark_id, row.get("match_type", "alias") or "alias")

        return cls(benchmarks=benchmarks, aliases=aliases)

    def resolve_name(self, raw_name: str) -> Optional[Tuple[str, str]]:
        key = exact_key(raw_name)
        benchmark_id = self.name_to_id.get(key) or self.alias_to_id.get(key)
        if not benchmark_id:
            return None
        return benchmark_id, self.benchmarks[benchmark_id]

    def canonical_id(self, raw_name: str) -> Optional[str]:
        return self.name_to_id.get(exact_key(raw_name))

    def explicit_alias_id(self, raw_name: str) -> Optional[str]:
        return self.alias_to_id.get(exact_key(raw_name))

    def explicit_alias_source(self, raw_name: str) -> str:
        return self.alias_notes.get(exact_key(raw_name), "")

    def scan(self, fragments: Sequence[PageFragment]) -> List[BenchmarkHit]:
        best_by_id: Dict[str, BenchmarkHit] = {}

        for fragment in fragments:
            if not fragment.text:
                continue
            for alias_pattern in self.patterns:
                match = alias_pattern.pattern.search(fragment.text)
                if not match:
                    continue
                score = score_source(fragment.source_kind, alias_pattern.alias)
                snippet = make_snippet(fragment.text, match.start(), match.end())
                if is_likely_false_positive(alias_pattern.alias, snippet):
                    continue
                hit = BenchmarkHit(
                    benchmark_id=alias_pattern.benchmark_id,
                    benchmark_name=alias_pattern.benchmark_name,
                    raw_match=match.group(0),
                    alias=alias_pattern.alias,
                    alias_source=alias_pattern.source,
                    source_kind=fragment.source_kind,
                    source_label=fragment.label,
                    snippet=snippet,
                    score=score,
                )
                current = best_by_id.get(hit.benchmark_id)
                if not current or hit.score > current.score or len(hit.snippet) > len(current.snippet):
                    best_by_id[hit.benchmark_id] = hit

        return sorted(best_by_id.values(), key=lambda hit: (-hit.score, hit.benchmark_name.casefold()))

    def _build_patterns(self) -> List[AliasPattern]:
        entries: Dict[str, Tuple[str, str]] = {}

        for benchmark_id, name in self.benchmarks.items():
            for alias in generated_aliases(name):
                entries[exact_key(alias)] = (benchmark_id, "canonical_or_generated")

        for alias, benchmark_id in self.alias_to_id.items():
            entries[exact_key(alias)] = (benchmark_id, self.alias_notes.get(alias, "alias"))

        patterns: List[AliasPattern] = []
        for alias, (benchmark_id, source) in entries.items():
            if not alias or benchmark_id not in self.benchmarks:
                continue
            patterns.append(
                AliasPattern(
                    alias=alias,
                    benchmark_id=benchmark_id,
                    benchmark_name=self.benchmarks[benchmark_id],
                    source=source,
                    pattern=compile_alias_pattern(alias),
                    priority=len(alias),
                )
            )

        # Longest and most specific aliases first reduces generic hits such as
        # MATH inside MATH 500 and MMMU inside MMMU Pro.
        return sorted(patterns, key=lambda item: (-item.priority, item.alias.casefold()))


def collapse_ws(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", normalized).strip()


def generated_aliases(name: str) -> Set[str]:
    return {exact_key(name)}


def compile_alias_pattern(alias: str) -> re.Pattern[str]:
    pieces = []
    for char in alias:
        if char.isspace():
            pieces.append(r"\s+")
        elif char in "-‐‑‒–—−":
            pieces.append(r"[-‐‑‒–—−\s]+")
        else:
            pieces.append(re.escape(char))

    body = "".join(pieces)
    flags = 0 if should_match_case_sensitively(alias) else re.IGNORECASE
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9])", flags)


def should_match_case_sensitively(alias: str) -> bool:
    normalized = alias.strip()
    if normalized in {"MATH", "STEM", "GRE", "IMO"}:
        return True
    letters = re.sub(r"[^A-Za-z]", "", normalized)
    return len(normalized) <= 5 and bool(letters) and letters.upper() == letters


def score_source(source_kind: str, alias: str) -> float:
    base_scores = {
        "rendered_visible_text": 1.0,
        "static_visible_text": 0.95,
        "table": 0.95,
        "reader_markdown": 0.94,
        "metadata": 0.75,
        "image_text": 0.65,
        "image_ocr": 0.92,
        "script_json": 0.58,
        "script_text": 0.52,
    }
    score = base_scores.get(source_kind, 0.5)
    if alias in {"MATH", "STEM", "GRE", "IMO"}:
        score -= 0.1
    return max(score, 0.0)


def make_snippet(text: str, start: int, end: int, radius: int = 170) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    prefix = "..." if left else ""
    suffix = "..." if right < len(text) else ""
    return prefix + text[left:right].strip() + suffix


def is_likely_false_positive(alias: str, snippet: str) -> bool:
    normalized = collapse_ws(snippet).casefold()
    if alias == "STEM" and (
        "incl. stem" in normalized
        or "including stem" in normalized
        or "stem, humanities" in normalized
        or "stem subjects" in normalized
    ):
        return True
    if alias == "GPQA" and "gpqa diamond" in normalized:
        return True
    if alias == "SWE-bench" and (
        "swe-bench verified" in normalized
        or "swe-bench pro" in normalized
        or "swe-bench multilingual" in normalized
    ):
        return True
    if alias in {"Terminal-bench", "Terminal-Bench"} and "terminal-bench 2.0" in normalized:
        return True
    if alias == "ARC-AGI" and "arc-agi-2" in normalized:
        return True
    if alias == "MRCR" and "mrcr v2" in normalized:
        return True
    if alias == "BrowseComp" and ("browsecomp-plus" in normalized or "browsecomp plus" in normalized):
        return True
    if alias == "Vending-Bench" and "vending-bench 2" in normalized:
        return True
    if alias == "MATH" and "math 500" in normalized:
        return True
    if alias == "MMLU" and "global mmlu" in normalized:
        return True
    if alias == "AIME" and (
        "aime/amc-like" in normalized
        or "aime/amc like" in normalized
        or "aime-like" in normalized
        or "aime like" in normalized
    ):
        return True
    if alias == "HumanEval" and ("humaneval-like" in normalized or "humaneval like" in normalized):
        return True
    if alias == "Codeforces" and "livecodebench pro from codeforces" in normalized:
        return True
    return False


def fetch_static_document(url: str, timeout: int = 30) -> PageDocument:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError("Static scraping requires requests and beautifulsoup4.") from e

    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,ko;q=0.8"}
    document = PageDocument(url=url, final_url=url)
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    document.final_url = response.url

    soup = BeautifulSoup(response.text, "html.parser")
    document.title = collapse_ws(soup.title.get_text(" ")) if soup.title else ""

    for meta in soup.find_all("meta"):
        content = meta.get("content")
        if not content:
            continue
        label = meta.get("property") or meta.get("name") or "meta"
        document.add_fragment("metadata", str(label), content, max_chars=10_000)

    for index, table in enumerate(soup.find_all("table"), start=1):
        document.add_fragment("table", f"table:{index}", table.get_text(" "), max_chars=80_000)

    for index, image in enumerate(soup.find_all("img"), start=1):
        image_bits = [
            image.get("alt") or "",
            image.get("title") or "",
            image.get("aria-label") or "",
        ]
        parent = image.find_parent(["figure", "picture", "section", "div"])
        if parent:
            caption = parent.find(["figcaption", "caption"])
            if caption:
                image_bits.append(caption.get_text(" "))
        src = image.get("src") or image.get("data-src") or ""
        if src:
            image_bits.append(urljoin(response.url, src))
        document.add_fragment("image_text", f"image:{index}", " | ".join(image_bits), max_chars=20_000)

    for index, script in enumerate(soup.find_all("script"), start=1):
        script_type = (script.get("type") or "").casefold()
        script_text = script.string or script.get_text(" ")
        if not script_text or not TEXT_HINT_RE.search(script_text):
            continue
        kind = "script_json" if "json" in script_type or script.get("id") == "__NEXT_DATA__" else "script_text"
        document.add_fragment(kind, f"script:{index}", script_text, max_chars=300_000)

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    document.add_fragment("static_visible_text", "body", soup.get_text(" "), max_chars=350_000)
    return document


def fetch_reader_document(url: str, timeout: int = 45) -> PageDocument:
    try:
        import requests
    except ImportError as e:
        raise RuntimeError("Reader fallback requires requests.") from e

    reader_url = READER_URL_PREFIX + url
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,ko;q=0.8"}
    response = requests.get(reader_url, headers=headers, timeout=timeout)
    response.raise_for_status()

    document = PageDocument(url=url, final_url=url)
    text = response.text
    title_match = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
    if title_match:
        document.title = collapse_ws(title_match.group(1))
    source_match = re.search(r"^URL Source:\s*(.+)$", text, re.MULTILINE)
    if source_match:
        document.final_url = collapse_ws(source_match.group(1))
    document.add_fragment("reader_markdown", "jina-reader", text, max_chars=500_000)
    return document


def fetch_rendered_document(
    url: str,
    timeout_ms: int = 45_000,
    max_clicks: int = 18,
    attempts: int = 3,
) -> PageDocument:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("Rendered scraping requires playwright.") from e

    best_document = PageDocument(url=url, final_url=url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for attempt in range(1, attempts + 1):
                document = PageDocument(url=url, final_url=url)
                page = browser.new_page(user_agent=DEFAULT_USER_AGENT, viewport={"width": 1440, "height": 1200})
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    try:
                        page.wait_for_load_state("networkidle", timeout=10_000)
                    except PlaywrightTimeoutError:
                        document.errors.append("networkidle timeout after domcontentloaded")
                    page.wait_for_timeout(800 * attempt)
                    document.final_url = page.url
                    document.title = collapse_ws(page.title())
                    collect_rendered_fragments(page, document, "initial")
                    if rendered_document_has_content(document):
                        click_interesting_controls(page, document, max_clicks=max_clicks)
                    else:
                        document.errors.append(f"rendered attempt {attempt} returned load-failure shell")
                finally:
                    page.close()

                if rendered_document_score(document) > rendered_document_score(best_document):
                    best_document = document
                if rendered_document_has_content(document):
                    break
        finally:
            browser.close()
    return best_document


def rendered_document_has_content(document: PageDocument) -> bool:
    text = " ".join(fragment.text for fragment in document.fragments if fragment.source_kind == "rendered_visible_text")
    normalized = text.casefold()
    if not text or len(text) < 200:
        return False
    if "this page couldn" in normalized and "reload to try again" in normalized:
        return False
    if "just a moment" in normalized and len(text) < 500:
        return False
    return True


def rendered_document_score(document: PageDocument) -> int:
    text_length = sum(len(fragment.text) for fragment in document.fragments)
    hint_bonus = sum(1 for fragment in document.fragments if TEXT_HINT_RE.search(fragment.text)) * 5_000
    return text_length + hint_bonus


def add_image_ocr_fragments(document: PageDocument, cache_dir: Path, max_images: int = 12) -> None:
    urls = candidate_image_urls(document)
    if not urls:
        return
    if not shutil.which("tesseract"):
        document.errors.append("image OCR skipped: tesseract is not installed")
        return

    try:
        import requests
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError as e:
        document.errors.append(f"image OCR skipped: missing dependency {e}")
        return

    cache_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept-Language": "en-US,en;q=0.9,ko;q=0.8"}

    for index, url in enumerate(urls[:max_images], start=1):
        try:
            response = requests.get(url, headers=headers, timeout=25)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            for frame_index, frame in iter_ocr_frames(image):
                width, height = frame.size
                if width < 320 or height < 160:
                    continue

                # OCR works much better when provider chart images are enlarged
                # and contrast-normalized. Several release pages encode the
                # benchmark table as a single tall GIF/PNG rather than HTML.
                processed = ImageOps.grayscale(frame)
                processed = ImageOps.autocontrast(processed)
                processed = ImageEnhance.Contrast(processed).enhance(1.35)
                scale = ocr_scale_factor(width, height)
                if scale > 1:
                    processed = processed.resize((width * scale, height * scale))

                ocr_texts: List[str] = []
                completed = run_tesseract(processed, cache_dir, psm="6")
                if completed.returncode != 0:
                    document.errors.append(f"image OCR failed for {url}: {completed.stderr.strip()[:200]}")
                    continue
                ocr_texts.append(completed.stdout)

                fallback = run_tesseract(processed, cache_dir, psm="11")
                if fallback.returncode == 0 and fallback.stdout.strip() not in {text.strip() for text in ocr_texts}:
                    ocr_texts.append(fallback.stdout)

                document.add_fragment(
                    "image_ocr",
                    f"ocr-image:{index}:frame:{frame_index}",
                    "\n".join(text for text in ocr_texts if text.strip()),
                    max_chars=120_000,
                )
        except Exception as e:
            document.errors.append(f"image OCR failed for {url}: {e}")


def iter_ocr_frames(image, max_frames: int = 4):
    frame_count = int(getattr(image, "n_frames", 1) or 1)
    if getattr(image, "is_animated", False) and frame_count > 1:
        frame_indexes = sorted({0, frame_count // 3, (frame_count * 2) // 3, frame_count - 1})[:max_frames]
    else:
        frame_indexes = [0]

    for frame_index in frame_indexes:
        image.seek(frame_index)
        yield frame_index, image.convert("RGB").copy()


def ocr_scale_factor(width: int, height: int) -> int:
    long_side = max(width, height)
    short_side = min(width, height)
    if long_side < 1_400:
        return 3
    if long_side < 3_600:
        return 2
    if short_side < 1_300 and long_side < 6_000:
        return 2
    return 1


def run_tesseract(image, cache_dir: Path, psm: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(suffix=".png", dir=cache_dir, delete=True) as tmp:
        image.save(tmp.name, dpi=(300, 300))
        return subprocess.run(
            ["tesseract", tmp.name, "stdout", "--psm", psm, "--dpi", "300"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=45,
        )


def candidate_image_urls(document: PageDocument) -> List[str]:
    urls: List[str] = []
    seen: Set[str] = set()
    for fragment in document.fragments:
        if fragment.source_kind != "image_text":
            continue
        text = fragment.text
        if not TEXT_HINT_RE.search(text) and not re.search(r"chart|table|score|performance", text, re.IGNORECASE):
            continue
        for raw_url in URL_RE.findall(text):
            url = raw_url.rstrip(".,;")
            lowered = url.casefold()
            if ".svg" in lowered or "newsletter" in lowered or "logo" in lowered:
                continue
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def collect_rendered_fragments(page, document: PageDocument, label: str) -> None:
    try:
        body_text = page.locator("body").inner_text(timeout=5_000)
        document.add_fragment("rendered_visible_text", f"rendered:{label}", body_text, max_chars=350_000)
    except Exception as e:
        document.errors.append(f"rendered text failed for {label}: {e}")

    try:
        image_texts = page.locator("img").evaluate_all(
            """imgs => imgs.map((img, index) => ({
                index: index + 1,
                alt: img.getAttribute('alt') || '',
                title: img.getAttribute('title') || '',
                aria: img.getAttribute('aria-label') || '',
                src: img.currentSrc || img.getAttribute('src') || ''
            }))"""
        )
        for image in image_texts:
            document.add_fragment(
                "image_text",
                f"rendered-image:{label}:{image.get('index')}",
                " | ".join(
                    [
                        image.get("alt") or "",
                        image.get("title") or "",
                        image.get("aria") or "",
                        image.get("src") or "",
                    ]
                ),
                max_chars=20_000,
            )
    except Exception as e:
        document.errors.append(f"rendered image extraction failed for {label}: {e}")


def click_interesting_controls(page, document: PageDocument, max_clicks: int) -> None:
    candidates: List[Tuple[str, int, str]] = []
    for selector in ["[role=tab]", "button", "a[href^='#']", "[aria-controls]"]:
        locator = page.locator(selector)
        try:
            count = min(locator.count(), max_clicks * 4)
        except Exception:
            continue
        for index in range(count):
            item = locator.nth(index)
            try:
                if not item.is_visible(timeout=500):
                    continue
                text = collapse_ws(item.inner_text(timeout=500))
                aria = collapse_ws(item.get_attribute("aria-label") or "")
                combined = " ".join(bit for bit in [text, aria] if bit)
                if not combined:
                    continue
                if selector == "[role=tab]" or TAB_HINT_RE.search(combined):
                    candidates.append((selector, index, combined[:80]))
            except Exception:
                continue

    seen_labels: Set[str] = set()
    clicked = 0
    for selector, index, label in candidates:
        if clicked >= max_clicks:
            break
        label_key = identity_key(label)
        if label_key in seen_labels:
            continue
        seen_labels.add(label_key)
        item = page.locator(selector).nth(index)
        try:
            item.click(timeout=1_500)
            page.wait_for_timeout(300)
            collect_rendered_fragments(page, document, f"click:{clicked + 1}:{label}")
            clicked += 1
        except Exception:
            continue


def merge_documents(primary: PageDocument, secondary: PageDocument) -> PageDocument:
    merged = PageDocument(
        url=primary.url,
        final_url=secondary.final_url or primary.final_url,
        title=secondary.title or primary.title,
        fragments=[],
        errors=[*primary.errors, *secondary.errors],
    )
    seen: Set[Tuple[str, str, str]] = set()
    for fragment in [*secondary.fragments, *primary.fragments]:
        key = (fragment.source_kind, fragment.label, fragment.text[:200])
        if key in seen:
            continue
        seen.add(key)
        merged.fragments.append(fragment)
    return merged


def merge_many_documents(documents: Sequence[PageDocument]) -> PageDocument:
    available = [document for document in documents if document]
    if not available:
        raise ValueError("No page documents to merge")
    merged = available[0]
    for document in available[1:]:
        merged = merge_documents(merged, document)
    return merged


def scrape_url(
    url: str,
    catalog: BenchmarkCatalog,
    provider: str = "",
    model_name: str = "",
    rendered: bool = False,
    reader_fallback: bool = True,
    ocr_images: bool = False,
    max_ocr_images: int = 12,
    use_openai_oauth: bool = False,
    openai_oauth_model: str = DEFAULT_OPENAI_OAUTH_MODEL,
    openai_oauth_base_url: str = DEFAULT_OPENAI_OAUTH_BASE_URL,
    openai_oauth_dir: Path | None = None,
    openai_oauth_auto_start: bool = True,
    openai_oauth_timeout: float = 120.0,
    openai_oauth_client: Optional[OpenAIOAuthClient] = None,
) -> ExtractionResult:
    errors: List[str] = []
    static_doc: Optional[PageDocument] = None
    reader_doc: Optional[PageDocument] = None
    try:
        static_doc = fetch_static_document(url)
    except Exception as e:
        errors.append(f"static fetch failed: {e}")

    document = static_doc or PageDocument(url=url, final_url=url)
    if reader_fallback:
        try:
            reader_doc = fetch_reader_document(url)
            document = merge_many_documents([document, reader_doc])
        except Exception as e:
            errors.append(f"reader fallback failed: {e}")

    if rendered:
        try:
            rendered_doc = fetch_rendered_document(url)
            document = merge_many_documents([document, rendered_doc])
        except Exception as e:
            errors.append(f"rendered fetch failed: {e}")

    if ocr_images:
        add_image_ocr_fragments(document, ROOT / "scraping" / "cache" / "ocr", max_images=max_ocr_images)

    hits = catalog.scan(document.fragments)
    result = ExtractionResult(
        url=url,
        final_url=document.final_url,
        title=document.title,
        provider=provider,
        model_name=model_name,
        rendered=rendered,
        used_openai_oauth=use_openai_oauth,
        hits=hits,
        errors=[*errors, *document.errors],
    )

    if use_openai_oauth:
        client = openai_oauth_client or OpenAIOAuthClient(
            base_url=openai_oauth_base_url,
            model=openai_oauth_model,
            project_dir=openai_oauth_dir,
            auto_start=openai_oauth_auto_start,
            timeout=openai_oauth_timeout,
        )
        try:
            llm_items = openai_oauth_extract_mentions(document, result, catalog, client)
            deterministic_ids = result.benchmark_ids
            llm_hits, review_mentions = partition_llm_items(llm_items, catalog)
            result.hits = merge_hits([*result.hits, *llm_hits])
            result.llm_added = [
                hit.benchmark_name for hit in llm_hits if hit.benchmark_id not in deterministic_ids
            ]
            result.review_required_mentions = review_mentions
            result.llm_unknown_mentions = sorted(
                {mention.raw_name for mention in review_mentions if not mention.canonical_name},
                key=str.casefold,
            )
            result.hits.sort(key=lambda hit: (-hit.score, hit.benchmark_name.casefold()))
        except Exception as e:
            result.errors.append(f"openai-oauth extraction failed: {e}")
        finally:
            if openai_oauth_client is None:
                client.close()

    return result


def merge_hits(hits: Sequence[BenchmarkHit]) -> List[BenchmarkHit]:
    best_by_id: Dict[str, BenchmarkHit] = {}
    for hit in hits:
        current = best_by_id.get(hit.benchmark_id)
        if not current or hit.score > current.score or len(hit.snippet) > len(current.snippet):
            best_by_id[hit.benchmark_id] = hit
    return list(best_by_id.values())


def partition_llm_items(
    items: Sequence[LLMExtractionItem],
    catalog: BenchmarkCatalog,
) -> Tuple[List[BenchmarkHit], List[ReviewMention]]:
    accepted_hits: List[BenchmarkHit] = []
    review_mentions: List[ReviewMention] = []
    for item in items:
        reason = llm_review_reason(item, catalog)
        if reason:
            if reason != "source_only_not_a_benchmark":
                review_mentions.append(
                    ReviewMention(
                        raw_name=item.raw_name,
                        canonical_name=item.canonical_name,
                        relationship=item.relationship,
                        confidence=item.confidence,
                        reason=reason,
                        source_excerpt=item.source_excerpt,
                        source_block=item.source_block,
                    )
                )
            continue

        resolved = catalog.resolve_name(item.canonical_name)
        if not resolved:
            continue
        benchmark_id, benchmark_name = resolved
        accepted_hits.append(
            BenchmarkHit(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                raw_match=item.raw_name,
                alias=item.canonical_name,
                alias_source=f"openai_oauth:{item.relationship or 'unspecified'}",
                source_kind="llm",
                source_label=item.source_block or "openai_oauth",
                snippet=item.source_excerpt or "Added by OpenAI OAuth from collected page source context.",
                score=max(0.0, min(1.0, item.confidence)),
            )
        )
    return merge_hits(accepted_hits), review_mentions


def llm_review_reason(item: LLMExtractionItem, catalog: BenchmarkCatalog) -> str:
    relationship = normalize_relationship(item.relationship)
    raw_name = exact_key(item.raw_name)
    canonical_name = exact_key(item.canonical_name)
    if not raw_name:
        return "missing_raw_name"
    if relationship == "reject_source_only":
        return "source_only_not_a_benchmark"
    if not canonical_name:
        return "new_or_unmapped_benchmark"
    resolved = catalog.resolve_name(canonical_name)
    if not resolved:
        return "canonical_not_in_catalog"
    if item.confidence < ACCEPT_MIN_CONFIDENCE:
        return "low_confidence_mapping"

    canonical_id, _ = resolved
    if catalog.canonical_id(raw_name) == canonical_id:
        return ""
    if (
        relationship in SAFE_LLM_RELATIONSHIPS
        and catalog.explicit_alias_id(raw_name) == canonical_id
    ):
        return ""
    if relationship == "semantic_equivalent":
        return "semantic_mapping_requires_review"
    if relationship == "variant_or_family":
        return "variant_or_family_mapping_requires_review"
    if relationship == "ocr_correction":
        return "ocr_correction_requires_review"
    if catalog.explicit_alias_id(raw_name) and catalog.explicit_alias_id(raw_name) != canonical_id:
        return "explicit_alias_conflicts_with_llm_mapping"
    return "not_exact_or_explicit_alias"


def normalize_relationship(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (value or "").casefold()).strip("_")


def openai_oauth_extract_mentions(
    document: PageDocument,
    result: ExtractionResult,
    catalog: BenchmarkCatalog,
    client: OpenAIOAuthClient,
) -> List[LLMExtractionItem]:
    deterministic_candidates = [
        {
            "canonical_name": hit.benchmark_name,
            "raw_match": hit.raw_match,
            "source": f"{hit.source_kind}:{hit.source_label}",
            "snippet": hit.snippet,
        }
        for hit in result.hits
    ]
    catalog_names = sorted(catalog.benchmarks.values(), key=str.casefold)
    source_context = build_llm_source_context(document.fragments)

    prompt = f"""You extract benchmark names from public model launch pages.

Project scope:
- Include benchmarks emphasized in the public launch/release page source context below.
- Include benchmark tables that appear in OCR text, even if formatting is imperfect.
- Do not include benchmarks merely because they are mentioned as source datasets, examples, related work, footnotes, navigation, or methodology notes.
- Do not invent aliases. First extract the raw benchmark name as written in the source context, then map it to the allowed catalog only when the mapping is semantically clear.
- If a raw benchmark mention is real but not in the catalog, keep canonical_name null and add it to unknown_mentions.
- Mark exact string matches as relationship="exact".
- Mark only explicit abbreviations as relationship="abbreviation"; do not use abbreviation for broad family/variant guesses.
- Mark variant/family rollups, semantic similarity, and OCR corrections honestly. The caller will require human review for those mappings.
- If the source context names a more specific variant and the catalog contains that variant, choose the specific variant rather than a broader family.
- If the source context says something like "LiveCodeBench Pro from Codeforces", include LiveCodeBench or LiveCodeBench Pro if available, not Codeforces.
- If OCR confuses a name but nearby context clearly identifies the benchmark, use the corrected canonical catalog name and explain using source context.
- Return only JSON.

Provider: {result.provider}
Model: {result.model_name}
URL: {document.final_url}

Allowed benchmark catalog:
{json.dumps(catalog_names, ensure_ascii=False)}

Deterministic candidates already found:
{json.dumps(deterministic_candidates, ensure_ascii=False)}

Collected page source context:
{source_context}

Return schema:
{{
  "benchmarks": [
    {{
      "raw_name": "name exactly as written or OCR-corrected from source context",
      "canonical_name": "one allowed catalog name, or null",
      "relationship": "exact | abbreviation | semantic_equivalent | variant_or_family | ocr_correction | unknown | reject_source_only",
      "confidence": 0.0,
      "source_block": "F001",
      "source_excerpt": "short quote or paraphrase from the block"
    }}
  ],
  "unknown_mentions": ["raw benchmark-like names not in the allowed catalog"],
  "notes": "short note about uncertainty"
}}
"""
    text = client.generate_text(prompt).strip().replace("```json", "").replace("```", "").strip()
    parsed = json.loads(re.search(r"\{.*\}", text, re.DOTALL).group(0) if not text.startswith("{") else text)
    raw_items = parsed.get("benchmarks", [])
    if not isinstance(raw_items, list):
        raise ValueError("OpenAI OAuth response field 'benchmarks' must be a list.")

    items: List[LLMExtractionItem] = []
    for raw_item in raw_items:
        if isinstance(raw_item, str):
            raw_name = exact_key(raw_item)
            canonical_name = raw_name
            relationship = "exact"
            confidence = ACCEPT_MIN_CONFIDENCE
            source_block = "openai_oauth"
            source_excerpt = "Added by OpenAI OAuth from collected page source context."
        elif isinstance(raw_item, Mapping):
            raw_name = exact_key(str(raw_item.get("raw_name") or raw_item.get("name") or ""))
            canonical_value = raw_item.get("canonical_name")
            canonical_name = exact_key(str(canonical_value)) if canonical_value is not None else ""
            relationship = normalize_relationship(str(raw_item.get("relationship") or ""))
            confidence = parse_confidence(raw_item.get("confidence"))
            source_block = exact_key(str(raw_item.get("source_block") or raw_item.get("evidence_block") or "openai_oauth"))
            source_excerpt = exact_key(str(raw_item.get("source_excerpt") or raw_item.get("evidence") or ""))
        else:
            continue

        if not raw_name:
            continue
        items.append(
            LLMExtractionItem(
                raw_name=raw_name,
                canonical_name=canonical_name,
                relationship=relationship or "unspecified",
                confidence=confidence,
                source_excerpt=source_excerpt,
                source_block=source_block,
            )
        )

    for mention in parsed.get("unknown_mentions", []) if isinstance(parsed.get("unknown_mentions", []), list) else []:
        mention_text = exact_key(str(mention))
        if mention_text:
            items.append(
                LLMExtractionItem(
                    raw_name=mention_text,
                    canonical_name="",
                    relationship="unknown",
                    confidence=ACCEPT_MIN_CONFIDENCE,
                    source_excerpt="Listed by OpenAI OAuth as an unknown benchmark-like mention.",
                    source_block="openai_oauth",
                )
            )

    return items


def parse_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return ACCEPT_MIN_CONFIDENCE
    if confidence > 1.0:
        confidence = confidence / 100.0
    return max(0.0, min(1.0, confidence))


def build_llm_source_context(fragments: Sequence[PageFragment], max_chars: int = 110_000) -> str:
    scored: List[Tuple[int, int, PageFragment]] = []
    source_rank = {
        "image_ocr": 9,
        "table": 8,
        "rendered_visible_text": 7,
        "reader_markdown": 6,
        "static_visible_text": 5,
        "image_text": 4,
        "metadata": 3,
        "script_json": 2,
        "script_text": 1,
    }
    for index, fragment in enumerate(fragments, start=1):
        text = fragment.text
        if not text:
            continue
        hint_hits = len(TEXT_HINT_RE.findall(text))
        if fragment.source_kind in {"image_ocr", "table", "image_text"}:
            hint_hits += 2
        if hint_hits == 0 and fragment.source_kind not in {"metadata", "reader_markdown"}:
            continue
        score = source_rank.get(fragment.source_kind, 0) * 1_000 + hint_hits
        scored.append((score, index, fragment))

    blocks: List[str] = []
    total_chars = 0
    for block_number, (_, original_index, fragment) in enumerate(
        sorted(scored, key=lambda item: (-item[0], item[1]))[:70],
        start=1,
    ):
        text = fragment.text[:5_000]
        header = f"[F{block_number:03d} original:{original_index} source:{fragment.source_kind}:{fragment.label}]"
        block = f"{header}\n{text}"
        if total_chars + len(block) > max_chars:
            break
        blocks.append(block)
        total_chars += len(block)
    return "\n\n".join(blocks)


def read_models(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def gold_benchmark_ids(row: Mapping[str, str], catalog: BenchmarkCatalog) -> Tuple[Set[str], List[str]]:
    ids: Set[str] = set()
    unresolved: List[str] = []
    for raw_name in split_benchmark_mentions(row.get("benchmarks", "")):
        resolved = catalog.resolve_name(raw_name)
        if resolved:
            ids.add(resolved[0])
        else:
            unresolved.append(raw_name)
    return ids, unresolved


def benchmark_names(ids: Iterable[str], catalog: BenchmarkCatalog) -> List[str]:
    return sorted((catalog.benchmarks.get(benchmark_id, benchmark_id) for benchmark_id in ids), key=str.casefold)


def accepted_mentions(result: ExtractionResult) -> List[str]:
    return sorted(
        {
            f"{hit.raw_match} -> {hit.benchmark_name}"
            if exact_key(hit.raw_match) != exact_key(hit.benchmark_name)
            else hit.benchmark_name
            for hit in result.hits
        },
        key=str.casefold,
    )


def review_required_mentions(result: ExtractionResult) -> List[str]:
    return sorted(
        {format_review_mention(mention) for mention in result.review_required_mentions},
        key=str.casefold,
    )


def format_review_mention(mention: ReviewMention) -> str:
    target = f" -> {mention.canonical_name}" if mention.canonical_name else ""
    relationship = mention.relationship or "unspecified"
    return (
        f"{mention.raw_name}{target} "
        f"[{relationship}, confidence={mention.confidence:.2f}, reason={mention.reason}]"
    )


def llm_raw_mentions(result: ExtractionResult) -> List[str]:
    return sorted(
        {
            *{hit.raw_match for hit in result.hits if hit.source_kind == "llm" and hit.raw_match},
            *{mention.raw_name for mention in result.review_required_mentions if mention.raw_name},
        },
        key=str.casefold,
    )


def llm_mappings(result: ExtractionResult) -> List[str]:
    return sorted(
        {
            f"{hit.raw_match} -> {hit.benchmark_name}"
            for hit in result.hits
            if hit.source_kind == "llm" and hit.raw_match
        },
        key=str.casefold,
    )


def evaluate_against_models(args: argparse.Namespace) -> int:
    catalog = BenchmarkCatalog.from_files(Path(args.benchmarks), Path(args.aliases))
    rows = read_models(Path(args.models))

    rows = [row for row in rows if exact_key(row.get("benchmarks", ""))]
    if args.provider:
        providers = {provider.casefold() for provider in args.provider}
        rows = [row for row in rows if row.get("Provider", "").casefold() in providers]
    if args.model_name:
        names = {name.casefold() for name in args.model_name}
        rows = [row for row in rows if row.get("Model name", "").casefold() in names]
    if args.max_pages:
        rows = rows[: args.max_pages]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report_rows: List[Dict[str, str]] = []
    total_gold = 0
    total_predicted = 0
    total_tp = 0
    openai_client = (
        OpenAIOAuthClient(
            base_url=args.openai_oauth_base_url,
            model=args.openai_oauth_model,
            project_dir=Path(args.openai_oauth_dir),
            auto_start=not args.no_openai_oauth_start,
            timeout=args.openai_oauth_timeout,
        )
        if args.use_openai_oauth
        else None
    )

    try:
        for index, row in enumerate(rows, start=1):
            provider = row.get("Provider", "")
            model_name = row.get("Model name", "")
            url = row.get("link", "")
            print(f"[{index}/{len(rows)}] scraping {provider} {model_name}: {url}", flush=True)

            gold_ids, unresolved_gold = gold_benchmark_ids(row, catalog)
            started = time.time()
            try:
                result = scrape_url(
                    url=url,
                    catalog=catalog,
                    provider=provider,
                    model_name=model_name,
                    rendered=args.rendered,
                    reader_fallback=not args.no_reader_fallback,
                    ocr_images=args.ocr_images,
                    max_ocr_images=args.max_ocr_images,
                    use_openai_oauth=args.use_openai_oauth,
                    openai_oauth_model=args.openai_oauth_model,
                    openai_oauth_base_url=args.openai_oauth_base_url,
                    openai_oauth_dir=Path(args.openai_oauth_dir),
                    openai_oauth_auto_start=not args.no_openai_oauth_start,
                    openai_oauth_timeout=args.openai_oauth_timeout,
                    openai_oauth_client=openai_client,
                )
            except Exception as e:
                result = ExtractionResult(url=url, final_url=url, provider=provider, model_name=model_name, errors=[str(e)])

            predicted_ids = result.benchmark_ids
            true_positive_ids = gold_ids & predicted_ids
            missing_ids = gold_ids - predicted_ids
            extra_ids = predicted_ids - gold_ids
            recall = len(true_positive_ids) / len(gold_ids) if gold_ids else 1.0
            precision = len(true_positive_ids) / len(predicted_ids) if predicted_ids else (1.0 if not gold_ids else 0.0)

            total_gold += len(gold_ids)
            total_predicted += len(predicted_ids)
            total_tp += len(true_positive_ids)

            print(
                f"  recall={recall:.2%} precision={precision:.2%} "
                f"gold={len(gold_ids)} predicted={len(predicted_ids)} missing={len(missing_ids)} extra={len(extra_ids)}",
                flush=True,
            )

            report_rows.append(
                {
                    "provider": provider,
                    "model_name": model_name,
                    "release_date": row.get("release date", ""),
                    "url": url,
                    "final_url": result.final_url,
                    "rendered": str(args.rendered),
                    "reader_fallback": str(not args.no_reader_fallback),
                    "ocr_images": str(args.ocr_images),
                    "used_openai_oauth": str(args.use_openai_oauth),
                    "gold_count": str(len(gold_ids)),
                    "predicted_count": str(len(predicted_ids)),
                    "true_positive_count": str(len(true_positive_ids)),
                    "recall": f"{recall:.4f}",
                    "precision": f"{precision:.4f}",
                    "missing": "; ".join(benchmark_names(missing_ids, catalog)),
                    "extra": "; ".join(benchmark_names(extra_ids, catalog)),
                    "predicted": "; ".join(result.benchmark_names),
                    "accepted_mentions": "; ".join(accepted_mentions(result)),
                    "review_required_mentions": "; ".join(review_required_mentions(result)),
                    "unresolved_gold": "; ".join(unresolved_gold),
                    "llm_added": "; ".join(result.llm_added),
                    "llm_raw_mentions": "; ".join(llm_raw_mentions(result)),
                    "llm_mappings": "; ".join(llm_mappings(result)),
                    "llm_unknown_mentions": "; ".join(result.llm_unknown_mentions),
                    "errors": " | ".join(result.errors),
                    "elapsed_seconds": f"{time.time() - started:.2f}",
                }
            )
    finally:
        if openai_client is not None:
            openai_client.close()

    fieldnames = [
        "provider",
        "model_name",
        "release_date",
        "url",
        "final_url",
        "rendered",
        "reader_fallback",
        "used_openai_oauth",
        "ocr_images",
        "gold_count",
        "predicted_count",
        "true_positive_count",
        "recall",
        "precision",
        "missing",
        "extra",
        "predicted",
        "accepted_mentions",
        "review_required_mentions",
        "unresolved_gold",
        "llm_added",
        "llm_raw_mentions",
        "llm_mappings",
        "llm_unknown_mentions",
        "errors",
        "elapsed_seconds",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    micro_recall = total_tp / total_gold if total_gold else 1.0
    micro_precision = total_tp / total_predicted if total_predicted else 0.0
    print(f"Wrote {output_path}")
    print(
        f"Micro recall={micro_recall:.2%} precision={micro_precision:.2%} "
        f"true_positive={total_tp} gold={total_gold} predicted={total_predicted}"
    )
    return 0 if report_rows else 1


def extract_one(args: argparse.Namespace) -> int:
    catalog = BenchmarkCatalog.from_files(Path(args.benchmarks), Path(args.aliases))
    result = scrape_url(
        url=args.url,
        catalog=catalog,
        provider=args.provider,
        model_name=args.model_name,
        rendered=args.rendered,
        reader_fallback=not args.no_reader_fallback,
        ocr_images=args.ocr_images,
        max_ocr_images=args.max_ocr_images,
        use_openai_oauth=args.use_openai_oauth,
        openai_oauth_model=args.openai_oauth_model,
        openai_oauth_base_url=args.openai_oauth_base_url,
        openai_oauth_dir=Path(args.openai_oauth_dir),
        openai_oauth_auto_start=not args.no_openai_oauth_start,
        openai_oauth_timeout=args.openai_oauth_timeout,
    )

    payload = {
        "url": result.url,
        "final_url": result.final_url,
        "title": result.title,
        "provider": result.provider,
        "model_name": result.model_name,
        "rendered": result.rendered,
        "reader_fallback": not args.no_reader_fallback,
        "ocr_images": args.ocr_images,
        "used_openai_oauth": result.used_openai_oauth,
        "benchmarks": [
            {
                "benchmark_id": hit.benchmark_id,
                "benchmark_name": hit.benchmark_name,
                "raw_match": hit.raw_match,
                "source_kind": hit.source_kind,
                "source_label": hit.source_label,
                "score": hit.score,
                "snippet": hit.snippet,
            }
            for hit in result.hits
        ],
        "accepted_mentions": accepted_mentions(result),
        "review_required_mentions": [
            {
                "raw_name": mention.raw_name,
                "canonical_name": mention.canonical_name,
                "relationship": mention.relationship,
                "confidence": mention.confidence,
                "reason": mention.reason,
                "source_block": mention.source_block,
                "source_excerpt": mention.source_excerpt,
            }
            for mention in result.review_required_mentions
        ],
        "llm_added": result.llm_added,
        "llm_unknown_mentions": result.llm_unknown_mentions,
        "errors": result.errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.hits else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmarks", default=str(ROOT / "data" / "benchmarks.csv"))
    parser.add_argument("--aliases", default=str(ROOT / "data" / "benchmark_aliases.csv"))
    parser.add_argument("--openai-oauth-model", default=DEFAULT_OPENAI_OAUTH_MODEL)
    parser.add_argument("--openai-oauth-base-url", default=DEFAULT_OPENAI_OAUTH_BASE_URL)
    parser.add_argument("--openai-oauth-dir", default=str(resolve_openai_oauth_dir()))
    parser.add_argument(
        "--no-openai-oauth-start",
        action="store_true",
        help="Do not auto-start the local openai-oauth proxy when LLM extraction is requested.",
    )
    parser.add_argument("--openai-oauth-timeout", type=float, default=120.0)

    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract", help="Extract benchmark mentions from one release page.")
    extract.add_argument("--url", required=True)
    extract.add_argument("--provider", default="")
    extract.add_argument("--model-name", default="")
    extract.add_argument("--rendered", action="store_true", help="Use Playwright-rendered text and click likely tabs.")
    extract.add_argument(
        "--no-reader-fallback",
        action="store_true",
        help="Disable reader/markdown fallback for pages blocked by static requests or browser rendering.",
    )
    extract.add_argument("--ocr-images", action="store_true", help="Run OCR over benchmark/performance-like images.")
    extract.add_argument("--max-ocr-images", type=int, default=12, help="Maximum candidate images to OCR.")
    extract.add_argument(
        "--use-openai-oauth",
        action="store_true",
        help="Use the local OpenAI OAuth proxy for source-first extraction and conservative catalog mapping.",
    )
    extract.set_defaults(func=extract_one)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate extraction against data/models.csv.")
    evaluate.add_argument("--models", default=str(ROOT / "data" / "models.csv"))
    evaluate.add_argument("--provider", action="append", default=[], help="Filter to provider. May be repeated.")
    evaluate.add_argument("--model-name", action="append", default=[], help="Filter to model name. May be repeated.")
    evaluate.add_argument("--max-pages", type=int, default=0, help="Limit evaluation rows. 0 means all.")
    evaluate.add_argument("--rendered", action="store_true", help="Use Playwright-rendered text and click likely tabs.")
    evaluate.add_argument(
        "--no-reader-fallback",
        action="store_true",
        help="Disable reader/markdown fallback for pages blocked by static requests or browser rendering.",
    )
    evaluate.add_argument("--ocr-images", action="store_true", help="Run OCR over benchmark/performance-like images.")
    evaluate.add_argument("--max-ocr-images", type=int, default=12, help="Maximum candidate images to OCR per page.")
    evaluate.add_argument(
        "--use-openai-oauth",
        action="store_true",
        help="Use the local OpenAI OAuth proxy for source-first extraction and conservative catalog mapping.",
    )
    evaluate.add_argument("--output", default=str(ROOT / "scraping" / "output" / "benchmark_scrape_eval.csv"))
    evaluate.set_defaults(func=evaluate_against_models)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
