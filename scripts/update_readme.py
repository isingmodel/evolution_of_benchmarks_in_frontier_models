import pandas as pd


README_BENCHMARK_COLUMNS = [
    "benchmark_name",
    "task_mode",
    "task_domain",
    "review_status",
]


def load_benchmark_table():
    benchmarks_df = pd.read_csv("data/benchmarks.csv").fillna("")
    return pd.DataFrame(
        {
            "benchmark_name": benchmarks_df["benchmark_name"],
            "task_mode": benchmarks_df["legacy_task_mode"],
            "task_domain": benchmarks_df["legacy_task_domain"],
            "review_status": benchmarks_df["review_status"],
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


def source_evidence_summary():
    models_df = pd.read_csv("data/models.csv")
    mentions_df = pd.read_csv("data/release_mentions.csv")
    evidence_df = pd.read_csv("data/evidence.csv")

    release_rows_with_mentions = models_df["benchmarks"].apply(lambda value: len(split_benchmarks(value)) > 0).sum()
    prominence_counts = mentions_df["mention_prominence"].fillna("unspecified").value_counts()
    benchmark_definition_evidence = (evidence_df["evidence_type"] == "benchmark_definition").sum()
    provider_quote_evidence = evidence_df["evidence_type"].isin(
        {"provider_mention", "technical_report", "model_card"}
    ).sum()

    rows = [
        {
            "layer": "Tracked model-release rows",
            "count": len(models_df),
            "current status": f"{release_rows_with_mentions} rows have captured benchmark mentions",
        },
        {
            "layer": "Resolved release-page mentions",
            "count": len(mentions_df),
            "current status": f"{mentions_df['source_url'].nunique()} source URLs; mention labels and order retained",
        },
        {
            "layer": "Mention prominence weights",
            "count": int(prominence_counts.get("release_page_unspecified", 0)),
            "current status": "All captured mentions still use release_page_unspecified / weight 1.0",
        },
        {
            "layer": "Benchmark-definition evidence",
            "count": int(benchmark_definition_evidence),
            "current status": "Seeded from benchmark reference links",
        },
        {
            "layer": "Quote/section/OCR provider evidence",
            "count": int(provider_quote_evidence),
            "current status": "Not represented yet",
        },
        {
            "layer": "Composite/family sensitivity runs",
            "count": 0,
            "current status": "Not run yet; listed as follow-up audit",
        },
    ]
    return pd.DataFrame(rows).to_markdown(index=False)


def projection_summary_tables(benchmark_table_df):
    statuses = ["accepted", "needs_review", "legacy_seed"]

    def summarize(index_column):
        summary = pd.crosstab(benchmark_table_df[index_column], benchmark_table_df["review_status"])
        for status in statuses:
            if status not in summary.columns:
                summary[status] = 0
        summary = summary[statuses]
        summary["total"] = summary.sum(axis=1)
        summary = summary.sort_values("total", ascending=False).reset_index()
        return summary.to_markdown(index=False)

    return "\n\nBy task mode:\n\n" + summarize("task_mode") + "\n\nBy task domain:\n\n" + summarize("task_domain")


def generate_markdown():
    models_df = load_models_table()
    benchmark_table_df = load_benchmark_table()

    with open("data/base_readme.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    models_table = models_df[
        ["Provider", "Model name", "release date", "benchmark_mentions_captured"]
    ].fillna("").to_markdown(index=False)
    md_content = md_content.replace("{{LATEST_RELEASE_SUMMARY_TABLE}}", latest_release_summary(models_df))
    md_content = md_content.replace("{{SOURCE_EVIDENCE_SUMMARY_TABLE}}", source_evidence_summary())
    md_content = md_content.replace("{{REVIEW_STATUS_SUMMARY_TABLE}}", review_status_summary(benchmark_table_df))
    md_content = md_content.replace("{{REVIEW_DEBT_TABLE}}", review_debt_summary())
    md_content = md_content.replace("{{PROJECTION_SUMMARY_TABLES}}", projection_summary_tables(benchmark_table_df))
    md_content = md_content.replace("{{MODELS_TABLE}}", models_table)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("README.md updated.")


if __name__ == "__main__":
    generate_markdown()
