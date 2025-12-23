# Seed Inventory CSV Improvements + Yield Merge

This note assumes you have:

- `seed-inventory.csv` (your master inventory)
- `harvest-tracker-grit-data.csv` (the GRIT “yields per plant” scrape you uploaded)

## 1) What to fill out in `seed-inventory.csv` right now

### A. Normalize *planting method* and handle `start` / `plant_out`
Use a small, consistent vocabulary for `seeding_method`:

- `direct_sow`
- `transplant` (start in trays, then transplant)
- `slips` (sweet potato slips)
- `perennial` (if you later track nursery starts separately)

Rules:
- If `seeding_method == direct_sow`, set:
  - `start = "N/A"`
  - `plant_out = "N/A"`
  - keep `sow_window` filled
- If `seeding_method == transplant`, set:
  - `days_to_transplant` (see defaults below)
  - keep `start` and `plant_out` if you’re using them as *seasonal windows*

### B. Fill `sow_window` for warm-season crops
In your current file, several warm-season crops have `start`/`plant_out` filled but `sow_window` blank.
I recommend setting `sow_window` to the *direct sow window if you were to direct sow* **or** (more useful) the *tray-start window* for transplants.

For Zone 10a Escondido, conservative windows:

- Tomatoes: `start` **Jan–Mar**, `plant_out` **Mar–Jun**
- Peppers: `start` **Jan–Mar**, `plant_out` **Apr–Jun**
- Eggplant: `start` **Jan–Mar**, `plant_out` **Apr–Jun**
- Cucumbers: `sow_window` **Mar–Aug** (direct sow), or start **Mar–Jun** for transplants
- Summer squash: `sow_window` **Mar–Aug**
- Winter squash: `sow_window` **Apr–Jun**
- Melons: `sow_window` **Apr–Jun**
- Beans: `sow_window` **Apr–Aug**
- Amaranth: `sow_window` **Apr–Aug**

### C. Add/standardize `days_to_transplant` defaults
Good “first-pass” values (tune later):

- Lettuce (heads): 21–35
- Broccoli/Cabbage: 28–45
- Cauliflower: 30–45
- Kale: 25–40
- Celery: 70–90
- Onions: 60–90
- Tomatoes: 35–60
- Peppers/Eggplant: 45–70
- Cucumbers (if transplant): 14–21
- Squash/melons (if transplant): 14–21

### D. Fill `planting_pattern` and `plants_per_linear_ft` (because your beds are long)
Even a simple placeholder helps downstream planning:

Suggested patterns for 30" beds:
- **Brassicas**: 1 row down center @ 18" spacing ⇒ ~0.67 plants/ft
- **Lettuce heads**: 2 rows @ 12" spacing ⇒ ~2.0 plants/ft (combined)
- **Chard**: 1 row @ 12" spacing ⇒ ~1.0 plants/ft
- **Celery**: 2 rows @ 10–12" spacing ⇒ ~2.0–2.4 plants/ft (combined)
- **Beets**: 2 bands, thin to 3–4" ⇒ ~6–8 plants/ft (depends on thinning)
- **Carrots**: 2–3 bands, thin to 2–3" ⇒ ~10–18 plants/ft
- **Radish**: band sow, thin to 1–2" ⇒ ~6–12 plants/ft
- **Peas**: 1 row at trellis, 1–2" spacing ⇒ ~6–12 plants/ft
- **Beans (bush)**: 1–2 rows, 4–6" ⇒ ~2–6 plants/ft
- **Beans (pole)**: 1 row at trellis, 4–6" ⇒ ~2–3 plants/ft

You can refine later; the point is to start capturing “order-of-magnitude” density.

---

## 2) Yield data integration (from your GRIT file)

Your `harvest-tracker-grit-data.csv` is a single-column scrape with lines like:
- `Beets 0.25`
- `Beans, green 0.5-1`

We can parse this into:
- `yield_low` and `yield_high` (numbers)
- optional `yield_unit` (left blank unless you choose a standard, e.g., lb/plant)

Then merge onto your seed inventory by `crop`.

Important: your inventory uses some plural and grouped crop names (e.g., `Beets`, `Cabbage / Asian Brassicas`).
You’ll want a small mapping dictionary for join keys.

---

## 3) Next “high leverage” columns to add
If you want this to become a serious planning tool, these add a lot:

- `germination_days`
- `transplant_temp_min_f`
- `row_spacing_in` and `in_row_spacing_in`
- `succession_interval_days` (especially for salad mixes)
- `harvest_window_days` (how long you can pick per planting)
- `notes_heat` (e.g., cauliflower stress, spinach bolting)
- `notes_pests` (aphids on brassicas, etc.)

---

## 4) Script to enrich and merge yields

See: `enrich_seed_inventory.py` (generated alongside this note).
