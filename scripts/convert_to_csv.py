#!/usr/bin/env -S uv run python
"""Convert seed-inventory.md to CSV format with detailed planting data."""

import re
import csv
from pathlib import Path

inventory_path = Path(__file__).parent.parent / "data" / "seeds" / "seed-inventory.md"
output_path = Path(__file__).parent.parent / "data" / "seeds" / "seed-inventory.csv"

# CSV columns
fieldnames = [
    'variety_name',
    'company',
    'url',
    'plant_type',        # vegetable, herb, flower
    'crop_group',        # brassicas, root vegetables, etc.
    'season',            # cool, warm, perennial
    'packet_type',       # single, mixed
    'water_needs',       # low, medium, high
    'sow_window',        # e.g., "Aug-Feb" or "Mar-Jun"
    'seeding_method',    # direct, transplant
    'days_to_transplant', # for transplant varieties
    'days_to_maturity',
    'planting_pattern',  # 5-star, box, 3-row, 4-row, 2-row, single-row
    'plants_per_linear_ft',
    'yield_per_plant',
    'harvest_info',
    'notes'
]

rows = []

# Current context trackers
current_plant_type = ""
current_season = ""
current_crop_group = ""
current_water = ""
current_sow_window = ""

with open(inventory_path) as f:
    for line in f:
        line = line.rstrip()

        # Skip empty lines and markdown headers/separators
        if not line or line.startswith('#') or line.startswith('>') or line == '---':
            continue

        # Track plant type (## Vegetables, ## Herbs, ## Flowers)
        if line.startswith('## '):
            current_plant_type = line[3:].strip().lower().rstrip('s')  # "Vegetables" -> "vegetable"
            continue

        # Track season (### Cool Season, ### Warm Season, etc.)
        if line.startswith('### '):
            season_text = line[4:].strip()
            if 'Cool Season' in season_text:
                current_season = 'cool'
            elif 'Warm Season' in season_text:
                current_season = 'warm'
            elif 'Perennial' in season_text or 'Multi-Season' in season_text:
                current_season = 'perennial'
            continue

        # Track crop group and extract water/sow info from group headers
        # Format: "- **Broccoli** *(Water: Medium–High • Sow: Aug–Feb)*"
        crop_match = re.match(r'^- \*\*([^*]+)\*\*(.*)$', line)
        if crop_match:
            current_crop_group = crop_match.group(1).strip()
            metadata = crop_match.group(2)

            # Extract water needs
            water_match = re.search(r'Water:\s*([^•\)]+)', metadata)
            if water_match:
                water_text = water_match.group(1).strip()
                # Normalize to low/medium/high
                if 'High' in water_text:
                    current_water = 'high'
                elif 'Medium' in water_text:
                    current_water = 'medium'
                elif 'Low' in water_text:
                    current_water = 'low'
                else:
                    current_water = ''

            # Extract sow window
            sow_match = re.search(r'Sow:\s*([^•\)]+)', metadata)
            if sow_match:
                current_sow_window = sow_match.group(1).strip()

            continue

        # Parse variety entries
        # Format: "  - [Variety Name](URL) (SDSC/JS) - notes"
        variety_match = re.match(r'^\s+- \[([^\]]+)\]\(([^)]+)\) \((SDSC|JS)\)(.*)$', line)
        if variety_match:
            variety_name = variety_match.group(1).strip()
            url = variety_match.group(2).strip()
            company = variety_match.group(3).strip()
            notes_text = variety_match.group(4).strip()

            # Determine packet type from variety name
            packet_type = 'mixed' if any(word in variety_name.lower() for word in ['mix', 'blend', 'collection', 'set']) else 'single'

            # Parse notes for additional info
            notes = notes_text.lstrip('- ').strip()

            row = {
                'variety_name': variety_name,
                'company': company,
                'url': url,
                'plant_type': current_plant_type,
                'crop_group': current_crop_group,
                'season': current_season,
                'packet_type': packet_type,
                'water_needs': current_water,
                'sow_window': current_sow_window,
                'seeding_method': '',  # To be filled
                'days_to_transplant': '',
                'days_to_maturity': '',
                'planting_pattern': '',
                'plants_per_linear_ft': '',
                'yield_per_plant': '',
                'harvest_info': '',
                'notes': notes
            }

            rows.append(row)

# Write CSV
with open(output_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✓ Converted {len(rows)} varieties to CSV")
print(f"  Output: {output_path}")
print(f"\nEmpty fields to populate:")
print(f"  - seeding_method (direct/transplant)")
print(f"  - days_to_transplant")
print(f"  - days_to_maturity")
print(f"  - planting_pattern (5-star, box, 3-row, 4-row, 2-row, single-row)")
print(f"  - plants_per_linear_ft")
print(f"  - yield_per_plant")
print(f"  - harvest_info")
