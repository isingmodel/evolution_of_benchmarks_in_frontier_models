# Benchmark Taxonomy Critique v2.0: From Categorization to Topology

This document is an updated critique and proposal for the benchmark taxonomy. It builds upon the initial critique by addressing the practical conflicts observed in the `README.md` dataset (e.g., the disappearance of "Coding" benchmarks into "Agent" categories) and proposes a **Hierarchical Topology** for academic analysis.

## 1. The Core Conflict: Capability vs. Domain

The previous critique correctly identified the "Dimensionality Confusion." However, simply prioritizing "Primary Bottleneck" creates a new problem: **Domain Erasure**.

* **Observation:** In `README.md`, benchmarks like *SWE-bench* and *Natural2Code* are prioritized as **Agent**.
* **The Problem:** By classifying them solely as "Agent," we lose the visibility of the "Coding" domain. An analysis might falsely conclude that "Coding benchmarks are declining," when in reality, coding is simply becoming the *medium* for agentic tasks.
* **Refinement:** We must distinguish between the **Task Format (Mode)** and the **Task Domain (Subject)**.

## 2. Revised Taxonomy Strategy: The "Sunburst" Model

Instead of a flat list, we propose a 2-layer hierarchical taxonomy. This allows for flat categorization (for simple charts) while retaining depth for academic rigor.

### Layer 1: The Mode (The "How")
*Defines the interaction model and the primary architectural capability being tested.*

1.  **Agentic (Autonomy):** Requires multi-step execution, environment interaction (tools, browsers, terminals), and error correction loop.
    * *Markers:* `SWE-bench`, `OSWorld`, `WebVoyager`, `Computer Use`.
2.  **Generative Reasoning (Chain-of-Thought):** Requires multi-step logical derivation to reach a conclusion, but typically in a static "Prompt -> Response" format (even if internally complex).
    * *Markers:* `GPQA`, `FrontierMath`, `ARC-AGI`.
3.  **Knowledge Retrieval (Memory):** Success depends primarily on recalling facts or crystallized intelligence.
    * *Markers:* `MMLU`, `SimpleQA`, `Jeopardy`.
4.  **Constraint Satisfaction (Control):** Success depends on adhering to strict formatting, structural, or negative constraints (refusal).
    * *Markers:* `IFEval`, `Jailbreak Eval`, `COLLIE`.
5.  **Multimodal Perception (Sensory):** The primary difficulty is bridging non-text modalities.
    * *Markers:* `MMMU`, `Video-MME`, `Gemini 1.5 Pro Vision`.

### Layer 2: The Domain (The "What")
*Defines the subject matter expertise required.*

* **STEM/Math:** Symbolic logic, calculation (`MATH`, `GSM8K`).
* **Coding/Engineering:** Software development, debugging (`HumanEval`, `LiveCodeBench`).
* **General/Commonsense:** Broad world knowledge.
* **Specialized (Law/Bio/Finance):** High-expertise verticals (`BigLaw`, `BioPipeline`).

---

## 3. Specific Re-Categorization Logic for `README.md`

Based on the `README.md` dataset, here is how specific controversial benchmarks should be handled to ensure the "Evolution Graph" tells the correct story.

### A. The "Coding" to "Agent" Pipeline
* **Critique:** *SWE-bench* is currently **Agent**.
* **Recommendation:** Keep as **Agent** in the main view, but strictly tag as **Domain: Coding**.
* **Analytical Insight:** "The field has moved from *generating code snippets* (HumanEval - Coding) to *acting as a software engineer* (SWE-bench - Agent)."

### B. The "Instruction" to "Constraint" Shift
* **Critique:** *IFEval* and *COLLIE* are classified as Instruction.
* **Recommendation:** Rename category to **Constraint Satisfaction**.
* **Rationale:** Modern models act as "systems." The ability to output valid JSON or avoid specific words is a system control capability, distinct from chat.

### C. The "Math" vs. "Reasoning" Boundary
* **Critique:** *AIME* and *FrontierMath* are often swapped between Math and Reasoning.
* **Recommendation:**
    * If the problem is purely symbolic/calculation: **Math**.
    * If the problem requires novel insight or logic puzzles (like ARC-AGI): **Reasoning**.
    * *Decision:* **FrontierMath** should be **Reasoning** (due to complexity exceeding standard math), while **GSM8K** is **Math**.

### D. Long Context as a Feature, Not a Category
* **Critique:** *Needle In A Haystack (NIAH)* is **Long Context**.
* **Recommendation:** Keep **Long Context** only for "Retrieve" tasks.
* **Edge Case:** If a benchmark is "Reasoning over long documents" (e.g., *Gemini 1.5 Tech Report benchmarks*), classify as **Long Context** only if the *length* is the primary failure mode. If it's just a long prompt but the reasoning is hard, it's Reasoning.

---

## 4. Proposed "Main Category" Priority Logic (v2)

For the purpose of the single-label pie chart in your visualization, use this refined priority logic. This ensures that the most "advanced" capability is always highlighted.

1.  **Agent:** Does it use tools or loops? (Highest complexity)
    * *(Captures SWE-bench, WebVoyager)*
2.  **Multimodal:** Does it see/hear?
    * *(Captures MMMU, Video-MME)*
3.  **Long Context:** Does it require >100k context?
    * *(Captures NIAH, RULER)*
4.  **Reasoning:** Is it a hard puzzle/logic task?
    * *(Captures GPQA, ARC-AGI, FrontierMath)*
5.  **Math/Coding:** Is it specialized symbolic execution?
    * *(Captures GSM8K, HumanEval - *Only if not Agentic*)*
6.  **Constraint/Safety:** Is it about format/safety?
    * *(Captures IFEval, Jailbreak)*
7.  **Knowledge:** Is it factual QA?
    * *(Captures MMLU, SimpleQA)*

**Key Change from v1:** "Reasoning" is moved *above* simple Math/Coding to reflect that modern "Reasoning" models (o1, o3) are a higher-order evolution than basic Math/Code solvers.

---

## 5. Summary for Academic Paper

"The evolution of AI evaluation has transitioned through three distinct epochs:
1.  **The Retention Epoch (2020-2022):** Focused on **Knowledge** (MMLU) and basic syntax (HumanEval).
2.  **The Reasoning Epoch (2023-2024):** Focused on **Chain-of-Thought** and complex logic (GPQA, MATH).
3.  **The Agency Epoch (2025-Present):** Focused on **Autonomous Execution** (Agent) and **Active Perception** (Multimodal).

Our taxonomy reflects this shift by categorizing benchmarks based on their **Primary Failure Mode**."