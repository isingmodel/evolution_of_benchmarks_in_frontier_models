# Benchmark reporting life cycles

Observation cutoff: **2026-09-30**. This report covers all **286**
catalog identities: **284** have an observed mention and
**2** have no observed mention through this cutoff.

The **59** model rows collapse to **55** distinct
announcements, **51** of which contain recorded benchmarks.
Aliases are deduplicated within each model row and then within each announcement.
There are **743** benchmark–announcement observations, compared with
**790** canonical benchmark–model-row observations.

**167** identities appear on one announcement,
**117** recur across announcements, and
**74** appear across multiple providers.
These are descriptions of the covered public pages, not a survival estimate.

First observed is entry into this sample, not publication or private adoption.
First-to-last span is an observed lower bound and can be zero. Last observed is
not retirement. Unobserved dates, spans and diffusion lags are blank; a blank
follow-up share means no defined denominator, not zero repeat use.

## Outputs and interpretation

- [All benchmark life cycles](benchmark_lifecycles.csv): dates, counts, diffusion, recency and cadence-adjusted reporting measures.
- [Per-provider life cycles](provider_lifecycles.csv): each provider's first/last mention and follow-up denominator, including unadopted identities.
- [Launch inventory](launch_events.csv): every covered announcement, including pages with no recorded benchmarks.
- [Launch observations](launch_mentions.csv): benchmark IDs, dates, source URLs and mentioning model rows for tracing each timeline.
- [Run summary](summary.json): cutoff, observation units and catalog coverage.

Follow-up reporting share divides mentions after a provider's first adoption date
by that provider's covered announcements after that date. Empty benchmark pages
are included as reporting opportunities; omission cannot establish non-use.
The aggregate pools opportunities only from adopting providers. Same-day events
are distinct when their URLs differ, but no within-day follow-up order is assumed.
Per-provider post-last gaps use each provider's own last mention; the aggregate
post-last gap uses the benchmark's last mention across all adopting providers.
Recent counts cover the last 180 calendar days inclusively.

Version and track identities follow the catalog. This analysis infers no family,
successor or replacement relationships. Existing combined historical identities
and provisional private-suite mappings affect the results; identity review status
is retained in the full table. See [methodology](README.md).

## Fast observed cross-provider diffusion

These lags use every provider's first observed date. Same-day first-adopter ties
remain ties, with zero second/third-provider lag.

| Benchmark | First observed | First providers | Second-provider lag (days) | Third-provider lag (days) |
| --- | --- | --- | --- | --- |
| Terminal-Bench 4.0 | 2026-09-01 | Anthropic | 1 | 2 |
| MMMLU | 2025-02-25 | Anthropic | 2 | 266 |
| Terminal-Bench Science 0.1 | 2026-09-01 | Anthropic | 2 | 29 |
| Terminal-Bench 2.0 | 2025-11-18 | Google | 6 | 79 |
| OfficeQA Pro | 2026-04-16 | Anthropic | 7 | — |
| Chartography | 2026-09-22 | Anthropic | 8 | — |
| Finance Agent v2 | 2026-05-19 | Google | 9 | — |
| Terminal-Bench 2.1 | 2026-05-19 | Google | 9 | 51 |
| GDPval-AA v2 | 2026-06-30 | Anthropic | 9 | 21 |
| DeepSWE v1.1 | 2026-07-09 | OpenAI | 12 | 15 |

## Complete catalog

`single_launch` means one announcement; `repeated_one_provider` means several
announcements from one provider; `shared_across_providers` means at least two
providers. `unobserved` means no covered mention by this cutoff. These labels
do not describe benchmark maturity, quality, inactivity or retirement.

| Benchmark | First observed | Last observed | Span (days) | Launches | Providers | Reporting pattern | Identity review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30-day simulated run-a-business eval | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| τ³-Banking Leaderboard | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | needs_review |
| 93-task coding benchmark | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| AA-Briefcase v1.1 | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| AA-LCR | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| AA-Omniscience | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| ActivityNet | 2024-05-13 | 2024-05-13 | 0 | 1 | 1 | single_launch | legacy_seed |
| Adaptyv Bio's protein design competitions | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Advanced Cybersecurity Completion Rate | 2026-08-10 | 2026-08-10 | 0 | 1 | 1 | single_launch | accepted |
| agentic code-review tests | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| Agents' Last Exam | 2026-07-09 | 2026-09-30 | 83 | 4 | 2 | shared_across_providers | accepted |
| Agents' Last Exam V1 | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| AI2D | 2024-03-04 | 2024-06-21 | 109 | 3 | 2 | shared_across_providers | legacy_seed |
| Aider Polyglot | 2025-03-25 | 2025-11-24 | 244 | 5 | 3 | shared_across_providers | legacy_seed |
| AIME | 2024-09-12 | 2025-11-18 | 432 | 15 | 3 | shared_across_providers | legacy_seed |
| Anthropic internal autonomous agentic coding evaluation | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| APEX-Agents | 2026-02-19 | 2026-03-05 | 14 | 2 | 2 | shared_across_providers | legacy_seed |
| ARC-AGI | 2024-03-04 | 2026-09-03 | 913 | 6 | 3 | shared_across_providers | legacy_seed |
| ARC-AGI-2 | 2025-11-24 | 2026-09-03 | 283 | 7 | 3 | shared_across_providers | legacy_seed |
| ARC-AGI-3 | 2026-07-09 | 2026-09-03 | 56 | 3 | 2 | shared_across_providers | accepted |
| Artificial Analysis Coding Agent Index v1.1 | 2026-07-09 | 2026-07-24 | 15 | 2 | 2 | shared_across_providers | accepted |
| Artificial Analysis Coding Agent Index v1.4 | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| Artificial Analysis Coding Index | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| Artificial Analysis Intelligence Index | 2026-04-23 | 2026-08-13 | 112 | 4 | 2 | shared_across_providers | accepted |
| Artificial Analysis Intelligence Index v4.1 | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | accepted |
| Artificial Analysis Intelligence Index v4.1.1 | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| Artificial Analysis Speech to Speech Index | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | accepted |
| automated alignment assessment | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| automated behavioral audit | 2026-04-16 | 2026-09-28 | 165 | 7 | 1 | repeated_one_provider | accepted |
| AutomationBench | 2026-06-09 | 2026-09-30 | 113 | 8 | 3 | shared_across_providers | accepted |
| AutomationBench 1.0.6 | 2026-09-22 | 2026-09-29 | 7 | 2 | 1 | repeated_one_provider | needs_review |
| BenchCAD | 2026-07-09 | 2026-09-03 | 56 | 2 | 1 | repeated_one_provider | accepted |
| Big Bench Audio | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | accepted |
| Big-Bench Hard | 2023-12-06 | 2024-06-21 | 198 | 3 | 2 | shared_across_providers | legacy_seed |
| Big Finance Bench | 2026-07-09 | 2026-09-22 | 75 | 2 | 2 | shared_across_providers | accepted |
| Big Sleep Evaluation | 2026-07-21 | 2026-07-21 | 0 | 1 | 1 | single_launch | accepted |
| BigLaw Bench | 2026-02-05 | 2026-04-23 | 77 | 4 | 2 | shared_across_providers | legacy_seed |
| Biology Olympiad | 2023-03-14 | 2023-03-14 | 0 | 1 | 1 | single_launch | legacy_seed |
| BioMysteryBench | 2026-06-09 | 2026-09-02 | 85 | 4 | 2 | shared_across_providers | accepted |
| BioPipelineBench | 2026-02-05 | 2026-02-05 | 0 | 1 | 1 | single_launch | accepted |
| Bird-SQL | 2024-12-11 | 2024-12-11 | 0 | 1 | 1 | single_launch | legacy_seed |
| BixBench | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| Blueprint-Bench 2 | 2026-05-19 | 2026-06-09 | 21 | 2 | 2 | shared_across_providers | accepted |
| Broken search | 2026-09-22 | 2026-09-29 | 7 | 2 | 1 | repeated_one_provider | needs_review |
| BrowseComp | 2025-04-16 | 2026-09-03 | 505 | 11 | 3 | shared_across_providers | legacy_seed |
| BrowseComp Long Context | 2025-12-11 | 2025-12-11 | 0 | 1 | 1 | single_launch | accepted |
| BrowseComp-Plus | 2025-11-24 | 2025-11-24 | 0 | 1 | 1 | single_launch | legacy_seed |
| browser-agent benchmark | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Capture-the-Flags challenge tasks (Internal) | 2026-04-23 | 2026-07-09 | 77 | 2 | 1 | repeated_one_provider | accepted |
| Chartography | 2026-09-22 | 2026-09-30 | 8 | 3 | 2 | shared_across_providers | needs_review |
| ChartQA | 2024-03-04 | 2024-06-21 | 109 | 3 | 2 | shared_across_providers | legacy_seed |
| CharXiv | 2025-04-14 | 2025-12-11 | 241 | 5 | 2 | shared_across_providers | legacy_seed |
| CharXiv Reasoning | 2026-03-03 | 2026-09-02 | 183 | 5 | 2 | shared_across_providers | accepted |
| Chrome Production Commit Scanning Pipeline | 2026-07-21 | 2026-07-21 | 0 | 1 | 1 | single_launch | needs_review |
| Citations eval | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Codeforces | 2024-09-12 | 2025-04-16 | 216 | 4 | 1 | repeated_one_provider | legacy_seed |
| Coding deception | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| coding evals | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| COLLIE | 2025-04-14 | 2025-08-07 | 115 | 2 | 1 | repeated_one_provider | legacy_seed |
| combined evaluation suite | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| ComplexFunc Bench | 2025-04-14 | 2025-04-14 | 0 | 1 | 1 | single_launch | legacy_seed |
| containment-boundary evaluation | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| containment evaluations | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| core analytics benchmark | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| CoT-Control | 2026-03-05 | 2026-03-05 | 0 | 1 | 1 | single_launch | accepted |
| CoVoST 2 | 2023-12-06 | 2024-12-11 | 371 | 2 | 1 | repeated_one_provider | legacy_seed |
| CritPt | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| CursorBench | 2026-04-16 | 2026-07-09 | 84 | 4 | 2 | shared_across_providers | accepted |
| CursorBench 3.2 | 2026-07-24 | 2026-09-01 | 39 | 2 | 1 | repeated_one_provider | accepted |
| CursorBench 4.0 | 2026-09-22 | 2026-09-28 | 6 | 2 | 1 | repeated_one_provider | needs_review |
| CWE-Bench | 2026-09-02 | 2026-09-02 | 0 | 1 | 1 | single_launch | needs_review |
| CWE-bench v0 | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | accepted |
| CWE-bench v1 | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | accepted |
| CyberGym | 2026-02-05 | 2026-09-02 | 209 | 7 | 3 | shared_across_providers | legacy_seed |
| Cybersecurity CTFs | 2024-09-12 | 2026-02-05 | 511 | 2 | 1 | repeated_one_provider | legacy_seed |
| CyScenarioBench | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | accepted |
| Data Science Tasks (Internal) | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| Database Migration Tasks (Internal) | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| DataBench | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| DeepSearchQA | 2026-07-24 | 2026-07-24 | 0 | 1 | 1 | single_launch | accepted |
| DeepSWE v1.1 | 2026-07-09 | 2026-09-30 | 83 | 9 | 3 | shared_across_providers | accepted |
| Design Tasks (Internal) | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| DocVQA | 2023-12-06 | 2024-06-21 | 198 | 4 | 3 | shared_across_providers | legacy_seed |
| DROP | 2023-12-06 | 2024-06-21 | 198 | 4 | 3 | shared_across_providers | legacy_seed |
| early design evals | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| EgoSchema | 2024-05-13 | 2024-12-11 | 212 | 2 | 2 | shared_across_providers | legacy_seed |
| ERQA | 2025-08-07 | 2025-08-07 | 0 | 1 | 1 | single_launch | legacy_seed |
| EVA-Bench | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | accepted |
| Eve's plaintiff-law tasks | 2026-06-30 | 2026-06-30 | 0 | 1 | 1 | single_launch | needs_review |
| everyday spreadsheet suite | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| Expert-SWE (Internal) | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| ExploitBench | 2026-06-09 | 2026-09-03 | 86 | 4 | 2 | shared_across_providers | needs_review |
| ExploitBench 2 | — | — | — | 0 | 0 | unobserved | needs_review |
| ExploitBench (June–August 2026) | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| ExploitGym | 2026-07-09 | 2026-09-03 | 56 | 3 | 1 | repeated_one_provider | needs_review |
| ExploitGym 3 | — | — | — | 0 | 0 | unobserved | needs_review |
| ExploitGym honeypot | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | accepted |
| FACTS Benchmark suite | 2025-11-18 | 2026-03-03 | 105 | 2 | 1 | repeated_one_provider | accepted |
| FACTS Grounding | 2024-12-11 | 2024-12-11 | 0 | 1 | 1 | single_launch | legacy_seed |
| Finance Agent | 2025-09-30 | 2026-02-05 | 128 | 2 | 1 | repeated_one_provider | legacy_seed |
| Finance Agent v2 | 2026-05-19 | 2026-09-30 | 134 | 4 | 2 | shared_across_providers | accepted |
| FinanceAgent v1.1 | 2026-03-05 | 2026-04-23 | 49 | 3 | 2 | shared_across_providers | accepted |
| Firefox | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| Firefox 147 exploit evaluation | 2026-06-30 | 2026-06-30 | 0 | 1 | 1 | single_launch | accepted |
| first-generation evals | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| FLEURS | 2023-12-06 | 2023-12-06 | 0 | 1 | 1 | single_launch | legacy_seed |
| frontend benchmark | 2026-07-24 | 2026-07-24 | 0 | 1 | 1 | single_launch | needs_review |
| Frontier-Bench v0.1 | 2026-07-24 | 2026-07-24 | 0 | 1 | 1 | single_launch | accepted |
| Frontier Science Research | 2026-03-05 | 2026-03-05 | 0 | 1 | 1 | single_launch | accepted |
| FrontierBench | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| FrontierCode (Diamond) | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | accepted |
| FrontierCode v1.1 | 2026-07-24 | 2026-09-28 | 66 | 6 | 3 | shared_across_providers | accepted |
| FrontierCode v1.1 (Extended) | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| FrontierFinance | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| FrontierMath | 2025-01-31 | 2026-04-23 | 447 | 5 | 1 | repeated_one_provider | legacy_seed |
| FrontierMath v2 | 2026-07-09 | 2026-09-03 | 56 | 2 | 1 | repeated_one_provider | accepted |
| FrontierSWE v2 | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | accepted |
| gdp.pdf | 2026-06-09 | 2026-09-29 | 112 | 5 | 3 | shared_across_providers | accepted |
| GDPval | 2025-12-11 | 2026-04-23 | 133 | 4 | 1 | repeated_one_provider | accepted |
| GDPval-AA | 2026-02-05 | 2026-06-09 | 124 | 7 | 3 | shared_across_providers | accepted |
| GDPval-AA v2 | 2026-06-30 | 2026-09-02 | 64 | 7 | 3 | shared_across_providers | accepted |
| GDPval-AA v2.1 | 2026-09-22 | 2026-09-28 | 6 | 2 | 1 | repeated_one_provider | needs_review |
| GeneBench | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| GeneBench Pro | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | accepted |
| GeneBench Pro v13 | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| Global PIQA | 2025-11-18 | 2025-11-18 | 0 | 1 | 1 | single_launch | legacy_seed |
| GPQA | 2024-03-04 | 2025-12-11 | 647 | 14 | 3 | shared_across_providers | legacy_seed |
| GPQA Diamond | 2024-10-23 | 2026-09-03 | 680 | 15 | 3 | shared_across_providers | legacy_seed |
| GraphWalks | 2025-04-14 | 2026-09-30 | 534 | 8 | 3 | shared_across_providers | legacy_seed |
| Gray Swan IPI benchmark | 2026-09-02 | 2026-09-30 | 28 | 2 | 1 | repeated_one_provider | accepted |
| Gray Swan prompt injection benchmark | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| GRE | 2023-07-11 | 2023-07-11 | 0 | 1 | 1 | single_launch | legacy_seed |
| GSM8K | 2023-07-11 | 2024-06-21 | 346 | 4 | 2 | shared_across_providers | legacy_seed |
| Harbor-Index | 2026-08-13 | 2026-08-13 | 0 | 1 | 1 | single_launch | accepted |
| Harvey LAB-AA | 2026-08-13 | 2026-08-13 | 0 | 1 | 1 | single_launch | accepted |
| Healthbench | 2025-08-07 | 2025-08-07 | 0 | 1 | 1 | single_launch | legacy_seed |
| HealthBench Professional | 2026-06-09 | 2026-09-03 | 86 | 4 | 2 | shared_across_providers | accepted |
| Hebbia's Finance Benchmark | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| HellaSwag | 2023-12-06 | 2024-03-04 | 89 | 2 | 2 | shared_across_providers | legacy_seed |
| HiddenMath | 2024-12-11 | 2024-12-11 | 0 | 1 | 1 | single_launch | legacy_seed |
| HLE (Humanity's Last Exam) | 2025-03-25 | 2026-09-28 | 552 | 20 | 3 | shared_across_providers | accepted |
| HLE-Verified | 2026-08-13 | 2026-09-02 | 20 | 2 | 1 | repeated_one_provider | accepted |
| HMMT | 2025-08-07 | 2025-12-11 | 126 | 2 | 1 | repeated_one_provider | legacy_seed |
| HumanEval | 2023-07-11 | 2024-10-23 | 470 | 7 | 3 | shared_across_providers | legacy_seed |
| IFBench | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| IFEval | 2025-02-25 | 2025-04-14 | 48 | 2 | 2 | shared_across_providers | legacy_seed |
| IMC research suite | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| IMC trading-analysis evaluations | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| IMO | 2024-09-12 | 2024-09-12 | 0 | 1 | 1 | single_launch | legacy_seed |
| implicit-need tests | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| incident investigation evals | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Infographic VQA | 2023-12-06 | 2023-12-06 | 0 | 1 | 1 | single_launch | legacy_seed |
| internal and external PR benchmarks | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| Internal circumvention benchmark | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| internal coding benchmarks | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| Internal computer use safety benchmark | 2026-09-03 | 2026-09-29 | 26 | 2 | 1 | repeated_one_provider | needs_review |
| internal factuality evaluation | 2026-09-22 | 2026-09-29 | 7 | 2 | 1 | repeated_one_provider | needs_review |
| internal Finance benchmark | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Internal hallucination benchmark | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| internal organic chemistry benchmark | 2026-07-24 | 2026-07-24 | 0 | 1 | 1 | single_launch | needs_review |
| internal research-agent benchmark | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| Internal Research Debugging Evaluation | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| internal testing benchmark | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| Investment Banking Modeling Tasks (Internal) | 2026-03-05 | 2026-04-23 | 49 | 2 | 1 | repeated_one_provider | accepted |
| Jailbreak Eval | 2024-09-12 | 2024-09-12 | 0 | 1 | 1 | single_launch | legacy_seed |
| KernelGen 1P | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| LABBench2 | 2026-08-13 | 2026-09-30 | 48 | 3 | 1 | repeated_one_provider | accepted |
| Legal Agent Benchmark | 2026-05-28 | 2026-09-30 | 125 | 6 | 2 | shared_across_providers | accepted |
| Legora's internal eval harness | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| LifeSciBench | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | accepted |
| LifeSciBench Gold v1 | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| LiveBench Coding | 2025-01-31 | 2025-01-31 | 0 | 1 | 1 | single_launch | legacy_seed |
| LiveCodeBench | 2024-12-11 | 2026-03-03 | 447 | 4 | 1 | repeated_one_provider | legacy_seed |
| LiveCodeBench Pro | 2026-02-19 | 2026-02-19 | 0 | 1 | 1 | single_launch | legacy_seed |
| LMArena | 2025-11-18 | 2026-03-03 | 105 | 2 | 1 | repeated_one_provider | legacy_seed |
| long-horizon molecular prediction and design evaluation | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| Lovable internal evals | 2026-07-24 | 2026-07-24 | 0 | 1 | 1 | single_launch | needs_review |
| LVBench | 2026-08-13 | 2026-09-30 | 48 | 3 | 1 | repeated_one_provider | accepted |
| M3Exam | 2024-05-13 | 2024-05-13 | 0 | 1 | 1 | single_launch | legacy_seed |
| Management Consulting Tasks (Internal) | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| MATH | 2023-12-06 | 2025-01-31 | 422 | 9 | 3 | shared_across_providers | legacy_seed |
| MATH 500 | 2025-02-25 | 2025-02-25 | 0 | 1 | 1 | single_launch | legacy_seed |
| MathArena Apex | 2025-11-18 | 2025-11-18 | 0 | 1 | 1 | single_launch | legacy_seed |
| MathVista | 2023-12-06 | 2025-04-16 | 497 | 7 | 3 | shared_across_providers | legacy_seed |
| MCQA | 2023-12-06 | 2023-12-06 | 0 | 1 | 1 | single_launch | legacy_seed |
| MedChemBench (Internal) | 2026-07-09 | 2026-09-03 | 56 | 2 | 1 | repeated_one_provider | needs_review |
| MGSM | 2024-03-04 | 2025-01-31 | 333 | 4 | 2 | shared_across_providers | legacy_seed |
| Mind2Web | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| MLE-Bench | 2026-07-21 | 2026-07-21 | 0 | 1 | 1 | single_launch | accepted |
| MMLU / MMLU-Pro | 2023-12-06 | 2025-04-14 | 495 | 10 | 3 | shared_across_providers | legacy_seed |
| MMMLU | 2025-02-25 | 2026-04-16 | 415 | 13 | 3 | shared_across_providers | legacy_seed |
| MMMU / MMMU Pro | 2023-12-06 | 2026-03-03 | 818 | 22 | 3 | shared_across_providers | legacy_seed |
| MMMU Pro | 2026-02-05 | 2026-07-09 | 154 | 5 | 3 | shared_across_providers | accepted |
| Model ML's FinBench | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| MRCR | 2024-12-11 | 2025-11-18 | 342 | 4 | 2 | shared_across_providers | legacy_seed |
| MRCR v2 | 2025-12-11 | 2026-09-03 | 266 | 11 | 3 | shared_across_providers | legacy_seed |
| MTOB benchmark | 2024-02-15 | 2024-02-15 | 0 | 1 | 1 | single_launch | legacy_seed |
| Multi-IF | 2025-04-14 | 2025-04-14 | 0 | 1 | 1 | single_launch | legacy_seed |
| multi-step Unity Editor and coding benchmark | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| MultiChallenge | 2025-04-14 | 2025-08-07 | 115 | 3 | 1 | repeated_one_provider | legacy_seed |
| NanoGPT | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| Natural2Code | 2023-12-06 | 2024-12-11 | 371 | 2 | 1 | repeated_one_provider | legacy_seed |
| Needle In A Haystack | 2024-02-15 | 2025-04-14 | 424 | 3 | 3 | shared_across_providers | legacy_seed |
| OfficeQA | 2026-03-05 | 2026-03-05 | 0 | 1 | 1 | single_launch | accepted |
| OfficeQA Pro | 2026-04-16 | 2026-04-23 | 7 | 2 | 2 | shared_across_providers | accepted |
| offline Slackbot evals | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| OmniDocBench | 2026-03-05 | 2026-03-05 | 0 | 1 | 1 | single_launch | accepted |
| OmniDocBench 1.5 | 2025-11-18 | 2025-11-18 | 0 | 1 | 1 | single_launch | legacy_seed |
| Online-Mind2Web | 2026-03-05 | 2026-05-28 | 84 | 2 | 2 | shared_across_providers | accepted |
| OpenRCA | 2026-02-05 | 2026-02-05 | 0 | 1 | 1 | single_launch | legacy_seed |
| OpenScore String Quartets | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| OSS-Fuzz | 2026-06-09 | 2026-07-24 | 45 | 2 | 1 | repeated_one_provider | accepted |
| OSWorld | 2024-10-23 | 2026-02-05 | 470 | 5 | 1 | repeated_one_provider | legacy_seed |
| OSWorld 2.0 | 2026-07-09 | 2026-09-30 | 83 | 9 | 3 | shared_across_providers | accepted |
| OSWorld 2.1 | 2026-09-22 | 2026-09-28 | 6 | 2 | 1 | repeated_one_provider | needs_review |
| OSWorld-Verified | 2026-02-05 | 2026-07-21 | 166 | 9 | 3 | shared_across_providers | accepted |
| Pokémon Red | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| PostTrainBench | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | accepted |
| PostTrainBench Lite | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| PowerPoint eval | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| private suite of 2441 finance tasks | 2026-09-28 | 2026-09-28 | 0 | 1 | 1 | single_launch | needs_review |
| prompt injection benchmark | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Qodo's real-world code review benchmark | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| Rakuten-SWE-Bench | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| Real-world Vulnerability Discovery | 2026-09-02 | 2026-09-30 | 28 | 2 | 1 | repeated_one_provider | accepted |
| receipt extraction benchmark | 2026-07-21 | 2026-07-21 | 0 | 1 | 1 | single_launch | needs_review |
| RedlineBench | 2026-09-01 | 2026-09-01 | 0 | 1 | 1 | single_launch | needs_review |
| Reviewer bypass | 2026-09-22 | 2026-09-29 | 7 | 2 | 1 | repeated_one_provider | needs_review |
| RiemannBench | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | needs_review |
| RSI Index | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| Scale MCP-Atlas | 2025-11-24 | 2026-05-19 | 176 | 8 | 3 | shared_across_providers | accepted |
| SciCode | 2026-02-19 | 2026-04-23 | 63 | 2 | 2 | shared_across_providers | legacy_seed |
| ScreenSpot-Pro | 2025-11-18 | 2026-09-03 | 289 | 4 | 3 | shared_across_providers | legacy_seed |
| SEC-Bench Pro | 2026-07-09 | 2026-09-03 | 56 | 2 | 1 | repeated_one_provider | accepted |
| seven-task benchmark | 2026-07-09 | 2026-07-09 | 0 | 1 | 1 | single_launch | needs_review |
| SimpleQA | 2025-01-31 | 2025-11-18 | 291 | 4 | 2 | shared_across_providers | legacy_seed |
| SimpleQA Verified | 2026-03-03 | 2026-03-03 | 0 | 1 | 1 | single_launch | legacy_seed |
| Speech Agent Arena | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | accepted |
| SRE-Bench | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| StaticBench | 2026-09-02 | 2026-09-02 | 0 | 1 | 1 | single_launch | needs_review |
| STEM | 2025-01-31 | 2025-01-31 | 0 | 1 | 1 | single_launch | legacy_seed |
| Structural Biology | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| Super-Agent benchmark | 2026-05-28 | 2026-05-28 | 0 | 1 | 1 | single_launch | needs_review |
| SWE-bench | 2025-02-27 | 2025-02-27 | 0 | 1 | 1 | single_launch | legacy_seed |
| SWE-bench Multilingual | 2025-11-24 | 2026-04-16 | 143 | 3 | 1 | repeated_one_provider | legacy_seed |
| SWE-bench Multimodal | 2026-04-16 | 2026-04-16 | 0 | 1 | 1 | single_launch | accepted |
| SWE-bench Pro | 2025-12-11 | 2026-07-21 | 222 | 12 | 3 | shared_across_providers | legacy_seed |
| SWE-bench verified | 2024-10-23 | 2026-04-16 | 540 | 18 | 3 | shared_across_providers | legacy_seed |
| SWE-Lancer | 2025-04-14 | 2025-12-11 | 241 | 3 | 1 | repeated_one_provider | legacy_seed |
| SWE-Lancer IC Diamond | 2026-02-05 | 2026-02-05 | 0 | 1 | 1 | single_launch | accepted |
| TAU-2 bench | 2025-08-07 | 2026-04-23 | 259 | 10 | 3 | shared_across_providers | accepted |
| Tau-bench | 2024-10-23 | 2025-08-05 | 286 | 6 | 2 | shared_across_providers | legacy_seed |
| Terminal-bench | 2025-05-23 | 2026-04-16 | 328 | 6 | 1 | repeated_one_provider | legacy_seed |
| Terminal-Bench 2.0 | 2025-11-18 | 2026-04-23 | 156 | 7 | 3 | shared_across_providers | legacy_seed |
| Terminal-Bench 2.1 | 2026-05-19 | 2026-09-02 | 106 | 8 | 3 | shared_across_providers | accepted |
| Terminal-Bench 3.0 | 2026-08-13 | 2026-08-13 | 0 | 1 | 1 | single_launch | accepted |
| Terminal-Bench 4.0 | 2026-09-01 | 2026-09-30 | 29 | 6 | 3 | shared_across_providers | accepted |
| Terminal-Bench Hard | 2026-04-23 | 2026-04-23 | 0 | 1 | 1 | single_launch | accepted |
| Terminal-Bench Science 0.1 | 2026-09-01 | 2026-09-30 | 29 | 5 | 3 | shared_across_providers | accepted |
| TextVQA | 2023-12-06 | 2023-12-06 | 0 | 1 | 1 | single_launch | legacy_seed |
| Toolathlon | 2025-12-11 | 2026-07-09 | 210 | 5 | 2 | shared_across_providers | legacy_seed |
| trading benchmark | 2026-07-24 | 2026-07-24 | 0 | 1 | 1 | single_launch | needs_review |
| trading intuition evaluations | 2026-09-03 | 2026-09-03 | 0 | 1 | 1 | single_launch | needs_review |
| trading-support suite | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| Unauthorized interaction | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| Uniform Bar Exam | 2023-03-14 | 2023-07-11 | 119 | 2 | 2 | shared_across_providers | legacy_seed |
| Vals Index | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | accepted |
| VATEX | 2023-12-06 | 2023-12-06 | 0 | 1 | 1 | single_launch | legacy_seed |
| Vending-Bench | 2025-11-24 | 2025-11-24 | 0 | 1 | 1 | single_launch | legacy_seed |
| Vending-Bench 2 | 2025-11-18 | 2026-04-16 | 149 | 3 | 2 | shared_across_providers | accepted |
| Vibe Code Bench | 2026-09-30 | 2026-09-30 | 0 | 1 | 1 | single_launch | accepted |
| Vibe-Eval | 2024-12-11 | 2025-03-25 | 104 | 2 | 1 | repeated_one_provider | legacy_seed |
| ViBench | 2026-06-09 | 2026-06-09 | 0 | 1 | 1 | single_launch | needs_review |
| Video-MME | 2025-04-14 | 2025-04-14 | 0 | 1 | 1 | single_launch | legacy_seed |
| Video-MMMU | 2025-08-07 | 2026-03-03 | 208 | 4 | 2 | shared_across_providers | legacy_seed |
| τ-Voice | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | accepted |
| τ-Voice-banking | 2026-09-15 | 2026-09-15 | 0 | 1 | 1 | single_launch | needs_review |
| VQAv2 | 2023-12-06 | 2023-12-06 | 0 | 1 | 1 | single_launch | legacy_seed |
| Vulnerability Discovery and Report Writing | 2026-08-10 | 2026-08-10 | 0 | 1 | 1 | single_launch | accepted |
| WANDR | 2026-09-22 | 2026-09-22 | 0 | 1 | 1 | single_launch | needs_review |
| Warning circumvention | 2026-09-22 | 2026-09-29 | 7 | 2 | 1 | repeated_one_provider | needs_review |
| WebArena-Verified | 2026-03-05 | 2026-03-05 | 0 | 1 | 1 | single_launch | accepted |
| WebDev Arena | 2026-08-13 | 2026-08-13 | 0 | 1 | 1 | single_launch | legacy_seed |
| WebVoyager | 2024-12-11 | 2024-12-11 | 0 | 1 | 1 | single_launch | legacy_seed |
| Wiz Penetration Test Benchmark | 2026-09-02 | 2026-09-30 | 28 | 2 | 1 | repeated_one_provider | accepted |
| Zero-Day Discovery Eval | 2026-08-10 | 2026-08-10 | 0 | 1 | 1 | single_launch | accepted |
