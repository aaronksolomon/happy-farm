# Grid Builder Usage Guide

**Happy Farm Garden Bed Planner**

## Overview

The grid builder generates visual bed layouts from CSV planning data. It produces a spatial grid showing crop assignments across beds and 5-foot blocks, with color-coding by plant family and water requirements.

**Pipeline:** CSV data → validation → spatial grid → SVG/PNG visualization

## Quick Start

### 1. Generate Succession Schedule

Calculate row-feet requirements and planting dates:

```bash
uv run scripts/calculate_succession_planting.py \
  --plant-data data/plants/vegetable-data-current.csv \
  --config data/schedules/succession-plan-config.csv \
  --output data/schedules/succession-schedule.csv
```

**Inputs:**
- `vegetable-data-current.csv` - crop data with spacing, yield, maturity days
- `succession-plan-config.csv` - target yields and stagger offsets per variety

**Output:** `succession-schedule.csv` with `wave_id`, `plant_date`, `row_feet`, `water`, `plant_type`

### 2. Create Bed Assignments

Manually create or edit `data/plans/bed-assignments.csv`:

```csv
bed_id,start_ft,length_ft,status,crop,variety,wave_id,plant_date,notes
1,0,15,CROP,Lettuce (Mixed),Wild Arugula,Lettuce (Mixed):Wild Arugula:2026-02-14,2026-02-14,
1,35,5,BENEFICIAL,,,,,Center beneficial strip
```

**Required columns:** `bed_id`, `start_ft`, `length_ft`, `status`
**For crops:** `crop`, `variety`, `wave_id`, `plant_date`
**For beneficial strips:** `status=BENEFICIAL` (crop fields optional)

**Validation rules:**
- `start_ft` and `length_ft` must align to 5 ft blocks
- No overlapping assignments per bed
- `wave_id` must exist in succession schedule

### 3. Render Grid Visualization

Generate spatial grid and visualizations:

```bash
uv run scripts/render_grid.py \
  --assignments data/plans/bed-assignments.csv \
  --schedule data/schedules/succession-schedule.csv \
  --geometry data/plans/config/bed-geometry.jsonl \
  --visuals data/plans/config/bed-visuals.jsonl \
  --output-csv data/plans/bed-grid.csv \
  --output-svg exports/bed-grid.svg \
  --output-png exports/bed-grid.png
```

**Outputs:**
- `bed-grid.csv` - derived occupancy grid with status, family, water per block
- `bed-grid.svg` - vector visualization (canonical)
- `bed-grid.png` - rasterized version

**Skip PNG generation:**
```bash
uv run scripts/render_grid.py --skip-png
```

## Configuration Files

### Bed Geometry (`data/plans/config/bed-geometry.jsonl`)

Defines farm layout and reserved zones:

```jsonl
{"schema_version": 1, "bed_count": 12, "bed_length_ft": 80, "block_size_ft": 5}
{"flower_blocks": [0, 15], "beneficial_block": null}
{"reserved_labels": {"FLOWER": "P/B", "BENEFICIAL": "BENE"}}
```

**Key fields:**
- `bed_count` - total number of beds
- `bed_length_ft` - length of each bed (must be divisible by `block_size_ft`)
- `block_size_ft` - spatial unit (typically 5 ft)
- `flower_blocks` - block indices reserved for flowers (list)
- `beneficial_block` - single block index for beneficial strip (use `null` to disable)

### Visual Styling (`data/plans/config/bed-visuals.jsonl`)

Controls rendering appearance:

```jsonl
{"schema_version": 1, "label_mode": "full", "show_legend": true}
{"family_colors": {"Brassica": "#6A9A1F", "Root Vegetable": "#D97A1E", "Baby Greens": "#2E8B57"}}
{"water_alpha": {"high": 1.0, "medium": 0.7, "low": 0.4}}
{"water_borders": {"high": "solid", "medium": "dashed", "low": "dotted"}}
{"cell_size": 40, "font_family": "Helvetica", "label_font_size": 6, "conflict_font_size": 5, "reserved_font_size": 6, "conflict_max_lines": 4, "row_label_width": 40, "notes_col_width_ratio": 0.33}
```

**Styling parameters:**
- `cell_size` - pixel size per block (default 40)
- `family_colors` - hex colors by plant family
- `water_alpha` - opacity by water requirement (0.0-1.0)
- `water_borders` - border style: `solid`, `dashed`, or `dotted`

## Grid Visualization

**Layout:**
- Rows represent beds (labeled 1-N)
- Columns represent 5 ft blocks (0-15 for 80 ft beds)
- Notes column on right shows per-bed annotations (from assignments)

**Cell colors:**
- Fill color = plant family (from `family_colors`)
- Opacity = water requirement (from `water_alpha`)
- Border style = water requirement (from `water_borders`)

**Special statuses:**
- `CROP` - standard crop assignment (2-line label: crop + variety)
- `BENEFICIAL` - beneficial insect strip (via `status=BENEFICIAL` rows)
- `FLOWER` - flower/perennial blocks (labeled from `reserved_labels`)
- `EMPTY` - unassigned blocks (light gray)
- `CONFLICT` - overlapping assignments (red, shows all conflicts)

**Merged blocks:** Contiguous blocks with identical crop/variety/wave_id are merged into single rectangles with one label.

## Data Flow

```
1. Plant Data (yields, spacing, maturity)
     ↓
2. Succession Config (targets, stagger)
     ↓
3. calculate_succession_planting.py
     ↓
4. Succession Schedule (wave_id, row_feet, water)
     ↓
5. Manual Bed Assignments (spatial layout)
     ↓
6. build_assignments.py (validation)
     ↓
7. render_grid.py (occupancy + visualization)
     ↓
8. Grid CSV + SVG + PNG
```

## Common Tasks

**Validate assignments without rendering:**
```bash
uv run scripts/build_assignments.py \
  --assignments data/plans/bed-assignments.csv \
  --schedule data/schedules/succession-schedule.csv \
  --config data/plans/config/bed-geometry.jsonl
```

**Change visual theme:** Edit `bed-visuals.jsonl` and re-run `render_grid.py`

**Add reserved zones:** Update `flower_blocks` in `bed-geometry.jsonl`

**Handle conflicts:** Grid shows overlaps in red. Fix by adjusting `start_ft`/`length_ft` in assignments CSV.

## Troubleshooting

**Error: "bed_id out of bounds"**
- Check `bed_count` in `bed-geometry.jsonl` matches assignment range

**Error: "start_ft must align to block size"**
- Ensure `start_ft` and `length_ft` are multiples of `block_size_ft` (typically 5)

**Error: "overlap detected in bed X"**
- Check assignments in bed X for overlapping `start_ft` to `start_ft + length_ft` ranges

**Error: "Unknown wave_id values"**
- Ensure `wave_id` in assignments matches entries in succession schedule
- Wave IDs format: `crop:variety:plant_date[:wave_seq]`

**Warning: PNG rasterization failed**
- Install CairoSVG: `uv pip install cairosvg`
- Or use `--skip-png` flag to generate SVG only

## File Reference

| Path | Purpose |
|------|---------|
| `data/plants/vegetable-data-current.csv` | Crop reference data |
| `data/schedules/succession-plan-config.csv` | Yield targets & stagger |
| `data/schedules/succession-schedule.csv` | Generated planting schedule |
| `data/plans/bed-assignments.csv` | Manual spatial assignments |
| `data/plans/config/bed-geometry.jsonl` | Farm layout config |
| `data/plans/config/bed-visuals.jsonl` | Rendering style config |
| `data/plans/bed-grid.csv` | Derived occupancy grid |
| `exports/bed-grid.svg` | Vector visualization |
| `exports/bed-grid.png` | Raster visualization |

## References

- [ADR03: Garden Bed Planner Pipeline](`docs/adr/adr03-garden-bed-planner-pipeline.md`)
- [ADR03.1: Render Grid Visualization](`docs/adr/adr03.1-render-grid-visualization.md`)
- [ADR03.02: Render Grid v1 (SVG-First)](`docs/adr/adr03.02-render-grid-v1-svg-first.md`)
