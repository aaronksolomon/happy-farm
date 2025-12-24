#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

# Columns expected from SDSC pages (order matters for output)
# Note: planting_season is scraped but validated against existing 'season' column
# Fields common to both sources get web_ prefix, SDSC-only get sdsc_ prefix
SDSC_COLUMNS: list[str] = [
    "web_botanical_name",
    "web_soil_temp",
    "web_planting_depth",
    "sdsc_days_to_germ",
    "web_days_to_maturity",
    "sdsc_succession",
    "web_best_planting_method",
    "web_thin_to",
    "web_final_spacing",
    "sdsc_area_to_sow",
    "web_seeds_per_packet",  # SDSC calls this "approx_seed_count" but we map it
    "sdsc_product_weight",
    "sdsc_plant_height",
    "sdsc_plant_spread",
]

# Additional fields we scrape for validation but don't add as columns
VALIDATION_ONLY_FIELDS: list[str] = [
    "planting_season",  # Validated against existing 'season' column
]

# Columns expected from Johnny's Selected Seeds pages
# Fields common to both sources get web_ prefix, JS-only get js_ prefix
JS_COLUMNS: list[str] = [
    "web_botanical_name",
    "web_planting_depth",
    "web_days_to_maturity",
    "web_thin_to",
    "web_final_spacing",
    "web_seeds_per_packet",
    "js_growing_notes",  # JS-only field
]

METADATA_COLUMNS: list[str] = [
    "scrape_status",
    "scrape_date",
]

# Preserve order from SDSC_COLUMNS (most complete), then add JS-only, then metadata
_sdsc_set = set(SDSC_COLUMNS)
_js_only = [c for c in JS_COLUMNS if c not in _sdsc_set]
ALL_SCRAPED_COLUMNS: list[str] = SDSC_COLUMNS + _js_only + METADATA_COLUMNS

USER_AGENT = "HappyFarmBot/1.0 (educational research)"

# Normalize table header labels to our column names (with prefixes)
SDSC_LABEL_MAP: dict[str, str] = {
    "product_weight": "sdsc_product_weight",
    "planting_season": "planting_season",
    "soil_temp_for_germination": "web_soil_temp",
    "soil_temp": "web_soil_temp",
    "planting_depth": "web_planting_depth",
    "area_to_sow": "sdsc_area_to_sow",
    "days_to_germ": "sdsc_days_to_germ",
    "days_to_maturity": "web_days_to_maturity",
    "best_planting_method": "web_best_planting_method",
    "thin_to": "web_thin_to",
    "final_spacing": "web_final_spacing",
    "succession": "sdsc_succession",
    "approx._seed_count": "web_seeds_per_packet",  # Map SDSC's approx_seed_count to unified field
    "approx_seed_count": "web_seeds_per_packet",   # Map SDSC's approx_seed_count to unified field
    "botanical_name": "web_botanical_name",
    "plant_spread": "sdsc_plant_spread",
    "plant_height": "sdsc_plant_height",
}


def normalize_label(label: str) -> str:
    """Normalize table header labels to snake_case keys."""
    normalized = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


def get_cache_path(url: str) -> Path:
    """Generate a deterministic cache filename from the URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_dir = Path(tempfile.gettempdir()) / "happy-farm-scraper"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{url_hash}.html"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def fetch_url(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    response = httpx.get(url, headers=headers, timeout=10.0)
    response.raise_for_status()
    return response.text


def fetch_with_cache(url: str, use_cache: bool = True) -> str:
    cache_path = get_cache_path(url)

    if use_cache and cache_path.exists():
        return cache_path.read_text()

    html = fetch_url(url)
    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")
    body_html = str(body) if body else html

    if use_cache:
        cache_path.write_text(body_html)

    return body_html


def parse_sdsc(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="woocommerce-product-attributes")
    if not table:
        return {}

    data: dict[str, Any] = {}
    for row in table.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue

        label = normalize_label(th.get_text(strip=True))
        value = td.get_text(strip=True)

        column = SDSC_LABEL_MAP.get(label)
        if column:
            data[column] = value

    return data


def parse_js_with_ai(html: str, prompt_file: Path | None = None) -> dict[str, Any]:
    """Parse Johnny's Seeds HTML using tnh-gen CLI for AI extraction.

    Args:
        html: HTML content from Johnny's Seeds product page
        prompt_file: Path to prompt template file (defaults to prompts/extract_johnnys_seeds_data.md)

    Returns:
        Dictionary of extracted plant data fields
    """
    import subprocess

    soup = BeautifulSoup(html, "html.parser")

    # Extract relevant sections
    sections = []

    # 1. Extract "Quick Facts" section (has days to maturity, latin name, etc.)
    quick_facts = soup.find("div", class_="c-facts")
    if quick_facts:
        sections.append(f"QUICK FACTS SECTION:\n{quick_facts.get_text(' ', strip=True)}")

    # 2. Extract "details" section (has packet size and notes)
    details_section = soup.find("div", class_="details")
    if details_section:
        sections.append(f"DETAILS SECTION:\n{details_section.get_text(' ', strip=True)}")

    # 3. Extract "Growing Information" accordion section
    # Find the accordion item with "Growing Information" heading
    for accordion_item in soup.find_all("div", class_="c-accordion__item"):
        heading_link = accordion_item.find("a", class_="c-accordion__heading__link")
        if heading_link and "Growing Information" in heading_link.get_text(strip=True):
            accordion_body = accordion_item.find("div", class_="c-accordion__body")
            if accordion_body:
                sections.append(f"GROWING INFORMATION SECTION:\n{accordion_body.get_text(' ', strip=True)}")
                break

    if not sections:
        return {}

    text_content = "\n\n".join(sections)
    if not text_content:
        return {}

    # Default prompt file location
    if prompt_file is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        prompt_file = project_root / "prompts" / "extract_johnnys_seeds_data.md"

    if not prompt_file.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}. "
            "Please ensure prompts/extract_johnnys_seeds_data.md exists."
        )

    # Write text content to temp file for tnh-gen to process
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write(text_content)
        tmp_path = tmp.name

    try:
        # Call tnh-gen CLI (installed via pipx)
        # Configure to use happy-farm's prompts directory via environment variable
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        prompts_dir = project_root / "prompts"

        # Use the prompt filename without extension as the key
        prompt_key = Path(prompt_file).stem  # e.g., "extract_johnnys_seeds_data"

        # Run tnh-gen with TNH_PROMPT_DIR environment variable to override catalog location
        # tnh-gen is installed via pipx --editable, so it's globally available
        env = {"TNH_PROMPT_DIR": str(prompts_dir)}
        result = subprocess.run(
            [
                "tnh-gen", "run",
                "--prompt", prompt_key,
                "--input-file", tmp_path
            ],
            env={**subprocess.os.environ, **env},  # Merge with existing env
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"tnh-gen failed with exit code {result.returncode}.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

        # Parse JSON output from tnh-gen
        # tnh-gen returns a response envelope: {"status": "succeeded", "result": {"text": "..."}}
        result_text = result.stdout.strip()

        response = json.loads(result_text)

        # Extract the actual data from the response envelope
        if response.get("status") != "succeeded":
            raise RuntimeError(f"tnh-gen extraction failed: {response}")

        # Get the text field from result
        extracted_text = response.get("result", {}).get("text", "").strip()

        # Remove markdown code fences if present in extracted text
        if extracted_text.startswith("```"):
            extracted_text = extracted_text.split("```")[1]
            if extracted_text.startswith("json"):
                extracted_text = extracted_text[4:]
            extracted_text = extracted_text.strip()

        data = json.loads(extracted_text)

        # Map scientific_name to web_botanical_name if present
        if "scientific_name" in data and data["scientific_name"]:
            data["web_botanical_name"] = data["scientific_name"]
            del data["scientific_name"]

        return data

    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


def mark_missing_fields(
    df: pd.DataFrame, idx: int, expected_cols: list[str], scraped: dict[str, Any]
) -> None:
    # Mark expected-but-missing fields
    for col in expected_cols:
        if col in df.columns and (
            pd.isna(df.at[idx, col]) or df.at[idx, col] == ""
        ):
            if col not in scraped:
                df.at[idx, col] = "NOT_FOUND"

    # Mark non-expected fields as N/A
    all_possible_cols = set(SDSC_COLUMNS + JS_COLUMNS)
    for col in all_possible_cols:
        if col not in expected_cols and col in df.columns:
            if pd.isna(df.at[idx, col]) or df.at[idx, col] == "":
                df.at[idx, col] = "N/A"


def scrape_single_row(
    idx: int,
    row: pd.Series,
    use_cache: bool = False,
) -> tuple[int, dict[str, Any], str, list[str]]:
    """Scrape a single row. Returns (idx, scraped_data, status, expected_cols)."""
    url = row.get("url")
    supplier = str(row.get("supplier", "")).upper()

    if not isinstance(url, str) or not url:
        return (idx, {}, "failed", [])

    try:
        html = fetch_with_cache(url, use_cache=use_cache)

        if supplier == "SDSC":
            scraped = parse_sdsc(html)
            expected_cols = SDSC_COLUMNS
        elif supplier == "JS":
            scraped = parse_js_with_ai(html)
            expected_cols = JS_COLUMNS
        else:
            scraped = {}
            expected_cols = []

        # Validate planting_season vs existing season column
        if "planting_season" in scraped and scraped["planting_season"]:
            existing_season = row.get("season")
            scraped_season = scraped["planting_season"]
            if existing_season and str(existing_season).strip():
                if str(existing_season).lower() != str(scraped_season).lower():
                    print(f"⚠️  Season mismatch for {row.get('variety')}: "
                          f"existing='{existing_season}' vs scraped='{scraped_season}'")
            # Don't write planting_season to avoid duplicate column
            del scraped["planting_season"]

        return (idx, scraped, "success", expected_cols)

    except Exception as exc:
        print(f"Failed to scrape {url}: {exc}")
        return (idx, {}, "failed", [])


def scrape_plant_data(
    csv_path: Path,
    output_path: Path,
    use_cache: bool = False,
    retry_failed_only: bool = False,
    batch_size: int = 20,
    batch_delay: float = 1.0,
) -> None:
    df = pd.read_csv(csv_path)

    for col in ALL_SCRAPED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Collect rows to process
    rows_to_process = []
    for idx, row in df.iterrows():
        if retry_failed_only and row.get("scrape_status") != "failed":
            continue
        rows_to_process.append((idx, row))

    if not rows_to_process:
        print("No rows to process")
        # Reorder and save anyway
        original_cols = [c for c in df.columns if c not in ALL_SCRAPED_COLUMNS]
        scraped_data_cols = [c for c in ALL_SCRAPED_COLUMNS if c not in METADATA_COLUMNS and c in df.columns]
        metadata_cols = [c for c in METADATA_COLUMNS if c in df.columns]
        df = df[original_cols + scraped_data_cols + metadata_cols]
        df.to_csv(output_path, index=False)
        return

    print(f"Processing {len(rows_to_process)} rows in batches of {batch_size}...")

    # Process in batches with threading
    for batch_start in range(0, len(rows_to_process), batch_size):
        batch_end = min(batch_start + batch_size, len(rows_to_process))
        batch = rows_to_process[batch_start:batch_end]

        print(f"Processing batch {batch_start//batch_size + 1} ({len(batch)} rows)...")

        # Use ThreadPoolExecutor to process batch concurrently
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {
                executor.submit(scrape_single_row, idx, row, use_cache): idx
                for idx, row in batch
            }

            for future in as_completed(futures):
                idx, scraped, status, expected_cols = future.result()

                # Update dataframe with results
                for key, value in scraped.items():
                    if key in df.columns:
                        df.at[idx, key] = value

                mark_missing_fields(df, idx, expected_cols, scraped)
                df.at[idx, "scrape_status"] = status
                df.at[idx, "scrape_date"] = pd.Timestamp.now().isoformat()

        # Delay between batches (except for last batch)
        if batch_end < len(rows_to_process):
            print(f"Waiting {batch_delay}s before next batch...")
            time.sleep(batch_delay)

    # Reorder columns: original columns, then scraped data, then metadata at end
    original_cols = [c for c in df.columns if c not in ALL_SCRAPED_COLUMNS]
    scraped_data_cols = [c for c in ALL_SCRAPED_COLUMNS if c not in METADATA_COLUMNS and c in df.columns]
    metadata_cols = [c for c in METADATA_COLUMNS if c in df.columns]
    df = df[original_cols + scraped_data_cols + metadata_cols]

    df.to_csv(output_path, index=False)
    print(f"Saved enriched data to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape plant data from supplier pages.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/plants/vegetable-data.csv"),
        help="Input CSV with plant rows and URLs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/plants/vegetable-data-enriched.csv"),
        help="Output CSV path for enriched data.",
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Cache fetched HTML in the system temp dir.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Only retry rows marked as failed.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of rows to process concurrently per batch (default: 20).",
    )
    parser.add_argument(
        "--batch-delay",
        type=float,
        default=1.0,
        help="Delay in seconds between batches (default: 1.0).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scrape_plant_data(
        csv_path=args.input,
        output_path=args.output,
        use_cache=args.use_cache,
        retry_failed_only=args.retry_failed,
        batch_size=args.batch_size,
        batch_delay=args.batch_delay,
    )


if __name__ == "__main__":
    main()
