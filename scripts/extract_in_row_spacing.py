#!/usr/bin/env -S uv run python
"""Extract in-row spacing from web_final_spacing using tnh-gen.

This script processes the vegetable data CSV and uses an LLM to extract
numeric in-row spacing values from the variable text in web_final_spacing.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


def extract_spacing_with_ai(spacing_text: str, prompts_dir: Path) -> float | None:
    """Extract in-row spacing in inches using tnh-gen.

    Args:
        spacing_text: The web_final_spacing text to parse
        prompts_dir: Path to prompts directory

    Returns:
        Spacing in inches, or None if extraction failed
    """
    if not spacing_text or pd.isna(spacing_text) or spacing_text == "N/A":
        return None

    # Write spacing text to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write(spacing_text)
        tmp_path = tmp.name

    try:
        env = {"TNH_PROMPT_DIR": str(prompts_dir)}
        result = subprocess.run(
            [
                "tnh-gen", "--api", "run",
                "--prompt", "extract_in_row_spacing",
                "--input-file", tmp_path
            ],
            env={**subprocess.os.environ, **env},
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"tnh-gen failed for '{spacing_text}': {result.stderr}")
            return None

        # Parse response envelope
        response = json.loads(result.stdout.strip())
        if response.get("status") != "succeeded":
            print(f"Extraction failed for '{spacing_text}': {response}")
            return None

        extracted_text = response.get("result", {}).get("text", "").strip()

        # Remove markdown code fences if present
        if extracted_text.startswith("```"):
            extracted_text = extracted_text.split("```")[1]
            if extracted_text.startswith("json"):
                extracted_text = extracted_text[4:]
            extracted_text = extracted_text.strip()

        data = json.loads(extracted_text)
        return data.get("in_row_spacing_inches")

    except Exception as exc:
        print(f"Error extracting spacing from '{spacing_text}': {exc}")
        return None

    finally:
        Path(tmp_path).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/plants/vegetable-data.csv"),
        help="Input CSV with plant data",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (defaults to overwriting input)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print extractions without saving",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = args.input

    # Find prompts directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    prompts_dir = project_root / "prompts"

    if not prompts_dir.exists():
        print(f"Error: Prompts directory not found: {prompts_dir}")
        return 1

    df = pd.read_csv(args.input)

    # Add column if missing
    if "in_row_spacing_ft" not in df.columns:
        df["in_row_spacing_ft"] = None

    # Get unique spacing values to minimize API calls
    unique_spacings = df["web_final_spacing"].dropna().unique()
    unique_spacings = [s for s in unique_spacings if s and s != "N/A"]

    print(f"Extracting spacing from {len(unique_spacings)} unique values...")

    # Build lookup of spacing text -> inches
    spacing_lookup: dict[str, float | None] = {}
    for spacing_text in unique_spacings:
        inches = extract_spacing_with_ai(str(spacing_text), prompts_dir)
        spacing_lookup[spacing_text] = inches
        feet = round(inches / 12, 3) if inches else None
        print(f"  '{spacing_text}' -> {inches} inches ({feet} ft)")

    if args.dry_run:
        print("\nDry run - not saving changes")
        return 0

    # Apply to dataframe
    def get_spacing_ft(row: pd.Series) -> float | None:
        spacing_text = row.get("web_final_spacing")
        if not spacing_text or pd.isna(spacing_text) or spacing_text == "N/A":
            return None
        inches = spacing_lookup.get(spacing_text)
        if inches is None:
            return None
        return round(inches / 12, 3)

    df["in_row_spacing_ft"] = df.apply(get_spacing_ft, axis=1)

    df.to_csv(args.output, index=False)
    print(f"\nSaved to {args.output}")

    # Summary
    extracted = df["in_row_spacing_ft"].notna().sum()
    total = len(df)
    print(f"Extracted spacing for {extracted}/{total} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
