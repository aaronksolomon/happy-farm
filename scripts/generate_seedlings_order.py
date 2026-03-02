#!/usr/bin/env -S uv run python
"""Generate seedlings order from succession schedule.

Processes succession schedule and outputs an order sheet. Transplants get
flat quantities rounded to nursery tray sizes; direct sow crops use target
values directly.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path


def generate_seedlings_order(
    schedule_path: Path,
    output_path: Path,
) -> None:
    """Generate seedlings order from succession schedule."""

    # Load succession schedule
    with open(schedule_path, 'r') as f:
        reader = csv.DictReader(f)
        schedule = list(reader)

    if not schedule:
        print("No planting events found in schedule")
        return

    # Build output rows with simplified columns for ordering
    order_rows = []
    for row in schedule:
        target_quantity = int(float(row['plant_count_or_sqft']))
        is_transplant = row['method'] == 'transplant'

        plant_date_str = row['plant_date']
        seed_date = ''
        if is_transplant:
            try:
                plant_date = datetime.strptime(plant_date_str, '%Y-%m-%d')
                seed_date = (plant_date - timedelta(days=28)).strftime('%Y-%m-%d')
            except ValueError:
                seed_date = ''

        target_row_feet = row.get('row_feet', '')

        # Read pre-computed values from succession schedule
        flat_quantity_str = row.get('flat_quantity', '')
        expected_lbs_week = row.get('expected_lbs_week', '')
        actual_row_feet = row.get('expected_row_feet', '')

        order_rows.append({
            'plant_name': row['crop'],
            'variety': row['variety'],
            'url': row['url'],
            'target_quantity': target_quantity,
            'flat_quantity': flat_quantity_str,
            'target_row_feet': target_row_feet,
            'actual_row_feet': actual_row_feet,
            'target_lbs_week': row['target_lbs_week'],
            'expected_lbs_week': expected_lbs_week,
            'avg_yield_per_plant': row['avg_yield_per_plant'],
            'succession_days': row['succession_days'],
            'harvest_weeks_per_planting': row['harvest_weeks_per_planting'],
            'plant_date': row['plant_date'],
            'seed_date': seed_date,
            'first_harvest_date': row['first_harvest_date'],
            'notes': row['notes'],
        })

    # Sort by plant date, then plant name
    order_rows.sort(key=lambda x: (x['plant_date'], x['plant_name']))

    # Write output
    fieldnames = [
        'plant_name', 'variety', 'url', 'target_quantity', 'flat_quantity',
        'target_row_feet', 'actual_row_feet',
        'target_lbs_week', 'expected_lbs_week', 'avg_yield_per_plant',
        'succession_days', 'harvest_weeks_per_planting', 'plant_date',
        'seed_date',
        'first_harvest_date', 'notes'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(order_rows)

    transplant_count = sum(1 for r in order_rows if r['flat_quantity'] != 'N/A')
    direct_sow_count = len(order_rows) - transplant_count
    print(f"Generated order with {transplant_count} transplants, {direct_sow_count} direct sow")
    print(f"Saved to {output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate seedlings order from succession schedule"
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
        default=Path('data/schedules/seedlings-order.csv'),
        help='Path to output seedlings order CSV'
    )

    args = parser.parse_args()

    try:
        generate_seedlings_order(
            schedule_path=args.schedule,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
