# Benchmark Audit Notes

이 문서는 v3 migration 중 source audit가 끝난 benchmark들의 분류 결정을 기록한다. 목표는 단일 `task_mode`로 애매한 benchmark를 억지로 고정하지 않고, legacy chart projection과 연구용 multi-facet annotation을 분리해 보존하는 것이다.

Accessed date: 2026-04-25

## Summary

| Benchmark | Legacy v2 projection | v3 audit status | Key decision |
|---|---|---|---|
| `TAU-2 bench` | `Agentic / General/Commonsense` | `accepted` | Autonomous driving trajectory rationale was wrong; TAU-2 is dual-control conversational agent evaluation. |
| `Vending-Bench 2` | `Agentic / General/Commonsense` | `accepted` | Cybersecurity rationale was wrong; the benchmark is long-horizon simulated vending-business operation. |
| `GDPval` | `Generative Reasoning / Specialized` | `accepted` | It is mixed professional deliverable generation, not GDP/economics-only reasoning. |
| `GDPval-AA` | `Agentic / Specialized` | `accepted` | Treat as Artificial Analysis' agentic GDPval-style knowledge-work evaluation. |
| `BrowseComp Long Context` | `Knowledge Retrieval / General` | `accepted` | This variant is long-context retrieval from noisy in-context data, not live browsing. |
| `FACTS Benchmark suite` | `Knowledge Retrieval / General` | `needs_review` | Suite-level projection is useful, but subbenchmarks should be carded separately. |
| `BioPipelineBench` | `Agentic / Specialized` | `needs_review` | Provider documentation supports bioinformatics workflow execution with tools, but public benchmark details are limited. |

## Decisions

### TAU-2 Bench

Evidence:

- https://arxiv.org/abs/2506.07982
- https://github.com/sierra-research/tau2-bench

Decision:

- Replace the incorrect autonomous-driving trajectory source with the TAU-2 paper.
- Use `Agentic` as the v2 headline projection.
- Use v3 facets for `agentic_task_completion`, `tool_use`, `tool_calling`, `multi_turn_dialogue`, `environment_interaction`, and `Other Specialized`.

Rationale:

The TAU-2 paper describes a dual-control environment where both the agent and user can use tools in shared task state. That is an agentic interaction construct, not multimodal perception or coding.

### Vending-Bench 2

Evidence:

- https://andonlabs.com/evals/vending-bench-2
- https://arxiv.org/abs/2502.15840

Decision:

- Replace the incorrect cybersecurity rationale.
- Use `Agentic` as the v2 headline projection.
- Use v3 facets for long-horizon business operation, tool use, environment interaction, multi-step planning, and `Other Specialized`.

Rationale:

Andon Labs frames Vending-Bench 2 as a simulated vending-machine business management task with purchasing, pricing, supplier negotiation, and delayed operational consequences.

### GDPval

Evidence:

- https://openai.com/index/gdpval/
- https://arxiv.org/abs/2510.04374

Decision:

- Replace acronym-derived rationale.
- Keep `Generative Reasoning` as the v2 headline projection.
- Use multi-domain v3 labels because the benchmark spans professional sectors and occupations.

Rationale:

GDPval evaluates realistic knowledge-work deliverables across occupations and sectors. The local v2 domain remains `Specialized (Law/Bio/Finance)` only as a broad chart-compatible projection.

### GDPval-AA

Evidence:

- https://artificialanalysis.ai/methodology/intelligence-benchmarking
- https://artificialanalysis.ai/evaluations/gdpval-aa

Decision:

- Treat `GDPval-AA` as a separate canonical benchmark from `GDPval`.
- Set source author to Artificial Analysis.
- Use `Agentic` as the v2 headline projection and preserve mixed professional domains in v3.

Rationale:

Artificial Analysis describes GDPval-AA as real-world knowledge work with agentic task completion, file outputs, and pairwise/Elo-style scoring.

### BrowseComp Long Context

Evidence:

- https://huggingface.co/datasets/openai/BrowseCompLongContext
- https://openai.com/index/browsecomp/

Decision:

- Use `Knowledge Retrieval` as the v2 headline projection.
- Use `long_context_primary` and `long_context_retrieval` in v3.

Rationale:

The dataset card says the benchmark converts BrowseComp questions into long-context tasks where models retrieve relevant information from noisy in-context data. It should not be treated as live browser interaction.

### FACTS Benchmark Suite

Evidence:

- https://deepmind.google/blog/facts-benchmark-suite-systematically-evaluating-the-factuality-of-large-language-models/
- https://storage.googleapis.com/deepmind-media/FACTS/FACTS_benchmark_suite_paper.pdf

Decision:

- Keep the suite-level v2 projection as `Knowledge Retrieval`.
- Mark v3 rows as `needs_review` because the suite aggregates parametric, search, multimodal, and grounding components.

Rationale:

The suite is a composite factuality benchmark. It is safer to split or card subbenchmarks before using it for strong fine-grained trend claims.

### BioPipelineBench

Evidence:

- https://www.anthropic.com/claude-sonnet-4-6-system-card
- https://www.anthropic.com/news/claude-opus-4-6

Decision:

- Use `Agentic` as the v2 headline projection.
- Use v3 facets for `Bio/Medicine`, tool use, code generation, terminal operation, and provider-created/private evaluation risk.
- Keep `needs_review` until a public benchmark card or dataset is available.

Rationale:

Anthropic's system card describes bioinformatics workflow execution with bash, code execution, and package-manager access. That supports an agentic workflow interpretation, but public scoring details remain limited.

### Firefox identity (open)

`benchmark_firefox` (“Firefox”) and `benchmark_firefox_147_exploit_evaluation` (“Firefox 147 exploit evaluation”) may refer to the same Mozilla exploit-evaluation track. The former remains `needs_review`; the latter is `accepted`, and both are attributed to Anthropic/Others(Mozilla). They have not been merged because changing canonical identity changes mention and benchmark counts. The pair is intentionally absent from `data/benchmark_distinctness.csv` until a maintainer reviews the source material and decides whether these are distinct evaluations or one track named at different granularity.

### Canonical-name containment review queue (open)

The near-duplicate validator also finds the following unresolved benchmark-family relationships by whole-token name containment. A warning does not imply that the rows should be merged: each pair needs source review and either a canonical-identity change or a documented distinctness decision.

- `BrowseComp` / `BrowseComp Long Context`
- `BrowseComp` / `BrowseComp-Plus`
- `CharXiv` / `CharXiv Reasoning`
- `CursorBench` / `CursorBench 3.2`
- `GDPval-AA` / `GDPval-AA v2`
- `GeneBench` / `GeneBench Pro`
- `Healthbench` / `HealthBench Professional`
- `LiveCodeBench` / `LiveCodeBench Pro`
- `OSWorld` / `OSWorld-Verified`
- `OSWorld` / `OSWorld 2.0`
- `OfficeQA` / `OfficeQA Pro`
- `Rakuten-SWE-Bench` / `SWE-bench`
- `SWE-Lancer` / `SWE-Lancer IC Diamond`
- `SWE-bench` / `SWE-bench Multilingual`
- `SWE-bench` / `SWE-bench Multimodal`
- `SWE-bench` / `SWE-bench Pro`
- `SWE-bench` / `SWE-bench verified`
- `SimpleQA` / `SimpleQA Verified`
- `Terminal-Bench Hard` / `Terminal-bench`

### Combined family labels versus standalone versions (reviewed)

Some historical release pages present one joint chart label, such as `MMLU / MMLU-Pro` or `MMMU / MMMU Pro`. Those exact joint surface forms remain family-level canonical rows because the extraction does not support assigning the displayed result to only one version. Standalone `MMMU Pro` and `MMMU-Pro` mentions now resolve to `benchmark_mmmu_pro`, which is distinct from the joint family row. Unused aliases that previously mapped standalone MMLU or MMMU versions into combined family rows were removed so future standalone labels fail validation until explicitly canonicalized.

## Open Caveats

The main known caveats are represented directly in `benchmarks.csv` review statuses and the generated facet rows:

- `MCP-Atlas`: confirm alias identity with `Scale MCP-Atlas`.
- `Humanity's Last Exam`: confirm whether canonical display name should remain `HLE (Humanity's Last Exam)`.
- `FACTS Benchmark suite`: decide whether to split into subbenchmark rows.
- `BioPipelineBench`: wait for public benchmark documentation or create a fuller BenchmarkCard from provider material.
- `Firefox` / `Firefox 147 exploit evaluation`: decide whether the two canonical rows identify one Mozilla evaluation track.
- Canonical-name containment pairs listed above: review whether each pair is one identity, related but distinct variants, or unrelated despite the shared tokens.
