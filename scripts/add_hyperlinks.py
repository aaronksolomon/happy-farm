#!/usr/bin/env -S uv run python
"""Add hyperlinks from seed-list.md URLs to seed-inventory.md variety names."""

import re
from pathlib import Path
from urllib.parse import urlparse
from difflib import SequenceMatcher

# Read seed-list.md and extract URLs
seed_list_path = Path(__file__).parent.parent / "seed-list.md"
inventory_path = Path(__file__).parent.parent / "seed-inventory.md"

def normalize_text(text):
    """Normalize text for fuzzy matching."""
    # Remove common prefixes/suffixes
    text = text.lower()
    text = re.sub(r'\b(organic|seeds?|f1|f-1|herb|vegetable|flower)\b', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

def similarity_ratio(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

# Parse URLs and create mapping
url_map = {}

with open(seed_list_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("http"):
            # Extract variety name from URL
            path = urlparse(line).path
            segments = [s for s in path.split('/') if s]
            if segments:
                last = segments[-1]
                # Remove file extensions
                name = last.replace('-seeds', '').replace('-seed', '').replace('.html', '')
                # Remove trailing product codes (e.g., 2815G, 703D)
                name = re.sub(r'-\d+[A-Z]?$', '', name)

                # Store with cleaned name as key
                key = name.replace('-', ' ')
                url_map[key] = line

# Read inventory
with open(inventory_path) as f:
    content = f.read()

# Find all variety entries (format: "  - Variety Name (SDSC/JS) - optional notes")
# Pattern: lines starting with "  - " followed by text, then (SDSC) or (JS)
lines = content.split('\n')
new_lines = []
matched_count = 0
total_count = 0

for line in lines:
    # Match pattern: "  - Variety Name (SDSC) - optional" or "  - [Variety](url) (SDSC) - optional"
    match = re.match(r'^(\s+- )(?:\[)?([^(\]]+?)(?:\])?\(?(?:https?://[^\)]+)?\)?( \((SDSC|JS)\).*?)$', line)
    if match:
        total_count += 1
        indent = match.group(1)
        variety = match.group(2).strip()
        suffix = match.group(3)
        company = match.group(4)

        # Skip if already has hyperlink
        if line.strip().startswith('- [') and '](http' in line:
            new_lines.append(line)
            matched_count += 1
            continue

        # Find best matching URL using fuzzy matching
        best_match = None
        best_score = 0.0
        threshold = 0.6  # Minimum similarity threshold

        for url_key, url in url_map.items():
            # Only match with same company
            if (company == 'SDSC' and 'sandiegoseed' not in url) or \
               (company == 'JS' and 'johnnyseeds' not in url):
                continue

            score = similarity_ratio(variety, url_key)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = url

        if best_match:
            # Create hyperlink: [Variety Name](URL)
            new_line = f"{indent}[{variety}]({best_match}){suffix}"
            new_lines.append(new_line)
            matched_count += 1
        else:
            # Keep original
            new_lines.append(line)
    else:
        new_lines.append(line)

# Write updated inventory
with open(inventory_path, 'w') as f:
    f.write('\n'.join(new_lines))

print(f"✓ Added hyperlinks to seed-inventory.md")
print(f"  Matched {matched_count}/{total_count} varieties ({matched_count*100//total_count}%)")
