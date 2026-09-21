# Stow-fit — synthetic cargo shipments

**Pack:** `domains/stow-fit/`  
**File:** `data/shipments.csv` (~250–600 rows)  
**No real shipper PII.**

## Honest scope

This is a **tabular suggestion head**: given dims / weight / hazmat / temp / value,
score **fit risk** and suggest equipment/mode actions (`dry20`, `dry40`, `hc40`,
`reefer`, `air_belly`, `ltl_truck`).

It is **not** a 3D bin packer, container loading optimizer, or WMS slotting engine.

## Columns

| name | role |
| --- | --- |
| `shipment_id` | id |
| `event_ts` | time (Thinking) |
| `lane_id` | group (Thinking) |
| `origin` / `dest` | high-card |
| `carrier` | fixture multi-carrier label |
| `client_id` | fixture multi-client label |
| `commodity` | low-card |
| `booking_note` / `ops_note` | free text (often missing) |
| `pieces` / `length_cm` / `width_cm` / `height_cm` | dims (missings) |
| `weight_kg` / `volume_cbm` | numeric (missings) |
| `temp_min_c` | numeric (missings = ambient) |
| `hazmat` / `urgency` | 0/1 |
| `cargo_value_usd` | numeric / desk money ticker |
| `requested_mode` | booked mode (dry20/dry40/hc40/reefer/air_belly/ltl_truck) |
| `suggested_mode` | demo suggestion head (feature_exclude — not a packing plan) |
| `reefer_hold` / `upsell_40hc` / `split_load` / `air_expedite` / `book_ltl` | playbook gates |
| `fit_risk` | label 0/1 |

## Playbook

reefer_hold → upsell_40hc → split_load → air_expedite → book_ltl → monitor

## Regenerate

First `tabpfn-hack demo --domain domains/stow-fit/domain.yaml --mode mock` auto-generates
`data/shipments.csv` (250 rows) if missing — same as other coda packs.

```bash
python scripts/gen_coda_packs.py --pack stow-fit --n 600
```
