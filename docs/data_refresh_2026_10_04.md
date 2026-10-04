# Release-page refresh checked through 2026-10-04

The discovery cutoff is October 4, 2026. The latest included launch is September
30. This refresh adds 12 model rows on nine announcement pages, following the
repository's public-page appearance policy. It covers general-purpose frontier
models and their cyber variants, including restricted launches. It does not claim
an exhaustive history of every product, specialized model, or evaluation run.

## Added releases

| Provider | Date | Model rows | Primary announcement |
| --- | --- | --- | --- |
| Anthropic | 2026-09-01 | Claude 5.1 (Fable / Mythos) | [Fable and Mythos 5.1](https://www.anthropic.com/claude-fable-and-mythos-5-1) |
| Google | 2026-09-02 | Gemini 3.8 Flash; Gemini 3.8 Flash Cyber | [Flash and Flash Cyber](https://blog.google/innovation-and-ai/models-and-research/gemini-models/3-8-flash-and-3-8-flash-cyber/) |
| OpenAI | 2026-09-03 | GPT-6 Astra | [GPT-6 Astra](https://openai.com/index/gpt-6-astra/) |
| Google | 2026-09-15 | Gemini 3.8 Live; Gemini 3.8 Live Extended Thinking | [Live and Extended Thinking](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/) |
| OpenAI | 2026-09-22 | GPT-6 Sol; GPT-6 Luna | [Sol and Luna](https://openai.com/index/introducing-gpt-6-sol-and-luna/) |
| Anthropic | 2026-09-22 | Claude 5.5 (Opus) | [Opus 5.5](https://www.anthropic.com/claude-opus-5-5) |
| Anthropic | 2026-09-28 | Claude 5.5 (Sonnet) | [Sonnet 5.5](https://www.anthropic.com/claude-sonnet-5-5) |
| OpenAI | 2026-09-29 | GPT-6.1 Sol | [GPT-6.1 Sol](https://openai.com/index/introducing-gpt-6-1-sol/) |
| Google | 2026-09-30 | Gemini 4 Argon | [Gemini 4 Argon](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/) |

Google's Live page has a September 17 update date; September 15 is its launch
date. Argon is included at its restricted Fairwind launch. Fable and Mythos 5.1
are one underlying model with different safeguards, so they remain one row,
consistent with the earlier Fable/Mythos entry. Separate named underlying models
on a shared page each carry that page's full benchmark set. This is association
with a page, not a claim that every model has a reported score on every test.
Those rows each receive a unit of weight in existing portfolio analyses.

## Extraction and checks

Discovery used the providers' news/model indexes and dated announcements. New
pages were inspected for prose, tables, tabs, footnotes, image text and alt text,
including partner evaluations. OpenAI's dynamic panels were inspected in native
Chrome alongside their accessible table/text representation. Google's benchmark
bitmaps received independent OCR passes and visual inspection; testimonial
images were also checked. Anthropic's new charts expose selectable SVG text;
their remaining bitmap assets were inspected for evaluation names. Independent
image review and PR review are recorded in the refresh PR.

When OpenAI's JavaScript chunks blocked hydration, the final visual pass rendered
the exact Vega-Lite specifications embedded in the official source HTML. Audit
dimensions and theme colors were fixed for legibility; labels, data and captions
were preserved. Two reviewers inspected all 32 Astra source panels and all ten
6.1 Sol source panels; the eleven Sol/Luna panels were reviewed from native
screenshots. This source-render method is distinct from a live-page screenshot.
The [compact OpenAI visual-audit manifest](data_refresh_2026_10_04_openai_visual_audit.json)
records all 53 states, source locations and independent pass completion.

Availability was rechecked for all 17 existing OpenAI URLs and all 12 existing
Google URLs. The latest existing Google and Anthropic benchmark tables were
checked for drift. This is a targeted historical recheck, not a claim that every
historical page was fully re-extracted. Provider pages can change after launch;
the CSV records the page content observed during this refresh.

System cards and benchmark papers only adjudicate identity or metadata here.
They do not add evaluations absent from the launch page. Specialized speech
generation/transcription models, GPT-Rosalind, and an Ultrafast service tier are
outside this release series. Generic statements about internal benchmarks with
no identifiable suite are omitted. Descriptive but identifiable private suites
remain provisional catalog entries.

## Identity decisions

| Labels | Decision and evidence |
| --- | --- |
| FrontierCode v1.1 Main; FrontierCode 1.1 (Main) | Resolve to the existing `FrontierCode v1.1` ID. The Opus 5 image table explicitly identifies Main. Preserve the stable historical ID; its rationale now specifies the track. |
| FrontierCode 1.1 Extended | Separate track explicitly named alongside Main on Astra. Keep a separate provisional identity. |
| CursorBench 3.2.0 / CursorBench 3.2 | Same Fable/Mythos chart and 73.4% result; narrow version-label alias. CursorBench 4.0 remains distinct. |
| AutomationBench / AutomationBench 1.0.6 | Sol/Luna and 6.1 prose and adjacent chart specify one result. Record the explicit revision once on those pages; keep older generic mentions separately. |
| Agents' Last Exam / Agents' Last Exam V1 | Sol/Luna prose and chart specify one result. Use V1 once there; no global historical version alias. |
| LifeSciBench / LifeSciBench Gold v1; GeneBench Pro / GeneBench Pro v13 | Astra footnote 12 identifies the table's exact revisions. Record each explicit revision once; preserve older generic identities. |
| OpenScore String Quartets / Legato camera subset | One optical music recognition result (0.84 Astra / 0.19 Sol). [LEGATO section 6](https://arxiv.org/html/2506.19065) defines Camera as an input subset. Store one corpus identity and retain the subset in the alias, not a second benchmark. `1 - OMR-NED` is a metric. |
| ExploitGym honeypot / Impossible ExploitGym | One safety test with complementary displayed metrics. Astra cross-references the impossible task evaluation; [system-card section 8.2.3](https://deploymentsafety.openai.com/gpt-6-astra) describes planted unauthorized targets in hard/impossible tasks. Keep ordinary ExploitGym capability evaluation separate. |
| FrontierMath / FrontierMath Tier 4 (v2) | Preserve `FrontierMath v2` as a changed dataset, collapsing tier slices within v2. [Epoch's changelog](https://epoch.ai/benchmarks/frontiermath-tier-4-v2) records corrections and removals on June 12. Older unversioned mentions remain separate. |
| GDP.PDF / GDP.pdf / gdp.pdf | Case spelling only. Normalize the new uppercase surface form to the existing `GDP.pdf` alias because the validator disallows duplicate aliases differing only in case. |
| Broken search / Broken search tool | One safety suite across Sol/Luna and 6.1. Both panels use the same long title, procedure and exact Astra 1.5%, Sol 4.9%, Luna 28.7% baseline results. Keep `Broken search`; alias the longer tab and chart labels. |
| Computer-use safety / Internal computer use safety benchmark | One stress test across Astra and 6.1, with identical chart title, general computer-use procedure without automatic safeguards and Astra 2.4% baseline. Store the precise `Computer-use safety stress test` chart title in 6.1 and alias it to the internal benchmark row. The shorter tab wording is retained here rather than added as a broad global alias. |
| Vals Finance Agent v2; Harvey's Legal Agent Benchmark; LABBench 2; ARC-AGI-1 | Existing Finance Agent v2, Legal Agent Benchmark, LABBench2 and ARC-AGI identities, respectively. Explicit narrow spelling/publisher aliases. |
| τ-Voice-banking / τ³-Banking Leaderboard | Same displayed score suggests continuity but the identity is unresolved; keep separate provisional rows. |
| StaticBench / CWE-Bench | Flash Cyber alt text says StaticBench while the visible chart says CWE-Bench. Retain StaticBench as a provisional appearance and flag the conflict rather than asserting an alias. |

Context lengths, reasoning budgets, prompt styles, scaffolds, repetitions, metrics
and implementation settings do not create extra benchmark identities. Terminal
versions, FrontierSWE v2, OSWorld 2.1, GDPval-AA v2.1 and other explicit new
revisions remain separate unless source evidence proves a spelling alias.
Uncertain continuity of private safety tests is left for review rather than
silenced in the distinctness table.

The Sonnet page's private finance suite is labeled `private suite of 2441 finance
tasks` in the CSV. Its printed thousands separator is removed so the label
remains one item in the comma-separated mention field.

## Targeted historical corrections

The [July 21 Google shared announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-6-flash-3-5-flash-lite-3-5-flash-cyber/)
previously split its benchmark list between Gemini 3.6 Flash and Gemini 3.5
Flash-Lite. Both blog-linked rows now carry the complete ten-item page set,
consistent with the appearance policy. Five charts and seven testimonial images
were independently OCRed and inspected. Ramp's testimonial identifies a receipt
extraction benchmark; it is added provisionally with Ramp authorship. CyberGym
is on this shared page; Big Sleep and Chrome vulnerability pipelines from the
separate DeepMind cyber page are not imported into these rows.

The current [GPT-5.6 page](https://openai.com/index/gpt-5-6/) reports ExploitBench
and ExploitGym without the previously stored 2/3 suffixes, and explicitly reports
FrontierMath v2. That row is corrected to the current observed labels. The old
versioned cyber catalog rows remain for traceability, marked `needs_review`;
their former attribution requires archived-source verification. This does not
establish when the source page changed.

Epoch's primary FrontierMath page identifies OpenAI funding, correcting the
catalog's earlier Google backing claim. Author is Epoch AI. Funding is excluded
from the repository's author-affiliation field, so both the generic and v2 rows
retain `none` there. WebDev Arena's primary
[web.lmarena.ai](https://web.lmarena.ai/) redirects to Arena's Code Arena; its
earlier Epoch AI author label is corrected to Arena.

## Taxonomy and reproducibility

New identity metadata is source-backed where possible, while private/ambiguous
identities remain `needs_review`. New facet rows are additive legacy-derived
seeds; none is presented as a completed facet audit. Existing facet decisions are
preserved. Regenerate everything with `scripts/run_pipeline.sh`; validate exact
resolution and run `python -m unittest discover -s tests -v`. The README exposes
the expanded review debt and updated confidence sensitivity.

The refresh also fixes Unicode benchmark IDs in the additive facet builder to
use the same canonical ID function as validation. A regression fixture covers
accented names, superscripts and an en dash; no existing ID is migrated.
