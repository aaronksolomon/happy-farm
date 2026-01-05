# ADR03.1: Render Grid Visualization Strategy

**Author:** Paul Hapman, Codex
**Date:** 2026-01-03
**Status:** Proposed

## Context

ADR03 defines the CSV → Pandas → Visualization pipeline but does not specify
rendering details or how visual styling is configured. We now need a concrete
rendering strategy for a spatial grid view and a place to encode graphical
properties (colors, labels, legends) in a way that can evolve with the data.

Key requirements:
- Deterministic rendering from data sources
- Clear spatial representation of beds and 5 ft blocks
- Encoding crop family and optional water class
- Ability to adjust styling without touching code

## Decision

Introduce a dedicated `render_grid.py` script and a lightweight visualization
schema that lives alongside the bed planning config. The rendering layer reads
the occupancy grid and applies presentation rules from a JSONL config file.

### Rendering Output (Phase 1)

Generate a static PNG:
- x-axis: block index (0..15 for 80 ft @ 5 ft blocks)
- y-axis: bed_id (1..N_BEDS)
- Each block drawn as a rectangle
- Fill color by family (primary signal)
- Optional hatch/alpha for water class (secondary signal)
- Required short crop label per block (e.g., "CARR.-BOL.")

### Visualization Config (Proposed)

Add `data/plans/config/bed-visuals.jsonl`:

```jsonl
{"schema_version": 1, "label_mode": "crop_code", "show_legend": true}
{"family_colors": {"Brassica": "#6A9A1F", "Root Vegetable": "#D97A1E", "Baby Greens": "#2E8B57"}}
{"water_hatches": {"high": "///", "medium": "..", "low": "xx"}}
{"water_alpha": {"high": 1.0, "medium": 0.7, "low": 0.4}}
{"water_borders": {"high": "solid", "medium": "dashed", "low": "dotted"}}
```

This file is versioned and read by `render_grid.py`. It is intentionally
separate from geometry (`bed-geometry.jsonl`) to keep spatial and styling
concerns decoupled.

### Crop Code Lookup (Optional)

Add `data/plans/config/crop-codes.jsonl` for human-curated short labels:

```jsonl
{"schema_version": 1}
{"Carrots": "CARR", "Broccoli": "BROC", "Lettuce (Mixed)": "LETT", "Arugula": "ARUG"}
{"Spinach": "SPIN", "Chicory": "CHIC", "Radishes": "RAD", "Beets": "BEET"}
```

Crop codes are **manually maintained** to optimize for quick visual recognition
(e.g., "CARR" not "CAR", "BROC" not "BRO"). If a crop lacks a code entry,
`render_grid.py` falls back to auto-truncation and warns.

Labels are built as: `{crop_code}.-{variety_abbrev}.` (e.g., "CARR.-BOL.")

### Data Inputs

`render_grid.py` will consume:
- `data/plans/bed-assignments.csv`
- `data/schedules/succession-schedule.csv` (includes family + water)
- `data/plans/config/bed-geometry.jsonl`
- `data/plans/config/bed-visuals.jsonl`
- `data/plans/config/crop-codes.jsonl` (optional; for human-curated labels)

### Data Outputs

- `data/plans/bed-grid.csv` (derived occupancy grid)
- `exports/bed-grid.png`

## Alternatives Considered

### Option 1: Hard-code visual settings in Python
- ✅ Fast to ship
- ❌ Styling changes require code edits
- ❌ Hard to diff/track tweaks

### Option 2: Single combined config file for geometry + visuals
- ✅ Fewer files
- ❌ Conflates spatial logic with styling rules

### Option 3: Chosen - Separate visuals JSONL
- ✅ Keeps concerns separate
- ✅ Easy to diff and version
- ✅ Supports future theming without code edits

## Consequences

### Positive
- Styling becomes data-driven and reproducible
- Visualization can evolve without refactoring data logic
- Lays groundwork for temporal (Gantt) view later

### Negative
- Adds one more config file to maintain
- Requires validation of a second schema

## Open Questions

- Should `bed-grid.csv` include a `color` or `label` column for convenience?
- Do we want multiple named themes (e.g., print vs screen)?
- Should variety abbreviation also be human-curated, or is auto-truncation sufficient?

## Implementation Notes

- `render_grid.py` should validate JSONL `schema_version` and required keys.
- If a crop family is missing a color, fall back to a neutral color and warn.
- If water class is missing, render without hatch.
- Crop labels: use `crop-codes.jsonl` if present; otherwise auto-generate and warn.
- Auto crop code rule: single-word crops → first 4 letters (e.g., "Carrots" → "CARR");
  multi-word crops → first 3 letters of word 1 + first 2 of word 2 (e.g.,
  "Lettuce (Mixed)" → "LETMI").
- Variety abbreviation: first 3 letters (e.g., "Bolero" → "BOL").
- Prefer `water_alpha` for small block readability; `water_hatches` or
  `water_borders` can be enabled when larger blocks or print output is used.
- `bed-grid.csv` schema (minimum): `bed_id`, `block_idx`, `status`, `crop`,
  `variety`, `wave_id`, `family`, `water`.
- Optional debug columns: `label`, `color`, `alpha`, `border_style`.
- PNG output naming should support a plan name or timestamp, e.g.
  `exports/bed-grid-2026-01-03.png` or `exports/bed-assignments-spring-2026.png`.

## References

- `docs/adr/adr03-garden-bed-planner-pipeline.md`
- `data/plans/config/bed-geometry.jsonl`
