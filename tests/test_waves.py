import pandas as pd

from scripts.io.waves import apply_wave_id, build_wave_id


def test_build_wave_id() -> None:
    assert build_wave_id("Carrot", "Bolero", "2026-02-21") == "Carrot:Bolero:2026-02-21"
    assert (
        build_wave_id("Carrot", "Bolero", "2026-02-21", 2)
        == "Carrot:Bolero:2026-02-21:2"
    )


def test_apply_wave_id() -> None:
    df = pd.DataFrame(
        {
            "crop": ["Carrot"],
            "variety": ["Bolero"],
            "plant_date": ["2026-02-21"],
        }
    )
    result = apply_wave_id(df)
    assert result["wave_id"].iloc[0] == "Carrot:Bolero:2026-02-21"


def test_apply_wave_id_with_seq() -> None:
    df = pd.DataFrame(
        {
            "crop": ["Carrot"],
            "variety": ["Bolero"],
            "plant_date": ["2026-02-21"],
            "wave_seq": [2],
        }
    )
    result = apply_wave_id(df)
    assert result["wave_id"].iloc[0] == "Carrot:Bolero:2026-02-21:2"


def test_build_wave_id_with_nan() -> None:
    """Test that NaN wave_seq values don't append ':nan' to wave_id."""
    import numpy as np

    assert build_wave_id("Arugula", "Wild", "2026-02-14", None) == "Arugula:Wild:2026-02-14"
    assert (
        build_wave_id("Arugula", "Wild", "2026-02-14", np.nan)
        == "Arugula:Wild:2026-02-14"
    )
    assert build_wave_id("Arugula", "Wild", "2026-02-14", "") == "Arugula:Wild:2026-02-14"


def test_apply_wave_id_with_nan_wave_seq() -> None:
    """Test that NaN values in wave_seq column are handled correctly."""
    import numpy as np

    df = pd.DataFrame(
        {
            "crop": ["Arugula", "Spinach", "Broccoli"],
            "variety": ["Wild Arugula", "Corvair", "Belstar F1"],
            "plant_date": ["2026-02-14", "2026-02-14", "2026-02-14"],
            "wave_seq": [np.nan, np.nan, np.nan],
        }
    )
    result = apply_wave_id(df)
    assert result["wave_id"].iloc[0] == "Arugula:Wild Arugula:2026-02-14"
    assert result["wave_id"].iloc[1] == "Spinach:Corvair:2026-02-14"
    assert result["wave_id"].iloc[2] == "Broccoli:Belstar F1:2026-02-14"
    # Ensure no ':nan' suffix
    assert ":nan" not in result["wave_id"].iloc[0]
    assert ":nan" not in result["wave_id"].iloc[1]
    assert ":nan" not in result["wave_id"].iloc[2]
