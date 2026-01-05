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


def test_calculate_plants_per_linear_foot_scatter() -> None:
    row = {"rows/pattern": "scatter", "count_sq_ft": "10"}
    result = csp.calculate_plants_per_linear_foot(row, "scatter")
    assert result == 10 * csp.BED_WIDTH_FEET


def test_calculate_succession_schedule_writes_output(tmp_path: Path) -> None:
    plant_path = tmp_path / "plants.csv"
    plant_path.write_text(
        "crop,variety,method,water,lo_yield,hi_yield,web_final_spacing,web_days_to_maturity,url\n"
        'Carrots,Bolero,direct_sow,medium,0.25,0.25,"6",70,http://x\n',
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
    assert row["plant_date"] == "2026-02-14"
    assert row["wave_seq"] == "1"
    assert row["first_harvest_date"] == "2026-04-25"
    assert row["row_feet"] == "33"
    assert row["water"] == "medium"

    df = pd.read_csv(output_path)
    assert "plants_per_linear_foot" in df.columns
    assert "wave_seq" in df.columns
