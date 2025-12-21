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

```bash
# Create Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install core dependencies
pip install pandas openpyxl jupyter matplotlib seaborn

# Create directory structure
mkdir -p data/{seeds,schedules,analytics}
mkdir -p scripts notebooks exports
```

## Example Usage

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

## Tech Stack

- **Python + Pandas**: Data manipulation
- **Jupyter**: Exploratory analysis (optional)
- **openpyxl/xlsxwriter**: Excel export with formatting
- **Git**: Local versioning
- **VS Code + Claude Code**: AI-assisted development

---

**Maintainer:** Paul Hapman
**Started:** December 2025
