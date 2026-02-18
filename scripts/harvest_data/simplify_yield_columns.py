#!/usr/bin/env -S uv run python
"""
Simplify yield columns:
- Change yield_type values from "per_plant"/"per_area" to "plant"/"sqft"
- Replace 4 yield columns with 2 simpler ones:
  - yield_per_harvest_lo (replaces yield_per_area_per_harvest_lo and yield_per_plant_per_harvest_lo)
  - yield_per_harvest_hi (replaces yield_per_area_per_harvest_hi and yield_per_plant_per_harvest_hi)
"""

import csv
from pathlib import Path


def main():
    input_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-with-harvest.csv')
    output_file = input_file  # Update in place

    # Read the CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        old_fieldnames = list(reader.fieldnames)
        description_row = next(reader)
        data_rows = list(reader)

    # Define column mapping
    columns_to_remove = [
        'yield_per_area_per_harvest_lo',
        'yield_per_area_per_harvest_hi',
        'yield_per_plant_per_harvest_lo',
        'yield_per_plant_per_harvest_hi'
    ]

    new_columns = [
        'yield_per_harvest_lo',
        'yield_per_harvest_hi'
    ]

    # Build new fieldnames list
    new_fieldnames = []
    for col in old_fieldnames:
        if col == 'yield_per_area_per_harvest_lo':
            # Insert both new columns here (where the first old column was)
            new_fieldnames.extend(new_columns)
        elif col not in columns_to_remove:
            # Keep all other columns
            new_fieldnames.append(col)

    # Update description row
    new_description_row = {}
    for col in new_fieldnames:
        if col == 'yield_type':
            new_description_row[col] = 'plant or sqft (units for yield_per_harvest fields)'
        elif col == 'yield_per_harvest_lo':
            new_description_row[col] = 'float - minimum yield per harvest (lbs/plant or lbs/sqft depending on yield_type)'
        elif col == 'yield_per_harvest_hi':
            new_description_row[col] = 'float - maximum yield per harvest (lbs/plant or lbs/sqft depending on yield_type)'
        elif col in description_row:
            new_description_row[col] = description_row[col]

    # Update data rows
    for row in data_rows:
        # Change yield_type values
        if row.get('yield_type') == 'per_plant':
            row['yield_type'] = 'plant'
        elif row.get('yield_type') == 'per_area':
            row['yield_type'] = 'sqft'

        # Add new empty yield columns
        row['yield_per_harvest_lo'] = ''
        row['yield_per_harvest_hi'] = ''

        # Remove old yield columns
        for col in columns_to_remove:
            row.pop(col, None)

    # Write updated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerow(new_description_row)
        writer.writerows(data_rows)

    print(f"✓ Simplified yield columns in {output_file}")
    print(f"\nChanges made:")
    print(f"  - Updated yield_type values:")
    print(f"    'per_plant' → 'plant'")
    print(f"    'per_area' → 'sqft'")
    print(f"\n  - Removed 4 columns:")
    for col in columns_to_remove:
        print(f"    - {col}")
    print(f"\n  - Added 2 simplified columns:")
    for col in new_columns:
        print(f"    + {col}")
    print(f"\n  Total columns: {len(old_fieldnames)} → {len(new_fieldnames)}")


if __name__ == '__main__':
    main()
