# Release discovery through November 22, 2026

This update extends the [October inventory](data_refresh_2026_10_04.md) with nine
model rows from eight announcements. The last observed launch is November 18.
Discovery covered the [Anthropic model index](https://www.anthropic.com/news/models),
[Google DeepMind model cards](https://deepmind.google/models/model-cards/),
[OpenAI product news](https://openai.com/news/product-releases/), and
[OpenAI model release notes](https://help.openai.com/en/articles/9624314-model-release-notes).
Each observation below comes from the linked launch page.

| Date | Announcement | Distinct benchmark mentions on page |
| --- | --- | ---: |
| Oct 7 | [Claude Haiku 5.5](https://www.anthropic.com/claude-haiku-5-5) | 12 |
| Oct 26 | [GPT-6.1 Terra](https://openai.com/index/introducing-gpt-6-1-terra/) | 7 |
| Oct 28 | [Gemini 4 Carbon](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/) | 22 |
| Nov 5 | [GPT-6 Cyber](https://openai.com/index/introducing-gpt-6-cyber/) | 10 |
| Nov 9 | [Claude Fable and Mythos 5.2](https://www.anthropic.com/claude-fable-and-mythos-5-2) | 23 |
| Nov 12 | [Gemini 4 Hydrogen](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/) | 18 |
| Nov 17 | [GPT-6.2 Astra and Sol](https://openai.com/index/introducing-gpt-6-2-astra-sol/) | 27 |
| Nov 18 | [Gemini 4 Neon](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/) | 32 |

## Counting releases

- Astra and Sol have separate model rows and share the page's full benchmark list. In the announcement-level analysis they contribute one observation per canonical benchmark.
- Anthropic identifies Fable and Mythos 5.2 as the same underlying model with different safeguards. They share one row, following the 5 and 5.1 entries.
- Carbon enters on the date of its restricted Fairwind launch. Its November 10 wider rollout and Argon's October public rollout extend access to models already in the inventory. Hydrogen's page displays a November 16 edit above its November 12 launch text. Neon includes Fairwind access for defenders on its launch page. The [model card](https://deepmind.google/models/model-cards/gemini-4-neon/) identifies one Neon model, which the inventory counts once.
- The [GPT-6 Chat update](https://openai.com/index/gpt-6-for-everyone/) uses the existing Sol and Luna names. This sample counts their September launch. The scope excludes specialized releases such as Rosalind Research, image and world generators, and the GPT-Live voice interface, which can delegate reasoning to a separate frontier model. Astra for Law is described on the Astra/Sol page as a configuration.

## Evidence and identity decisions

The review covered launch prose, comparison tables, captions, footnotes, and
partner testimonials. Anthropic's tables and chart panels expose their labels
in HTML and SVG. For OpenAI, the page source also contains tab content and
Vega-Lite specifications. Six Terra, eight Cyber, and sixteen Astra/Sol chart
specifications were checked, including panels absent from the initial article
text. Google's benchmark graphics were read with Tesseract and Apple Vision,
including middle and final frames of Hydrogen's animations. Visual inspection
of the three summary tables settled version punctuation and the distinction
between benchmark names and score columns.

| Decision | Evidence |
| --- | --- |
| Agents' Last Exam V1 and v1.1 remain separate | Terra's figure says v1. Carbon's table, the Hydrogen and Neon tables, and the GPT-6.2 chart specify v1.1. |
| BenchCAD 2.1 on Fable and BenchCAD 2.1 Core on GPT-6.2 share an ID | The [benchmark authors](https://benchcad.com/blog/benchcad-2-1) identify both runs as Core and give the same 83.5 score for Fable as the launch chart. Harness choices remain run settings. |
| Preserve reported index and implementation differences | Carbon's table specifies AA Index v5.0. Hydrogen, Astra/Sol and Neon specify v5.0.1. Both Carbon and Neon name Vals Index v2.2. Hydrogen links [AutomationBench-AA](https://artificialanalysis.ai/evaluations/automationbench-aa), while Carbon and Neon credit Zapier. |
| Preserve both Terra and Sol factuality records pending review | Terra and the [6.1 Sol page](https://openai.com/index/introducing-gpt-6-1-sol/) give their chart the same title. Their GPT-6 Astra low-effort reference error rates differ, at 13.3% and 6.26%, respectively. The pages leave the relationship between the runs open. |
| Scope private evaluations to their source | Haiku's FrontierCode 1.1 result is distinct from Cognition's unversioned FrontierCode comparison for Devin Fusion. Jump Trading's research automation and hardware optimization evaluations have different descriptions. Hydrogen's “HealthBench Pro” remains provisional pending confirmation of its relationship to HealthBench Professional. |
| Keep attribution and facet review separate | [SWE-sweep](https://swesweep.com/) lists Meta and university authors. Meta is recorded in the source-author field and falls outside the current affiliation analysis's six-label vocabulary. [MKA](https://blog.google/innovation-and-ai/models-and-research/gemini-models/multimodal-knowledge-agent-benchmark/) credits Google DeepMind and Artificial Analysis. New identities and their rule-derived facets are marked for review. |

Linked reports and benchmark sites helped identify names already present on the
launch pages. The inventory uses the versions of those pages available at
review time. The [launch mentions](../analysis/benchmark_lifecycle/launch_mentions.csv)
give the resulting canonical observations and their source URLs.
