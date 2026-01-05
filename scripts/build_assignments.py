#!/usr/bin/env -S uv run python
"""Validate bed assignments and compute block ranges."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.io.schema import ensure_jsonl_schema, validate_required_columns
from scripts.io.waves import apply_wave_id


def _load_config(path: Path, schema_version: int) -> dict:
    ensure_jsonl_schema(path, schema_version)
    config: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        obj = json.loads(stripped)
        config.update(obj)
    return config


def _validate_bounds(df: pd.DataFrame, bed_count: int, bed_length_ft: int) -> None:
    if df["bed_id"].min() < 1 or df["bed_id"].max() > bed_count:
        raise ValueError("bed_id out of bounds")
    if (df["start_ft"] < 0).any():
        raise ValueError("start_ft must be >= 0")
    if ((df["start_ft"] + df["length_ft"]) > bed_length_ft).any():
        raise ValueError("assignment exceeds bed length")


def _validate_alignment(df: pd.DataFrame, block_size_ft: int) -> None:
    if (df["start_ft"] % block_size_ft != 0).any():
        raise ValueError("start_ft must align to block size")
    if (df["length_ft"] % block_size_ft != 0).any():
        raise ValueError("length_ft must align to block size")


def _validate_overlaps(df: pd.DataFrame) -> None:
    for bed_id, group in df.groupby("bed_id"):
        sorted_group = group.sort_values("start_ft")
        prev_end = None
        for _, row in sorted_group.iterrows():
            start = row["start_ft"]
            end = row["start_ft"] + row["length_ft"]
            if prev_end is not None and start < prev_end:
                raise ValueError(f"overlap detected in bed {bed_id}")
            prev_end = end


def build_assignments(
    assignments_path: Path,
    schedule_path: Path,
    config_path: Path,
    schema_version: int,
) -> pd.DataFrame:
    config = _load_config(config_path, schema_version)
    bed_count = int(config["bed_count"])
    bed_length_ft = int(config["bed_length_ft"])
    block_size_ft = int(config["block_size_ft"])

    df_assignments = pd.read_csv(assignments_path, comment="#")
    if df_assignments.empty:
        raise ValueError("bed assignments is empty")

    # Drop fully empty rows
    df_assignments = df_assignments.dropna(how="all")

    # Coerce numeric columns and remove stray rows (e.g., accidental trailing tokens)
    bed_id_num = pd.to_numeric(df_assignments["bed_id"], errors="coerce")
    invalid_bed_id = bed_id_num.isna()
    if invalid_bed_id.any():
        other_cols = [col for col in df_assignments.columns if col != "bed_id"]
        stray = invalid_bed_id & df_assignments[other_cols].isna().all(axis=1)
        df_assignments = df_assignments.loc[~stray].copy()
        bed_id_num = pd.to_numeric(df_assignments["bed_id"], errors="coerce")
        invalid_bed_id = bed_id_num.isna()
        if invalid_bed_id.any():
            raise ValueError("bed assignments has non-numeric bed_id values")
    df_assignments["bed_id"] = bed_id_num
    df_schedule = pd.read_csv(schedule_path, comment="#")

    if "status" not in df_assignments.columns:
        df_assignments["status"] = "CROP"
    df_assignments["status"] = df_assignments["status"].fillna("CROP")

    validate_required_columns(
        df_assignments,
        ["bed_id", "start_ft", "length_ft", "status"],
        "bed assignments",
    )
    df_assignments["start_ft"] = pd.to_numeric(df_assignments["start_ft"], errors="coerce")
    df_assignments["length_ft"] = pd.to_numeric(
        df_assignments["length_ft"], errors="coerce"
    )
    if df_assignments[["start_ft", "length_ft"]].isna().any().any():
        raise ValueError("bed assignments has non-numeric start_ft/length_ft values")
    required_crop_fields = ["crop", "variety", "wave_id", "plant_date"]
    for field in required_crop_fields:
        if field not in df_assignments.columns:
            raise ValueError(f"bed assignments is missing required columns: {field}")

    crop_rows = df_assignments["status"].str.upper() != "BENEFICIAL"
    crop_subset = df_assignments[crop_rows]
    validate_required_columns(
        crop_subset,
        ["crop", "variety", "wave_id", "plant_date"],
        "bed assignments (crop rows)",
    )
    validate_required_columns(
        df_schedule,
        ["crop", "variety", "plant_date", "succession_days", "row_feet", "water"],
        "succession schedule",
    )
    df_schedule = apply_wave_id(df_schedule)
    valid_waves = set(df_schedule["wave_id"].tolist())

    _validate_bounds(df_assignments, bed_count, bed_length_ft)
    _validate_alignment(df_assignments, block_size_ft)
    _validate_overlaps(df_assignments)

    missing = set(crop_subset["wave_id"].tolist()) - valid_waves
    if missing:
        raise ValueError(f"Unknown wave_id values: {sorted(missing)}")

    df_assignments = df_assignments.copy()
    df_assignments["start_block"] = (df_assignments["start_ft"] / block_size_ft).astype(
        int
    )
    df_assignments["end_block"] = (
        (df_assignments["start_ft"] + df_assignments["length_ft"]) / block_size_ft
    ).astype(int)

    return df_assignments


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assignments",
        default="data/plans/bed-assignments.csv",
        help="Path to bed assignments CSV",
    )
    parser.add_argument(
        "--schedule",
        default="data/schedules/succession-schedule.csv",
        help="Path to succession schedule CSV",
    )
    parser.add_argument(
        "--config",
        default="data/plans/config/bed-geometry.jsonl",
        help="Path to bed geometry JSONL",
    )
    parser.add_argument(
        "--schema-version",
        type=int,
        default=1,
        help="Expected schema_version for inputs",
    )
    args = parser.parse_args()

    try:
        df = build_assignments(
            Path(args.assignments),
            Path(args.schedule),
            Path(args.config),
            args.schema_version,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Validated assignments: {len(df)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
