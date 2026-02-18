#!/usr/bin/env -S uv run python
"""
Populate yield_per_harvest_lo/hi fields for plant-type crops.
For yield_type='plant', copy values from lo_yield and hi_yield.
For yield_type='sqft', leave blank (will compute separately).
"""

import csv
from pathlib import Path


def main():
    input_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-with-harvest.csv')
    output_file = input_file  # Update in place

    # Read the CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        description_row = next(reader)  # Skip description row but save it
        data_rows = list(reader)

    # Track updates
    plant_updated = 0
    sqft_skipped = 0
    no_yield_data = []

    # Populate yield_per_harvest fields
    for row in data_rows:
        yield_type = row.get('yield_type', '')

        if yield_type == 'plant':
            # Copy from lo_yield and hi_yield
            lo_yield = row.get('lo_yield', '').strip()
            hi_yield = row.get('hi_yield', '').strip()

            if lo_yield or hi_yield:
                row['yield_per_harvest_lo'] = lo_yield
                row['yield_per_harvest_hi'] = hi_yield
                plant_updated += 1
            else:
                # Track varieties with no yield data
                no_yield_data.append(f"{row['crop']} - {row['variety']}")

        elif yield_type == 'sqft':
            # Leave blank for sqft types (will compute separately)
            row['yield_per_harvest_lo'] = ''
            row['yield_per_harvest_hi'] = ''
            sqft_skipped += 1

    # Write back to CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(description_row)
        writer.writerows(data_rows)

    # Print summary
    print(f"✓ Updated yield_per_harvest fields\n")
    print(f"Plant-type crops:")
    print(f"  - Updated: {plant_updated} varieties (copied from lo_yield/hi_yield)")
    if no_yield_data:
        print(f"  - No yield data: {len(no_yield_data)} varieties")

    print(f"\nSqft-type crops:")
    print(f"  - Skipped: {sqft_skipped} varieties (will compute separately)")

    if no_yield_data:
        print(f"\nVarieties with no yield data:")
        for v in sorted(no_yield_data):
            print(f"  - {v}")


if __name__ == '__main__':
    main()
