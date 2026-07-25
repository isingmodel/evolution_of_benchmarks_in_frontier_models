#!/usr/bin/env bash
# Run every reproducible build, validation, and analysis step.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-${ROOT}/.venv/bin/python}"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Python interpreter not found at ${PYTHON}. Build .venv from requirements.txt first." >&2
  exit 1
fi

cd "${ROOT}"

AS_OF="${AS_OF:-$(
  "${PYTHON}" -c \
    'import pandas as pd; print(pd.read_csv("data/models.csv")["release date"].max())'
)}"

echo "Running full pipeline as of ${AS_OF}"

"${PYTHON}" scripts/build_normalized_data.py
"${PYTHON}" scripts/validate_data.py

"${PYTHON}" analysis/common_snapshot/analyze.py --as-of "${AS_OF}"
"${PYTHON}" analysis/provider_strategy_long_context/analyze.py --as-of "${AS_OF}"
"${PYTHON}" analysis/frontier_lab_benchmark_hegemony/analyze.py --as-of "${AS_OF}"
"${PYTHON}" analysis/ideation_network_dynamics/analyze.py --as-of "${AS_OF}"
"${PYTHON}" analysis/ideation_narrative_strategy/analyze.py --as-of "${AS_OF}"
"${PYTHON}" analysis/ideation_methodology_visuals/analyze.py --as-of "${AS_OF}"

"${PYTHON}" analysis/benchmark_evolution/analyze.py --as-of "${AS_OF}" --strict-resolution
"${PYTHON}" analysis/benchmark_evolution/benchmark_count_trend.py --as-of "${AS_OF}" --window-days 90 --strict-resolution
"${PYTHON}" analysis/benchmark_taxonomy_trends/task_mode_trend.py --as-of "${AS_OF}" --window-days 180 --strict-resolution
"${PYTHON}" analysis/benchmark_taxonomy_trends/separate_axis_trends.py --as-of "${AS_OF}" --window-days 180 --strict-resolution
"${PYTHON}" analysis/benchmark_taxonomy_trends/facet_trends.py --as-of "${AS_OF}" --window-days 180 --axes modality,interaction_pattern,context_pressure --top-labels 8 --strict-resolution
"${PYTHON}" analysis/readme_story/analyze.py --as-of "${AS_OF}"

"${PYTHON}" scripts/validate_data.py
