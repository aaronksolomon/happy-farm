#!/usr/bin/env -S uv run python
"""
Remove harvest_interval_planned column from vegetable data CSV.
This is a planning field, not plant data.
"""

import csv
from pathlib import Path


def main():
    input_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-with-harvest.csv')
    output_file = input_file  # Update in place

    column_to_remove = 'harvest_interval_planned'

    # Read the CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        old_fieldnames = list(reader.fieldnames)
        description_row = next(reader)
        data_rows = list(reader)

    # Remove the column from fieldnames
    new_fieldnames = [col for col in old_fieldnames if col != column_to_remove]

    # Remove from description row
    if column_to_remove in description_row:
        del description_row[column_to_remove]

    # Remove from data rows
    for row in data_rows:
        if column_to_remove in row:
            del row[column_to_remove]

    # Write updated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerow(description_row)
        writer.writerows(data_rows)

    print(f"✓ Removed column: {column_to_remove}")
    print(f"  Total columns: {len(old_fieldnames)} → {len(new_fieldnames)}")
    print(f"\nRemaining harvest-related columns:")
    harvest_cols = [col for col in new_fieldnames if 'harvest' in col or 'yield' in col or 'regrowth' in col]
    for col in harvest_cols:
        print(f"  - {col}")


if __name__ == '__main__':
    main()
