# Benchmark Classification Prompt (Single Benchmark, Taxonomy v3)

Use this prompt when classifying one benchmark at a time with input:
- `benchmark_name`
- `reference_link`
- optional `provider`
- optional `model_name`
- optional `release_page_url`
- optional `release_page_context`

This prompt follows the [v3 benchmark classification methodology](benchmark_classification_methodology_v3.md). It is intentionally multi-facet; `scripts/classify_benchmarks_gemini.py` writes reviewable v3 candidate outputs by default instead of overwriting canonical facet data.

```text
You are classifying one AI benchmark using Benchmark Classification Methodology v3.

Input:
- benchmark_name: <BENCHMARK_NAME>
- reference_link: <REFERENCE_LINK>
- provider: <OPTIONAL_PROVIDER>
- model_name: <OPTIONAL_MODEL_NAME>
- release_page_url: <OPTIONAL_RELEASE_PAGE_URL>
- release_page_context: <OPTIONAL_TEXT_AROUND_THE_BENCHMARK_MENTION>

Task:
1) Classify the benchmark with multiple documented facets. Do not force a single exclusive label.
2) Distinguish benchmark identity from release-page framing when provider context is available.
3) Derive one headline_projection only after assigning facets.
4) Return exactly one JSON object only.
5) No markdown, no code fences, no extra text.

Output JSON schema:
{
  "benchmark_name": "string",
  "reference_link": "string",
  "benchmark_construct_claim": ["labels from methodology v3 section 5.1"],
  "provider_construct_claim": ["labels from methodology v3 section 5.1, or [] if unavailable"],
  "facets": {
    "construct_claim": [
      {"label": "string", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "task_mechanism": [
      {"label": "label from methodology v3 section 5.2", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "domain": [
      {"label": "label from methodology v3 section 5.3", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "modality": [
      {"label": "label from methodology v3 section 5.4", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "interaction_pattern": [
      {"label": "label from methodology v3 section 5.5", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "metric_type": [
      {"label": "label from methodology v3 section 5.6, or unknown", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "context_pressure": [
      {"label": "label from methodology v3 section 5.7", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ],
    "benchmark_lifecycle_risk": [
      {"label": "label from methodology v3 section 5.8", "label_weight": 0.0, "classification_confidence": 0.0, "evidence": "short source note"}
    ]
  },
  "headline_projection": "Agentic / Environment Interaction | Multimodal / Perceptual Understanding | Constraint / Safety / Control | Generative or Deliberative Reasoning | Knowledge / Retrieval | Long Context Projection | needs_review",
  "projection_rationale": "one concise sentence explaining why this projection was chosen",
  "review_status": "accepted | needs_review | disputed | deprecated",
  "rationale": "one concise sentence summarizing the classification"
}

Rules:
- Evidence before label: use the reference link and release-page context when available. If evidence is weak, lower confidence and set review_status to needs_review.
- Projection is not identity: headline_projection is only for charts. Preserve all relevant facets even when one headline category is selected.
- Separate confidence from importance: classification_confidence reflects evidence quality, not how prominently the benchmark appears on a release page.
- Weights within each facet axis should sum to approximately 1.0 when multiple labels are present.
- Long context is a facet. Use Long Context Projection only when context length is the primary release-page emphasis or benchmark bottleneck.
- If provider framing differs from the benchmark's original purpose, preserve both benchmark_construct_claim and provider_construct_claim.

Projection priority when a single headline category is required:
1) Long Context Projection, only when context length is the primary benchmark bottleneck
2) Agentic / Environment Interaction
3) Multimodal / Perceptual Understanding
4) Constraint / Safety / Control
5) Generative or Deliberative Reasoning
6) Knowledge / Retrieval

Now produce one JSON object for the given input.
```
