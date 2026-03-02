#!/usr/bin/env -S uv run python
"""Generate condensed planting summary in markdown format."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def generate_planting_summary(
    schedule_path: Path,
    output_path: Path,
) -> None:
    """Generate markdown summary from succession schedule."""

    with open(schedule_path, 'r') as f:
        reader = csv.DictReader(f)
        schedule = list(reader)

    if not schedule:
        print("No planting events found in schedule")
        return

    # Sort by plant type, then crop
    schedule.sort(key=lambda x: (x['plant_type'], x['crop'], x['variety']))

    # Split by method
    transplants = [r for r in schedule if r['method'] == 'transplant']
    direct_sow = [r for r in schedule if r['method'] == 'direct_sow']

    ROW_LENGTH_FT = 70

    lines = ["# Planting Summary", "", f"Row length: {ROW_LENGTH_FT} ft", ""]

    # Transplants table
    lines.append("## Transplants")
    lines.append("")
    lines.append("| Crop | Variety | Expected lbs/wk | Expected row ft | Rows |")
    lines.append("|------|---------|-----------------|-----------------|------|")

    transplant_lbs = 0
    transplant_row_ft = 0

    for row in transplants:
        expected_lbs = round(float(row['expected_lbs_week']))
        expected_row_ft = round(float(row['expected_row_feet']))
        row_count = round(expected_row_ft / ROW_LENGTH_FT, 1)
        transplant_lbs += expected_lbs
        transplant_row_ft += expected_row_ft
        lines.append(f"| {row['crop']} | {row['variety']} | {expected_lbs} | {expected_row_ft} | {row_count} |")

    transplant_rows = round(transplant_row_ft / ROW_LENGTH_FT, 1)
    lines.append(f"| **Total** | | **{transplant_lbs}** | **{transplant_row_ft}** | **{transplant_rows}** |")
    lines.append("")

    # Direct sow table
    lines.append("## Direct Sow")
    lines.append("")
    lines.append("| Crop | Variety | Expected lbs/wk | Expected row ft | Rows |")
    lines.append("|------|---------|-----------------|-----------------|------|")

    direct_sow_lbs = 0
    direct_sow_row_ft = 0

    for row in direct_sow:
        expected_lbs = round(float(row['expected_lbs_week']))
        expected_row_ft = round(float(row['expected_row_feet']))
        row_count = round(expected_row_ft / ROW_LENGTH_FT, 1)
        direct_sow_lbs += expected_lbs
        direct_sow_row_ft += expected_row_ft
        lines.append(f"| {row['crop']} | {row['variety']} | {expected_lbs} | {expected_row_ft} | {row_count} |")

    direct_sow_rows = round(direct_sow_row_ft / ROW_LENGTH_FT, 1)
    lines.append(f"| **Total** | | **{direct_sow_lbs}** | **{direct_sow_row_ft}** | **{direct_sow_rows}** |")
    lines.append("")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Generated planting summary with {len(schedule)} entries")
    print(f"Saved to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate condensed planting summary in markdown"
    )
    parser.add_argument(
        '--schedule',
        type=Path,
        default=Path('data/schedules/succession-schedule.csv'),
        help='Path to succession schedule CSV'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/schedules/planting-summary.md'),
        help='Path to output markdown file'
    )

    args = parser.parse_args()

    try:
        generate_planting_summary(
            schedule_path=args.schedule,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
