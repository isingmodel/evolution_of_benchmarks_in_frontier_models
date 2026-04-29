import argparse
from pathlib import Path

import pandas as pd


DEFAULT_BASE_README = Path("data/base_readme.md")
DEFAULT_OUTPUT = Path("README.md")
DEFAULT_STORY_DIR = Path("analysis/readme_story")


def parse_args():
    parser = argparse.ArgumentParser(description="Regenerate the top-level README from data/base_readme.md.")
    parser.add_argument("--base", default=DEFAULT_BASE_README, type=Path, help="README template path.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Generated README output path.")
    parser.add_argument(
        "--story-dir",
        default=DEFAULT_STORY_DIR,
        type=Path,
        help="Generated story-analysis CSV directory.",
    )
    return parser.parse_args()


def percent(value):
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return ""


def number(value, digits=2):
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return ""


def table_or_note(path, builder):
    if not path.exists():
        return f"_Run `.venv/bin/python analysis/readme_story/analyze.py` to generate `{path}`._"
    data = pd.read_csv(path).fillna("")
    if data.empty:
        return "_No rows generated._"
    return builder(data).to_markdown(index=False)


def static_work_table(story_dir=DEFAULT_STORY_DIR):
    def build(data):
        return pd.DataFrame(
            {
                "Year": data["year_label"],
                "Static exam-style": data["static_exam_share"].map(percent),
                "Work simulation": data["work_simulation_share"].map(percent),
                "Specialized domains": data["specialized_domain_share"].map(percent),
                "Benchmarked releases": data["benchmarked_release_pages"].astype(int),
            }
        )

    return table_or_note(story_dir / "static_work_annual.csv", build)


def work_contributor_table(story_dir=DEFAULT_STORY_DIR):
    def build(data):
        top = data.head(8).copy()
        return pd.DataFrame(
            {
                "Benchmark": top["benchmark_name"],
                "Weighted mentions": top["release_weighted_mentions"].map(lambda value: number(value, 2)),
                "Raw mentions": top["raw_mentions"].astype(int),
                "Providers": top["providers"],
            }
        )

    return table_or_note(story_dir / "work_simulation_top_contributors.csv", build)


def long_context_table(story_dir=DEFAULT_STORY_DIR):
    def build(data):
        return pd.DataFrame(
            {
                "Provider": data["provider"],
                "Broad long-context share": data["broad_long_context_share"].map(percent),
                "Primary-only share": data["primary_long_context_share"].map(percent),
                "Main 2024 driver": data["main_2024_driver"],
                "Benchmarked releases": data["benchmarked_releases"].astype(int),
            }
        )

    return table_or_note(story_dir / "long_context_2024_case_table.csv", build)


def borrowed_authority_table(story_dir=DEFAULT_STORY_DIR):
    def build(data):
        rows = []
        for provider_group in ["Anthropic+Google", "Anthropic", "Google"]:
            group = data[data["provider_group"] == provider_group].set_index("period")
            if group.empty:
                continue
            row = {"Provider group": provider_group}
            for period in ["2023-2024", "2025-2026"]:
                if period not in group.index:
                    row[period] = ""
                    continue
                item = group.loc[period]
                row[period] = (
                    f"{percent(item['openai_source_or_affiliated_share'])} raw; "
                    f"{percent(item['openai_source_or_affiliated_release_normalized_share'])} release-normalized"
                )
            rows.append(row)
        return pd.DataFrame(rows)

    return table_or_note(story_dir / "borrowed_benchmark_authority.csv", build)


def diffusion_table(story_dir=DEFAULT_STORY_DIR):
    def build(data):
        top = data.head(6).copy()
        return pd.DataFrame(
            {
                "Benchmark": top["benchmark_name"],
                "First tracked public mention": top["first_tracked_providers"]
                + " ("
                + top["first_tracked_public_mention"]
                + ")",
                "Next provider": top["next_provider"] + " (" + top["next_provider_date"] + ")",
                "Lag": top["days_to_next_provider"].astype(int).astype(str) + " days",
            }
        )

    return table_or_note(story_dir / "public_benchmark_diffusion_fastest.csv", build)


def generate_markdown(base_path=DEFAULT_BASE_README, output_path=DEFAULT_OUTPUT, story_dir=DEFAULT_STORY_DIR):
    md_content = base_path.read_text(encoding="utf-8")

    md_content = md_content.replace("{{STATIC_WORK_TABLE}}", static_work_table(story_dir))
    md_content = md_content.replace("{{WORK_SIMULATION_CONTRIBUTORS_TABLE}}", work_contributor_table(story_dir))
    md_content = md_content.replace("{{LONG_CONTEXT_TABLE}}", long_context_table(story_dir))
    md_content = md_content.replace("{{BORROWED_AUTHORITY_TABLE}}", borrowed_authority_table(story_dir))
    md_content = md_content.replace("{{DIFFUSION_TABLE}}", diffusion_table(story_dir))

    output_path.write_text(md_content, encoding="utf-8")

    print(f"{output_path} updated.")


if __name__ == "__main__":
    args = parse_args()
    generate_markdown(base_path=args.base, output_path=args.output, story_dir=args.story_dir)
