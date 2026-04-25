import pandas as pd


def generate_markdown():
    models_df = pd.read_csv("data/models.csv")
    taxonomy_df = pd.read_csv("data/benchmark_taxonomy_v2.csv")

    models_df["release date"] = pd.to_datetime(models_df["release date"])
    models_df = models_df.sort_values("release date", ascending=False)
    models_df["release date"] = models_df["release date"].dt.strftime("%Y-%m-%d")

    with open("data/base_readme.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    models_table = models_df.fillna("").to_markdown(index=False)
    taxonomy_table = taxonomy_df.fillna("").to_markdown(index=False)

    md_content = md_content.replace("{{MODELS_TABLE}}", models_table)
    md_content = md_content.replace("{{TAXONOMY_TABLE}}", taxonomy_table)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("README.md updated.")


if __name__ == "__main__":
    generate_markdown()
