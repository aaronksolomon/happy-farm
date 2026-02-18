import json
from pathlib import Path

import pytest

from scripts.build_assignments import build_assignments


def _write_jsonl(path: Path, objects: list[dict]) -> None:
    lines = [json.dumps(obj) for obj in objects]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_schedule(path: Path) -> None:
    path.write_text(
        "# schema_version: 1\n"
        "crop,variety,method,water,plant_date,first_harvest_date,target_lbs_week,row_feet,"
        "succession_days,notes,url,avg_yield_per_plant,plants_per_linear_foot,plant_count_or_sqft\n"
        "Carrot,Bolero,direct_sow,medium,2026-02-21,2026-05-07,15,10,21,Note,http://x,0.25,6.0,66\n",
        encoding="utf-8",
    )


def test_build_assignments_validates_and_computes_blocks(tmp_path: Path) -> None:
    assignments = tmp_path / "assignments.csv"
    assignments.write_text(
        "# schema_version: 1\n"
        "bed_id,start_ft,length_ft,crop,variety,wave_id,plant_date,notes\n"
        "1,0,10,Carrot,Bolero,Carrot:Bolero:2026-02-21,2026-02-21,\n",
        encoding="utf-8",
    )
    schedule = tmp_path / "schedule.csv"
    _write_schedule(schedule)
    config = tmp_path / "config.jsonl"
    _write_jsonl(
        config,
        [
            {"schema_version": 1, "bed_count": 12, "bed_length_ft": 80, "block_size_ft": 5},
            {"flower_blocks": [0, 15], "beneficial_block": 7},
        ],
    )

    df = build_assignments(assignments, schedule, config, 1)
    assert df["start_block"].iloc[0] == 0
    assert df["end_block"].iloc[0] == 2


def test_build_assignments_unknown_wave_id(tmp_path: Path) -> None:
    assignments = tmp_path / "assignments.csv"
    assignments.write_text(
        "# schema_version: 1\n"
        "bed_id,start_ft,length_ft,crop,variety,wave_id,plant_date,notes\n"
        "1,0,10,Carrot,Bolero,BadWave,2026-02-21,\n",
        encoding="utf-8",
    )
    schedule = tmp_path / "schedule.csv"
    _write_schedule(schedule)
    config = tmp_path / "config.jsonl"
    _write_jsonl(
        config,
        [
            {"schema_version": 1, "bed_count": 12, "bed_length_ft": 80, "block_size_ft": 5},
        ],
    )

    with pytest.raises(ValueError, match="Unknown wave_id"):
        build_assignments(assignments, schedule, config, 1)


def test_build_assignments_fixture() -> None:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "bed-assignments-sample.csv"
    schedule_path = Path("data/schedules/succession-schedule.csv")
    config_path = Path("data/plans/config/bed-geometry.jsonl")

    df = build_assignments(fixture_path, schedule_path, config_path, 1)
    assert len(df) > 0
    first = df.iloc[0]
    assert first["start_block"] >= 0
    assert first["end_block"] > first["start_block"]


def test_build_assignments_beneficial_status(tmp_path: Path) -> None:
    assignments = tmp_path / "assignments.csv"
    assignments.write_text(
        "# schema_version: 1\n"
        "bed_id,start_ft,length_ft,status,crop,variety,wave_id,plant_date,notes\n"
        "1,10,5,BENEFICIAL,,,,,Center strip\n",
        encoding="utf-8",
    )
    schedule = tmp_path / "schedule.csv"
    _write_schedule(schedule)
    config = tmp_path / "config.jsonl"
    _write_jsonl(
        config,
        [
            {"schema_version": 1, "bed_count": 12, "bed_length_ft": 80, "block_size_ft": 5},
        ],
    )

    df = build_assignments(assignments, schedule, config, 1)
    assert df["status"].iloc[0] == "BENEFICIAL"
