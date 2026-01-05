from pathlib import Path

from scripts.load_data import load_data


def test_load_data_builds_wave_id(tmp_path: Path) -> None:
    crops_path = tmp_path / "crops.csv"
    crops_path.write_text(
        "# schema_version: 1\ncrop,variety\nCarrot,Bolero\n",
        encoding="utf-8",
    )
    schedule_path = tmp_path / "schedule.csv"
    schedule_path.write_text(
        "# schema_version: 1\n"
        "crop,variety,method,water,plant_date,first_harvest_date,target_lbs_week,row_feet,"
        "succession_days,notes,url,avg_yield_per_plant,plants_per_linear_foot,plants_count\n"
        "Carrot,Bolero,direct_sow,medium,2026-02-21,2026-05-07,15,11,21,Note,http://x,0.25,6.0,66\n",
        encoding="utf-8",
    )

    df_crops, df_schedule = load_data(crops_path, schedule_path, 1)
    assert len(df_crops) == 1
    assert len(df_schedule) == 1
    assert df_schedule["wave_id"].iloc[0] == "Carrot:Bolero:2026-02-21"
