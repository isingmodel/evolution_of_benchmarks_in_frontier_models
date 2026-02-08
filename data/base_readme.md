# Benchmark Evolution in Frontier Models
**Abstract**
This repository provides a comprehensive analysis of the evolution of benchmarks used by frontier AI models. By tracking benchmarks cited in technical reports from major AI providers (OpenAI, Google, Anthropic, etc.), we visualize the shifting landscape of AI evaluation. The project offers data-driven insights into the growth of benchmark categories, model capabilities, and the taxonomy of evaluation metrics.

This repository tracks the benchmarks used by frontier AI models (OpenAI, Google, etc.) over time.

## Evolution Graph
![Benchmark Evolution](assets/benchmark_evolution.png)

## Benchmark Landscape Growth
The following graph shows the evolution of the benchmark landscape composition over time (rolling 6-month window).
![Benchmark Growth](assets/benchmark_growth.png)

## Analysis & Observations

### Case Study: Gemini 1.5
When Gemini 1.5 was released in February 2024, GPT-4 was the market leader. Lacking significant performance advantages in other areas compared to GPT-4, Google focused heavily on promoting its **Long Context** capabilities. While competitors like GPT and Llama were limited to tens of thousands of tokens, Gemini 1.5 boasted support for hundreds of thousands, making Long Context the highlight of its release page.

### Benchmark Analysis Methodology
This analysis focuses on benchmarks featured prominently on the models' main release pages, rather than those buried in technical reports, to identify what capabilities providers seemingly prioritize for marketing.

### Evolution of Benchmarks
*   **Early GPT (3, 3.5)**: Focused on simple knowledge-based QA benchmarks (e.g., Biology Olympiad), reflecting the limitations of early LLMs.
*   **Expansion**: The landscape shifted towards **Multimodal** and **Coding** benchmarks as model capabilities matured.
*   **Current Trend**: **Agentic** benchmarks are rapidly increasing. We anticipate a surge in agent-related benchmarks for the upcoming frontier models in the first half of this year.

### The Battle for Hegemony
Observations from the model cards reveal a strategic battle:
*   **Google's Catch-up**: As a fast follower in the LLM product space, Google's early Gemini releases heavily adopted benchmarks established by OpenAI.
*   **OpenAI's Lead**: OpenAI often created new benchmarks to define the direction of the field. Google followed suit, and the landscape has now become highly competitive with comparable performance metrics.

## Models Data
The following table lists the models and their associated benchmarks.

{{MODELS_TABLE}}

## Benchmark Taxonomy
Classification of various benchmarks by category.

{{TAXONOMY_TABLE}}

## Categorization Logic
To simplify visualizations, each benchmark is assigned a single **Main Category**. When a benchmark maps to multiple categories, the following priority logic is applied:
1. **Agent**: Tasks requiring environment interaction or multi-step tool use.
2. **Multimodal**: Tasks involving vision, audio, or video.
3. **Math/Coding**: Specialized technical skills.
4. **Long Context**: Retrieval/reasoning over long sequences.
5. **Safety/Instruction**: Alignment, safety, or formatting constraints.
6. **Reasoning**: General high-level reasoning.
7. **Knowledge**: General factual Q&A.

## Auto-Update
To keep this repository up-to-date, run:
```bash
python scripts/generate_visuals.py
python scripts/generate_trend_graph.py
python scripts/update_readme.py
```
