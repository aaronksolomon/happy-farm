#!/usr/bin/env -S uv run python
"""Load crop and succession schedule data with schema validation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.io.schema import validate_required_columns
from scripts.io.waves import apply_wave_id


def load_data(
    crops_path: Path,
    schedule_path: Path,
    schema_version: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_crops = pd.read_csv(crops_path, comment="#")
    df_schedule = pd.read_csv(schedule_path, comment="#")

    validate_required_columns(
        df_schedule,
        ["crop", "variety", "plant_date", "succession_days", "row_feet", "water"],
        "succession schedule",
    )

    df_schedule = apply_wave_id(df_schedule)

    return df_crops, df_schedule


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--crops",
        default="data/plants/vegetable-data-current.csv",
        help="Path to crop plan CSV",
    )
    parser.add_argument(
        "--schedule",
        default="data/schedules/succession-schedule.csv",
        help="Path to succession schedule CSV",
    )
    parser.add_argument(
        "--schema-version",
        type=int,
        default=1,
        help="Expected schema_version for CSV inputs",
    )
    args = parser.parse_args()

    try:
        crops_path = Path(args.crops)
        schedule_path = Path(args.schedule)
        df_crops, df_schedule = load_data(
            crops_path, schedule_path, args.schema_version
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Loaded crops: {len(df_crops)} rows")
    print(f"Loaded succession schedule: {len(df_schedule)} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
