#!/usr/bin/env -S uv run python
"""Update count_ft in vegetable data based on rows/pattern and in_row_spacing_ft."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def format_count(value: float) -> str:
    """Format float to a compact string with up to 2 decimals."""
    text = f"{value:.2f}"
    text = text.rstrip("0").rstrip(".")
    return text


def compute_count_ft(rows_pattern: str, in_row_spacing_ft: str) -> tuple[str, str | None]:
    rows_pattern = rows_pattern.strip().lower()
    if not rows_pattern:
        return "", "rows/pattern is empty"

    if "5-star" in rows_pattern or "5star" in rows_pattern:
        return format_count(1.5), None

    if "scatter" in rows_pattern or "broadcast" in rows_pattern:
        return "", None

    if re.fullmatch(r"\d+", rows_pattern):
        try:
            spacing_ft = float(in_row_spacing_ft)
        except (TypeError, ValueError):
            return "", None
        if spacing_ft <= 0:
            return "", None
        num_rows = int(rows_pattern)
        return format_count(num_rows * (1.0 / spacing_ft)), None

    return "", f"unrecognized rows/pattern: {rows_pattern}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/plants/vegetable-data.csv"),
        help="Input CSV with plant data",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (defaults to overwriting input)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without saving",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = args.input

    df = pd.read_csv(args.input, dtype=str, keep_default_na=False)

    required_columns = {"rows/pattern", "in_row_spacing_ft", "count_ft"}
    missing = required_columns - set(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise SystemExit(f"Missing required columns: {missing_list}")

    old_count = df["count_ft"].copy()

    warnings: list[str] = []

    def apply_count(row: pd.Series) -> str:
        value, warning = compute_count_ft(
            row.get("rows/pattern", ""),
            row.get("in_row_spacing_ft", ""),
        )
        if warning:
            warnings.append(warning)
        return value

    df["count_ft"] = df.apply(apply_count, axis=1)

    changes = (df["count_ft"] != old_count).sum()
    empty = (df["count_ft"] == "").sum()
    total = len(df)

    print(f"Updated count_ft for {changes}/{total} rows.")
    print(f"Blank count_ft rows: {empty}/{total}.")
    if warnings:
        unique_warnings = sorted(set(warnings))
        print(f"Warnings: {len(warnings)} (unique: {len(unique_warnings)})")
        for warning in unique_warnings[:10]:
            print(f"- {warning}")
        if len(unique_warnings) > 10:
            print("... (more warnings truncated)")

    if args.dry_run:
        print("Dry run - not saving changes.")
        return 0

    df.to_csv(args.output, index=False)
    print(f"Saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
