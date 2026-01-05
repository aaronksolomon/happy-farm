# ADR03.02: Render Grid v1 (SVG-First) Strategy

**Author:** Aaron Solomon, Codex
**Date:** 2026-01-03
**Status:** Proposed

## Context

The v0 renderer proves the data pipeline but has limitations:

- Labels are abbreviated despite available space.
- Overlaps are surfaced but not richly explained.
- Repeated contiguous crops still render as individual cells.
- Beneficial/perennial strips are visualized without labels.
- Matplotlib limits typography/layout control for future polish.

We want v1 rendering to be crisp, deterministic, and future-friendly.

## Decision

Adopt **SVG-first rendering** as the canonical v1 output and split the pipeline
into two phases:

1. **Layout / Scene Graph Build** (pure data)
2. **Render Backend** (SVG → optional PNG)

The scene graph consists of primitives: `Rect`, `TextBlock`, `Marker`.
No backend-specific logic is allowed in layout.

Primary output: `exports/bed-grid.svg`  
Secondary output: `exports/bed-grid.png` derived by rasterizing SVG.

### Rationale

- SVG supports merged regions, crisp borders, and multi-line labels natively.
- SVG is the golden artifact for QA/diffing.
- Deterministic text + geometry is diffable for QA and review.
- Keeps v2 paths open (web, print, hi-res) without reworking layout logic.

## Goals (v1)

- Full crop name on line 1; full variety name on line 2.
- Merge contiguous blocks for identical crop+variety+wave_id into a single
  rectangle (spreadsheet merge).
- Conflict cells show `!` plus a compact list of overlapping items.
- Render titles for reserved strips (FLOWER / BENEFICIAL).
- Maintain deterministic output and CSV-driven workflow.

## Renderer Options (Considered)

### Option A: Matplotlib (extend current)

**Pros:** already in stack; fast to implement; direct PNG export.  
**Cons:** limited font/layout control; complex text fitting; manual legend/titles.

### Option B: Bokeh (interactive-first, export PNG)

**Pros:** flexible labeling, hover tooltips; good for future interactivity.  
**Cons:** PNG export requires extra dependencies; more boilerplate.

### Option C: Plotly (interactive-first, export PNG)

**Pros:** rich styling, good annotations; strong ecosystem.  
**Cons:** PNG export needs kaleido; heavier runtime.

### Option D: Pillow (draw directly)

**Pros:** full control of layout, fonts, and merged regions.  
**Cons:** more custom code; no built-in axes/legend.

**Decision:** SVG-first with a scene-graph layout step and rasterization via
CairoSVG for PNG parity.

## Data & Labeling Changes

### Full Labels

Use two-line labels:

- Line 1: full crop name
- Line 2: full variety name

If text overflow occurs, shrink font size per-cell or truncate with ellipsis.
Add a `label_wrap` utility to fit text within merged block width/height.

### Merged Blocks

Compute runs of identical `(bed_id, crop, variety, wave_id, status)` across
adjacent block indices. Render one rectangle per run with a single label.

### Conflict Annotations

For conflicts, render:

- Background: red overlay
- Label: `!` + stacked crop/variety pairs, e.g.:

  ```
  !
  Arugula / Wild Arugula
  Lettuce / Allstar
  ```

Use smaller font for conflict text; cap at N lines and append `+N more`.

### Reserved Strip Labels

Add configurable titles for reserved zones:

- `FLOWER` strip label: "FLOWERS / PERENNIALS"
- `BENEFICIAL` strip label: "BENEFICIAL STRIP"

Source: `bed-geometry.jsonl` could add:

```jsonl
{"reserved_labels": {"FLOWER": "FLOWERS / PERENNIALS", "BENEFICIAL": "BENEFICIAL STRIP"}}
```

## Proposed v1 Inputs/Outputs

Inputs (unchanged):

- `data/plans/bed-assignments.csv`
- `data/schedules/succession-schedule.csv`
- `data/plans/config/bed-geometry.jsonl`
- `data/plans/config/bed-visuals.jsonl`

Outputs:

- `data/plans/bed-grid.csv` (add run_id + conflict_details)
- `exports/bed-grid.svg` (canonical)
- `exports/bed-grid.png` (derived from SVG)

## Implementation Notes

- Add a pre-render pass to build merged runs and conflict summaries.
- Store `conflict_details` in `bed-grid.csv` for debugging and QA.
- Keep label styling (font size, line spacing) in `bed-visuals.jsonl`.
- Use CairoSVG to rasterize `bed-grid.svg` into PNG for parity.
- If text fit becomes brittle, consider Pango/Cairo text measurement using
  the same scene graph.

## Open Questions

- Do we want a separate legend for water class vs family?
- Should reserved strip labels render once per bed or once per strip run?
- Should `bed-grid.csv` include merged run widths for downstream exports?
- Do we want a CLI flag to skip PNG rasterization?

## References

- `docs/adr/adr03.1-render-grid-visualization.md`
