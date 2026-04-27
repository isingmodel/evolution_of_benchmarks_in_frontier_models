import pandas as pd


README_BENCHMARK_COLUMNS = [
    "benchmark_name",
    "reference_link",
    "source_author",
    "frontier_lab_author_affiliations",
    "task_mode",
    "task_domain",
    "review_status",
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
            "review_status": benchmarks_df["review_status"],
            "rationale": benchmarks_df["legacy_rationale"],
        },
        columns=README_BENCHMARK_COLUMNS,
    )


def split_benchmarks(value):
    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text or text.casefold() == "nan":
        return []

    return [part.strip() for part in text.split(",") if part.strip()]


def load_models_table():
    models_df = pd.read_csv("data/models.csv")
    models_df["release date"] = pd.to_datetime(models_df["release date"])
    models_df = models_df.sort_values("release date", ascending=False)
    models_df["benchmark_mentions_captured"] = models_df["benchmarks"].apply(lambda value: len(split_benchmarks(value)))
    models_df["release date"] = models_df["release date"].dt.strftime("%Y-%m-%d")
    models_df["benchmarks"] = models_df["benchmarks"].fillna("").replace(
        {"": "No public launch-page benchmark mentions captured."}
    )
    return models_df


def latest_release_summary(models_df, row_count=10):
    return models_df.head(row_count)[
        ["Provider", "Model name", "release date", "benchmark_mentions_captured"]
    ].to_markdown(index=False)


def review_status_summary(benchmarks_df):
    counts = (
        benchmarks_df["review_status"]
        .fillna("unspecified")
        .value_counts()
        .rename_axis("benchmark_review_status")
        .reset_index(name="benchmark_rows")
    )
    counts["share"] = (counts["benchmark_rows"] / counts["benchmark_rows"].sum()).map("{:.1%}".format)
    return counts.to_markdown(index=False)


def review_debt_summary():
    facets_df = pd.read_csv("data/benchmark_facet_edges.csv")
    facets_df["classification_confidence"] = pd.to_numeric(
        facets_df["classification_confidence"], errors="coerce"
    )
    facets_df["review_status"] = facets_df["review_status"].fillna("").str.casefold()
    rows = []
    for facet_axis, group in facets_df.groupby("facet_axis", sort=True):
        low_confidence = group["classification_confidence"] < 0.7
        review_needed = group["review_status"].isin({"needs_review", "disputed"})
        rows.append(
            {
                "facet_axis": facet_axis,
                "facet_rows": len(group),
                "low_confidence_rows": int(low_confidence.sum()),
                "low_confidence_share": f"{low_confidence.mean():.1%}",
                "needs_review_or_disputed_rows": int(review_needed.sum()),
                "needs_review_or_disputed_share": f"{review_needed.mean():.1%}",
            }
        )
    return pd.DataFrame(rows).to_markdown(index=False)


def generate_markdown():
    models_df = load_models_table()
    benchmark_table_df = load_benchmark_table()

    with open("data/base_readme.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    models_table = models_df.fillna("").to_markdown(index=False)
    taxonomy_table = benchmark_table_df.fillna("").to_markdown(index=False)

    md_content = md_content.replace("{{LATEST_RELEASE_SUMMARY_TABLE}}", latest_release_summary(models_df))
    md_content = md_content.replace("{{REVIEW_STATUS_SUMMARY_TABLE}}", review_status_summary(benchmark_table_df))
    md_content = md_content.replace("{{REVIEW_DEBT_TABLE}}", review_debt_summary())
    md_content = md_content.replace("{{MODELS_TABLE}}", models_table)
    md_content = md_content.replace("{{TAXONOMY_TABLE}}", taxonomy_table)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("README.md updated.")


if __name__ == "__main__":
    generate_markdown()
