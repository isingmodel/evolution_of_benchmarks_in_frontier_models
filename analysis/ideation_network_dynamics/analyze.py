#!/usr/bin/env python3
"""Prototype network, diffusion, and competitive benchmark-attention analyses.

The project tracks benchmark mentions on public frontier model release pages.
This script therefore treats a benchmark mention as an attention/adoption event,
not as evidence about underlying model capability.
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SCRIPT_DIR = ROOT / "scripts"

sys.path.insert(0, str(SCRIPT_DIR))
from plot_utils import add_derived_headline_task_mode  # noqa: E402
from taxonomy_utils import CanonicalResolver, split_benchmark_mentions  # noqa: E402


SOURCE_GROUP_ORDER = [
    "Self-affiliated frontier lab",
    "Other frontier lab-affiliated",
    "Academia",
    "Independent/industry",
    "Unknown",
]


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def split_mentions(value: object) -> list[str]:
    text = clean_text(value)
    if not text or text.casefold() == "nan":
        return []
    return split_benchmark_mentions(text)


def parse_lab_affiliations(value: object) -> set[str]:
    text = clean_text(value)
    if not text or text.casefold() == "none":
        return set()
    return {part.strip() for part in text.split(";") if part.strip()}


def has_self_affiliation(provider: str, lab_affiliations: object, source_author: object = "") -> bool:
    labs = parse_lab_affiliations(lab_affiliations)
    if provider in labs:
        return True
    source = clean_text(source_author)
    return provider in {part.strip() for part in source.replace(",", ";").split(";") if part.strip()}


def source_author_group(provider: str, source_author: object, lab_affiliations: object) -> str:
    labs = parse_lab_affiliations(lab_affiliations)
    if has_self_affiliation(provider, lab_affiliations, source_author):
        return "Self-affiliated frontier lab"
    if labs:
        return "Other frontier lab-affiliated"

    source = clean_text(source_author)
    if not source:
        return "Unknown"
    if "Academia" in {part.strip() for part in source.replace(",", ";").split(";")}:
        return "Academia"
    if source.startswith("Academia"):
        return "Academia"
    return "Independent/industry"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    models = pd.read_csv(DATA_DIR / "models.csv")
    models["release_date"] = pd.to_datetime(models["release date"], errors="raise")
    benchmarks = pd.read_csv(DATA_DIR / "benchmarks.csv").fillna("")
    facets = add_derived_headline_task_mode(pd.read_csv(DATA_DIR / "benchmark_facets.csv").fillna(""))
    return models, benchmarks, facets


def facet_label_lookup(facets: pd.DataFrame, axis: str) -> dict[str, str]:
    filtered = facets[facets["facet_axis"] == axis].copy()
    if filtered.empty:
        return {}
    return (
        filtered.groupby("benchmark_id")["facet_label"]
        .apply(lambda values: "; ".join(sorted(set(clean_text(v) for v in values if clean_text(v)))))
        .to_dict()
    )


def build_mentions(
    models: pd.DataFrame,
    benchmarks: pd.DataFrame,
    facets: pd.DataFrame,
) -> pd.DataFrame:
    resolver = CanonicalResolver.from_files(DATA_DIR / "benchmarks.csv", DATA_DIR / "benchmark_aliases.csv")
    benchmarks_by_id = benchmarks.set_index("benchmark_id", drop=False).to_dict("index")
    headline_by_id = facet_label_lookup(facets, "headline_task_mode")
    risk_by_id = facet_label_lookup(facets, "benchmark_lifecycle_risk")
    construct_by_id = facet_label_lookup(facets, "construct_claim")
    domain_by_id = facet_label_lookup(facets, "domain")

    rows: list[dict[str, object]] = []
    unresolved: list[tuple[str, str, str]] = []

    models_sorted = models.sort_values(["release_date", "Provider", "Model name"]).reset_index(drop=True)
    for release_sequence, (_, model_row) in enumerate(models_sorted.iterrows(), start=1):
        provider = clean_text(model_row["Provider"])
        model = clean_text(model_row["Model name"])
        release_date = model_row["release_date"]
        release_key = f"{provider}::{model}::{release_date.date()}"

        for mention_position, raw_mention in enumerate(split_mentions(model_row.get("benchmarks", "")), start=1):
            resolution = resolver.resolve(raw_mention)
            if not resolution:
                unresolved.append((provider, model, raw_mention))
                continue

            meta = benchmarks_by_id[resolution.benchmark_id]
            lab_affiliations = clean_text(meta.get("frontier_lab_author_affiliations", ""))
            source_author = clean_text(meta.get("source_author", ""))
            rows.append(
                {
                    "release_sequence": release_sequence,
                    "release_key": release_key,
                    "provider": provider,
                    "model": model,
                    "release_date": release_date,
                    "mention_position": mention_position,
                    "raw_mention": raw_mention,
                    "benchmark_id": resolution.benchmark_id,
                    "benchmark_name": resolution.benchmark_name,
                    "match_source": resolution.match_source,
                    "match_type": resolution.match_type,
                    "source_author": source_author,
                    "frontier_lab_author_affiliations": lab_affiliations,
                    "source_author_group": source_author_group(provider, source_author, lab_affiliations),
                    "self_affiliated_source": has_self_affiliation(provider, lab_affiliations, source_author),
                    "legacy_task_mode": clean_text(meta.get("legacy_task_mode", "")),
                    "legacy_task_domain": clean_text(meta.get("legacy_task_domain", "")),
                    "headline_task_mode": headline_by_id.get(resolution.benchmark_id, ""),
                    "facet_domain": domain_by_id.get(resolution.benchmark_id, ""),
                    "construct_claim": construct_by_id.get(resolution.benchmark_id, ""),
                    "benchmark_lifecycle_risk": risk_by_id.get(resolution.benchmark_id, ""),
                }
            )

    if unresolved:
        sample = "; ".join(f"{provider}/{model}: {raw}" for provider, model, raw in unresolved[:10])
        raise ValueError(f"Unresolved mentions encountered despite exact resolver: {sample}")

    mentions = pd.DataFrame(rows)
    if mentions.empty:
        return mentions
    return mentions.sort_values(
        ["release_date", "provider", "model", "mention_position", "benchmark_name"]
    ).reset_index(drop=True)


def build_cascade_tables(
    mentions: pd.DataFrame,
    models: pd.DataFrame,
    benchmarks: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    provider_windows = (
        models.groupby("Provider")["release_date"]
        .agg(provider_first_release="min", provider_last_release="max")
        .reset_index()
        .rename(columns={"Provider": "provider"})
    )
    provider_last = dict(zip(provider_windows["provider"], provider_windows["provider_last_release"]))
    all_providers = sorted(provider_windows["provider"].unique())
    as_of = models["release_date"].max()
    benchmark_meta = benchmarks.set_index("benchmark_id", drop=False).to_dict("index")

    cascade_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []

    for benchmark_id, group in mentions.groupby("benchmark_id", sort=False):
        group = group.sort_values(["release_date", "provider", "model", "mention_position"]).copy()
        meta = benchmark_meta[benchmark_id]
        first_date = group["release_date"].min()
        last_date = group["release_date"].max()
        total_mentions = len(group)
        half_index = max(math.ceil(total_mentions / 2) - 1, 0)
        time_to_50pct_mentions = (group.iloc[half_index]["release_date"] - first_date).days

        provider_firsts = (
            group.drop_duplicates("provider", keep="first")[
                ["provider", "release_date", "model", "raw_mention"]
            ]
            .rename(columns={"release_date": "provider_first_date", "model": "provider_first_model"})
            .sort_values(["provider_first_date", "provider"])
            .reset_index(drop=True)
        )
        provider_firsts["adoption_order"] = (
            provider_firsts["provider_first_date"].rank(method="dense").astype(int)
        )

        first_providers = provider_firsts.loc[
            provider_firsts["provider_first_date"] == first_date, "provider"
        ].tolist()
        follower_firsts = provider_firsts[~provider_firsts["provider"].isin(first_providers)]
        second_date = pd.NaT
        second_provider = ""
        days_to_second = pd.NA
        if not follower_firsts.empty:
            second_date = follower_firsts.iloc[0]["provider_first_date"]
            second_provider = follower_firsts.iloc[0]["provider"]
            days_to_second = int((second_date - first_date).days)

        eligible_provider_count = sum(1 for provider in all_providers if provider_last[provider] >= first_date)
        raw_variants = sorted(set(group["raw_mention"]))
        provider_path = " -> ".join(
            f"{row.provider} ({row.provider_first_date.date()})" for row in provider_firsts.itertuples()
        )

        for row in provider_firsts.itertuples():
            event_rows.append(
                {
                    "benchmark_id": benchmark_id,
                    "benchmark_name": group.iloc[0]["benchmark_name"],
                    "provider": row.provider,
                    "provider_first_date": row.provider_first_date.date().isoformat(),
                    "provider_first_model": row.provider_first_model,
                    "raw_mention": row.raw_mention,
                    "adoption_order": int(row.adoption_order),
                    "lag_days_since_benchmark_first": int((row.provider_first_date - first_date).days),
                    "is_first_provider": row.provider in first_providers,
                    "first_providers": "; ".join(first_providers),
                    "source_author": clean_text(meta.get("source_author", "")),
                    "frontier_lab_author_affiliations": clean_text(
                        meta.get("frontier_lab_author_affiliations", "")
                    ),
                    "legacy_task_mode": clean_text(meta.get("legacy_task_mode", "")),
                    "legacy_task_domain": clean_text(meta.get("legacy_task_domain", "")),
                }
            )

        cascade_rows.append(
            {
                "benchmark_id": benchmark_id,
                "benchmark_name": group.iloc[0]["benchmark_name"],
                "source_author": clean_text(meta.get("source_author", "")),
                "frontier_lab_author_affiliations": clean_text(
                    meta.get("frontier_lab_author_affiliations", "")
                ),
                "legacy_task_mode": clean_text(meta.get("legacy_task_mode", "")),
                "legacy_task_domain": clean_text(meta.get("legacy_task_domain", "")),
                "first_date": first_date.date().isoformat(),
                "last_date": last_date.date().isoformat(),
                "first_providers": "; ".join(first_providers),
                "first_provider_count": len(first_providers),
                "provider_count": provider_firsts["provider"].nunique(),
                "eligible_provider_count": eligible_provider_count,
                "provider_reach_share": provider_firsts["provider"].nunique() / eligible_provider_count
                if eligible_provider_count
                else 0,
                "total_mentions": total_mentions,
                "release_count": group["release_key"].nunique(),
                "raw_variant_count": len(raw_variants),
                "raw_variants": "; ".join(raw_variants),
                "provider_adoption_path": provider_path,
                "second_provider": second_provider,
                "second_provider_date": "" if pd.isna(second_date) else second_date.date().isoformat(),
                "days_to_second_provider": days_to_second,
                "active_span_days": int((last_date - first_date).days),
                "time_to_50pct_mentions_days": int(time_to_50pct_mentions),
                "observed_days_since_first": int((as_of - first_date).days),
                "first_provider_is_author_affiliated": any(
                    has_self_affiliation(
                        provider,
                        meta.get("frontier_lab_author_affiliations", ""),
                        meta.get("source_author", ""),
                    )
                    for provider in first_providers
                ),
                "cross_provider_cascade": provider_firsts["provider"].nunique() > len(first_providers),
            }
        )

    cascade = pd.DataFrame(cascade_rows).sort_values(
        ["provider_count", "total_mentions", "benchmark_name"], ascending=[False, False, True]
    )
    adoption_events = pd.DataFrame(event_rows).sort_values(
        ["provider_first_date", "benchmark_name", "provider"]
    )
    provider_roles = build_provider_roles(mentions, cascade, adoption_events)
    return cascade, adoption_events, provider_roles


def split_semicolon(value: object) -> list[str]:
    return [part.strip() for part in clean_text(value).split(";") if part.strip()]


def build_provider_roles(
    mentions: pd.DataFrame,
    cascade: pd.DataFrame,
    adoption_events: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for provider in sorted(mentions["provider"].unique()):
        provider_mentions = mentions[mentions["provider"] == provider]
        provider_events = adoption_events[adoption_events["provider"] == provider]

        originated_mask = cascade["first_providers"].apply(lambda value: provider in split_semicolon(value))
        originated = cascade[originated_mask]
        exported = originated[
            originated["provider_count"] > originated["first_provider_count"]
        ]
        imported_events = provider_events[~provider_events["is_first_provider"]]

        follower_adoptions_created = 0
        for row in originated.itertuples():
            follower_adoptions_created += len(
                adoption_events[
                    (adoption_events["benchmark_id"] == row.benchmark_id)
                    & (~adoption_events["provider"].isin(split_semicolon(row.first_providers)))
                ]
            )

        import_lags = pd.to_numeric(
            imported_events["lag_days_since_benchmark_first"], errors="coerce"
        ).dropna()
        rows.append(
            {
                "provider": provider,
                "total_mentions": len(provider_mentions),
                "unique_benchmarks_mentioned": provider_mentions["benchmark_id"].nunique(),
                "first_mover_benchmarks": len(originated),
                "exported_benchmarks_later_adopted": len(exported),
                "follower_adoptions_created": follower_adoptions_created,
                "imported_benchmarks": len(imported_events),
                "avg_import_lag_days": round(import_lags.mean(), 1) if not import_lags.empty else "",
                "median_import_lag_days": round(import_lags.median(), 1) if not import_lags.empty else "",
                "net_export_balance": len(exported) - len(imported_events),
                "first_mover_share_of_portfolio": len(originated)
                / provider_mentions["benchmark_id"].nunique()
                if provider_mentions["benchmark_id"].nunique()
                else 0,
            }
        )

    return pd.DataFrame(rows).sort_values("provider")


def build_release_strategy_metrics(mentions: pd.DataFrame, models: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    release_base = models.sort_values(["release_date", "Provider", "Model name"]).copy()

    for _, release in release_base.iterrows():
        provider = clean_text(release["Provider"])
        model = clean_text(release["Model name"])
        release_date = release["release_date"]
        release_mentions = mentions[
            (mentions["provider"] == provider)
            & (mentions["model"] == model)
            & (mentions["release_date"] == release_date)
        ]
        benchmark_ids = set(release_mentions["benchmark_id"])
        total = len(benchmark_ids)
        prior_global = set(mentions[mentions["release_date"] < release_date]["benchmark_id"])
        prior_provider = set(
            mentions[
                (mentions["provider"] == provider) & (mentions["release_date"] < release_date)
            ]["benchmark_id"]
        )
        prior_other = set(
            mentions[
                (mentions["provider"] != provider) & (mentions["release_date"] < release_date)
            ]["benchmark_id"]
        )

        new_global = benchmark_ids - prior_global
        self_repeat = benchmark_ids & prior_provider
        follower = benchmark_ids & prior_other
        new_to_provider = benchmark_ids - prior_provider

        def share(count: int) -> float:
            return count / total if total else 0.0

        rows.append(
            {
                "provider": provider,
                "model": model,
                "release_date": release_date.date().isoformat(),
                "total_unique_benchmarks": total,
                "new_global_benchmarks": len(new_global),
                "new_global_share": share(len(new_global)),
                "new_to_provider_benchmarks": len(new_to_provider),
                "new_to_provider_share": share(len(new_to_provider)),
                "self_repeat_benchmarks": len(self_repeat),
                "self_repeat_share": share(len(self_repeat)),
                "already_used_by_other_provider_benchmarks": len(follower),
                "already_used_by_other_provider_share": share(len(follower)),
            }
        )

    return pd.DataFrame(rows)


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def build_similarity_tables(
    mentions: pd.DataFrame,
    models: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    providers = sorted(models["Provider"].dropna().unique())
    rows: list[dict[str, object]] = []
    for release_date in sorted(models["release_date"].unique()):
        portfolios = {
            provider: set(
                mentions[
                    (mentions["provider"] == provider) & (mentions["release_date"] <= release_date)
                ]["benchmark_id"]
            )
            for provider in providers
        }
        for left, right in itertools.combinations(providers, 2):
            left_set = portfolios[left]
            right_set = portfolios[right]
            rows.append(
                {
                    "date": pd.Timestamp(release_date).date().isoformat(),
                    "provider_pair": f"{left} - {right}",
                    "left_provider": left,
                    "right_provider": right,
                    "left_portfolio_size": len(left_set),
                    "right_portfolio_size": len(right_set),
                    "intersection_size": len(left_set & right_set),
                    "union_size": len(left_set | right_set),
                    "jaccard_similarity": jaccard(left_set, right_set),
                }
            )

    timeseries = pd.DataFrame(rows)
    latest_date = timeseries["date"].max()
    latest = timeseries[timeseries["date"] == latest_date].copy()
    return timeseries, latest


def build_source_dependency_tables(mentions: pd.DataFrame, models: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    provider_rows: list[dict[str, object]] = []
    for provider, group in mentions.groupby("provider"):
        total = len(group)
        group_counts = group["source_author_group"].value_counts().to_dict()
        self_affiliated = int(group_counts.get("Self-affiliated frontier lab", 0))
        other_frontier = int(group_counts.get("Other frontier lab-affiliated", 0))
        academia = int(group_counts.get("Academia", 0))
        independent = int(group_counts.get("Independent/industry", 0))
        unknown = int(group_counts.get("Unknown", 0))
        provider_created = int(
            group["benchmark_lifecycle_risk"].str.contains("provider_created_benchmark", na=False).sum()
        )

        def share(count: int) -> float:
            return count / total if total else 0.0

        provider_rows.append(
            {
                "provider": provider,
                "total_mentions": total,
                "unique_benchmarks": group["benchmark_id"].nunique(),
                "self_affiliated_mentions": self_affiliated,
                "self_affiliated_share": share(self_affiliated),
                "other_frontier_lab_affiliated_mentions": other_frontier,
                "other_frontier_lab_affiliated_share": share(other_frontier),
                "academia_mentions": academia,
                "academia_share": share(academia),
                "independent_industry_mentions": independent,
                "independent_industry_share": share(independent),
                "unknown_source_mentions": unknown,
                "unknown_source_share": share(unknown),
                "provider_created_risk_mentions": provider_created,
                "provider_created_risk_share": share(provider_created),
            }
        )

    release_rows: list[dict[str, object]] = []
    for _, release in models.sort_values(["release_date", "Provider", "Model name"]).iterrows():
        provider = clean_text(release["Provider"])
        model = clean_text(release["Model name"])
        date = release["release_date"]
        group = mentions[
            (mentions["provider"] == provider)
            & (mentions["model"] == model)
            & (mentions["release_date"] == date)
        ]
        total = len(group)
        counts = group["source_author_group"].value_counts().to_dict()
        row = {
            "provider": provider,
            "model": model,
            "release_date": date.date().isoformat(),
            "total_mentions": total,
        }
        for source_group in SOURCE_GROUP_ORDER:
            count = int(counts.get(source_group, 0))
            row[f"{source_group}_mentions"] = count
            row[f"{source_group}_share"] = count / total if total else 0.0
        release_rows.append(row)

    return pd.DataFrame(provider_rows).sort_values("provider"), pd.DataFrame(release_rows)


def save_portfolio_similarity_chart(similarity: pd.DataFrame) -> None:
    if similarity.empty:
        return
    plot_df = similarity.copy()
    plot_df["date"] = pd.to_datetime(plot_df["date"])

    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.lineplot(
        data=plot_df,
        x="date",
        y="jaccard_similarity",
        hue="provider_pair",
        marker="o",
        linewidth=2.2,
        ax=ax,
    )
    ax.set_title("Cumulative Benchmark Portfolio Similarity")
    ax.set_xlabel("Release date")
    ax.set_ylabel("Jaccard similarity")
    ax.set_ylim(0, max(0.55, plot_df["jaccard_similarity"].max() + 0.05))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(title="Provider pair", loc="upper left", frameon=True)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "portfolio_similarity_over_time.png", dpi=180)
    plt.close(fig)


def save_provider_role_chart(provider_roles: pd.DataFrame) -> None:
    if provider_roles.empty:
        return
    plot_df = provider_roles.melt(
        id_vars=["provider"],
        value_vars=["exported_benchmarks_later_adopted", "imported_benchmarks"],
        var_name="role_metric",
        value_name="count",
    )
    label_map = {
        "exported_benchmarks_later_adopted": "First-used, later adopted",
        "imported_benchmarks": "Adopted after another provider",
    }
    plot_df["role_metric"] = plot_df["role_metric"].map(label_map)

    fig, ax = plt.subplots(figsize=(8.5, 5))
    sns.barplot(
        data=plot_df,
        x="provider",
        y="count",
        hue="role_metric",
        order=sorted(provider_roles["provider"].unique()),
        palette=["#2A9D8F", "#E76F51"],
        ax=ax,
    )
    ax.set_title("Benchmark Import/Export Role Balance")
    ax.set_xlabel("")
    ax.set_ylabel("Unique benchmarks")
    ax.legend(title="", loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "provider_role_balance.png", dpi=180)
    plt.close(fig)


def save_source_dependency_chart(source_dependency: pd.DataFrame) -> None:
    if source_dependency.empty:
        return
    plot_df = source_dependency.set_index("provider")
    columns = [
        "self_affiliated_mentions",
        "other_frontier_lab_affiliated_mentions",
        "academia_mentions",
        "independent_industry_mentions",
    ]
    labels = [
        "Self-affiliated frontier lab",
        "Other frontier lab-affiliated",
        "Academia",
        "Independent/industry",
    ]
    colors = ["#7B4EA3", "#3A86FF", "#2A9D8F", "#E9C46A"]

    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = pd.Series(0, index=plot_df.index)
    for column, label, color in zip(columns, labels, colors):
        values = plot_df[column]
        ax.bar(plot_df.index, values, bottom=bottom, label=label, color=color)
        bottom = bottom + values
    ax.set_title("Source Authorship Mix of Benchmark Mentions")
    ax.set_xlabel("")
    ax.set_ylabel("Mention count")
    ax.legend(title="", loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=True)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "source_author_mix_by_provider.png", dpi=180)
    plt.close(fig)


def build_summary_metrics(
    mentions: pd.DataFrame,
    cascade: pd.DataFrame,
    provider_roles: pd.DataFrame,
    similarity_latest: pd.DataFrame,
    source_dependency: pd.DataFrame,
) -> pd.DataFrame:
    cross_provider = cascade[cascade["cross_provider_cascade"]]
    fastest = cross_provider.dropna(subset=["days_to_second_provider"]).sort_values("days_to_second_provider").head(5)
    slowest = cross_provider.dropna(subset=["days_to_second_provider"]).sort_values(
        "days_to_second_provider", ascending=False
    ).head(5)
    latest_similarity = similarity_latest.sort_values("jaccard_similarity", ascending=False)

    rows: list[dict[str, object]] = [
        {"metric": "resolved_mentions", "value": len(mentions), "detail": ""},
        {
            "metric": "unique_benchmarks_mentioned",
            "value": mentions["benchmark_id"].nunique(),
            "detail": "",
        },
        {
            "metric": "cross_provider_cascades",
            "value": len(cross_provider),
            "detail": "benchmarks adopted by more providers than their first-provider set",
        },
        {
            "metric": "single_provider_benchmarks",
            "value": len(cascade) - len(cross_provider),
            "detail": "",
        },
    ]

    for row in fastest.itertuples():
        rows.append(
            {
                "metric": "fastest_cascade",
                "value": row.days_to_second_provider,
                "detail": f"{row.benchmark_name}: {row.first_providers} -> {row.second_provider}",
            }
        )

    for row in slowest.itertuples():
        rows.append(
            {
                "metric": "slowest_cascade",
                "value": row.days_to_second_provider,
                "detail": f"{row.benchmark_name}: {row.first_providers} -> {row.second_provider}",
            }
        )

    for row in provider_roles.sort_values("net_export_balance", ascending=False).itertuples():
        rows.append(
            {
                "metric": "provider_net_export_balance",
                "value": row.net_export_balance,
                "detail": row.provider,
            }
        )

    for row in latest_similarity.itertuples():
        rows.append(
            {
                "metric": "latest_portfolio_similarity",
                "value": round(row.jaccard_similarity, 3),
                "detail": row.provider_pair,
            }
        )

    for row in source_dependency.sort_values("self_affiliated_share", ascending=False).itertuples():
        rows.append(
            {
                "metric": "self_affiliated_mention_share",
                "value": round(row.self_affiliated_share, 3),
                "detail": row.provider,
            }
        )

    return pd.DataFrame(rows)


def write_outputs() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models, benchmarks, facets = load_inputs()

    mentions = build_mentions(models, benchmarks, facets)
    cascade, adoption_events, provider_roles = build_cascade_tables(mentions, models, benchmarks)
    release_strategy = build_release_strategy_metrics(mentions, models)
    similarity, similarity_latest = build_similarity_tables(mentions, models)
    source_dependency, release_author_mix = build_source_dependency_tables(mentions, models)
    summary = build_summary_metrics(
        mentions,
        cascade,
        provider_roles,
        similarity_latest,
        source_dependency,
    )

    outputs = {
        "normalized_mentions.csv": mentions,
        "cascade_metrics.csv": cascade,
        "adoption_events.csv": adoption_events,
        "provider_diffusion_roles.csv": provider_roles,
        "release_strategy_metrics.csv": release_strategy,
        "provider_similarity_timeseries.csv": similarity,
        "provider_similarity_latest.csv": similarity_latest,
        "source_author_dependency_by_provider.csv": source_dependency,
        "release_source_author_mix.csv": release_author_mix,
        "summary_metrics.csv": summary,
    }
    for filename, frame in outputs.items():
        frame.to_csv(OUT_DIR / filename, index=False)

    save_portfolio_similarity_chart(similarity)
    save_provider_role_chart(provider_roles)
    save_source_dependency_chart(source_dependency)

    manifest = {
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "resolved_mentions": int(len(mentions)),
        "unique_benchmarks_mentioned": int(mentions["benchmark_id"].nunique()),
        "providers": sorted(models["Provider"].dropna().unique().tolist()),
        "latest_release_date": models["release_date"].max().date().isoformat(),
        "csv_outputs": sorted(outputs),
        "chart_outputs": [
            "portfolio_similarity_over_time.png",
            "provider_role_balance.png",
            "source_author_mix_by_provider.png",
        ],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    manifest = write_outputs()
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
