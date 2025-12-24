#!/usr/bin/env python3
"""Test Johnny's Seeds scraping with tnh-gen integration."""

from pathlib import Path
import sys

# Add parent to path to import scrape_plant_data
sys.path.insert(0, str(Path(__file__).parent))

from scrape_plant_data import fetch_with_cache, parse_js_with_ai

# Test URL from the vegetable data CSV
TEST_URL = "https://www.johnnyseeds.com/vegetables/broccoli/standard-broccoli/belstar-organic-f1-broccoli-seed-2815G.html"

def main():
    print(f"Testing Johnny's Seeds scraper with tnh-gen")
    print(f"URL: {TEST_URL}\n")

    try:
        # Fetch the HTML
        print("Fetching HTML...")
        html = fetch_with_cache(TEST_URL, use_cache=True)
        print(f"✓ Fetched {len(html)} characters\n")

        # Parse with AI
        print("Parsing with tnh-gen...")
        data = parse_js_with_ai(html)

        print("✓ Extraction successful!\n")
        print("Extracted data:")
        print("-" * 60)
        for key, value in data.items():
            print(f"  {key:20s}: {value}")
        print("-" * 60)

        # Check for expected fields
        expected_fields = [
            "botanical_name", "planting_depth", "days_to_maturity",
            "final_spacing", "seeds_per_packet", "growing_notes"
        ]

        missing = [f for f in expected_fields if f not in data or data[f] is None]
        if missing:
            print(f"\n⚠️  Missing fields: {', '.join(missing)}")
        else:
            print(f"\n✓ All expected fields present!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
