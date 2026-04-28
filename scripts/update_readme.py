import argparse
from pathlib import Path

import pandas as pd


DEFAULT_BASE_README = Path("data/base_readme.md")
DEFAULT_OUTPUT = Path("README.md")

README_BENCHMARK_COLUMNS = [
    "benchmark_name",
    "reference_link",
    "source_author",
    "frontier_lab_author_affiliations",
    "task_mode",
    "task_domain",
    "rationale",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Regenerate the top-level README from data/base_readme.md.")
    parser.add_argument("--base", default=DEFAULT_BASE_README, type=Path, help="README template path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Generated README output path.")
    return parser.parse_args()


def load_benchmark_table(benchmarks_path=Path("data/benchmarks.csv")):
    benchmarks_df = pd.read_csv(benchmarks_path).fillna("")
    return pd.DataFrame(
        {
            "benchmark_name": benchmarks_df["benchmark_name"],
            "reference_link": benchmarks_df["reference_link"],
            "source_author": benchmarks_df["source_author"],
            "frontier_lab_author_affiliations": benchmarks_df[
                "frontier_lab_author_affiliations"
            ],
            "task_mode": benchmarks_df["legacy_task_mode"],
            "task_domain": benchmarks_df["legacy_task_domain"],
            "rationale": benchmarks_df["legacy_rationale"],
        },
        columns=README_BENCHMARK_COLUMNS,
    )


def generate_markdown(base_path=DEFAULT_BASE_README, output_path=DEFAULT_OUTPUT):
    models_df = pd.read_csv("data/models.csv")
    benchmark_table_df = load_benchmark_table()

    models_df["release date"] = pd.to_datetime(models_df["release date"])
    models_df = models_df.sort_values("release date", ascending=False)
    models_df["release date"] = models_df["release date"].dt.strftime("%Y-%m-%d")

    md_content = base_path.read_text(encoding="utf-8")

    models_table = models_df.fillna("").to_markdown(index=False)
    taxonomy_table = benchmark_table_df.fillna("").to_markdown(index=False)

    md_content = md_content.replace("{{MODELS_TABLE}}", models_table)
    md_content = md_content.replace("{{TAXONOMY_TABLE}}", taxonomy_table)

    output_path.write_text(md_content, encoding="utf-8")

    print(f"{output_path} updated.")


if __name__ == "__main__":
    args = parse_args()
    generate_markdown(base_path=args.base, output_path=args.output)
