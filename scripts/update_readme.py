import pandas as pd


README_BENCHMARK_COLUMNS = [
    "benchmark_name",
    "reference_link",
    "source_author",
    "frontier_lab_author_affiliations",
    "task_mode",
    "task_domain",
    "rationale",
]


def load_benchmark_table():
    benchmarks_df = pd.read_csv("data/benchmarks.csv").fillna("")
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


def generate_markdown():
    models_df = pd.read_csv("data/models.csv")
    benchmark_table_df = load_benchmark_table()

    models_df["release date"] = pd.to_datetime(models_df["release date"])
    models_df = models_df.sort_values("release date", ascending=False)
    models_df["release date"] = models_df["release date"].dt.strftime("%Y-%m-%d")

    with open("data/base_readme.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    models_table = models_df.fillna("").to_markdown(index=False)
    taxonomy_table = benchmark_table_df.fillna("").to_markdown(index=False)

    md_content = md_content.replace("{{MODELS_TABLE}}", models_table)
    md_content = md_content.replace("{{TAXONOMY_TABLE}}", taxonomy_table)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("README.md updated.")


if __name__ == "__main__":
    generate_markdown()
