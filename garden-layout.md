# Garden Layout Specifications

## Overall Garden Configuration

The Happy Farm garden consists of **3 gardens** with consistent dimensions and spacing.

### Garden Count and Row Configuration

- **Total gardens:** 3
- **Rows per garden:** 12
- **Total rows:** 36 (3 gardens × 12 rows)

### Row Dimensions

- **Row length:** 80 ft
- **Row width:** 30"
- **Row spacing:** 18" (between rows within a garden)

### Garden Spacing

- **Between gardens:** 4 ft
- **Edge spacing:** 3 ft (on outer edges of garden area)
- **End borders:** 5 ft (at ends of rows)

## Layout Diagram

```
Edge: 3 ft
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Garden 1 (12 rows)                                │
│  ├─ Row 1  [30" wide × 80 ft long]                │
│  ├─ 18" spacing                                     │
│  ├─ Row 2                                           │
│  ├─ 18" spacing                                     │
│  ...                                                │
│  └─ Row 12                                          │
│                                                     │
│  ──── 4 ft spacing ────                            │
│                                                     │
│  Garden 2 (12 rows)                                │
│  ├─ Row 13                                          │
│  ...                                                │
│  └─ Row 24                                          │
│                                                     │
│  ──── 4 ft spacing ────                            │
│                                                     │
│  Garden 3 (12 rows)                                │
│  ├─ Row 25                                          │
│  ...                                                │
│  └─ Row 36                                          │
│                                                     │
└─────────────────────────────────────────────────────┘
Edge: 3 ft

End borders: 5 ft on each end
```

## Total Dimensions

### Width Calculations

Per garden:
- 12 rows × 30" = 360" = 30 ft
- 11 gaps × 18" = 198" = 16.5 ft
- **Total per garden:** 46.5 ft

Total width:
- 3 gardens × 46.5 ft = 139.5 ft
- 2 inter-garden spaces × 4 ft = 8 ft
- 2 edge spaces × 3 ft = 6 ft
- **Total width:** 153.5 ft

### Length

- Row length: 80 ft
- Borders: 5 ft × 2 = 10 ft
- **Total length:** 90 ft

## Current Planning System

The bed-geometry configuration at [data/plans/config/bed-geometry.jsonl](data/plans/config/bed-geometry.jsonl) represents a **subset** of the full garden layout:
- Uses 12 beds (likely representing one garden or a partial planning area)
- Divides beds into 5 ft planning blocks for succession planting
- Total of 80 ft length matches row length specification

## Notes

- The planning system currently works with a subset of the full garden
- Physical layout specifications documented here represent the complete farm infrastructure
- Individual garden beds can be planned and tracked independently using the existing tools
