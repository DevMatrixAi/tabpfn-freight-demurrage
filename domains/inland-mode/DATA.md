# Inland mode — synthetic moves

**Pack:** `domains/inland-mode/`  
**File:** `data/moves.csv` (~250 rows; regenerate with `--n 600` for full)  
**No real shipper PII.**

## Columns

| name | role |
| --- | --- |
| `move_id` | id |
| `event_ts` | time (Thinking) |
| `lane_id` | group (Thinking) |
| `terminal` / `destination` | high-card |
| `container_id` | high-card |
| `shipper_note` / `ops_note` | free text |
| `distance_mi` | numeric (missings) |
| `free_days_left` | numeric |
| `truck_transit_h` / `rail_transit_h` | numeric |
| `truck_cost_usd` / `rail_cost_usd` | numeric |
| `cargo_value_usd` | numeric |
| `dwell_at_terminal_d` | numeric |
| `appointment_tight` | 0/1 |
| `chassis_ok` | 0/1 |
| `expedite_flag` | 0/1 |
| `book_rail` / `book_truck` / `expedite_inland` / `hold_for_ramp` | playbook gates |
| `prefer_rail` | label 0/1 |

## Playbook

expedite_inland → book_rail → hold_for_ramp → book_truck → monitor

## Regenerate

```bash
python scripts/gen_coda_packs.py --pack inland-mode --n 600
```
