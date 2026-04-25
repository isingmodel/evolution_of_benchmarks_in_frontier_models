#!/usr/bin/env python3
"""Apply local release mention prominence overrides.

This is a deterministic file transform. It never scrapes live release pages;
reviewers should add source-backed rows to data/mention_prominence_overrides.csv.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from mention_prominence import (
    apply_prominence_overrides,
    read_prominence_overrides,
    validate_prominence_overrides,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply manual release mention prominence overrides.")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Directory containing v3 data CSVs.")
    parser.add_argument(
        "--release-mentions",
        help="Path to release_mentions.csv. Defaults to DATA_DIR/release_mentions.csv.",
    )
    parser.add_argument(
        "--overrides",
        help="Path to mention_prominence_overrides.csv. Defaults to DATA_DIR/mention_prominence_overrides.csv.",
    )
    parser.add_argument("--output", help="Output path. Defaults to overwrite release_mentions.csv.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without writing.")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    release_mentions_path = Path(args.release_mentions) if args.release_mentions else data_dir / "release_mentions.csv"
    overrides_path = Path(args.overrides) if args.overrides else data_dir / "mention_prominence_overrides.csv"
    output_path = Path(args.output) if args.output else release_mentions_path
    evidence_path = data_dir / "evidence.csv"

    release_mentions = pd.read_csv(release_mentions_path).fillna("")
    overrides = read_prominence_overrides(overrides_path)
    evidence_ids = set(pd.read_csv(evidence_path).fillna("")["evidence_id"]) if evidence_path.exists() else None

    errors, warnings = validate_prominence_overrides(
        overrides,
        known_mention_ids=set(release_mentions["mention_id"]),
        known_evidence_ids=evidence_ids,
    )
    for warning in warnings:
        print(f"Warning: {warning}")
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    updated, applied_count = apply_prominence_overrides(release_mentions, overrides)
    print(f"Applied {applied_count} active mention prominence override(s) from {overrides_path}.")

    if args.dry_run:
        print("Dry run only; no files written.")
        return

    updated.to_csv(output_path, index=False)
    print(f"Wrote {len(updated)} release mention row(s) to {output_path}.")


if __name__ == "__main__":
    main()
