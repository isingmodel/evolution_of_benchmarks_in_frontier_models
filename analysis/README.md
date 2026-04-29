# Experimental Analyses

This directory collects exploratory analyses built on the benchmark-release data.
Each subfolder should be reproducible from local CSVs and should preserve the core project caveat: the dataset tracks benchmark mentions on public release pages, not direct model capability.

## Folders

- `SYNTHESIS.md`: integrated findings and recommended story structure from the exploratory analyses.
- `benchmark_evolution/`: README-facing benchmark evolution timeline analysis.
- `benchmark_taxonomy_trends/`: README-facing rolling taxonomy trend and review-debt analyses.
- `common_snapshot/`: baseline resolved mention tables and review-debt context shared by the exploratory analyses.
- `frontier_lab_benchmark_hegemony/`: tests cross-lab benchmark adoption and frontier-lab benchmark influence.
- `provider_strategy_long_context/`: tests provider benchmark-showcase strategies, especially Google's 2024 long-context emphasis.
- `ideation_network_dynamics/`: new network, diffusion, and competitive-dynamics analyses.
- `ideation_narrative_strategy/`: new narrative and release-positioning analyses.
- `ideation_methodology_visuals/`: visualization and methodology proposals for making the project more publication-ready.
- `meta_review/`: review notes, scoring rubrics, and presentation recommendations for the exploratory analyses.
- `readme_story/`: generated CSV tables and the analysis script for the README story sections.

Run analysis scripts from the repository root with `.venv/bin/python`.
Most folders use `analyze.py`; grouped analyses may use descriptive script names. See each folder README for exact commands and outputs.
