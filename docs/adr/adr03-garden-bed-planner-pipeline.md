# ADR03: Garden Bed Planner Pipeline Strategy

**Author:** Aaron Solomon, Codex
**Date:** 2026-01-03
**Status:** Proposed

## Context

Happy Farm needs a repeatable, deterministic way to plan bed layouts and successions for market-garden production. The project already relies on CSV as the authoritative data source and uses Python scripts in `scripts/` for transforms. A key existing script, `calculate_succession.py`, computes row feet per crop for succession waves and should remain a first-class part of the pipeline.

The goal is a native Python workflow that turns CSV data into reproducible spatial and (later) temporal visualizations, without introducing heavier infrastructure or UI dependencies.

## Decision

Adopt a **CSV → Pandas → Visualization** pipeline with clear separation between input data, spatial assignments, and derived occupancy. The pipeline is script-driven (not notebook-driven) and uses a single configuration source for bed geometry and reserved zones.

### Strategy Overview

```text
CSV source data
    ↓
Pandas transforms (scripts/)
    ↓
Derived spatial grid (bed/block occupancy)
    ↓
Static visualization (PNG)
```

### Data Layers

1) **Crop Plan (input)**
   - Source: `data/plants/vegetable-data-current.csv`
   - Parsed into rows with succession metadata
   - `calculate_succession.py` computes `row_ft_required` per succession wave
   - No spatial meaning at this stage

2) **Bed Assignments (authoritative spatial intent)**
   - Source: new CSV table in `data/plans/` (manual for now)
   - Schema: `bed_id,start_ft,length_ft,crop,variety,wave_id,plant_date,notes`
   - `wave_id` references `data/schedules/succession-schedule.csv`
   - `plant_date` is canonical for temporal alignment
   - Derived fields: `start_block`, `end_block`
   - This is the single source of truth for layout decisions

3) **Occupancy Grid (derived)**
   - Internal DataFrame for rendering and validation
   - Columns: `bed_id, block_idx, status, crop, variety, wave_id, family, water`
   - Status enum: `FLOWER`, `BENEFICIAL`, `CROP`, `EMPTY`
   - Possible future statuses: `RESERVED`, `CONFLICT`
   - Used to detect overlaps and render output

### Contract Shape (Current)

The bed plan and succession schedule are intentionally coupled. The contract
is defined by a shared set of identifiers and required columns. Changes to
either CSV are expected to ripple both endpoints.

**Succession schedule (source of wave definitions)**
- File: `data/schedules/succession-schedule.csv`
- Required columns: `crop`, `variety`, `method`, `plant_date`, `succession_days`, `row_feet`
- Wave identifiers are derived from this table (e.g., in `load_data.py`)

**Bed assignments (source of spatial intent)**
- File: `data/plans/<name>.csv`
- Required columns: `bed_id`, `start_ft`, `length_ft`, `crop`, `variety`, `wave_id`, `plant_date`
- Optional columns: `notes`
- `wave_id` must resolve to a derived wave in the succession schedule
- `plant_date` aligns spatial placement to the schedule

### Script Responsibilities

- `load_data.py`
  - Read crop CSV
  - Normalize columns and infer family
  - Parse succession fields
  - Validate units
  - Parse succession schedule and build wave identifiers

- `build_assignments.py`
  - Read assignment CSV
  - Validate bed bounds and block alignment
  - Compute block ranges and detect overlap
  - Validate `wave_id` against succession schedule
  - Optional validation hooks (future): row-foot reconciliation, water zoning

- `render_grid.py`
  - Build full bed/block grid
  - Apply reserved zones
  - Fill crop blocks and assert no collisions
  - Output derived grid and visualization

### Visualization (Phase 1)

Generate a static spatial grid (PNG):
- x-axis: block index (5 ft blocks)
- y-axis: bed id
- Color by crop family; optional hatch/alpha for water class
- Optional short labels per block

### Configuration

All geometry and reserved zones live in
`data/plans/config/bed-geometry.jsonl`, versioned in repo (not gitignored).
JSONL keeps the structure extensible for future per-bed overrides while
staying line-oriented for diffs.

Example shape (one JSON object per line):

```jsonl
{"schema_version": 1, "bed_count": 12, "bed_length_ft": 80, "block_size_ft": 5}
{"flower_blocks": [0, 15], "beneficial_block": 7}
```

## Non-Goals

- No XLS/Google Sheets export yet
- No UI or drag/drop editor
- No irrigation simulation
- No automatic schedule optimization
- No partial-block placement in v1

## Consequences

### Positive
- Deterministic, scriptable workflow
- Clear separation of data concerns
- Layout decisions trace to a single CSV
- Visualization is reproducible from source data
- Easy to extend to XLS/Sheets or Streamlit later
- Clear contract between bed planning and succession scheduling

### Negative
- Manual effort required to author bed assignments
- Validation burden shifts to scripts
- No interactive editing in early phases
- Contract changes will ripple both scheduling and planning inputs

## Alternatives Considered

### Option 1: Spreadsheet-only Planning
- ✅ Easy editing and sharing
- ❌ Hard to version and reproduce
- ❌ Visual layout generation is manual

### Option 2: Interactive UI First
- ✅ Faster iteration for non-technical users
- ❌ Delays core data pipeline
- ❌ More maintenance overhead

### Option 3: Chosen - Scripted CSV/Pandas Pipeline
- ✅ Reproducible and git-friendly
- ✅ Compatible with existing scripts (incl. `calculate_succession.py`)
- ✅ Scales to additional outputs later
- ❌ Requires command-line workflow discipline

## Open Questions

- How should the bed plan and succession schedule contract be versioned as both evolve?
- Should we support partial-block placement (non-5 ft) later?
- How to encode succession timing for the optional Gantt view?

## Implementation Notes

- Start with a minimal assignment CSV and validate block alignment.
- Keep reserved blocks configurable (flower/beneficial strips).
- Keep `calculate_succession.py` as the authoritative source for row-foot needs.

## References

- `scripts/calculate_succession.py`
- `data/plants/vegetable-data-current.csv`
- `data/schedules/succession-schedule.csv`

---

**Next Steps:**
1. Agree on assignment CSV location and schema
2. Implement `load_data.py`, `build_assignments.py`, `render_grid.py`
3. Produce first `bed_grid.png` and review

## Addendum (2026-01-03)

Implementation has begun. The contract now includes an optional `wave_seq`
field to disambiguate wave identifiers when needed.

**Contract Update**
- Succession schedule: add `wave_seq` column (optional, integer-like)
- Wave identifiers may include sequence: `crop:variety:plant_date:wave_seq`

## Addendum (2026-01-03) - Schedule Water Class

Implementation has begun. The succession schedule contract now includes
`water` so rendering and planning do not need to join crop data at render time.

**Contract Update**
- Succession schedule: add `water` column (required)

## Addendum (2026-01-03) - Beneficial Assignments

Implementation has begun. Bed assignments now support a `status` column to
explicitly mark beneficial strips in the center blocks.

**Contract Update**
- Bed assignments: add `status` column (optional; default `CROP`)
- `status=BENEFICIAL` rows do not require crop/variety/wave_id

## Addendum (2026-01-03) - CSV Schema Comments

CSV header comments for `schema_version` are removed to keep files compatible
with common CSV viewers. Schema versioning remains only in JSONL configs.
