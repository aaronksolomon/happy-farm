# Happy Farm - Workflow & Agent Guide

> **Last Updated**: 2025-12-21
> **Purpose**: Project-specific information for AI agents and collaborators

---

## Project Overview

This project manages planning, inventory, and documentation for a home farm in Zone 10a (Escondido, CA - North San Diego County).

---

## Directory Structure

```text
happy-farm/
├── data/
│   └── seeds/           # Seed inventory and planning documents
├── scripts/             # Planning scripts and notes
├── WORKFLOW.md          # This file - workflow and agent guide
└── README.md            # Project documentation
```

---

## Google Drive Integration

### Shared Drive Location

**Local mount path**:
```
/Users/phapman/Library/CloudStorage/GoogleDrive-aaron.kyle.solomon@gmail.com/Shared drives/happy-farm-data
```

**Usage**: This is the primary location for sharing documents with stakeholders who may not have direct access to the git repository.

### Document Export Workflow

When exporting documents for stakeholder review:

1. Generate/update the document in the local `data/` directory (markdown format preferred)
2. Export to DOCX using pandoc:
   ```bash
   pandoc <source.md> -o <output.docx>
   ```
3. Copy to Google Drive shared folder:
   ```bash
   cp <output.docx> "/Users/phapman/Library/CloudStorage/GoogleDrive-aaron.kyle.solomon@gmail.com/Shared drives/happy-farm-data/"
   ```

**Example**:
```bash
# Export seed inventory
pandoc data/seeds/seed-inventory.md -o data/seeds/seed-inventory.docx
cp data/seeds/seed-inventory.docx "/Users/phapman/Library/CloudStorage/GoogleDrive-aaron.kyle.solomon@gmail.com/Shared drives/happy-farm-data/"
```

---

## Document Formats

- **Source of truth**: Markdown files in git repository
- **Stakeholder sharing**: DOCX exports via Google Drive
- **Conversion tool**: pandoc (installed locally)

---

## Project Context

### Location Details
- **Zone**: 10a
- **Region**: Escondido, CA (North San Diego County)
- **Climate**: Hot, dry summers; mild winters; coastal/inland transition zone

### Primary Data Sources
- **San Diego Seed Company** (SDSC) - local, regional varieties
- **Johnny's Selected Seeds** (JS) - specialty and organic varieties

---

## Notes for AI Agents

- When asked to export documents for sharing, use the Google Drive path above
- Maintain markdown as source, DOCX as export format
- Keep seed inventory organized by: Plant Type → Season → Crop Group → Packet Type
- Reference Zone 10a planting windows when making recommendations
