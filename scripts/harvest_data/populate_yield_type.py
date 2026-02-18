#!/usr/bin/env -S uv run python
"""
Populate yield_type field in vegetable data CSV.
"""

import csv
from pathlib import Path


def determine_yield_type(crop, variety, rows_pattern, count_sq_ft):
    """
    Determine yield type based on planting pattern and density.

    Returns: per_plant or per_area
    """
    crop_lower = crop.lower()
    variety_lower = variety.lower()
    pattern_lower = rows_pattern.lower() if rows_pattern else ""

    # Per area crops - scattered/broadcast seeding, measured by area yield
    # These are typically baby greens, salad mixes, or microgreens

    # Check for scattered/dense planting pattern
    if 'scattered' in pattern_lower:
        return 'per_area'

    # Check for mix varieties (usually broadcast seeded)
    if 'mix' in variety_lower and 'greens' in crop_lower:
        return 'per_area'

    if 'mix' in variety_lower and ('lettuce' in crop_lower or 'arugula' in crop_lower):
        return 'per_area'

    # Check for very high density plantings (>15 plants per sq ft)
    try:
        if count_sq_ft and float(count_sq_ft) > 15:
            return 'per_area'
    except (ValueError, TypeError):
        pass

    # Baby leaf greens and microgreens
    baby_greens = ['arugula', 'mesclun', 'microgreen']
    for keyword in baby_greens:
        if keyword in crop_lower or keyword in variety_lower:
            return 'per_area'

    # Everything else is measured per plant
    return 'per_plant'


def main():
    input_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-with-harvest.csv')
    output_file = input_file  # Update in place

    # Read the CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        description_row = next(reader)  # Skip description row but save it
        data_rows = list(reader)

    # Populate yield_type
    updates = {
        'per_area': [],
        'per_plant': []
    }

    for row in data_rows:
        yield_type = determine_yield_type(
            row['crop'],
            row['variety'],
            row.get('rows/pattern', ''),
            row.get('count_sq_ft', '')
        )
        row['yield_type'] = yield_type
        updates[yield_type].append(f"{row['crop']} - {row['variety']}")

    # Write back to CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(description_row)
        writer.writerows(data_rows)

    # Print summary
    print(f"✓ Updated yield_type for {len(data_rows)} varieties\n")

    for yield_type, varieties in sorted(updates.items()):
        if varieties:
            print(f"{yield_type.upper()} ({len(varieties)}):")
            for v in sorted(varieties):
                print(f"  - {v}")
            print()


if __name__ == '__main__':
    main()
