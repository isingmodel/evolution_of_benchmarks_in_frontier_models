import argparse
import re
from pathlib import Path

import pandas as pd

from mention_prominence import apply_prominence_overrides, read_prominence_overrides
from taxonomy_utils import MENTION_PROMINENCE_DEFAULT, MENTION_PROMINENCE_WEIGHTS


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


PREFERRED_CANONICAL_NAMES = {
    "swe-lancer": "SWE-Lancer",
}


PROMINENCE_DEFAULT = MENTION_PROMINENCE_DEFAULT
MENTION_WEIGHT_DEFAULT = MENTION_PROMINENCE_WEIGHTS[PROMINENCE_DEFAULT]
RULE_SEED_CONFIDENCE = 0.6
LEGACY_SEED_CONFIDENCE = 0.7
REVIEW_NEEDED_CONFIDENCE = 0.55


MANUAL_FACET_OVERRIDES = {
    "TAU-2 bench": [
        ("headline_task_mode", "Agentic", 1.0, 0.93, "accepted", "TAU-2 is a dual-control conversational agent benchmark with shared tool-mediated state."),
        ("construct_claim", "agentic_task_completion", 0.7, 0.93, "accepted", "The benchmark tests whether an agent can complete tasks while coordinating with an active simulated user."),
        ("construct_claim", "tool_use", 0.3, 0.93, "accepted", "Both agent and user can use tools in the shared environment."),
        ("task_mechanism", "tool_calling", 1.0, 0.93, "accepted", "Task progress depends on tool-mediated changes to the environment state."),
        ("domain", "Other Specialized", 1.0, 0.93, "accepted", "The audited source describes a telecom/customer-support style domain rather than coding or autonomous driving."),
        ("modality", "text", 0.7, 0.93, "accepted", "Interaction is primarily conversational text."),
        ("modality", "tool_api", 0.3, 0.93, "accepted", "The environment exposes tools to agent and simulated user."),
        ("interaction_pattern", "environment_interaction", 0.5, 0.93, "accepted", "Agent actions alter a shared environment state."),
        ("interaction_pattern", "multi_turn_dialogue", 0.3, 0.93, "accepted", "The task is a conversational agent-user interaction."),
        ("interaction_pattern", "human_in_the_loop", 0.2, 0.93, "accepted", "The simulated user actively participates in the task state."),
        ("metric_type", "completion_rate", 0.6, 0.93, "accepted", "The benchmark reports task success/pass style outcomes."),
        ("metric_type", "accuracy", 0.4, 0.93, "accepted", "World-state correctness is used to determine success."),
        ("context_pressure", "medium", 1.0, 0.93, "accepted", "The source emphasizes coordination and tool use more than context length."),
        ("benchmark_lifecycle_risk", "version_instability", 0.5, 0.93, "accepted", "The benchmark family is evolving across tau-bench variants."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.5, 0.93, "accepted", "Dual-control simulation is an explicit proxy for real support workflows."),
    ],
    "Vending-Bench 2": [
        ("headline_task_mode", "Agentic", 1.0, 0.94, "accepted", "Vending-Bench 2 evaluates long-horizon autonomous business operation."),
        ("construct_claim", "agentic_task_completion", 1.0, 0.94, "accepted", "The benchmark scores agents by success in a simulated vending-machine business."),
        ("task_mechanism", "tool_calling", 1.0, 0.94, "accepted", "Agents operate through business-management tools and stateful actions."),
        ("domain", "Other Specialized", 1.0, 0.94, "accepted", "The task domain is simulated small-business operations."),
        ("modality", "text", 0.4, 0.94, "accepted", "The simulation is mediated through textual instructions and state."),
        ("modality", "tool_api", 0.6, 0.94, "accepted", "Tool use is central to ordering, pricing, and operational decisions."),
        ("interaction_pattern", "environment_interaction", 0.55, 0.94, "accepted", "Agent choices change the simulated business environment."),
        ("interaction_pattern", "multi_step_planning", 0.45, 0.94, "accepted", "Performance depends on sustained planning over a year-long simulation."),
        ("metric_type", "composite_score", 1.0, 0.94, "accepted", "The benchmark summarizes business outcomes with final performance scoring."),
        ("context_pressure", "long_context_supporting", 1.0, 0.94, "accepted", "Long-horizon state tracking supports the task but is not the only construct."),
        ("benchmark_lifecycle_risk", "version_instability", 0.34, 0.94, "accepted", "The benchmark has active variants such as Vending-Bench Arena."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.33, 0.94, "accepted", "The simulation is a proxy for real business operation."),
        ("benchmark_lifecycle_risk", "distribution_shift_risk", 0.33, 0.94, "accepted", "Supplier and market dynamics may change across benchmark versions."),
    ],
    "GDPval": [
        ("headline_task_mode", "Generative Reasoning", 1.0, 0.92, "accepted", "GDPval asks models to produce realistic professional deliverables."),
        ("construct_claim", "domain_expertise", 1.0, 0.92, "accepted", "Tasks span professional occupations and require domain-specific work products."),
        ("task_mechanism", "free_form_generation", 1.0, 0.92, "accepted", "The benchmark compares generated deliverables against expert work."),
        ("domain", "Other Specialized", 0.4, 0.92, "accepted", "GDPval spans many professional sectors beyond the named v2 buckets."),
        ("domain", "Coding/Engineering", 0.2, 0.92, "accepted", "OpenAI lists software developers and mechanical engineers among included occupations."),
        ("domain", "Law", 0.15, 0.92, "accepted", "OpenAI lists lawyers among included occupations."),
        ("domain", "Bio/Medicine", 0.15, 0.92, "accepted", "OpenAI lists registered nurses among included occupations."),
        ("domain", "Finance", 0.1, 0.92, "accepted", "Economically significant sectors include finance-adjacent professional work."),
        ("modality", "text", 0.55, 0.92, "accepted", "Most deliverables are text or document-centered work products."),
        ("modality", "document_layout", 0.25, 0.92, "accepted", "Professional deliverables may require document structure and formatting."),
        ("modality", "code", 0.1, 0.92, "accepted", "Some occupations include software or engineering deliverables."),
        ("modality", "multimodal_mixed", 0.1, 0.92, "accepted", "The task suite spans heterogeneous professional artifacts."),
        ("interaction_pattern", "static_prompt_response", 1.0, 0.92, "accepted", "GDPval is framed as deliverable generation rather than environment interaction."),
        ("metric_type", "human_preference", 0.6, 0.92, "accepted", "Expert comparison is central to scoring."),
        ("metric_type", "rubric_score", 0.4, 0.92, "accepted", "Evaluation depends on professional quality judgments."),
        ("context_pressure", "long_context_supporting", 1.0, 0.92, "accepted", "Professional deliverables can require substantial context, but context length is not the primary construct."),
        ("benchmark_lifecycle_risk", "provider_created_benchmark", 0.4, 0.92, "accepted", "GDPval is introduced by OpenAI."),
        ("benchmark_lifecycle_risk", "private_or_opaque_eval", 0.3, 0.92, "accepted", "Full evaluation details and items are not fully public in the legacy data."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.3, 0.92, "accepted", "Professional work quality is difficult to reduce to one benchmark score."),
    ],
    "GDPval-AA": [
        ("headline_task_mode", "Agentic", 1.0, 0.88, "accepted", "Artificial Analysis runs GDPval-AA through an agentic task-completion harness."),
        ("construct_claim", "agentic_task_completion", 0.5, 0.88, "accepted", "The methodology describes agentic completion with file outputs."),
        ("construct_claim", "domain_expertise", 0.5, 0.88, "accepted", "The tasks remain real-world professional knowledge-work tasks."),
        ("task_mechanism", "tool_calling", 0.5, 0.88, "accepted", "The benchmark allows tool usage in the evaluation harness."),
        ("task_mechanism", "free_form_generation", 0.5, 0.88, "accepted", "The agent must produce professional file or deliverable outputs."),
        ("domain", "Other Specialized", 0.4, 0.88, "accepted", "GDPval-AA covers mixed professional domains."),
        ("domain", "Coding/Engineering", 0.2, 0.88, "accepted", "The source categorizes it as real-world knowledge work with technical occupations included."),
        ("domain", "Law", 0.15, 0.88, "accepted", "The underlying GDPval-style task set includes legal work."),
        ("domain", "Bio/Medicine", 0.15, 0.88, "accepted", "The underlying GDPval-style task set includes healthcare work."),
        ("domain", "Finance", 0.1, 0.88, "accepted", "The suite includes economically significant professional sectors."),
        ("modality", "text", 0.35, 0.88, "accepted", "Task inputs and final answers are primarily language-mediated."),
        ("modality", "document_layout", 0.25, 0.88, "accepted", "File outputs can require professional document structure."),
        ("modality", "code", 0.15, 0.88, "accepted", "Some tasks may require technical or computational artifacts."),
        ("modality", "tool_api", 0.15, 0.88, "accepted", "The harness exposes tools to the agent."),
        ("modality", "multimodal_mixed", 0.1, 0.88, "accepted", "The task suite spans heterogeneous work products."),
        ("interaction_pattern", "environment_interaction", 0.4, 0.88, "accepted", "The agent operates in an evaluation environment to complete tasks."),
        ("interaction_pattern", "terminal_or_codebase_interaction", 0.3, 0.88, "accepted", "The harness can include shell or file interactions."),
        ("interaction_pattern", "single_turn_tool_use", 0.3, 0.88, "accepted", "Tool calls are part of the task-completion pathway."),
        ("metric_type", "win_rate", 0.5, 0.88, "accepted", "Artificial Analysis reports pairwise/Elo-style scoring."),
        ("metric_type", "human_preference", 0.5, 0.88, "accepted", "The score is based on pairwise quality comparison of outputs."),
        ("context_pressure", "long_context_supporting", 1.0, 0.88, "accepted", "Professional task completion can require substantial context but is not only a context test."),
        ("benchmark_lifecycle_risk", "private_or_opaque_eval", 0.35, 0.88, "accepted", "The full evaluation implementation is not fully represented in local data."),
        ("benchmark_lifecycle_risk", "unclear_metric", 0.2, 0.88, "accepted", "Pairwise/Elo aggregation requires careful interpretation."),
        ("benchmark_lifecycle_risk", "version_instability", 0.2, 0.88, "accepted", "Artificial Analysis evaluation methodology evolves over time."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.25, 0.88, "accepted", "Real-world professional work is difficult to compress into a single score."),
    ],
    "BrowseComp Long Context": [
        ("headline_task_mode", "Knowledge Retrieval", 1.0, 0.9, "accepted", "The long-context variant converts browsing questions into in-context retrieval."),
        ("construct_claim", "long_context_retrieval", 1.0, 0.9, "accepted", "The dataset card states that it retrieves relevant information from noisy context."),
        ("task_mechanism", "long_context_retrieval", 1.0, 0.9, "accepted", "The task is to answer from provided long-context URL content."),
        ("domain", "General/Commonsense", 1.0, 0.9, "accepted", "Questions are broad BrowseComp-style information queries."),
        ("modality", "text", 1.0, 0.9, "accepted", "The Hugging Face dataset card lists text modality."),
        ("interaction_pattern", "static_prompt_response", 1.0, 0.9, "accepted", "The converted task is answered from provided context rather than live browsing."),
        ("metric_type", "exact_match", 0.5, 0.9, "accepted", "Question-answering tasks can be judged by answer match."),
        ("metric_type", "accuracy", 0.5, 0.9, "accepted", "Accuracy summarizes correct retrieval and answer synthesis."),
        ("context_pressure", "long_context_primary", 1.0, 0.9, "accepted", "Long context is the primary benchmark bottleneck."),
        ("benchmark_lifecycle_risk", "contamination_risk", 0.5, 0.9, "accepted", "The dataset card includes canary warnings about benchmark data exposure."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.5, 0.9, "accepted", "Converted browsing tasks may not measure live web-agent behavior."),
    ],
    "FACTS Benchmark suite": [
        ("headline_task_mode", "Knowledge Retrieval", 1.0, 0.86, "needs_review", "FACTS is a factuality suite; this is a projection over several subbenchmarks."),
        ("construct_claim", "factual_knowledge", 1.0, 0.86, "needs_review", "The suite evaluates factual accuracy across several settings."),
        ("task_mechanism", "short_answer_qa", 0.3, 0.86, "needs_review", "The parametric component uses factoid question answering."),
        ("task_mechanism", "visual_question_answering", 0.25, 0.86, "needs_review", "The multimodal component asks image-grounded factual questions."),
        ("task_mechanism", "browser_navigation", 0.25, 0.86, "needs_review", "The search component evaluates use of search as a tool."),
        ("task_mechanism", "long_context_synthesis", 0.2, 0.86, "needs_review", "The grounding component tests answers grounded in provided context."),
        ("domain", "General/Commonsense", 0.7, 0.86, "needs_review", "Most factuality tasks cover broad general knowledge."),
        ("domain", "Visual/Document", 0.3, 0.86, "needs_review", "The suite includes a multimodal image-based component."),
        ("modality", "text", 0.5, 0.86, "needs_review", "Textual factuality tasks are central to the suite."),
        ("modality", "image", 0.25, 0.86, "needs_review", "The multimodal benchmark uses image inputs."),
        ("modality", "tool_api", 0.15, 0.86, "needs_review", "The search benchmark exposes search as a tool."),
        ("modality", "multimodal_mixed", 0.1, 0.86, "needs_review", "The suite aggregates multiple input modalities."),
        ("interaction_pattern", "static_prompt_response", 0.7, 0.86, "needs_review", "Parametric, grounding, and multimodal components are primarily prompt-response tasks."),
        ("interaction_pattern", "single_turn_tool_use", 0.3, 0.86, "needs_review", "The search component introduces tool use."),
        ("metric_type", "accuracy", 0.5, 0.86, "needs_review", "FACTS score is based on accuracy across public and private sets."),
        ("metric_type", "composite_score", 0.3, 0.86, "needs_review", "The suite averages multiple benchmark components."),
        ("metric_type", "LLM_judge", 0.2, 0.86, "needs_review", "Factuality scoring can involve automated judging; confirm per component before acceptance."),
        ("context_pressure", "long_context_supporting", 1.0, 0.86, "needs_review", "Grounding and search tasks can require synthesizing supplied context."),
        ("benchmark_lifecycle_risk", "private_or_opaque_eval", 0.25, 0.86, "needs_review", "The suite includes private held-out sets."),
        ("benchmark_lifecycle_risk", "unclear_metric", 0.25, 0.86, "needs_review", "Metric details differ by component and should be carded separately."),
        ("benchmark_lifecycle_risk", "version_instability", 0.25, 0.86, "needs_review", "The suite extends and updates earlier FACTS benchmarks."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.25, 0.86, "needs_review", "Composite factuality scores can hide subtask differences."),
    ],
    "BioPipelineBench": [
        ("headline_task_mode", "Agentic", 1.0, 0.72, "needs_review", "Anthropic describes bash/code/package-manager access for computational-biology workflows."),
        ("construct_claim", "domain_expertise", 0.5, 0.72, "needs_review", "The benchmark requires specialized bioinformatics knowledge."),
        ("construct_claim", "tool_use", 0.5, 0.72, "needs_review", "The system card describes access to bash, code execution, and package managers."),
        ("task_mechanism", "tool_calling", 0.4, 0.72, "needs_review", "Workflow execution depends on external tools."),
        ("task_mechanism", "code_generation", 0.3, 0.72, "needs_review", "Bioinformatics workflows can require scripts and code."),
        ("task_mechanism", "terminal_operation", 0.3, 0.72, "needs_review", "The benchmark is run with bash access."),
        ("domain", "Bio/Medicine", 1.0, 0.72, "needs_review", "The benchmark covers bioinformatics workflows."),
        ("modality", "text", 0.3, 0.72, "needs_review", "Task descriptions are language-mediated."),
        ("modality", "code", 0.4, 0.72, "needs_review", "Computational workflows involve scripts and code artifacts."),
        ("modality", "tool_api", 0.3, 0.72, "needs_review", "Package managers and execution tools are part of the environment."),
        ("interaction_pattern", "terminal_or_codebase_interaction", 0.55, 0.72, "needs_review", "The system card describes bash and code execution."),
        ("interaction_pattern", "environment_interaction", 0.45, 0.72, "needs_review", "The model executes workflows in a computational environment."),
        ("metric_type", "accuracy", 1.0, 0.72, "needs_review", "Anthropic reports a percentage score, but detailed public scoring criteria need review."),
        ("context_pressure", "medium", 1.0, 0.72, "needs_review", "The bottleneck is workflow execution and domain reasoning, not primarily long context."),
        ("benchmark_lifecycle_risk", "private_or_opaque_eval", 0.35, 0.72, "needs_review", "The benchmark appears in an Anthropic system card rather than a public benchmark card."),
        ("benchmark_lifecycle_risk", "provider_created_benchmark", 0.25, 0.72, "needs_review", "The available evidence is provider documentation."),
        ("benchmark_lifecycle_risk", "unclear_metric", 0.2, 0.72, "needs_review", "The public source gives scores but limited metric detail."),
        ("benchmark_lifecycle_risk", "construct_validity_risk", 0.2, 0.72, "needs_review", "Bioinformatics workflow execution needs benchmark-card review before strong claims."),
    ],
}


def stable_id(prefix, *parts):
    raw = " ".join(str(part) for part in parts if str(part).strip())
    slug = re.sub(r"[^a-z0-9]+", "_", raw.casefold()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not slug:
        slug = "unknown"
    return f"{prefix}_{slug}"


def normalize_name(value):
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def read_aliases(path):
    if not path.exists():
        return pd.DataFrame(columns=["alias", "benchmark_id", "match_type", "notes"])

    aliases = pd.read_csv(path).fillna("")
    required = {"alias", "benchmark_id"}
    missing = required - set(aliases.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return aliases


def read_review_queue(path):
    if not path.exists():
        return pd.DataFrame(columns=["benchmark_name", "issue_type", "priority", "reason", "suggested_action"])
    return pd.read_csv(path).fillna("")


def dedupe_taxonomy(taxonomy_df):
    preferred_by_norm = {
        normalize_name(name): preferred for name, preferred in PREFERRED_CANONICAL_NAMES.items()
    }

    rows_by_norm = {}
    for _, row in taxonomy_df.fillna("").iterrows():
        name = str(row["benchmark_name"]).strip()
        if not name:
            continue
        key = normalize_name(name)
        preferred = preferred_by_norm.get(key)
        if preferred:
            if name == preferred:
                rows_by_norm[key] = row
            elif key not in rows_by_norm:
                rows_by_norm[key] = row
            continue

        # Last row wins for normalized duplicates. The validator still reports
        # duplicate legacy rows so they can be cleaned intentionally.
        rows_by_norm[key] = row

    return pd.DataFrame(rows_by_norm.values()).reset_index(drop=True)


def build_canonical_lookup(benchmarks_df, aliases_df):
    canonical = {}
    for name in benchmarks_df["benchmark_name"]:
        name = str(name).strip()
        canonical[normalize_name(name)] = name

    name_by_id = dict(zip(benchmarks_df["benchmark_id"], benchmarks_df["benchmark_name"]))
    for _, row in aliases_df.iterrows():
        alias = str(row["alias"]).strip()
        benchmark_id = str(row["benchmark_id"]).strip()
        if not alias or not benchmark_id:
            continue
        if benchmark_id not in name_by_id:
            raise ValueError(f"Alias target {benchmark_id!r} is not in canonical benchmark table")

        key = normalize_name(alias)
        target = name_by_id[benchmark_id]
        if key in canonical and canonical[key] != target:
            raise ValueError(f"Alias collision for {alias!r}: {canonical[key]!r} vs {target!r}")
        canonical[key] = target

    return canonical


def resolve_benchmark(raw_name, canonical_lookup):
    key = normalize_name(raw_name)
    if key not in canonical_lookup:
        raise KeyError(f"Unresolved benchmark mention: {raw_name!r}")
    return canonical_lookup[key]


def build_review_notes(review_queue_df, canonical_lookup):
    notes = {}
    for _, row in review_queue_df.iterrows():
        raw_name = str(row.get("benchmark_name", "")).strip()
        if not raw_name:
            continue
        canonical_name = canonical_lookup.get(normalize_name(raw_name), raw_name)
        notes[canonical_name] = {
            "priority": str(row.get("priority", "")).strip(),
            "issue_type": str(row.get("issue_type", "")).strip(),
            "reason": str(row.get("reason", "")).strip(),
        }
    return notes


def split_benchmarks(value):
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text or text.casefold() == "nan":
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def manual_benchmark_status(benchmark_name):
    overrides = MANUAL_FACET_OVERRIDES.get(benchmark_name)
    if not overrides:
        return ""

    statuses = {status for _, _, _, _, status, _ in overrides}
    if statuses == {"accepted"}:
        return "accepted"
    if "disputed" in statuses:
        return "disputed"
    if "needs_review" in statuses:
        return "needs_review"
    return "legacy_seed"


def build_benchmarks(taxonomy_df):
    rows = []
    for _, row in taxonomy_df.fillna("").iterrows():
        benchmark_name = str(row["benchmark_name"]).strip()
        benchmark_id = stable_id("benchmark", benchmark_name)
        review_status = manual_benchmark_status(benchmark_name)
        if not review_status:
            review_status = "legacy_seed"
        rows.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": benchmark_name,
                "reference_link": str(row.get("reference_link", "")).strip(),
                "source_author": str(row.get("source_author", "")).strip(),
                "legacy_task_mode": str(row.get("task_mode", "")).strip(),
                "legacy_task_domain": str(row.get("task_domain", "")).strip(),
                "legacy_rationale": str(row.get("rationale", "")).strip(),
                "review_status": review_status,
            }
        )
    return pd.DataFrame(rows).sort_values("benchmark_name").reset_index(drop=True)


def apply_benchmark_review_status(benchmarks_df, review_notes):
    if not review_notes:
        return benchmarks_df

    benchmarks_df = benchmarks_df.copy()
    for index, row in benchmarks_df.iterrows():
        current_status = str(row["review_status"]).strip()
        if current_status in {"accepted", "disputed"}:
            continue

        note = review_notes.get(str(row["benchmark_name"]).strip())
        if note and note.get("priority") in {"high", "medium"}:
            benchmarks_df.at[index, "review_status"] = "needs_review"
    return benchmarks_df


def build_evidence(benchmarks_df, accessed_date):
    rows = []
    for _, row in benchmarks_df.iterrows():
        benchmark_id = row["benchmark_id"]
        rows.append(
            {
                "evidence_id": stable_id("evidence", benchmark_id, "definition"),
                "benchmark_id": benchmark_id,
                "evidence_type": "benchmark_definition",
                "title": f"Definition/source for {row['benchmark_name']}",
                "url": row["reference_link"],
                "source_date": "",
                "accessed_date": accessed_date,
                "notes": "Seeded from legacy benchmark_taxonomy_v2 reference_link.",
            }
        )
    return pd.DataFrame(rows)


def text_blob(row):
    return " ".join(
        [
            str(row.get("benchmark_name", "")),
            str(row.get("legacy_task_mode", "")),
            str(row.get("legacy_task_domain", "")),
            str(row.get("legacy_rationale", "")),
            str(row.get("source_author", "")),
        ]
    ).casefold()


def infer_domain(row):
    name = str(row["benchmark_name"]).casefold()
    legacy_domain = str(row["legacy_task_domain"]).strip()
    text = text_blob(row)

    if legacy_domain in {"General/Commonsense", "STEM/Math", "Coding/Engineering"}:
        return legacy_domain
    if any(token in name for token in ["bar exam", "biglaw", "law"]):
        return "Law"
    if any(token in name for token in ["bio", "health", "medical", "biology"]):
        return "Bio/Medicine"
    if "finance" in name:
        return "Finance"
    if any(token in name for token in ["ctf", "cyber"]):
        return "Cybersecurity"
    if any(token in name for token in ["multilingual", "polyglot"]) or "translation" in text:
        return "Multilingual"
    return "Other Specialized"


def infer_construct_claim(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])
    text = text_blob(row)

    if mode == "Agentic":
        if "browse" in name or "web" in name:
            return "web_navigation"
        if "mcp" in name or "tool" in name or "function" in text:
            return "tool_use"
        if "osworld" in name or "computer" in text or "desktop" in text:
            return "computer_use"
        return "agentic_task_completion"
    if mode == "Multimodal Perception":
        if "doc" in name or "chart" in name or "screen" in name:
            return "document_understanding"
        return "multimodal_understanding"
    if mode == "Constraint Satisfaction":
        if "jailbreak" in name or "safety" in text or "refusal" in text:
            return "safety_or_refusal"
        return "instruction_following"
    if mode == "Knowledge Retrieval":
        if "facts" in name or "factual" in text:
            return "factual_knowledge"
        return "factual_knowledge"
    if "math" in name or domain == "STEM/Math" or any(token in name for token in ["aime", "gpqa", "hmmt", "imo"]):
        return "mathematical_reasoning" if "math" in name or domain == "STEM/Math" else "scientific_reasoning"
    if domain == "Coding/Engineering":
        return "software_engineering" if any(token in name for token in ["swe", "terminal", "openrca"]) else "coding"
    if domain == "Specialized (Law/Bio/Finance)":
        return "domain_expertise"
    return "reasoning"


def infer_task_mechanism(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])
    text = text_blob(row)

    if any(token in name for token in ["swe-bench", "swe-lancer", "swe-lancer", "swe"]):
        return "repository_issue_resolution"
    if "terminal" in name:
        return "terminal_operation"
    if "browse" in name or "webvoyager" in name:
        return "browser_navigation"
    if any(token in name for token in ["mcp", "tool", "tau", "finance agent", "complexfunc", "vending"]):
        return "tool_calling"
    if "osworld" in name:
        return "computer_control_task"
    if "screen" in name:
        return "visual_grounding"
    if mode == "Constraint Satisfaction":
        return "adversarial_refusal" if "jailbreak" in name else "format_constrained_output"
    if mode == "Multimodal Perception":
        if "video" in name or "activitynet" in name or "egoschema" in name or "vatex" in name:
            return "video_question_answering"
        if "doc" in name or "chart" in name or "infographic" in name:
            return "document_parsing"
        if "fleurs" in name or "covost" in name:
            return "speech_or_audio_translation"
        return "visual_question_answering"
    if "lmarena" in name or "arena" in name:
        return "human_preference_comparison"
    if domain == "Coding/Engineering":
        if "sql" in name:
            return "sql_generation"
        if "ctf" in name or "cyber" in name:
            return "security_challenge_solving"
        return "code_generation"
    if domain == "STEM/Math" or "math" in name or any(token in name for token in ["aime", "hmmt", "imo"]):
        return "math_problem_solving"
    if mode == "Knowledge Retrieval":
        if "facts" in name:
            return "factuality_verification"
        return "short_answer_qa"
    if "mmlu" in name or "gpqa" in name or "mcqa" in name:
        return "multiple_choice_qa"
    return "free_form_generation"


def infer_modality(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])

    if "video" in name or "activitynet" in name or "egoschema" in name or "vatex" in name:
        return "video"
    if "fleurs" in name or "covost" in name:
        return "audio"
    if any(token in name for token in ["doc", "chart", "infographic", "screen"]):
        return "document_layout" if "screen" not in name else "desktop_ui"
    if mode == "Multimodal Perception" or any(token in name for token in ["mmmu", "mathvista", "vqa", "ai2d", "charxiv"]):
        return "image"
    if any(token in name for token in ["browse", "webvoyager"]):
        return "browser_ui"
    if "osworld" in name:
        return "desktop_ui"
    if any(token in name for token in ["mcp", "tool", "tau", "finance agent", "vending"]):
        return "tool_api"
    if domain == "Coding/Engineering" or any(token in name for token in ["code", "swe", "terminal"]):
        return "code"
    return "text"


def infer_interaction_pattern(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])

    if "browse" in name or "webvoyager" in name:
        return "browser_or_web_interaction"
    if "terminal" in name or "swe" in name or "cybergym" in name:
        return "terminal_or_codebase_interaction"
    if "osworld" in name or "screen" in name:
        return "computer_control"
    if any(token in name for token in ["mcp", "tool", "tau", "finance agent", "vending", "complexfunc"]):
        return "single_turn_tool_use"
    if mode == "Agentic":
        return "environment_interaction"
    if "multi-if" in name or "mrcr" in name:
        return "multi_turn_dialogue"
    return "static_prompt_response"


def infer_metric_type(row):
    name = str(row["benchmark_name"]).casefold()
    mode = str(row["legacy_task_mode"])
    domain = str(row["legacy_task_domain"])

    if "lmarena" in name or "arena" in name:
        return "win_rate"
    if any(token in name for token in ["swe", "humaneval", "livecode", "aider", "terminal"]):
        return "unit_test_pass_rate"
    if mode == "Agentic":
        return "completion_rate"
    if "jailbreak" in name:
        return "safety_violation_rate"
    if mode == "Constraint Satisfaction":
        return "exact_match"
    if mode == "Knowledge Retrieval" or "simpleqa" in name:
        return "exact_match"
    if domain == "Coding/Engineering":
        return "pass_at_k"
    return "accuracy"


def infer_context_pressure(row):
    name = str(row["benchmark_name"]).casefold()
    if "needle" in name or "long context" in name:
        return "long_context_primary"
    if "mrcr" in name or "egoschema" in name:
        return "long_context_supporting"
    return "none"


def infer_lifecycle_risk(row):
    name = str(row["benchmark_name"]).casefold()
    source = str(row["source_author"]).casefold()
    text = text_blob(row)

    if "hidden" in name or "internal" in text:
        return "private_or_opaque_eval"
    if "openai" in source or "google" in source or "anthropic" in source or "scale" in source:
        return "provider_created_benchmark"
    if "lmarena" in name or "judge" in text or "human voting" in text:
        return "unclear_metric"
    return "none_identified"


def seed_status_and_confidence(benchmark_name, review_notes, default_status, default_confidence):
    note = review_notes.get(benchmark_name)
    if not note:
        return default_status, default_confidence
    if note.get("priority") == "high":
        return "needs_review", REVIEW_NEEDED_CONFIDENCE
    if note.get("priority") == "low":
        return default_status, default_confidence
    return "needs_review", min(default_confidence, RULE_SEED_CONFIDENCE)


def add_facet_row(rows, row, evidence_id, axis, label, status, confidence, rationale, label_weight=1.0):
    if not label:
        return
    rows.append(
        {
            "benchmark_id": row["benchmark_id"],
            "facet_axis": axis,
            "facet_label": label,
            "label_weight": label_weight,
            "classification_confidence": confidence,
            "evidence_id": evidence_id,
            "review_status": status,
            "rationale": rationale,
        }
    )


def add_manual_facet_rows(rows, row, evidence_id, benchmark_name):
    overrides = MANUAL_FACET_OVERRIDES.get(benchmark_name)
    if not overrides:
        return False

    for axis, label, label_weight, confidence, status, rationale in overrides:
        add_facet_row(
            rows,
            row,
            evidence_id,
            axis,
            label,
            status,
            confidence,
            rationale,
            label_weight=label_weight,
        )
    return True


def build_facet_edges(benchmarks_df, evidence_df, review_notes):
    evidence_by_benchmark = dict(zip(evidence_df["benchmark_id"], evidence_df["evidence_id"]))
    rows = []
    for _, row in benchmarks_df.iterrows():
        benchmark_id = row["benchmark_id"]
        evidence_id = evidence_by_benchmark[benchmark_id]
        benchmark_name = str(row["benchmark_name"]).strip()
        review_note = review_notes.get(benchmark_name)
        review_reason = f" Review note: {review_note['reason']}" if review_note else ""

        if add_manual_facet_rows(rows, row, evidence_id, benchmark_name):
            continue

        projected_seed_labels = {
            "headline_task_mode": str(row["legacy_task_mode"]).strip(),
            "domain": infer_domain(row),
        }
        for axis, label in projected_seed_labels.items():
            if not label:
                continue
            status, confidence = seed_status_and_confidence(
                benchmark_name,
                review_notes,
                default_status="legacy_seed",
                default_confidence=LEGACY_SEED_CONFIDENCE,
            )
            add_facet_row(
                rows,
                row,
                evidence_id,
                axis,
                label,
                status,
                confidence,
                f"{row['legacy_rationale']}{review_reason}",
            )

        inferred_axes = {
            "construct_claim": infer_construct_claim(row),
            "task_mechanism": infer_task_mechanism(row),
            "modality": infer_modality(row),
            "interaction_pattern": infer_interaction_pattern(row),
            "metric_type": infer_metric_type(row),
            "context_pressure": infer_context_pressure(row),
            "benchmark_lifecycle_risk": infer_lifecycle_risk(row),
        }
        for axis, label in inferred_axes.items():
            status, confidence = seed_status_and_confidence(
                benchmark_name,
                review_notes,
                default_status="needs_review",
                default_confidence=RULE_SEED_CONFIDENCE,
            )
            rationale = (
                f"Rule-based v3 seed inferred from legacy task_mode={row['legacy_task_mode']!r}, "
                f"task_domain={row['legacy_task_domain']!r}, benchmark name, and legacy rationale."
                f"{review_reason}"
            )
            add_facet_row(rows, row, evidence_id, axis, label, status, confidence, rationale)

    return pd.DataFrame(rows).sort_values(["benchmark_id", "facet_axis", "facet_label"]).reset_index(drop=True)


def build_release_mentions(models_df, benchmarks_df, canonical_lookup):
    benchmark_id_by_name = dict(zip(benchmarks_df["benchmark_name"], benchmarks_df["benchmark_id"]))

    rows = []
    for _, model in models_df.fillna("").iterrows():
        provider = str(model["Provider"]).strip()
        model_name = str(model["Model name"]).strip()
        release_date = str(model["release date"]).strip()
        model_id = stable_id("model", provider, model_name, release_date)
        source_url = str(model.get("link", "")).strip()
        benchmarks = split_benchmarks(model.get("benchmarks", ""))

        for mention_index, raw_mention in enumerate(benchmarks, start=1):
            benchmark_name = resolve_benchmark(raw_mention, canonical_lookup)
            benchmark_id = benchmark_id_by_name[benchmark_name]
            mention_id = stable_id("mention", model_id, f"{mention_index:03d}")
            rows.append(
                {
                    "mention_id": mention_id,
                    "model_id": model_id,
                    "provider": provider,
                    "model_name": model_name,
                    "release_date": release_date,
                    "source_url": source_url,
                    "benchmark_id": benchmark_id,
                    "benchmark_name": benchmark_name,
                    "raw_mention": raw_mention,
                    "mention_index": mention_index,
                    "mention_prominence": PROMINENCE_DEFAULT,
                    "mention_weight": MENTION_WEIGHT_DEFAULT,
                }
            )

    return pd.DataFrame(rows).sort_values(["release_date", "provider", "model_name", "mention_index"]).reset_index(drop=True)


def build_v3_data(accessed_date):
    models_df = pd.read_csv(DATA_DIR / "models.csv")
    taxonomy_df = pd.read_csv(DATA_DIR / "benchmark_taxonomy_v2.csv")
    aliases_df = read_aliases(DATA_DIR / "benchmark_aliases.csv")
    review_queue_df = read_review_queue(DATA_DIR / "benchmark_review_queue.csv")

    canonical_taxonomy_df = dedupe_taxonomy(taxonomy_df)
    benchmarks_df = build_benchmarks(canonical_taxonomy_df)
    canonical_lookup = build_canonical_lookup(benchmarks_df, aliases_df)
    review_notes = build_review_notes(review_queue_df, canonical_lookup)
    benchmarks_df = apply_benchmark_review_status(benchmarks_df, review_notes)
    evidence_df = build_evidence(benchmarks_df, accessed_date=accessed_date)
    facet_edges_df = build_facet_edges(benchmarks_df, evidence_df, review_notes)
    release_mentions_df = build_release_mentions(models_df, benchmarks_df, canonical_lookup)
    prominence_overrides_df = read_prominence_overrides(DATA_DIR / "mention_prominence_overrides.csv")
    release_mentions_df, prominence_override_count = apply_prominence_overrides(
        release_mentions_df,
        prominence_overrides_df,
    )

    benchmarks_df.to_csv(DATA_DIR / "benchmarks.csv", index=False)
    evidence_df.to_csv(DATA_DIR / "evidence.csv", index=False)
    facet_edges_df.to_csv(DATA_DIR / "benchmark_facet_edges.csv", index=False)
    release_mentions_df.to_csv(DATA_DIR / "release_mentions.csv", index=False)

    print(f"Wrote {len(benchmarks_df)} benchmarks")
    print(f"Wrote {len(evidence_df)} evidence records")
    print(f"Wrote {len(facet_edges_df)} facet edges")
    print(f"Wrote {len(release_mentions_df)} release mentions")
    print(f"Applied {prominence_override_count} mention prominence override(s)")


def main():
    parser = argparse.ArgumentParser(description="Build v3 normalized benchmark data from legacy CSVs.")
    parser.add_argument("--accessed-date", default="2026-04-25", help="Date to stamp seeded evidence rows.")
    args = parser.parse_args()
    build_v3_data(accessed_date=args.accessed_date)


if __name__ == "__main__":
    main()
