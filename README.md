# Happy Farm Analytics

Analytics, task scheduling, and planning tools for [Deer Park Happy Farm](https://deerparkmonastery.org/initiatives/deer-park-happy-farm/).

## Quick Overview

This is a lightweight Python workspace for farm data analysis and planning. The workflow is simple:

**Markdown/CSV/XLSX** → **AI transforms** → **Pandas analysis** → **Excel exports** → **Share with team**

## Project Structure

```
happy-farm/
├── data/
│   ├── seeds/          # Master seed lists and research
│   ├── schedules/      # Task schedules and planning
│   └── analytics/      # Analysis outputs
├── scripts/            # Reusable transformation scripts
├── notebooks/          # Jupyter notebooks for exploration
├── exports/            # Generated spreadsheets (gitignored)
└── docs/               # ADRs and documentation
```

## Workflow

1. **Source Data**: Keep master data in simple formats (Markdown notes, CSV lists, XLSX tables)
2. **Transform**: Use AI to clean/reshape data or write reusable scripts
3. **Analyze**: Load into pandas for calculations and views
4. **Export**: Generate Excel files for stakeholders
5. **Iterate**: Reimport stakeholder edits and merge back to master

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for Python environment and dependency management.

```bash
# Install uv (if not already installed)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies and create virtual environment
uv sync

# Create directory structure
mkdir -p data/{seeds,schedules,analytics}
mkdir -p scripts notebooks exports
```

## Example Usage

Run Python scripts and notebooks using `uv run`:

```bash
# Run a script
uv run scripts/scrape_plant_data.py --input data/plants/vegetable-data.csv

# Start Jupyter
uv run jupyter notebook

# Run Python interactively
uv run python
```

Quick analysis example:

```python
import pandas as pd

# Load seed data
df = pd.read_csv('data/seeds/tomatoes.csv')

# Quick analysis
early_varieties = df[df['days_to_harvest'] < 60]
print(f"Found {len(early_varieties)} early-maturing varieties")

# Export for sharing
df.to_excel('exports/tomato_varieties_2025.xlsx', index=False)
```

## Key Principles

- **Master data lives in `data/`** - Version controlled, source of truth
- **Exports live in `exports/`** - Gitignored, regenerable snapshots
- **Use AI for one-offs** - Quick data transforms via prompts
- **Scripts for repeatables** - Anything you'll run multiple times
- **Keep it simple** - Favor straightforward pandas over clever code

## Documentation

- [ADR01: Workspace Architecture](docs/adr01-workspace-architecture.md) - Full rationale and design decisions
- [ADR02: Plant Data Web Scraping Architecture](docs/adr/adr02-plant-data-web-scraping.md) - Hybrid SDSC/JS scraping plan

## Plant Data Scraping

Enrich plant CSVs with supplier growing info using `scripts/scrape_plant_data.py`:

```bash
# Example (cached dev run)
uv run scripts/scrape_plant_data.py \
  --input data/plants/vegetable-data.csv \
  --output data/plants/vegetable-data-enriched.csv \
  --use-cache

# Retry only failed rows
uv run scripts/scrape_plant_data.py --retry-failed

# Process only new rows (skip already successful)
uv run scripts/scrape_plant_data.py --only-new
```

**Requirements:**

- SDSC rows rely on `httpx`, `beautifulsoup4`, and `tenacity` (installed via `uv sync`)
- JS (Johnny's Seeds) rows require `tnh-gen` CLI tool installed separately via pipx

## Tech Stack

- **uv**: Python environment and dependency management
- **Python + Pandas**: Data manipulation
- **Jupyter**: Exploratory analysis (optional)
- **openpyxl/xlsxwriter**: Excel export with formatting
- **Git**: Local versioning
- **VS Code + Claude Code**: AI-assisted development

## Development Workflow with uv

```bash
# First time setup
uv sync                          # Install all dependencies

# Running scripts
uv run scripts/scrape_plant_data.py --use-cache
uv run scripts/extract_plant_subset.py

# Interactive Python
uv run python                    # Python REPL with project dependencies
uv run jupyter notebook          # Start Jupyter

# Add new dependencies
uv add package-name              # Add to pyproject.toml and install
uv add --dev package-name        # Add as dev dependency

# Update dependencies
uv sync                          # Sync after pulling changes
```

---

**Maintainer:** Paul Hapman
**Started:** December 2025
