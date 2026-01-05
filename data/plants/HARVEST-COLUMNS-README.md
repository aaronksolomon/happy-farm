# Harvest Columns Addition - Vegetable Data

## Overview

Created a new version of the vegetable data CSV with additional harvest-related columns and data type descriptions.

## Files

- **Original**: `vegetable-data-current.csv` (preserved, unchanged)
- **New**: `vegetable-data-with-harvest.csv`

## Changes Made

### 1. Added Data Type Description Row

Row 2 now contains descriptions for each column, explaining the data type and expected values.

Example:
```
Column: harvest_type
Description: cut_and_come_again, single_harvest, multi-pick, or storage
```

### 2. Added 8 New Harvest Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `harvest_type` | string | cut_and_come_again, single_harvest, multi-pick, or storage |
| `yield_type` | string | per_plant or per_area |
| `lbs_per_area_per_harvest_lo` | float | minimum pounds per square foot per harvest |
| `lbs_per_area_per_harvest_hi` | float | maximum pounds per square foot per harvest |
| `lbs_per_plant_per_harvest_lo` | float | minimum pounds per individual plant per harvest |
| `lbs_per_plant_per_harvest_hi` | float | maximum pounds per individual plant per harvest |
| `harvest_interval_planned` | int | desired days between successive harvests |
| `regrowth_period` | int | days required for plant/area to regrow before reharvest |

## Structure

- **Row 1**: Column headers (46 total columns)
- **Row 2**: Data type descriptions for each column
- **Rows 3-100**: Plant data (98 varieties)

## Next Steps

1. Populate the new harvest columns with actual data
2. Update computation scripts to use these new fields
3. Consider creating helper functions to calculate:
   - Total seasonal yield based on harvest intervals
   - Succession planting schedules using regrowth periods
   - Optimal harvest timing based on yield types

## Script

The transformation was performed by `scripts/add_harvest_columns.py`, which can be re-run if needed.
