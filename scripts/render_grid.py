#!/usr/bin/env -S uv run python
"""Render a bed/block occupancy grid to CSV, SVG, and PNG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import pandas as pd

from scripts.build_assignments import build_assignments
from scripts.io.schema import ensure_jsonl_schema
from scripts.io.waves import apply_wave_id


DEFAULT_STATUS_COLORS = {
    "EMPTY": "#F2F2F2",
    "FLOWER": "#E6A8D7",
    "BENEFICIAL": "#B3D9FF",
    "CROP": "#CCCCCC",
    "CONFLICT": "#E63946",
}


def load_jsonl_config(path: Path, schema_version: int) -> dict:
    ensure_jsonl_schema(path, schema_version)
    config: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        obj = json.loads(stripped)
        config.update(obj)
    return config


def _reserved_label(status: str, reserved_labels: dict[str, str]) -> str:
    return reserved_labels.get(status, status)


def fit_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return text[: max_chars - 3] + "..."


def _line_capacity(font_size: int, width_px: float) -> int:
    # Rough width estimate: average character ~0.6 * font_size
    return max(1, int(width_px / (font_size * 0.6)))


def wrap_text(text: str, max_chars: int, max_lines: int) -> list[str]:
    if max_chars <= 0 or max_lines <= 0:
        return []
    words = text.split()
    if not words:
        return [fit_text(text, max_chars)]

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if lines and len(lines) == max_lines and " ".join(words).strip() != " ".join(lines).strip():
        lines[-1] = fit_text(lines[-1], max_chars)
    return lines


def build_crop_label_lines(
    crop: str,
    variety: str,
    width_px: float,
    font_size: int,
) -> list[str]:
    max_chars = _line_capacity(font_size, width_px)
    crop_lines = wrap_text(crop, max_chars, 1)
    variety_lines = wrap_text(variety, max_chars, 1)
    return [crop_lines[0] if crop_lines else "", variety_lines[0] if variety_lines else ""]


def build_conflict_label_lines(
    details: list[str],
    width_px: float,
    font_size: int,
    max_lines: int,
) -> list[str]:
    max_chars = _line_capacity(font_size, width_px)
    lines = ["!"]
    available = max_lines - 1
    truncated = details[:available]
    for item in truncated:
        lines.append(fit_text(item, max_chars))
    if len(details) > available:
        lines.append("+" + str(len(details) - available) + " more")
    return lines


def _svg_text(
    x: float,
    y: float,
    lines: list[str],
    font_size: int,
    font_family: str,
    fill: str,
) -> str:
    if not lines:
        return ""
    line_height = font_size * 1.2
    total_height = line_height * len(lines)
    start_y = y - total_height / 2 + font_size
    parts = [
        f'<text x="{x}" y="{start_y}" text-anchor="middle" '
        f'font-size="{font_size}" font-family="{html.escape(font_family)}" '
        f'fill="{fill}">'
    ]
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else line_height
        parts.append(
            f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>'
        )
    parts.append("</text>")
    return "".join(parts)


def render_grid(
    assignments_path: Path,
    schedule_path: Path,
    geometry_path: Path,
    visuals_path: Path,
    output_csv: Path,
    output_svg: Path,
    output_png: Path | None,
    schema_version: int,
) -> pd.DataFrame:
    geometry = load_jsonl_config(geometry_path, schema_version)
    visuals = load_jsonl_config(visuals_path, schema_version)

    bed_count = int(geometry["bed_count"])
    bed_length_ft = int(geometry["bed_length_ft"])
    block_size_ft = int(geometry["block_size_ft"])
    if bed_length_ft % block_size_ft != 0:
        raise ValueError("bed_length_ft must be divisible by block_size_ft")

    blocks_per_bed = bed_length_ft // block_size_ft
    flower_blocks = geometry.get("flower_blocks", [])
    beneficial_block = geometry.get("beneficial_block")
    reserved_labels = geometry.get("reserved_labels", {})

    df_assignments = build_assignments(
        assignments_path,
        schedule_path,
        geometry_path,
        schema_version,
    )

    df_schedule = pd.read_csv(schedule_path, comment="#")
    df_schedule = apply_wave_id(df_schedule)
    schedule_lookup = df_schedule[["wave_id", "plant_type", "water"]].rename(
        columns={"plant_type": "family"}
    )
    df_assignments = df_assignments.merge(schedule_lookup, on="wave_id", how="left")
    df_assignments["status"] = df_assignments["status"].fillna("CROP").str.upper()

    crop_rows = df_assignments["status"] != "BENEFICIAL"
    if df_assignments.loc[crop_rows, "family"].isna().any():
        raise ValueError("Missing family data for some crop wave_id values")

    bed_notes = (
        df_assignments.groupby("bed_id")["notes"]
        .apply(lambda s: "; ".join(sorted({v for v in s if isinstance(v, str) and v})))
        .to_dict()
    )

    cell_items: dict[tuple[int, int], list[dict]] = {}
    for bed_id in range(1, bed_count + 1):
        for block_idx in range(blocks_per_bed):
            items = []
            if block_idx in flower_blocks:
                items.append({"kind": "RESERVED", "status": "FLOWER"})
            if beneficial_block is not None and block_idx == beneficial_block:
                items.append({"kind": "RESERVED", "status": "BENEFICIAL"})
            cell_items[(bed_id, block_idx)] = items

    for _, row in df_assignments.iterrows():
        bed_id = int(row["bed_id"])
        for block_idx in range(int(row["start_block"]), int(row["end_block"])):
            if row["status"] == "BENEFICIAL":
                cell_items[(bed_id, block_idx)].append(
                    {"kind": "RESERVED", "status": "BENEFICIAL"}
                )
                continue
            cell_items[(bed_id, block_idx)].append(
                {
                    "kind": "CROP",
                    "status": "CROP",
                    "crop": row["crop"],
                    "variety": row["variety"],
                    "wave_id": row["wave_id"],
                    "family": row["family"],
                    "water": row["water"],
                    "notes": row.get("notes", ""),
                }
            )

    grid_rows = []
    for (bed_id, block_idx), items in cell_items.items():
        status = "EMPTY"
        crop = variety = wave_id = family = water = notes = ""
        conflict_details: list[str] = []

        if len(items) == 1:
            item = items[0]
            if item["kind"] == "RESERVED":
                status = item["status"]
            else:
                status = "CROP"
                crop = item["crop"]
                variety = item["variety"]
                wave_id = item["wave_id"]
                family = item["family"]
                water = item["water"]
                notes = item.get("notes", "")
        elif len(items) > 1:
            status = "CONFLICT"
            for item in items:
                if item["kind"] == "RESERVED":
                    conflict_details.append(_reserved_label(item["status"], reserved_labels))
                else:
                    conflict_details.append(f"{item['crop']} / {item['variety']}")

        grid_rows.append(
            {
                "bed_id": bed_id,
                "block_idx": block_idx,
                "status": status,
                "crop": crop,
                "variety": variety,
                "wave_id": wave_id,
                "family": family,
                "water": water,
                "notes": notes,
                "conflict_details": " | ".join(conflict_details),
            }
        )

    grid = pd.DataFrame(grid_rows)

    family_colors = visuals.get("family_colors", {})
    water_alpha = visuals.get("water_alpha", {})
    water_borders = visuals.get("water_borders", {})
    status_colors = {**DEFAULT_STATUS_COLORS, **visuals.get("status_colors", {})}

    def _color_for(row: pd.Series) -> str:
        if row["status"] == "CROP":
            return family_colors.get(row["family"], DEFAULT_STATUS_COLORS["CROP"])
        return status_colors.get(row["status"], DEFAULT_STATUS_COLORS["EMPTY"])

    def _alpha_for(row: pd.Series) -> float:
        if row["status"] != "CROP":
            return 1.0
        return float(water_alpha.get(row["water"], 1.0))

    def _border_for(row: pd.Series) -> str:
        if row["status"] != "CROP":
            return "solid"
        return str(water_borders.get(row["water"], "solid"))

    grid["color"] = grid.apply(_color_for, axis=1)
    grid["alpha"] = grid.apply(_alpha_for, axis=1)
    grid["border_style"] = grid.apply(_border_for, axis=1)

    # Build merged runs
    runs = []
    run_id = 0
    for bed_id in range(1, bed_count + 1):
        bed_rows = grid[grid["bed_id"] == bed_id].sort_values("block_idx")
        current = None
        for _, row in bed_rows.iterrows():
            key = (
                row["status"],
                row["crop"],
                row["variety"],
                row["wave_id"],
                row["conflict_details"],
            )
            if current is None:
                current = {
                    "bed_id": bed_id,
                    "start_block": int(row["block_idx"]),
                    "end_block": int(row["block_idx"]) + 1,
                    "key": key,
                    "row": row,
                }
                continue
            if key == current["key"] and row["block_idx"] == current["end_block"]:
                current["end_block"] += 1
            else:
                current["run_id"] = run_id
                runs.append(current)
                run_id += 1
                current = {
                    "bed_id": bed_id,
                    "start_block": int(row["block_idx"]),
                    "end_block": int(row["block_idx"]) + 1,
                    "key": key,
                    "row": row,
                }
        if current is not None:
            current["run_id"] = run_id
            runs.append(current)
            run_id += 1

    # Assign run_id to grid
    run_lookup = {}
    for run in runs:
        for block_idx in range(run["start_block"], run["end_block"]):
            run_lookup[(run["bed_id"], block_idx)] = run["run_id"]
    grid["run_id"] = grid.apply(
        lambda r: run_lookup[(r["bed_id"], r["block_idx"])], axis=1
    )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    grid.to_csv(output_csv, index=False)

    # SVG render
    cell_size = int(visuals.get("cell_size", 40))
    font_family = visuals.get("font_family", "Helvetica")
    label_font_size = int(visuals.get("label_font_size", 10))
    conflict_font_size = int(visuals.get("conflict_font_size", 8))
    reserved_font_size = int(visuals.get("reserved_font_size", 9))
    conflict_max_lines = int(visuals.get("conflict_max_lines", 4))
    row_label_width = int(visuals.get("row_label_width", cell_size))
    notes_width_ratio = float(visuals.get("notes_col_width_ratio", 0.33))

    grid_width = blocks_per_bed * cell_size
    notes_width = int(grid_width * notes_width_ratio)
    width_px = row_label_width + grid_width + notes_width
    height_px = bed_count * cell_size
    x_offset = row_label_width

    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px}" height="{height_px}" ',
        f'viewBox="0 0 {width_px} {height_px}">',
    ]

    # Row number column
    for bed_id in range(1, bed_count + 1):
        y = (bed_id - 1) * cell_size
        svg_parts.append(
            f'<rect x="0" y="{y}" width="{row_label_width}" height="{cell_size}" '
            f'fill="#FFFFFF" stroke="#333333" stroke-width="1" />'
        )
        svg_parts.append(
            _svg_text(
                row_label_width / 2,
                y + cell_size / 2,
                [str(bed_id)],
                reserved_font_size,
                font_family,
                "#111111",
            )
        )

    # Notes column
    for bed_id in range(1, bed_count + 1):
        y = (bed_id - 1) * cell_size
        x = x_offset + grid_width
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{notes_width}" height="{cell_size}" '
            f'fill="#FFFFFF" stroke="#333333" stroke-width="1" />'
        )
        notes_text = bed_notes.get(bed_id, "")
        if notes_text:
            lines = wrap_text(
                notes_text,
                _line_capacity(reserved_font_size, notes_width),
                2,
            )
            svg_parts.append(
                _svg_text(
                    x + notes_width / 2,
                    y + cell_size / 2,
                    lines,
                    reserved_font_size,
                    font_family,
                    "#111111",
                )
            )

    # Grid runs
    for run in runs:
        row = run["row"]
        status = row["status"]
        x = x_offset + run["start_block"] * cell_size
        y = (run["bed_id"] - 1) * cell_size
        run_width = (run["end_block"] - run["start_block"]) * cell_size
        run_height = cell_size

        fill = row["color"]
        fill_opacity = row["alpha"]
        border_style = row["border_style"]
        stroke_dasharray = ""
        if border_style == "dashed":
            stroke_dasharray = "4,2"
        elif border_style == "dotted":
            stroke_dasharray = "1,2"

        stroke_attr = (
            f' stroke="#333333" stroke-width="1"'
            + (f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else "")
        )

        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{run_width}" height="{run_height}" '
            f'fill="{fill}" fill-opacity="{fill_opacity}"{stroke_attr} />'
        )

        center_x = x + run_width / 2
        center_y = y + run_height / 2

        if status == "CROP":
            lines = build_crop_label_lines(
                row["crop"],
                row["variety"],
                run_width,
                label_font_size,
            )
            svg_parts.append(
                _svg_text(
                    center_x,
                    center_y,
                    lines,
                    label_font_size,
                    font_family,
                    "#111111",
                )
            )
        elif status == "CONFLICT":
            details = row["conflict_details"].split(" | ") if row["conflict_details"] else []
            lines = build_conflict_label_lines(
                details,
                run_width,
                conflict_font_size,
                conflict_max_lines,
            )
            svg_parts.append(
                _svg_text(
                    center_x,
                    center_y,
                    lines,
                    conflict_font_size,
                    font_family,
                    "#111111",
                )
            )
        elif status in ("FLOWER", "BENEFICIAL"):
            label = _reserved_label(status, reserved_labels)
            lines = [fit_text(label, _line_capacity(reserved_font_size, run_width))]
            svg_parts.append(
                _svg_text(
                    center_x,
                    center_y,
                    lines,
                    reserved_font_size,
                    font_family,
                    "#111111",
                )
            )

    svg_parts.append("</svg>")
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    output_svg.write_text("".join(svg_parts), encoding="utf-8")

    if output_png is not None:
        try:
            import cairosvg

            output_png.parent.mkdir(parents=True, exist_ok=True)
            cairosvg.svg2png(url=str(output_svg), write_to=str(output_png))
        except Exception as exc:  # pragma: no cover - runtime-only dependency
            print(f"Warning: PNG rasterization failed: {exc}")

    return grid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assignments",
        default="data/plans/bed-assignments.csv",
        help="Path to bed assignments CSV",
    )
    parser.add_argument(
        "--schedule",
        default="data/schedules/succession-schedule.csv",
        help="Path to succession schedule CSV",
    )
    parser.add_argument(
        "--geometry",
        default="data/plans/config/bed-geometry.jsonl",
        help="Path to bed geometry JSONL",
    )
    parser.add_argument(
        "--visuals",
        default="data/plans/config/bed-visuals.jsonl",
        help="Path to bed visuals JSONL",
    )
    parser.add_argument(
        "--output-csv",
        default="data/plans/bed-grid.csv",
        help="Path to output grid CSV",
    )
    parser.add_argument(
        "--output-svg",
        default="exports/bed-grid.svg",
        help="Path to output grid SVG",
    )
    parser.add_argument(
        "--output-png",
        default="exports/bed-grid.png",
        help="Path to output grid PNG",
    )
    parser.add_argument(
        "--skip-png",
        action="store_true",
        help="Skip PNG rasterization",
    )
    parser.add_argument(
        "--schema-version",
        type=int,
        default=1,
        help="Expected schema_version for inputs",
    )
    args = parser.parse_args()

    output_png = None if args.skip_png else Path(args.output_png)
    try:
        render_grid(
            Path(args.assignments),
            Path(args.schedule),
            Path(args.geometry),
            Path(args.visuals),
            Path(args.output_csv),
            Path(args.output_svg),
            output_png,
            args.schema_version,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Saved grid CSV to {args.output_csv}")
    print(f"Saved grid SVG to {args.output_svg}")
    if output_png is not None:
        print(f"Saved grid PNG to {args.output_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
