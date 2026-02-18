#!/usr/bin/env -S uv run python
"""
Populate harvest_type field in vegetable data CSV.
"""

import csv
from pathlib import Path


def determine_harvest_type(crop, variety, notes):
    """
    Determine harvest type based on crop name, variety, and notes.

    Returns: cut_and_come_again, single_harvest, multi-pick, or storage
    """
    crop_lower = crop.lower()
    variety_lower = variety.lower()
    notes_lower = notes.lower() if notes else ""

    # Cut and come again crops - can harvest leaves/stems repeatedly
    cut_and_come_again = [
        'kale',
        'arugula',
        'lettuce',
        'spinach',
        'celery',
        'mustard',
        'pak choi',
        'swiss chard',
        'greens',
        'chicory',
    ]

    # Multi-pick crops - harvest fruit/pods over extended period
    multi_pick = [
        'tomato',
        'pepper',
        'cucumber',
        'bean',
        'pea',
        'zucchini',
        'squash',
    ]

    # Broccoli is special - main head is single, but side shoots make it multi-pick
    if 'broccoli' in crop_lower:
        # Sprouting types and those with good side-shoot production are multi-pick
        if 'sprouting' in variety_lower or 'sprouting' in notes_lower:
            return 'multi-pick'
        # Happy Rich specifically noted for side shoots
        if 'happy rich' in variety_lower or 'side shoot' in notes_lower or 'side-shoot' in notes_lower:
            return 'multi-pick'
        # Standard broccoli - single main head harvest
        return 'single_harvest'

    # Check cut and come again
    for keyword in cut_and_come_again:
        if keyword in crop_lower:
            return 'cut_and_come_again'

    # Check multi-pick
    for keyword in multi_pick:
        if keyword in crop_lower:
            return 'multi-pick'

    # Root vegetables, brassica heads, etc. - single harvest
    single_harvest_crops = [
        'beet',
        'carrot',
        'radish',
        'onion',
        'cabbage',
        'cauliflower',
        'napa',
    ]

    for keyword in single_harvest_crops:
        if keyword in crop_lower:
            return 'single_harvest'

    # Default to single harvest if unknown
    return 'single_harvest'


def main():
    input_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-with-harvest.csv')
    output_file = input_file  # Update in place

    # Read the CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        description_row = next(reader)  # Skip description row but save it
        data_rows = list(reader)

    # Populate harvest_type
    updates = {
        'cut_and_come_again': [],
        'multi-pick': [],
        'single_harvest': []
    }

    for row in data_rows:
        harvest_type = determine_harvest_type(
            row['crop'],
            row['variety'],
            row.get('notes', '')
        )
        row['harvest_type'] = harvest_type
        updates[harvest_type].append(f"{row['crop']} - {row['variety']}")

    # Write back to CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(description_row)
        writer.writerows(data_rows)

    # Print summary
    print(f"✓ Updated harvest_type for {len(data_rows)} varieties\n")

    for harvest_type, varieties in updates.items():
        if varieties:
            print(f"{harvest_type.upper()} ({len(varieties)}):")
            for v in sorted(varieties):
                print(f"  - {v}")
            print()


if __name__ == '__main__':
    main()
