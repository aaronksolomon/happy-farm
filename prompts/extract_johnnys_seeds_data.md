---
key: extract_johnnys_seeds_data
name: Extract Johnny's Seeds Plant Data
version: 1.0.0
description: Extract structured planting data from Johnny's Selected Seeds product pages
task_type: extraction
required_variables: []
optional_variables: []
tags: [web-scraping, data-extraction, agriculture]
default_variables: {}
---

# Extract Johnny's Seeds Plant Data

## Identity and Purpose

- You will be extracting structured planting data from seed supplier product pages.
- We specific information from Johnny's Selected Seeds product descriptions.
- The output must be valid JSON with precise field names.

## Input

- HTML content from a Johnny's Selected Seeds product page accordion sections.
- The content contains narrative text about planting instructions, growing conditions, and seed specifications.

## Task

- Extract the following planting data fields from the text:
  - `scientific_name`: Scientific/botanical name (will be mapped to web_botanical_name)
  - `planting_season`: Growing season (Warm/Cool/Spring/Fall)
  - `web_soil_temp`: Soil temperature for germination (e.g., "65° F+")
  - `web_planting_depth`: How deep to plant seeds (e.g., "1/4\"")
  - `web_days_to_maturity`: Days to maturity (e.g., "65+")
  - `web_best_planting_method`: Planting method (Transplant/Direct sow/either)
  - `web_thin_to`: Thinning spacing (e.g., "2\" apart")
  - `web_final_spacing`: Final plant spacing (e.g., "18-24\"")
  - `web_seeds_per_packet`: Number of seeds per packet (from "Packet: X seeds" in details)
  - `js_growing_notes`: General growing notes from the details section (description, disease resistance, etc.)
- If a field cannot be found in the text, use `null` for that field.
- Preserve exact units and formatting from the source text (e.g., keep quotes for inches, keep ° symbol).

## Output

- Output ONLY valid JSON with no markdown formatting, no code fences, no explanatory text.
- Use exactly these field names in the JSON output.
- Example output format:

{
  "scientific_name": "Solanum melongena",
  "planting_season": "Warm",
  "web_soil_temp": "70-90° F",
  "web_planting_depth": "1/4\"",
  "web_days_to_maturity": "65-80",
  "web_best_planting_method": "Transplant",
  "web_thin_to": "2-3\" apart",
  "web_final_spacing": "18-24\"",
  "web_seeds_per_packet": 100,
  "js_growing_notes": "Example growing notes text"
}

- Return ONLY the JSON object, with no additional text before or after.
