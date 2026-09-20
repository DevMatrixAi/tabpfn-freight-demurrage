# Freight demurrage — synthetic containers

**Pack:** `domains/freight-demurrage/`  
**File:** `data/containers.csv` (~1200 rows)  
**No PHI / no real shipper PII.**

## Columns

| name | role |
| --- | --- |
| `container_id` | id |
| `event_ts` | time (Thinking group_time) |
| `vessel_id` | group (Thinking group_col) |
| `bol_id` | high-card bill of lading |
| `pol` / `pod` | high-card ports |
| `terminal_note` | free text (often missing) |
| `weather_alert` | free text |
| `free_days_left` | numeric |
| `dwell_days_so_far` | numeric (missings) |
| `teu` | numeric |
| `cargo_value_usd` | numeric |
| `daily_demurrage_usd` | numeric |
| `blank_sailing` | 0/1 → rebook gate |
| `inland_can_beat_freedays` | 0/1 → expedite gate |
| `fee_inevitable` | 0/1 → authorize_fee gate |
| `cargo_vs_fee_collapse` | 0/1 → cancel_booking gate |
| `projected_demurrage_usd` | numeric (for judge spreadsheet) |
| `demurrage_risk` | label 0/1 |

## Playbook

divert → rebook (blank_sailing) → expedite (inland) → authorize_fee → cancel_booking → monitor

## Regenerating the full table

If the repo ships a truncated sample (e.g. 200 rows), regenerate the full ~1200-row `data/containers.csv` with:

```bash
python scripts/gen_synthetic_table.py --domain freight-demurrage --n-rows 1200 \
  --out domains/freight-demurrage/data/containers.csv
```
