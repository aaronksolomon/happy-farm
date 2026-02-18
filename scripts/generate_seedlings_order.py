#!/usr/bin/env -S uv run python
"""Generate seedlings order from succession schedule.

Filters succession schedule for transplants only and outputs a simplified
order sheet for nursery ordering.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path


# Available plug flat sizes (half and full trays of 50 and 72 cell flats)
FLAT_SIZES = [25, 36, 50, 72]


def round_to_flat_quantity(target: int) -> int:
    """Round up target quantity to nearest available flat size.

    For quantities larger than 72, use multiples of flat sizes.
    """
    if target <= 0:
        return FLAT_SIZES[0]

    # For small quantities, find the smallest flat that fits
    for size in FLAT_SIZES:
        if target <= size:
            return size

    # For larger quantities, find best combination
    # Use largest flat (72) as base, then add smallest flat that covers remainder
    full_flats = target // 72
    remainder = target % 72

    if remainder == 0:
        return full_flats * 72

    # Find smallest flat that covers the remainder
    for size in FLAT_SIZES:
        if remainder <= size:
            return (full_flats * 72) + size

    # If remainder > 72 (shouldn't happen), add another full flat
    return (full_flats + 1) * 72


def generate_seedlings_order(
    schedule_path: Path,
    output_path: Path,
) -> None:
    """Generate seedlings order from succession schedule."""

    # Load succession schedule
    with open(schedule_path, 'r') as f:
        reader = csv.DictReader(f)
        schedule = list(reader)

    # Filter for transplants only
    transplants = [row for row in schedule if row['method'] == 'transplant']

    if not transplants:
        print("No transplants found in schedule")
        return

    # Loss rates (must match calculate_succession_planting.py)
    GERMINATION_RATE = 0.95
    FIELD_SURVIVAL_RATE = 0.95

    # Build output rows with simplified columns for ordering
    order_rows = []
    for row in transplants:
        target_quantity = int(row['plant_count_or_sqft'])
        flat_quantity = round_to_flat_quantity(target_quantity)

        plant_date_str = row['plant_date']
        seed_date = ''
        try:
            plant_date = datetime.strptime(plant_date_str, '%Y-%m-%d')
            seed_date = (plant_date - timedelta(days=28)).strftime('%Y-%m-%d')
        except ValueError:
            seed_date = ''

        # Calculate expected lbs/week based on flat_quantity (what we'll actually plant)
        avg_yield = float(row['avg_yield_per_plant'])
        harvest_weeks = float(row['harvest_weeks_per_planting'])
        surviving_plants = flat_quantity * GERMINATION_RATE * FIELD_SURVIVAL_RATE
        expected_lbs_week = round(surviving_plants * avg_yield / harvest_weeks, 1)

        plants_per_linear_foot = row.get('plants_per_linear_foot', '')
        if plants_per_linear_foot and plants_per_linear_foot != '':
            try:
                plants_per_linear_foot_val = float(plants_per_linear_foot)
            except ValueError:
                plants_per_linear_foot_val = 0
        else:
            plants_per_linear_foot_val = 0

        target_row_feet = row.get('row_feet', '')
        actual_row_feet = ''
        if plants_per_linear_foot_val > 0:
            actual_row_feet = round(surviving_plants / plants_per_linear_foot_val, 1)

        order_rows.append({
            'plant_name': row['crop'],
            'variety': row['variety'],
            'url': row['url'],
            'target_quantity': target_quantity,
            'flat_quantity': flat_quantity,
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

    print(f"Generated seedlings order with {len(order_rows)} transplants")
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
