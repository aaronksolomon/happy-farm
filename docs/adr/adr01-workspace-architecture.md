# ADR01: Happy Farm Analytics Workspace Architecture

**Author:** Aaron Solomon, Claude Sonnet 4.5
**Date:** December 2025
**Status:** Proposed

## Context

Happy Farm (https://deerparkmonastery.org/initiatives/deer-park-happy-farm/) needs tools for analytics, task scheduling, planning, and seed management. The workspace should support quick iteration and easy sharing with stakeholders and team members.

**Key Requirements:**
- Fast generation of spreadsheet views for analysis
- Export to Google Sheets and Excel for collaboration
- Flexible data transformation workflow
- Simple enough for solo maintenance
- Leverage AI tools within VS Code for data manipulation

## Decision

Build a **lightweight Python-based analytics workspace** with this workflow:

```
Markdown/CSV/XLSX source files
    ↓
AI transforms / prompting (VS Code AI tools)
    ↓
Pandas DataFrames (analysis + visualization)
    ↓
Export to XLSX
    ↓
Share or reimport for further analysis
```

**Tech Stack:**
- **Python + Pandas**: Core data manipulation
- **Jupyter notebooks** (optional): For exploratory analysis with inline visualization
- **openpyxl/xlsxwriter**: Excel export with formatting
- **AI-assisted transforms**: Use Claude Code for data massage/cleanup
- **Git**: Local versioning (no GitHub needed initially)

**Data Organization:**
- `data/seeds/` - Master seed lists and research
- `data/schedules/` - Task schedules and planning
- `data/analytics/` - Analysis outputs
- `scripts/` - Reusable transformation scripts
- `notebooks/` - Jupyter notebooks for exploratory work
- `exports/` - Generated spreadsheets for sharing (gitignored)

**Workflow Pattern:**

1. **Source Data**: Maintain master data in simple formats
   - Markdown for seed research notes
   - CSV for structured lists
   - XLSX for complex tables with formatting

2. **Transform**: Use AI prompts to clean/reshape data
   - "Convert this markdown seed list to CSV with columns X, Y, Z"
   - "Add planting date calculations based on these rules"
   - "Merge these two datasets on variety name"

3. **Analyze**: Load into pandas for views/calculations
   ```python
   df = pd.read_csv('data/seeds/master_list.csv')
   # Quick analysis, pivot tables, filtering
   ```

4. **Export**: Generate shareable spreadsheets
   ```python
   df.to_excel('exports/planting_schedule_2026.xlsx',
               sheet_name='Schedule', index=False)
   ```

5. **Iterate**: Reimport exports if stakeholders add data
   ```python
   updated = pd.read_excel('exports/planting_schedule_2026.xlsx')
   # Process changes, merge back to master
   ```

**Best Practices:**
- Keep master data in `data/` (version controlled)
- Keep exports in `exports/` (gitignored, regenerable)
- Use descriptive filenames with dates: `tomato_varieties_2025-12-20.csv`
- Scripts should be idempotent (safe to re-run)
- Prefer simple pandas operations over complex custom code
- Use AI for one-off transforms, scripts for repeatable operations

## Alternatives Considered

### Option 1: Pure Spreadsheets (Status Quo)
- ✅ Familiar to all stakeholders
- ❌ Hard to version control
- ❌ Limited automation
- ❌ Difficult to reproduce analyses

### Option 2: Full Web Dashboard (e.g., Streamlit, Dash)
- ✅ Interactive exploration
- ✅ Real-time collaboration
- ❌ Overkill for current needs
- ❌ Deployment/hosting overhead
- ❌ More complex to maintain solo

### Option 3: Database-backed System
- ✅ Structured queries
- ✅ Better for large datasets
- ❌ Too much infrastructure for farm-scale data
- ❌ Harder to ad-hoc explore with AI assistance

### Option 4: Chosen - Python/Pandas with AI Workflow
- ✅ Flexible and fast for small-to-medium data
- ✅ Works well with AI code generation
- ✅ Easy to generate stakeholder-friendly exports
- ✅ Simple git-based versioning
- ✅ No deployment needed
- ❌ Requires some Python knowledge (but AI helps!)

## Consequences

### Positive
- Quick iteration on data views and analyses
- Easy sharing via familiar spreadsheet formats
- AI tools accelerate data transformation tasks
- Git provides audit trail for data changes
- Low maintenance burden for solo developer
- Can scale up to web dashboard later if needed

### Negative
- Stakeholder edits require manual reimport/merge
- No real-time collaboration (but not needed yet)
- Pandas has learning curve (mitigated by AI assistance)
- Excel exports are static snapshots

## Open Questions

- Should we set up automated exports on a schedule? (Probably not yet)
- How to handle conflicts when reimporting stakeholder edits?
- Need for data validation rules before exports?
- Would a simple CLI help (e.g., `farm export seeds --format=xlsx`)?

## Implementation Notes

### Quick Start Setup

```bash
# Project structure
mkdir -p data/{seeds,schedules,analytics}
mkdir -p scripts notebooks exports

# Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install pandas openpyxl jupyter matplotlib seaborn

# Optional: VS Code extensions
# - Jupyter
# - Python
# - Data Wrangler (pandas DataFrame viewer)
```

## Addendum (2026-01-03) - Dependency Policy

The workspace now uses a single dependency group. All runtime and tooling
dependencies live in `[project].dependencies` to keep setup simple and avoid
multi-group state.

## Addendum (2026-01-03) - CLI Error Handling

Scripts should handle errors gracefully by printing `Error: ...` and returning
a non-zero exit code rather than dumping stack traces.

### Example: Seed List Transform

**Input** (`data/seeds/master_seed_list.md`):
```markdown
## Tomatoes
- Cherokee Purple: Heirloom, 80 days, indeterminate
- Early Girl: Hybrid, 50 days, determinate
```

**AI Prompt**: "Convert to CSV with columns: variety, type, days_to_harvest, growth_habit"

**Output** (`data/seeds/tomatoes.csv`):
```csv
variety,type,days_to_harvest,growth_habit
Cherokee Purple,Heirloom,80,Indeterminate
Early Girl,Hybrid,50,Determinate
```

**Analysis** (pandas):
```python
import pandas as pd

df = pd.read_csv('data/seeds/tomatoes.csv')
early_varieties = df[df['days_to_harvest'] < 60]
print(f"Found {len(early_varieties)} early-maturing varieties")

# Export for stakeholders
df.to_excel('exports/tomato_varieties_2025.xlsx', index=False)
```

---

**Next Steps:**
1. Set up Python environment with pandas, openpyxl
2. Create initial data directory structure
3. Convert master seed list to structured format
4. Write first transform script or notebook
5. Test export workflow with sample data
