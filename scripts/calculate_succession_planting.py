#!/usr/bin/env -S uv run python
"""Calculate succession planting schedule from plant data and yield targets.

This script generates a succession planting schedule with:
- Order dates (accounting for 35-day nursery lead time for transplants)
- Planting dates (staggered for variety diversity)
- Row feet needed per planting
- Harvest dates and intervals
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path


# Constants
NURSERY_LEAD_TIME_DAYS = 35  # Days before planting to order transplants
GERMINATION_RATE = 0.95  # 95% germination success
FIELD_SURVIVAL_RATE = 0.95  # 95% field survival (accounts for transplant shock, pests, etc.)
BED_WIDTH_INCHES = 30  # Standard bed width
BED_WIDTH_FEET = 30 / 12  # 2.5 feet
INITIAL_PLANTING_DATE = datetime(2026, 2, 14)  # Feb 14, 2026
NUM_SUCCESSION_WAVES = 1  # Generate only 1 initial planting for now

# Plant type categories for grouping (used instead of botanical name)
PLANT_TYPE_MAPPING = {
    # Head lettuce and romaine
    'Lettuce (Single)': 'Head Lettuce',

    # Baby greens and salad mixes
    'Lettuce (Mixed)': 'Baby Greens',
    'Arugula': 'Baby Greens',
    'Greens Mixes': 'Baby Greens',
    'Mustard Greens': 'Baby Greens',
    'Chicory': 'Baby Greens',
    'Spinach': 'Baby Greens',

    # Brassicas (cabbage family)
    'Broccoli': 'Brassica',
    'Napa Cabbage': 'Brassica',
    'Cabbage': 'Brassica',
    'Pak Choi': 'Brassica',
    'Chinese Cabbage': 'Brassica',
    'Cauliflower': 'Brassica',
    'Kale': 'Brassica',

    # Root vegetables
    'Beets': 'Root Vegetable',
    'Carrots': 'Root Vegetable',
    'Radishes': 'Root Vegetable',
    'Radishes (Mixed)': 'Root Vegetable',

    # Onion family
    'Onions': 'Allium',

    # Fruiting crops
    'Tomatoes': 'Fruiting Crop',
    'Peppers (Sweet)': 'Fruiting Crop',
    'Peppers (Hot)': 'Fruiting Crop',
    'Eggplant': 'Fruiting Crop',

    # Cucurbits
    'Cucumber': 'Cucurbit',
    'Summer Squash / Zucchini': 'Cucurbit',
    'Winter Squash': 'Cucurbit',
    'Melons': 'Cucurbit',

    # Legumes
    'Beans (Bush)': 'Legume',
    'Beans (Bush Mixed)': 'Legume',
    'Beans (Pole)': 'Legume',
    'Fava Beans': 'Legume',

    # Other vegetables
    'Swiss Chard': 'Leafy Green',
    'Celery': 'Leafy Green',
    'Sweet Potatoes (Slips)': 'Root Vegetable',
    'Amaranth': 'Leafy Green',
}


def get_plant_type(crop: str) -> str:
    """Map crop name to plant type category."""
    return PLANT_TYPE_MAPPING.get(crop, 'Other')


def parse_spacing(spacing_str: str) -> float | None:
    """Parse spacing string to get plants per linear foot.

    Examples:
        "≥24\" apart" -> 0.5 plants/ft (1 plant every 24 inches)
        "≥5\" apart" -> 2.4 plants/ft (1 plant every 5 inches)
        "12-18\"" -> 0.67-1.0 plants/ft (use midpoint)
    """
    if not spacing_str or spacing_str == 'N/A':
        return None

    # Extract numbers from string
    import re
    numbers = re.findall(r'(\d+)', spacing_str)
    if not numbers:
        return None

    # Take first number or average if range
    if len(numbers) == 1:
        inches = float(numbers[0])
    else:
        # Average the range
        inches = sum(float(n) for n in numbers[:2]) / 2

    # Convert to plants per foot
    plants_per_foot = 12 / inches if inches > 0 else None
    return plants_per_foot


def calculate_plants_per_linear_foot(row: dict, method: str) -> float:
    """Calculate how many plants fit per linear foot of bed.

    For transplants: Use spacing from web_final_spacing
    For scatter/broadcast: Use count_sq_ft × bed_width_feet
    """
    # Check if planted in scattered/broadcast pattern
    rows_pattern = row.get('rows/pattern', '').lower()
    if 'scatter' in rows_pattern or 'broadcast' in rows_pattern or method == 'scatter' or method == 'broadcast':
        # Baby greens planted densely
        count_sq_ft = row.get('count_sq_ft', '')
        if count_sq_ft and count_sq_ft != '':
            try:
                plants_per_sq_ft = float(count_sq_ft)
                return plants_per_sq_ft * BED_WIDTH_FEET
            except ValueError:
                pass

    # Standard spacing for transplants or direct sow in rows
    spacing_str = row.get('web_final_spacing', '')
    plants_per_ft = parse_spacing(spacing_str)

    # If we have rows/pattern info, use that
    if not plants_per_ft:
        rows_pattern = row.get('rows/pattern', '')
        count_ft = row.get('count_ft', '')
        if count_ft:
            try:
                plants_per_ft = float(count_ft)
            except ValueError:
                pass

    return plants_per_ft if plants_per_ft else 1.0  # Default to 1 plant/ft if unknown


def get_succession_interval(plant_row: dict, config_row: dict) -> int:
    """Get succession interval in days.

    Priority:
    1. Override from config
    2. sdsc_succession field
    3. Default based on crop type
    """
    # Check config override
    override = config_row.get('succession_days_override', '')
    if override and override != '':
        try:
            return int(override)
        except ValueError:
            pass

    # Check plant data
    succession_str = plant_row.get('sdsc_succession', '')
    if succession_str and succession_str != '':
        # Extract first number from succession string (e.g., "10-21 days" -> 10)
        import re
        numbers = re.findall(r'(\d+)', succession_str)
        if numbers:
            return int(numbers[0])

    # Defaults by crop type if nothing else
    crop = plant_row.get('crop', '').lower()
    if 'radish' in crop:
        return 7
    elif 'lettuce' in crop or 'spinach' in crop:
        return 10
    elif 'beet' in crop or 'carrot' in crop:
        return 14
    else:
        return 21  # Default for most crops


def get_days_to_maturity(plant_row: dict) -> int:
    """Extract days to maturity as integer."""
    dtm_str = plant_row.get('web_days_to_maturity', '')
    if not dtm_str or dtm_str == '':
        return 60  # Default

    # Extract first number
    import re
    numbers = re.findall(r'(\d+)', dtm_str)
    if numbers:
        return int(numbers[0])
    return 60


def get_avg_yield_per_plant(plant_row: dict) -> float:
    """Calculate average yield per plant in lbs."""
    lo_str = plant_row.get('lo_yield', '')
    hi_str = plant_row.get('hi_yield', '')

    try:
        lo = float(lo_str) if lo_str else 0
        hi = float(hi_str) if hi_str else lo
        return (lo + hi) / 2 if hi > 0 else lo
    except ValueError:
        return 0.5  # Default fallback


def calculate_succession_schedule(
    plant_data_path: Path,
    config_path: Path,
    output_path: Path,
) -> None:
    """Generate succession planting schedule."""

    # Load plant data
    plant_data = {}
    with open(plant_data_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['crop'], row['variety'])
            plant_data[key] = row

    # Load config
    config_rows = []
    with open(config_path, 'r') as f:
        reader = csv.DictReader(f)
        config_rows = list(reader)

    # Generate schedule
    schedule = []

    for config_row in config_rows:
        crop = config_row['crop']
        variety = config_row['variety']
        target_lbs_week = float(config_row['target_lbs_week'])
        stagger_days = int(float(config_row.get('stagger_offset_days', 0) or 0))

        # Look up plant data
        plant_row = plant_data.get((crop, variety))
        if not plant_row:
            print(f"Warning: No plant data found for {crop} - {variety}")
            continue

        # Get key parameters
        method = plant_row.get('method', 'transplant')
        is_transplant = method == 'transplant'
        succession_days = get_succession_interval(plant_row, config_row)
        days_to_maturity = get_days_to_maturity(plant_row)
        avg_yield_per_plant = get_avg_yield_per_plant(plant_row)
        plants_per_linear_foot = calculate_plants_per_linear_foot(plant_row, method)
        plant_type = get_plant_type(crop)

        # Skip if we don't have yield data
        if avg_yield_per_plant == 0:
            print(f"Warning: No yield data for {crop} - {variety}, skipping")
            continue

        # Calculate plants needed per planting (accounting for losses)
        plants_needed = (target_lbs_week / avg_yield_per_plant
                        / GERMINATION_RATE / FIELD_SURVIVAL_RATE)

        # Calculate row feet needed and round to nearest integer
        # Minimum of 1 row foot to ensure at least some plants
        row_feet = plants_needed / plants_per_linear_foot if plants_per_linear_foot > 0 else 0
        row_feet = max(1, round(row_feet))

        # Generate succession waves
        for wave in range(1, NUM_SUCCESSION_WAVES + 1):
            # Calculate dates
            plant_date = INITIAL_PLANTING_DATE + timedelta(days=(wave - 1) * succession_days + stagger_days)
            order_date = plant_date - timedelta(days=NURSERY_LEAD_TIME_DAYS) if is_transplant else plant_date
            first_harvest_date = plant_date + timedelta(days=days_to_maturity)

            schedule.append({
                'plant_type': plant_type,
                'crop': crop,
                'variety': variety,
                'method': method,
                'water': plant_row.get('water', ''),
                'plant_date': plant_date.strftime('%Y-%m-%d'),
                'wave_seq': wave,
                'first_harvest_date': first_harvest_date.strftime('%Y-%m-%d'),
                'target_lbs_week': target_lbs_week,
                'row_feet': row_feet,
                'succession_days': succession_days,
                'notes': config_row.get('notes', ''),
                'url': plant_row.get('url', ''),
                'avg_yield_per_plant': round(avg_yield_per_plant, 3),
                'plants_per_linear_foot': round(plants_per_linear_foot, 2),
                'plants_count': int(plants_needed),
            })

    # Sort by plant type, then crop, then variety
    # This groups vegetables by category (baby greens, brassicas, root vegetables, etc.)
    schedule.sort(key=lambda x: (x['plant_type'], x['crop'], x['variety']))

    # Write output
    if schedule:
        fieldnames = [
            'plant_type', 'crop', 'variety', 'method', 'water', 'plant_date',
            'wave_seq', 'first_harvest_date', 'target_lbs_week', 'row_feet',
            'succession_days', 'notes', 'url', 'avg_yield_per_plant',
            'plants_per_linear_foot', 'plants_count'
        ]

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(schedule)

        print(f"Generated succession schedule with {len(schedule)} planting events")
        print(f"Saved to {output_path}")
    else:
        print("No schedule generated - check warnings above")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate succession planting schedule from plant data and yield targets"
    )
    parser.add_argument(
        '--plant-data',
        type=Path,
        default=Path('data/plants/vegetable-data-current.csv'),
        help='Path to plant data CSV'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('data/schedules/succession-plan-config.csv'),
        help='Path to succession plan config CSV'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/schedules/succession-schedule.csv'),
        help='Path to output succession schedule CSV'
    )

    args = parser.parse_args()

    try:
        calculate_succession_schedule(
            plant_data_path=args.plant_data,
            config_path=args.config,
            output_path=args.output,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
