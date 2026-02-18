#!/usr/bin/env -S uv run python
"""
Add harvest-related columns to vegetable data CSV with data type descriptions.
Creates a new file preserving the original.
"""

import csv
from pathlib import Path

# Columns to delete
COLUMNS_TO_DELETE = ['notes.1', 'web_botanical_name', 'sdsc_product_weight']

# Define the new columns with their descriptions (in order they should appear)
NEW_COLUMNS = {
    'harvest_type': 'cut_and_come_again, single_harvest, multi-pick, or storage',
    'yield_type': 'per_plant or per_area',
    'yield_per_area_per_harvest_lo': 'float - minimum pounds per square foot per harvest',
    'yield_per_area_per_harvest_hi': 'float - maximum pounds per square foot per harvest',
    'yield_per_plant_per_harvest_lo': 'float - minimum pounds per individual plant per harvest',
    'yield_per_plant_per_harvest_hi': 'float - maximum pounds per individual plant per harvest',
    'harvest_interval_planned': 'int - desired days between successive harvests',
    'regrowth_period': 'int - days required for plant/area to regrow before reharvest'
}

# Column to insert new columns after
INSERT_AFTER_COLUMN = 'hi_yield'

# Define descriptions for existing columns
EXISTING_COLUMN_DESCRIPTIONS = {
    'crop': 'string - common name of crop',
    'botanical': 'string - scientific/botanical name',
    'variety': 'string - specific variety name',
    'supplier': 'string - seed supplier code (SDSC, JS, etc.)',
    'last_order': 'date - most recent order date',
    'stock_quantity': 'string - current inventory count',
    'season': 'string - cool or warm season crop',
    'water': 'string - water requirement level',
    'plant_window': 'string - months suitable for planting',
    'method': 'string - planting method (transplant, direct_sow, etc.)',
    'transplant_after': 'float - days from seed to transplant',
    'mature_after': 'int - days from planting to maturity',
    'rows/pattern': 'string - row configuration or planting pattern',
    'count_ft': 'float - plants per linear foot',
    'count_sq_ft': 'float - plants per square foot',
    'lo_yield': 'float - minimum expected yield (pounds)',
    'hi_yield': 'float - maximum expected yield (pounds)',
    'notes': 'string - general notes and growing info',
    'url': 'string - product URL',
    'packet_type': 'string - single, mixed, etc.',
    'notes.1': 'string - additional notes',
    'web_botanical_name': 'string - botanical name from web scrape',
    'web_soil_temp': 'string - optimal soil temperature from web',
    'web_planting_depth': 'string - planting depth from web',
    'sdsc_days_to_germ': 'string - germination time range from SDSC',
    'web_days_to_maturity': 'string - days to maturity from web',
    'sdsc_succession': 'string - succession planting interval from SDSC',
    'web_best_planting_method': 'string - recommended method from web',
    'web_thin_to': 'string - thinning spacing from web',
    'web_final_spacing': 'string - final plant spacing from web',
    'sdsc_area_to_sow': 'string - area coverage per packet from SDSC',
    'web_seeds_per_packet': 'string - seed count from web',
    'sdsc_product_weight': 'string - product weight from SDSC',
    'sdsc_plant_height': 'string - expected plant height from SDSC',
    'sdsc_plant_spread': 'string - expected plant spread from SDSC',
    'js_growing_notes': 'string - growing notes from Johnny\'s Seeds',
    'scrape_status': 'string - web scraping status',
    'scrape_date': 'string - date of last web scrape'
}

def main():
    # File paths
    input_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-current.csv')
    output_file = Path('/Users/phapman/Desktop/Projects/happy-farm/data/plants/vegetable-data-with-harvest.csv')

    # Read the current CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        existing_columns = list(reader.fieldnames)
        data_rows = list(reader)

    # Remove columns to delete
    filtered_columns = [col for col in existing_columns if col not in COLUMNS_TO_DELETE]

    # Find the insertion point
    if INSERT_AFTER_COLUMN not in filtered_columns:
        raise ValueError(f"Column '{INSERT_AFTER_COLUMN}' not found in CSV")

    insert_index = filtered_columns.index(INSERT_AFTER_COLUMN) + 1

    # Build new column list: columns before insert point + new columns + columns after
    all_columns = (
        filtered_columns[:insert_index] +
        list(NEW_COLUMNS.keys()) +
        filtered_columns[insert_index:]
    )

    # Create description row
    description_row = {}
    for col in filtered_columns:
        description_row[col] = EXISTING_COLUMN_DESCRIPTIONS.get(col, 'string - no description')
    for col, desc in NEW_COLUMNS.items():
        description_row[col] = desc

    # Write the new CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)

        # Write header
        writer.writeheader()

        # Write description row
        writer.writerow(description_row)

        # Write existing data rows (new columns will be empty, deleted columns excluded)
        for row in data_rows:
            # Remove deleted columns
            for col in COLUMNS_TO_DELETE:
                row.pop(col, None)
            # Add empty values for new columns
            for col in NEW_COLUMNS.keys():
                row[col] = ''
            writer.writerow(row)

    print(f"✓ Created new file: {output_file}")
    print(f"  - Deleted {len(COLUMNS_TO_DELETE)} columns: {', '.join(COLUMNS_TO_DELETE)}")
    print(f"  - Added {len(NEW_COLUMNS)} new columns after '{INSERT_AFTER_COLUMN}'")
    print(f"  - Added description row as row 2")
    print(f"  - Preserved {len(data_rows)} data rows")
    print(f"\nNew columns added (after '{INSERT_AFTER_COLUMN}'):")
    for col in NEW_COLUMNS.keys():
        print(f"  - {col}")

if __name__ == '__main__':
    main()
