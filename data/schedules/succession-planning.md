# Succession Planning System

This document describes the succession planting workflow, from yield targets through to nursery orders and bed grid visualization.

## Overview

The succession planning system calculates how many plants to grow and when to plant them based on weekly harvest targets. It accounts for:

- Germination and field survival rates (95% each)
- Days to maturity and succession intervals
- Planting patterns and in-row spacing
- Nursery lead times (35 days for transplants)

## Data Flow

```
vegetable-data.csv          succession-plan-config.csv
        |                            |
        +------------+---------------+
                     |
                     v
    scripts/calculate_succession_planting.py
                     |
                     v
          succession-schedule.csv
                     |
        +------------+---------------+
        |                            |
        v                            v
scripts/generate_seedlings_order.py  scripts/render_grid.py
        |                            |
        v                            v
  seedlings-order.csv          exports/bed-grid.svg
                               exports/bed-grid.png
```

## Input Files

### `succession-plan-config.csv`

Defines what crops to grow and weekly yield targets:

| Column | Description |
|--------|-------------|
| `crop` | Crop name (must match vegetable-data.csv) |
| `variety` | Variety name (must match vegetable-data.csv) |
| `target_lbs_week` | Target harvest in pounds per week |
| `succession_days_override` | Override default succession interval |
| `stagger_offset_days` | Offset planting date to stagger varieties |
| `notes` | Supplier info, grouping notes |

### `vegetable-data.csv` (in `data/plants/`)

Master plant database with spacing, yield, and maturity data. Key columns used:

- `count_ft` - Plants per linear foot (computed from rows/pattern + in_row_spacing_ft)
- `yield_per_harvest_lo/hi` - Yield per plant in pounds
- `yield_type` - Whether yield is per plant or per sqft
- `web_days_to_maturity` - Days from planting to first harvest
- `sdsc_succession` - Recommended succession planting interval
- `method` - `transplant` or `direct_sow`

## Scripts

### `calculate_succession_planting.py`

Generates the succession schedule from plant data and yield targets.

```bash
uv run scripts/calculate_succession_planting.py \
  --plant-data data/plants/vegetable-data.csv \
  --config data/schedules/succession-plan-config.csv \
  --output data/schedules/succession-schedule.csv
```

**Key calculations:**

1. **Plants needed** = (target_lbs_week * harvest_weeks_per_planting) / avg_yield / survival_rates
2. **Row feet** = plants_needed / plants_per_linear_foot
3. **Order date** = plant_date - 35 days (for transplants)

Use `--ignore-stagger-offset` to generate a schedule without variety staggering (all start on initial planting date).

### `generate_seedlings_order.py`

Filters the succession schedule for transplants and rounds quantities to available flat sizes.

```bash
uv run scripts/generate_seedlings_order.py \
  --schedule data/schedules/succession-schedule.csv \
  --output data/schedules/seedlings-order.csv
```

**Tray sizes:** 64 (half tray) or 128 (full tray) from Sage Hill nursery. Any multiple of 64 is valid.

## Output Files

### `succession-schedule.csv`

Full schedule with all calculated values:

| Column | Description |
|--------|-------------|
| `plant_type` | Category (Brassica, Root Vegetable, etc.) |
| `plant_date` | When to plant in field |
| `first_harvest_date` | Expected first harvest |
| `plant_count_or_sqft` | Number of plants (or sqft for broadcast crops) |
| `row_feet` | Linear bed feet needed |
| `succession_days` | Days between succession plantings |
| `harvest_weeks_per_planting` | How many weeks one planting sustains |

### `succession-schedule-offsets.csv`

Same as above but with `stagger_offset_days` applied from config.

### `seedlings-order.csv`

Simplified order sheet for nursery:

| Column | Description |
|--------|-------------|
| `target_quantity` | Calculated plants needed |
| `flat_quantity` | Rounded to available flat size |
| `seed_date` | When nursery should seed (plant_date - 28 days) |
| `expected_lbs_week` | Projected yield based on flat_quantity |

## Bed Grid Visualization

### `render_grid.py`

Generates visual bed occupancy grid from bed assignments and succession schedule.

```bash
uv run scripts/render_grid.py \
  --assignments data/plans/bed-assignments.csv \
  --schedule data/schedules/succession-schedule.csv \
  --geometry data/plans/config/bed-geometry.jsonl \
  --visuals data/plans/config/bed-visuals.jsonl
```

**Outputs:**
- `data/plans/bed-grid.csv` - Grid data with cell status, colors
- `exports/bed-grid.svg` - Visual SVG grid
- `exports/bed-grid.png` - Rasterized PNG (requires cairosvg)

### Configuration Files

**`bed-geometry.jsonl`** - Physical bed layout:
```json
{"bed_count": 12, "bed_length_ft": 80, "block_size_ft": 5}
{"flower_blocks": [0, 15], "beneficial_block": null}
```

**`bed-visuals.jsonl`** - Colors and styling:
```json
{"family_colors": {"Brassica": "#6A9A1F", "Root Vegetable": "#D97A1E"}}
{"water_alpha": {"high": 1.0, "medium": 0.7, "low": 0.4}}
```

---

## Notes

### Tray Quantity Rounding

Orders are rounded up to multiples of 64 (Sage Hill's half-tray size). This can cause significant overproduction when target quantities are low:

| Target | Rounds to | Overage |
|-------:|----------:|--------:|
| 22 | 64 | +191% |
| 33 | 64 | +94% |
| 66 | 128 | +94% |
| 142 | 192 | +35% |

To minimize waste, consider:
- Adjusting `target_lbs_week` to align with 64-plant increments
- Extending succession intervals for crops that round up significantly
- Accepting surplus for donation or market sales
