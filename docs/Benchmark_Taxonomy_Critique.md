# Critique of Benchmark Taxonomy for Academic Analysis

 This document provides a detailed critique of the current benchmark categorization strategy used in the project, along with concrete recommendations for improvement to support a rigorous academic analysis.

## 1. Core Structural Critique: Dimensionality Confusion

### The Issue
The current taxonomy flattens three orthogonal dimensions of evaluation into a single list of mutually exclusive categories. This creates analytical ambiguity because many benchmarks inherently belong to multiple dimensions simultaneously.

**The Three Hidden Dimensions:**
1.  **Domain (Subject Matter)**: What field of knowledge is being tested?
    *   *Examples:* Math, Coding, Law, Medicine, General Knowledge.
2.  **Modality (Input/Output)**: What form does the data take?
    *   *Examples:* Text-only, Multimodal (Image/Video/Audio), Long Context.
3.  **Capability/Mode (System Behavior)**: How must the system behave to solve the task?
    *   *Examples:* Static QA (Knowledge), Reasoning (Multi-step logic), Agentic (Environment interaction), Constraint Satisfaction (Instruction following).

### Why This Matters for Interpretation
Under the current flat structure, a benchmark like **SWE-bench** is classified as **Agent**. However, it is fundamentally also a **Coding** benchmark. By prioritizing "Agent" over "Coding" in the `Main Category` logic, the analysis might inadvertently suggest that "Coding benchmarks are disappearing," when in reality, coding benchmarks are simply evolving into agentic forms.

Similarly, **GPQA** (Graduate-Level Google-Proof Q&A) is classified as **Reasoning**, while **MMLU** is classified as **Knowledge**. Both are multiple-choice QA benchmarks. The distinction relies on a qualitative assessment of "difficulty" or "derivability," which can be subjective without a rigorous definition.

## 2. Recommendations for "Main Category" Definition

To maintain a single "Main Category" for visualization while ensuring academic rigor, we must formalize the definition of this category.

### Proposed Definition: "Primary Bottleneck"
Define the `Main Category` as the **primary capability bottleneck** that the benchmark is designed to stress-test.

| Category | Proposed Definition (Primary Bottleneck) | Justification for Academic Context |
| :--- | :--- | :--- |
| **Knowledge** | The bottleneck is **information retrieval and storage**. Success depends on knowing facts (e.g., MMLU, Jeopardy). | Distinguishes "knowing" from "solving". |
| **Reasoning** | The bottleneck is **multi-step logical derivation** or **inference**. Success depends on manipulating known facts to reach a conclusion (e.g., ARC-AGI, GPQA). | Crucial for separating "smart" models from "knowledgeable" ones. |
| **Math/Coding** | The bottleneck is **formal language manipulation** and **symbolic logic**. Success depends on strict syntax and execution correctness. | These domains require a distinct type of precision (execution) essentially different from natural language. |
| **Agent** | The bottleneck is **autonomy in an environment**. Success depends on error correction, tool use, and multi-turn state management (e.g., SWE-bench, OSWorld). | Represents a shift from "Passive" to "Active" systems. |
| **Multimodal** | The bottleneck is **cross-modal understanding**. Success depends on bridging the gap between pixel/audio data and semantic text (e.g., MMMU, Video-MME). | A distinct architectural capability (Vision Encoder interactions). |
| **Long Context** | The bottleneck is **information processing over scale**. Success depends on retrieval accuracy over massive windows (e.g., NIAH). | Tests the "Attention span" architecture directly. |
| **Safety** | The bottleneck is **alignment and refusal**. Success depends on *not* doing something or doing it safely (e.g., Jailbreak Eval). | Represents the "brake" system rather than the "engine". |
| **Instruction** | **RENAME to: Constraint Satisfaction**. The bottleneck is **adherence to specific formatting/structural rules**. (e.g., IFEval). | "Instruction" is too vague. "Constraint Satisfaction" is a measurable capability. |

## 3. Specific Category Refinements

### A. Rename "Instruction" to "Constraint Satisfaction" or "Robustness"
*   **Critique:** "Instruction Following" is now a baseline capability for all models. It is no longer a differentiating factor.
*   **Recommendation:** Use **Constraint Satisfaction**. Benchmarks like **IFEval** or **COLLIE** don't just ask for an answer; they ask for an answer *in a specific JSON format*, *without using letter 'e'*, etc. This tests control and steerability, not just "following orders."

### B. Rename "Safety" to "Safety & Alignment"
*   **Critique:** "Safety" can be narrow (e.g., just hate speech).
*   **Recommendation:** **Safety & Alignment** covers a broader range, including bias detection, refusal behavior (refusing unsafe prompts), and jailbreak robustness.

### C. Handle "Long Context" Carefully
*   **Critique:** Long Context is a *modality* of input (length), not necessarily a *task*.
*   **Recommendation:** Keep it, but strictly for benchmarks where the *length* is the primary difficulty (e.g., Needle In A Haystack). If a benchmark is just "Reasoning but with a long prompt," it should probably remain in purely Long Context only if the reasoning is trivial without the length.

## 4. Analytical Framework for the Paper

For your paper, I recommend presenting the data not just as a flat pie chart, but using a hierarchical framework:

### Layer 1: The "What" (Domain)
*   *Is this General, Math, Coding, or Specialized (Law/Bio)?*
*   (This allows you to track if models are becoming "specialists".)

### Layer 2: The "How" (Capability Mode)
*   **Static/Passive:** The model receives a query and outputs an answer one-shot (e.g., MMLU, GSM8K).
*   **Interactive/Agentic:** The model enters a loop of Action -> Observation -> Action (e.g., SWE-bench, WebVoyager).
*   (This is the most important trend to highlight: the shift from Static to Agentic.)

### Layer 3: The "Input" (Modality)
*   Text, Vision, Audio, Long-Context.

## 5. Review of Edge Cases in Current Data

*   **GPQA**: Currently **Reasoning**.
    *   *Verdict:* **Keep as Reasoning.** While it is "Questions," the answers require PhD-level derivation that cannot simply be looked up. It tests inference, not just memory.
*   **MMLU**: Currently **Knowledge**.
    *   *Verdict:* **Keep as Knowledge.** Most questions can be answered by knowing the fact.
*   **Math vs. Reasoning**:
    *   *Critique:* Math is a subset of Reasoning.
    *   *Verdict:* Keep **Math** separate. Math requires specific symbol manipulation and often calculation, which is a distinct failure mode for LLMs compared to linguistic reasoning.

## 6. Summary for the Paper
"We propose a taxonomy based on the **Primary Evaluation Bottleneck**. This approach avoids the ambiguity of multi-label benchmarks by focusing on the specific capability the benchmark was introduced to demonstrate. We observe a clear trend: the frontier of evaluation is moving from **Static Knowledge (Information Bottleneck)** to **Agentic Execution (Autonomy Bottleneck)**."
