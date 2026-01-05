"""Wave identifier helpers."""

from __future__ import annotations

import pandas as pd


def build_wave_id(
    crop: str,
    variety: str,
    plant_date: str,
    wave_seq: str | int | None = None,
) -> str:
    base = f"{crop.strip()}:{variety.strip()}:{plant_date.strip()}"
    if wave_seq is None or pd.isna(wave_seq) or str(wave_seq).strip() == "":
        return base
    return f"{base}:{str(wave_seq).strip()}"


def apply_wave_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    has_wave_seq = "wave_seq" in df.columns

    if has_wave_seq:
        df["wave_id"] = df.apply(
            lambda row: build_wave_id(
                row["crop"], row["variety"], row["plant_date"], row["wave_seq"]
            ),
            axis=1,
        )
    else:
        df["wave_id"] = df.apply(
            lambda row: build_wave_id(row["crop"], row["variety"], row["plant_date"]),
            axis=1,
        )
    return df
