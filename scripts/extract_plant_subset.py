#!/usr/bin/env -S uv run python
"""
Extract specific varieties and columns from vegetable-data.csv

This script allows flexible subsetting of plant data by variety and columns.
Configuration can be provided via command-line arguments or by modifying
the default config in this file.
"""

import csv
import argparse
from pathlib import Path
from typing import List, Dict, Set


def load_csv(filepath: Path) -> tuple[List[str], List[Dict]]:
    """Load CSV file and return headers and data rows."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def filter_rows(rows: List[Dict], filters: List[Dict]) -> List[Dict]:
    """
    Filter rows based on criteria.

    filters: List of dicts with keys like {'crop': 'Tomatoes', 'variety': 'Jolene F1'}
             Can use 'supplier': 'JS' to get all Johnny's Seeds varieties of a crop
    """
    filtered = []

    for filter_spec in filters:
        for row in rows:
            match = True
            for key, value in filter_spec.items():
                if row.get(key, '').strip() != value.strip():
                    match = False
                    break
            if match and row not in filtered:
                filtered.append(row)

    return filtered


def select_columns(rows: List[Dict], columns: List[str]) -> List[Dict]:
    """Select only specified columns from rows."""
    return [{col: row.get(col, '') for col in columns} for row in rows]


def write_csv(filepath: Path, rows: List[Dict], columns: List[str]):
    """Write filtered data to CSV file."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description='Extract specific varieties and columns from vegetable data CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default configuration (edit script for custom defaults)
  python extract_plant_subset.py

  # Specify custom input/output files
  python extract_plant_subset.py -i data/plants/vegetable-data.csv -o output.csv
        """
    )

    parser.add_argument('-i', '--input',
                       default='data/plants/vegetable-data.csv',
                       help='Input CSV file (default: data/plants/vegetable-data.csv)')
    parser.add_argument('-o', '--output',
                       default='data/plants/selected-varieties.csv',
                       help='Output CSV file (default: data/plants/selected-varieties.csv)')

    args = parser.parse_args()

    # === CONFIGURATION ===
    # Define which varieties to extract
    # Each dict specifies criteria that all must match for a row to be selected
    variety_filters = [
        # NEW varieties to add to early2026-varieties.csv
        # 2 Peppers
        {'crop': 'Peppers (Sweet)', 'variety': 'Goddess F1 Banana'},
        {'crop': 'Peppers (Sweet)', 'variety': 'Cornito Pepper Mix Organic F1'},

        # 4 Tomatoes
        {'crop': 'Tomatoes', 'variety': 'Galahad Organic F1'},
        {'crop': 'Tomatoes', 'variety': 'Sun Gold F1'},
        {'crop': 'Tomatoes', 'variety': 'Jasper Organic F1'},
        {'crop': 'Tomatoes', 'variety': 'Supersweet 100 F1'},

        # 1 Turnip
        {'crop': 'Turnips', 'variety': 'Hakurei F1'},
    ]

    # Define which columns to extract
    selected_columns = [
        'crop',
        'variety',
        'last_order',
        'lo_yield',
        'hi_yield',
        'notes',
        'url',
        'web_days_to_maturity',
        'web_final_spacing',
        'web_seeds_per_packet',
        'js_growing_notes',
    ]
    # === END CONFIGURATION ===

    # Set up paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    input_path = project_root / args.input
    output_path = project_root / args.output

    # Load data
    print(f"Loading data from {input_path}...")
    headers, all_rows = load_csv(input_path)
    print(f"Loaded {len(all_rows)} rows with {len(headers)} columns")

    # Filter rows
    print(f"\nFiltering rows based on {len(variety_filters)} criteria...")
    filtered_rows = filter_rows(all_rows, variety_filters)
    print(f"Found {len(filtered_rows)} matching rows:")
    for row in filtered_rows:
        print(f"  - {row.get('crop', 'N/A')}: {row.get('variety', 'N/A')} ({row.get('supplier', 'N/A')})")

    # Select columns
    print(f"\nSelecting {len(selected_columns)} columns...")
    subset = select_columns(filtered_rows, selected_columns)

    # Verify all selected columns exist
    missing_cols = set(selected_columns) - set(headers)
    if missing_cols:
        print(f"\nWarning: These columns don't exist in input: {missing_cols}")

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output_path, subset, selected_columns)
    print(f"\n✓ Wrote {len(subset)} rows to {output_path}")
    print(f"  Columns: {', '.join(selected_columns)}")


if __name__ == '__main__':
    main()
