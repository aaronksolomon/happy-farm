#!/usr/bin/env -S uv run python
"""Enrich seed inventory data with yield ranges."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import pandas as pd


@dataclass(frozen=True)
class YieldRange:
    low: float | None
    high: float | None


def parse_grit_yields(path: Path) -> pd.DataFrame:
    """Parse the GRIT scrape CSV (single column) into a crop->yield range table."""
    df_raw = pd.read_csv(path)

    # The file is a 1-col scrape; the header itself is a URL.
    col = df_raw.columns[0]
    lines = df_raw[col].astype(str).tolist()

    crops: list[str] = []
    lows: list[float | None] = []
    highs: list[float | None] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # split on last whitespace
        try:
            crop_part, yield_part = line.rsplit(" ", 1)
        except ValueError:
            continue

        crop = crop_part.strip()
        y = yield_part.strip()

        # normalize some yield strings: e.g. '2-3', '0.5-1', '2'
        m_range = re.fullmatch(r"(?P<low>\d+(?:\.\d+)?)-(?P<high>\d+(?:\.\d+)?)", y)
        m_single = re.fullmatch(r"(?P<val>\d+(?:\.\d+)?)", y)

        if m_range:
            low = float(m_range.group("low"))
            high = float(m_range.group("high"))
        elif m_single:
            low = float(m_single.group("val"))
            high = float(m_single.group("val"))
        else:
            low = None
            high = None

        crops.append(crop)
        lows.append(low)
        highs.append(high)

    df = pd.DataFrame({"crop_key": crops, "yield_low": lows, "yield_high": highs})
    return df


def normalize_crop_key(s: str) -> str:
    """Light normalization for joining."""
    s2 = s.strip().lower()
    s2 = re.sub(r"\s+", " ", s2)
    return s2


def enrich_seed_inventory(seed_csv: Path, grit_csv: Path, out_csv: Path) -> None:
    inv = pd.read_csv(seed_csv)
    grit = parse_grit_yields(grit_csv)

    # Build join keys
    inv["crop_key"] = inv["crop"].astype(str).map(normalize_crop_key)
    grit["crop_key"] = grit["crop_key"].astype(str).map(normalize_crop_key)

    # Minimal mapping for known mismatches
    crop_key_map: dict[str, str] = {
        "cabbage / asian brassicas": "cabbage",
        "lettuce (single)": "lettuce",
        "lettuce (mixed)": "lettuce",
        "radishes": "beets",  # Using beets as proxy (0.25 lb)
        "radishes (mixed)": "beets",
        "summer squash / zucchini": "squash, summer",
        "sweet potatoes (slips)": "potatoes, sweet",
        "beans (bush)": "beans, green",
        "beans (bush mixed)": "beans, green",
        "beans (pole)": "beans, green",
        "peppers (sweet)": "peppers",
        "peppers (hot)": "peppers",
        "winter squash": "squash, winter",
        "swiss chard": "swiss chard",
        "cilantro/coriander": "lettuce",  # proxy for greens
        "basil (italian)": "lettuce",
        "basil (asian)": "lettuce",
        "holy basil (tulsi)": "lettuce",
    }

    inv["crop_key"] = inv["crop_key"].map(lambda k: crop_key_map.get(k, k))

    merged = inv.merge(grit, on="crop_key", how="left")

    # Define direct sow vs transplant crops based on normalized crop names
    direct_sow_crops = {
        "beets",
        "carrots",
        "radishes",
        "radishes (mixed)",
        "arugula",
        "greens mixes",
        "mustard greens",
        "chicory",
        "fava beans",
        "beans (bush)",
        "beans (bush mixed)",
        "beans (pole)",
        "cucumbers",
        "winter squash",
        "melons",
        "summer squash / zucchini",
        "amaranth",
        "fennel",
        "onions (bulbing types vary by daylength)",
        # Herbs that are typically direct sown
        "cilantro/coriander",
        "parsley",
        "dill",
        # Flowers that are typically direct sown
        "poppies",
        "poppies (mixed)",
        "other cool season annuals",
        "calendula",
        "sunflowers",
        "zinnias",
        "cosmos",
        "marigolds",
        "other annuals",
        "vines",
        "california natives",
        "other perennials",
        "wildflower mixes",
        "bee balm",
        "hyssop",
    }

    # Transplant crops with their typical days_to_transplant
    transplant_defaults = {
        "lettuce (single)": 28,
        "lettuce (mixed)": 28,
        "spinach": 21,
        "swiss chard": 21,
        "broccoli": 35,
        "cabbage / asian brassicas": 35,
        "cauliflower": 35,
        "kale": 30,
        "celery": 80,
        "tomatoes": 50,
        "peppers (sweet)": 55,
        "peppers (hot)": 55,
        "eggplant": 55,
        "sweet potatoes (slips)": 0,  # Already slips
        # Warm-season basil often transplanted
        "basil (italian)": 21,
        "basil (asian)": 21,
        "holy basil (tulsi)": 21,
    }

    # Apply seeding_method based on crop type
    def get_seeding_method(crop: str) -> str:
        norm_crop = normalize_crop_key(crop)
        if norm_crop in {normalize_crop_key(x) for x in direct_sow_crops}:
            return "direct_sow"
        elif "perennial" in str(crop).lower() or crop in [
            "Lavender", "Marjoram", "Mexican Tarragon", "Oregano", "Rosemary",
            "Sage", "Thyme", "Lemon Balm", "Shiso", "Chives", "Lovage",
            "Stevia", "Chamomile", "Echinacea", "Angelica", "Caraway",
            "Cumin", "Rue", "Mexican Mint Marigold"
        ]:
            return "perennial"
        elif crop == "Sweet Potatoes (Slips)":
            return "slips"
        else:
            return "transplant"

    merged["seeding_method"] = merged["crop"].map(get_seeding_method)

    # Apply N/A rules for direct_sow crops
    is_direct = merged["seeding_method"] == "direct_sow"
    merged.loc[is_direct, "start"] = merged.loc[is_direct, "start"].fillna("N/A")
    merged.loc[is_direct, "plant_out"] = merged.loc[is_direct, "plant_out"].fillna("N/A")
    merged.loc[is_direct, "days_to_transplant"] = "N/A"

    # Apply N/A rules for perennial crops (no start/transplant typically)
    is_perennial = merged["seeding_method"] == "perennial"
    merged.loc[is_perennial, "start"] = merged.loc[is_perennial, "start"].fillna("N/A")
    merged.loc[is_perennial, "plant_out"] = merged.loc[is_perennial, "plant_out"].fillna("N/A")
    merged.loc[is_perennial, "days_to_transplant"] = merged.loc[is_perennial, "days_to_transplant"].fillna("N/A")

    # Fill days_to_transplant for transplant crops
    for crop, days in transplant_defaults.items():
        mask = (merged["crop"] == crop) & (merged["seeding_method"] == "transplant")
        merged.loc[mask, "days_to_transplant"] = merged.loc[mask, "days_to_transplant"].fillna(days)

    # Drop the temporary crop_key column
    merged = merged.drop(columns=["crop_key"])

    merged.to_csv(out_csv, index=False)
    print(f"✓ Enriched seed inventory saved to {out_csv}")
    print(f"  - Added seeding_method classification")
    print(f"  - Filled days_to_transplant defaults")
    print(f"  - Merged yield data from GRIT")


def main() -> None:
    seed_csv = Path("data/seeds/seed-inventory.csv")
    grit_csv = Path("data/seeds/harvest-tracker-grit-data.csv")
    out_csv = Path("data/seeds/seed-inventory.csv")  # Overwrite original

    enrich_seed_inventory(seed_csv=seed_csv, grit_csv=grit_csv, out_csv=out_csv)


if __name__ == "__main__":
    main()
