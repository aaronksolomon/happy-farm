import csv
from pathlib import Path

import pandas as pd

from scripts import calculate_succession_planting as csp


def test_parse_spacing() -> None:
    assert csp.parse_spacing('≥24" apart') == 0.5
    assert round(csp.parse_spacing('12-18"') or 0, 2) == 0.8


def test_get_succession_interval_override() -> None:
    plant_row = {"crop": "Carrots"}
    config_row = {"succession_days_override": "9"}
    assert csp.get_succession_interval(plant_row, config_row) == 9


def test_calculate_plants_per_linear_foot_scatter_with_count() -> None:
    row = {"rows/pattern": "scatter", "count_sq_ft": "10"}
    result = csp.calculate_plants_per_linear_foot(row, "scatter")
    assert result == 10 * csp.BED_WIDTH_FEET


def test_calculate_plants_per_linear_foot_scatter_without_count() -> None:
    row = {"rows/pattern": "scattered"}
    result = csp.calculate_plants_per_linear_foot(row, "direct_sow")
    assert result is None


def test_calculate_plants_per_linear_foot_5star() -> None:
    row = {"rows/pattern": "5-star"}
    result = csp.calculate_plants_per_linear_foot(row, "transplant")
    assert result == 1.5


def test_calculate_plants_per_linear_foot_rows() -> None:
    # 4 rows with 0.167 ft (2") in-row spacing = 4 * 6 = 24 plants/ft
    row = {"rows/pattern": "4", "in_row_spacing_ft": "0.167"}
    result = csp.calculate_plants_per_linear_foot(row, "direct_sow")
    assert round(result, 1) == 24.0


def test_calculate_succession_schedule_writes_output(tmp_path: Path) -> None:
    plant_path = tmp_path / "plants.csv"
    plant_path.write_text(
        "crop,variety,method,water,yield_per_harvest_lo,yield_per_harvest_hi,web_final_spacing,web_days_to_maturity,url,rows/pattern,in_row_spacing_ft\n"
        'Carrots,Bolero,direct_sow,medium,0.25,0.25,"6",70,http://x,4,0.167\n',
        encoding="utf-8",
    )
    config_path = tmp_path / "config.csv"
    config_path.write_text(
        "crop,variety,target_lbs_week,stagger_offset_days,notes\n"
        "Carrots,Bolero,15,0,Test\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "schedule.csv"

    csp.calculate_succession_schedule(plant_path, config_path, output_path)

    with output_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]
    assert row["plant_type"] == "Root Vegetable"
    assert row["plant_date"] == "2026-02-28"
    assert row["wave_seq"] == "1"
    assert row["first_harvest_date"] == "2026-05-09"
    assert row["water"] == "medium"

    df = pd.read_csv(output_path)
    assert "plants_per_linear_foot" in df.columns
    assert "wave_seq" in df.columns
    assert "planting_pattern" in df.columns
    assert "in_row_spacing_ft" in df.columns
    assert str(df["planting_pattern"].iloc[0]) == "4"
    # 4 rows with 0.167 ft spacing = ~24 plants/ft
    assert df["plants_per_linear_foot"].iloc[0] > 20
