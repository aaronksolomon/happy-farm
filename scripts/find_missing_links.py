#!/usr/bin/env -S uv run python
"""Find unlinked varieties and suggest possible URL matches."""

import re
from pathlib import Path

seed_list_path = Path(__file__).parent.parent / "seed-list.md"
inventory_path = Path(__file__).parent.parent / "seed-inventory.md"

# Read all URLs
urls = []
with open(seed_list_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("http"):
            urls.append(line)

# Read inventory and find unlinked varieties
with open(inventory_path) as f:
    for line in f:
        # Match unlinked varieties: "  - Variety Name (SDSC/JS)"
        match = re.match(r'^\s+- ([^[\(]+) \((SDSC|JS)\)', line)
        if match:
            variety = match.group(1).strip()
            company = match.group(2)

            # Extract first two words from variety name
            words = re.findall(r'\w+', variety)
            if len(words) >= 2:
                word1, word2 = words[0].lower(), words[1].lower()
            elif len(words) == 1:
                word1 = words[0].lower()
                word2 = ""
            else:
                continue

            # Filter URLs by company
            company_urls = [u for u in urls if
                           ('sandiegoseed' in u if company == 'SDSC' else 'johnnyseeds' in u)]

            # Find matching URLs
            matches = []
            for url in company_urls:
                url_lower = url.lower()
                if word1 in url_lower and (not word2 or word2 in url_lower):
                    matches.append(url)

            # Print results
            print(f"\n{variety} ({company})")
            if matches:
                for i, url in enumerate(matches, 1):
                    print(f"  {i}. {url}")
            else:
                print("  No matches found")
