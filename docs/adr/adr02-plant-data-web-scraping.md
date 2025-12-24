# ADR02: Plant Data Web Scraping Architecture

**Author:** Aaron Solomon, Claude Sonnet 4.5
**Date:** 2025-12-22
**Status:** Proposed

## Context

The vegetable-data.csv (and related plant CSVs) contain URLs to seed supplier product pages. These pages contain rich growing information that would be valuable to include in our planting database:

- Planting season, soil temperature, planting depth
- Days to germination, days to maturity
- Spacing requirements (thin to, final spacing)
- Plant dimensions (height, spread)
- Seed counts, botanical names
- Growing method recommendations

**Current State:**

- All vegetables in `data/plants/vegetable-data.csv` have URLs
- Two primary suppliers with different page structures:
  - **San Diego Seed Company (SDSC)**: Structured HTML table format
  - **Johnny's Selected Seeds (JS)**: Narrative/paragraph format

**Challenge:**

- SDSC data is well-structured and easily parseable
- JS data is embedded in prose and requires AI extraction
- Need to handle both formats and add ~15+ columns to existing CSV

## Decision

Build a **two-stage web scraping pipeline** that:

1. **Stage 1: HTML Extraction** - Fetch and parse supplier pages
2. **Stage 2: Data Normalization** - Extract structured data using format-specific strategies

### Architecture Overview

```text
vegetable-data.csv (with URLs)
    ↓
[Scraper] Fetch HTML for each URL
    ↓
[Parser] Extract data based on supplier:
    - SDSC: BeautifulSoup HTML table parsing
    - JS: AI-based text extraction via tnh-gen
    ↓
[Normalizer] Map to common schema
    ↓
enriched-vegetable-data.csv (original + scraped columns)
```

### Tech Stack

- **httpx**: HTTP requests with proper headers/rate limiting
- **BeautifulSoup4**: HTML parsing for structured data (SDSC)
- **tnh-gen** (from tnh-scholar): AI-based extraction for narrative text (JS)
- **pandas**: CSV I/O and data merging
- **tenacity**: Retry logic for failed requests

### Proposed Schema Extensions

New columns to add to plant CSV:

```python
# Columns expected from SDSC
SDSC_COLUMNS = [
    'product_weight',       # e.g., "0.15G"
    'planting_season',      # e.g., "Warm", "Cool"
    'soil_temp',            # e.g., "65° F+"
    'planting_depth',       # e.g., "1/4\""
    'area_to_sow',          # e.g., "50' row"
    'days_to_germ',         # e.g., "3-10+"
    'days_to_maturity',     # e.g., "65+"
    'best_planting_method', # e.g., "Transplant", "Direct sow"
    'thin_to',              # e.g., "≥2\" apart"
    'final_spacing',        # e.g., "≥24\" apart"
    'succession',           # e.g., "NA", "2 weeks"
    'approx_seed_count',    # e.g., "60"
    'botanical_name',       # e.g., "Solanum lycopersicum"
    'plant_spread',         # e.g., "24-36\""
    'plant_height',         # e.g., "36-90\""
]

# Columns expected from JS (overlaps with SDSC, plus JS-specific fields)
JS_COLUMNS = [
    'scientific_name',      # e.g., "Solanum melongena"
    'planting_depth',       # e.g., "1/4\""
    'days_to_maturity',     # e.g., "65+"
    'final_spacing',        # e.g., "18-24\" apart"
    'approx_seed_count',    # Calculated from "800 plants/1,000 seeds"
    'botanical_name',       # May be listed as scientific_name
    # Note: JS may have additional culture/maintenance notes in text
]

# Metadata columns (both suppliers)
METADATA_COLUMNS = [
    'scrape_status',        # "success", "failed", "partial"
    'scrape_date',          # ISO timestamp
]

# All columns combined (union of SDSC + JS + metadata)
ALL_SCRAPED_COLUMNS = list(set(SDSC_COLUMNS + JS_COLUMNS + METADATA_COLUMNS))
```

**Missing Value Strategy:**

- `"NOT_FOUND"` - Expected field for this supplier but not found on page (requires investigation)
- `"N/A"` - Field not available from this supplier (normal)
- Empty string - Field exists but has no value (rare, treat as NOT_FOUND)

### Implementation Approach

#### SDSC Parser (Structured HTML)

HTML pattern:

```html
<table class="woocommerce-product-attributes">
  <tr class="woocommerce-product-attributes-item--attribute_pa_planting-season">
    <th>Planting Season</th>
    <td><p>Warm</p></td>
  </tr>
</table>
```

Strategy:

```python
def parse_sdsc(html: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='woocommerce-product-attributes')

    data = {}
    for row in table.find_all('tr'):
        label = row.find('th').text.strip()
        value = row.find('td').text.strip()
        data[normalize_key(label)] = value

    return data
```

#### JS Parser (AI Extraction)

Text pattern:

```html
<div class="c-accordion__body">
  SCIENTIFIC NAME: Solanum melongena
  CULTURE: Eggplants require fertile soil...
  DAYS TO MATURITY: From date of transplanting.
  TRANSPLANTING: Sow 4 seeds/in., ¼" deep...
</div>
```

Strategy:

```python
def parse_js_with_ai(html: str) -> dict:
    # Extract growing info section
    soup = BeautifulSoup(html, 'html.parser')
    accordion = soup.find('div', class_='c-accordion__body')
    text_content = accordion.get_text()

    # Use tnh-gen for structured extraction
    prompt = f"""
    Extract the following planting data from this text in JSON format:
    - planting_season (Warm/Cool)
    - soil_temp (e.g., "65° F+")
    - planting_depth (e.g., "1/4\"")
    - days_to_germ (e.g., "3-10+")
    - days_to_maturity (e.g., "65+")
    - best_planting_method (Transplant/Direct sow)
    - final_spacing (e.g., "18-24\"")
    - approx_seed_count (number)
    - botanical_name (e.g., "Solanum melongena")

    Text:
    {text_content}

    Return only valid JSON. Use null for missing values.
    """

    result = tnh_gen.generate(prompt, model="claude-haiku")
    return json.loads(result)
```

#### HTML Caching Strategy

During development/debugging, cache HTML body content to avoid repeated requests:

```python
import hashlib
import tempfile
from pathlib import Path

def get_cache_path(url: str) -> Path:
    """Generate cache filename from URL hash in system temp directory."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_dir = Path(tempfile.gettempdir()) / 'happy-farm-scraper'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / f"{url_hash}.html"

def fetch_with_cache(url: str, use_cache: bool = True) -> str:
    """Fetch URL with optional caching of HTML body."""
    cache_path = get_cache_path(url)

    if use_cache and cache_path.exists():
        return cache_path.read_text()

    html = fetch_url(url)

    # Extract and cache body content only (not headers/scripts)
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.find('body')
    body_html = str(body) if body else html

    if use_cache:
        cache_path.write_text(body_html)

    return body_html
```

**Benefits of using `tempfile`:**

- System manages temp directory location automatically
- No manual directory creation needed
- Automatic cleanup on system reboot
- No git tracking concerns

#### Main Scraper Pipeline

```python
import pandas as pd
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def fetch_url(url: str) -> str:
    """Fetch URL with retries and rate limiting."""
    headers = {'User-Agent': 'HappyFarmBot/1.0 (educational research)'}
    response = httpx.get(url, headers=headers, timeout=10.0)
    response.raise_for_status()
    return response.text

def scrape_plant_data(csv_path: str, output_path: str, use_cache: bool = False):
    """Main scraper pipeline."""
    df = pd.read_csv(csv_path)

    # Add scraped columns
    for col in ALL_SCRAPED_COLUMNS:
        if col not in df.columns:
            df[col] = None

    for idx, row in df.iterrows():
        url = row['url']
        supplier = row['supplier']

        try:
            html = fetch_with_cache(url, use_cache=use_cache)

            if supplier == 'SDSC':
                data = parse_sdsc(html)
                expected_cols = SDSC_COLUMNS
            elif supplier == 'JS':
                data = parse_js_with_ai(html)
                expected_cols = JS_COLUMNS
            else:
                data = {}
                expected_cols = []

            # Merge scraped data into row
            for key, value in data.items():
                if key in df.columns:
                    df.at[idx, key] = value

            # Mark expected but missing fields as NOT_FOUND
            for col in expected_cols:
                if col in df.columns and (pd.isna(df.at[idx, col]) or df.at[idx, col] == ''):
                    if col not in data:
                        df.at[idx, col] = 'NOT_FOUND'

            # Mark non-expected fields as N/A
            all_possible_cols = set(SDSC_COLUMNS + JS_COLUMNS)
            for col in all_possible_cols:
                if col not in expected_cols and col in df.columns:
                    if pd.isna(df.at[idx, col]) or df.at[idx, col] == '':
                        df.at[idx, col] = 'N/A'

            df.at[idx, 'scrape_status'] = 'success'
            df.at[idx, 'scrape_date'] = pd.Timestamp.now().isoformat()

            # Rate limiting (only if not using cache)
            if not use_cache:
                time.sleep(1)  # 1 second between requests

        except Exception as e:
            df.at[idx, 'scrape_status'] = 'failed'
            print(f"Failed to scrape {url}: {e}")

    df.to_csv(output_path, index=False)
    print(f"Saved enriched data to {output_path}")
```

### Usage

```bash
# Development: Use cache to avoid repeated requests while debugging
python scripts/scrape_plant_data.py \
  --input data/plants/vegetable-data.csv \
  --output data/plants/vegetable-data-enriched.csv \
  --use-cache

# Production: Fresh scrape without cache
python scripts/scrape_plant_data.py \
  --input data/plants/vegetable-data.csv \
  --output data/plants/vegetable-data-enriched.csv

# Re-run for failed rows only
python scripts/scrape_plant_data.py \
  --input data/plants/vegetable-data-enriched.csv \
  --output data/plants/vegetable-data-enriched.csv \
  --retry-failed
```

## Alternatives Considered

### Option 1: Manual Data Entry

- ✅ Most accurate
- ❌ Extremely time-consuming (~90 varieties × 5 min each = 7.5 hours)
- ❌ Error-prone for repetitive data

### Option 2: Pure BeautifulSoup Parsing (Both Suppliers)

- ✅ Fast and deterministic
- ❌ JS format is too variable/narrative for reliable regex/CSS selectors
- ❌ Would require extensive pattern matching

### Option 3: Full AI Scraping (Both Suppliers)

- ✅ Handles any format
- ❌ Slower (API calls for every page)
- ❌ More expensive
- ❌ Overkill for SDSC's structured data

### Option 4: Chosen - Hybrid Scraper

- ✅ Fast for SDSC (direct HTML parsing)
- ✅ Accurate for JS (AI extraction)
- ✅ Leverages existing tnh-gen infrastructure
- ✅ Extensible to other suppliers
- ❌ Requires both parsing strategies in codebase

## Consequences

### Positive

- Enriches plant database with 15+ critical growing parameters
- Automated process can re-run for new varieties
- Hybrid approach balances speed and accuracy
- Rate limiting respects supplier servers
- Retry logic handles transient failures
- Scrape status tracking enables incremental updates

### Negative

- Dependency on tnh-scholar's tnh-gen tool (`~/projects/tnh-scholar`)
- AI extraction may occasionally misparse JS data (requires manual validation)
- CSV schema grows significantly (consider splitting to related tables later)
- Scraper brittleness if supplier websites change structure
- AI costs for JS scraping (~$0.01-0.05 per page estimate)

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Supplier blocks scraper | Use polite rate limiting, descriptive User-Agent, consider robots.txt |
| HTML structure changes | Version scraper code, add integration tests with sample pages |
| AI misparses JS data | Add validation step, manual review of first 5-10 results |
| Large CSV becomes unwieldy | Future: split to `plants.csv` + `plant_growing_info.csv` with foreign key |

## Resolved Design Questions

### Q: Should we scrape flower-data.csv and herb-data.csv too?

**A:** Yes. Herbs will be scraped alongside vegetables. Prototype on vegetable-data.csv first, then apply to herb-data.csv. Flowers can follow if needed.

### Q: How to handle missing/null values in scraped data?

**A:** Use supplier-specific field expectations:

- `"NOT_FOUND"` - Expected field missing (requires investigation)
- `"N/A"` - Field not available from this supplier (normal)
- SDSC expected fields: product_weight, planting_season, soil_temp, etc.
- JS expected fields: scientific_name, botanical_name, spacing, etc.

### Q: Should we cache HTML locally for debugging/re-parsing?

**A:** Yes. Cache `<body>` content only (not headers/scripts) using Python's `tempfile` module (system temp directory). Use `--use-cache` flag during development. Skip caching in production runs. System manages cleanup automatically.

### Q: Do we need a separate validation script to flag suspicious values?

**A:** Not initially. Start with manual hand-validation by reviewing scraped results. Add basic type checks (is_number, is_text). Future enhancement: automated outlier detection script if patterns emerge.

## Open Questions

- Should botanical names be used to cross-validate variety correctness?
- How to handle partial scrapes (some fields found, others not)?
- Should we track scrape duration per URL for performance monitoring?

## Implementation Plan

### Phase 1: SDSC Scraper (Low Risk)

1. Install dependencies: `pip install httpx beautifulsoup4 tenacity`
2. Write SDSC parser with unit tests using sample HTML
3. Test on 5 SDSC vegetables, manually validate results
4. Run full SDSC scrape (~40 varieties)

### Phase 2: JS AI Scraper (Higher Risk)

1. Verify tnh-gen is accessible from happy-farm project
2. Write JS parser using tnh-gen
3. Test on 5 JS vegetables, manually validate extraction quality
4. Tune AI prompt if needed based on validation
5. Run full JS scrape (~50 varieties)

### Phase 3: Integration & Validation

1. Merge scraped data with original CSV
2. Add basic type validation (is_number for counts, is_text for names)
3. Manual hand-validation: review 10-20% of results per supplier
4. Update documentation with new column definitions

### Phase 4: Apply to Herbs

1. Run scraper on herb-data.csv using same pipeline
2. Validate herb results
3. Document any herb-specific quirks or differences

### Phase 5: Iteration (If Needed)

1. Address any failed scrapes
2. Tune AI prompts based on validation findings
3. Add automated outlier detection if needed
4. Document maintenance process for future updates

## Dependencies

- **Python packages**: httpx, beautifulsoup4, tenacity, pandas
- **External tool**: tnh-scholar's tnh-gen (for AI extraction)
  - Location: `~/projects/tnh-scholar`
  - Design docs: `~/projects/tnh-scholar/docs/architecture/tnh-gen/` (ADRs)
  - Integration: Python import or CLI (TBD during implementation)

## References

- San Diego Seed Company product page structure (see initial requirements)
- Johnny's Selected Seeds product page structure (see initial requirements)
- tnh-scholar project: `~/projects/tnh-scholar`
- tnh-gen design: `~/projects/tnh-scholar/docs/architecture/tnh-gen/` (ADRs)

---

**Next Steps:**

1. Review and approve ADR
2. Install Python dependencies
3. Begin Phase 1 implementation
