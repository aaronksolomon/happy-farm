---
key: extract_in_row_spacing
name: Extract In-Row Spacing
version: 1.0.0
description: Extract numeric in-row spacing in inches from plant spacing text
task_type: extraction
required_variables: []
optional_variables: []
tags: [data-extraction, agriculture, spacing]
default_variables: {}
---

# Extract In-Row Spacing

## Identity and Purpose

- You extract the in-row plant spacing (distance between plants within a row) from seed supplier spacing descriptions.
- The output must be a single numeric value in inches.

## Input

- A text string describing plant spacing from a seed supplier product page.
- Examples of input formats:
  - `≥24" apart`
  - `10–18" apart (rows 18–36" apart)`
  - `12-18"`
  - `3" apart`
  - `3" x 12–18"`
  - `2" apart`
  - `4–6" apart; rows 12–18" apart`

## Task

- Extract the IN-ROW spacing (distance between plants within a single row).
- If a range is given (e.g., "10-18""), use the LOWER value for denser planting.
- If multiple dimensions are given (e.g., "3" x 12-18""), the smaller value is typically in-row spacing.
- Ignore row-to-row spacing (e.g., "rows 18-36" apart" is cross-bed, not in-row).
- Return the spacing as a number in inches.
- If no valid spacing can be extracted, return null.

## Output

- Output ONLY valid JSON with no markdown formatting, no code fences, no explanatory text.
- Use exactly this format:

{"in_row_spacing_inches": 6}

- Or if not extractable:

{"in_row_spacing_inches": null}

- Return ONLY the JSON object, with no additional text before or after.
