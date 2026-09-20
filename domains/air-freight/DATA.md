# Air freight — synthetic AWB shipments

**Pack:** `domains/air-freight/`  
**File:** `data/shipments.csv` (~250–600 rows)  
**No real shipper / airline PII.**

## Columns

| name | role |
| --- | --- |
| `awb_id` | id |
| `event_ts` | time (Thinking) |
| `flight_id` | group (Thinking) |
| `route_id` / `origin` / `dest` | high-card lane |
| `carrier` | fixture multi-carrier label |
| `client_id` | fixture multi-client label |
| `commodity` | low-card |
| `handling_note` / `ops_note` | free text (often missing) |
| `pieces` / `weight_kg` / `volume_cbm` | numeric (missings) |
| `is_aog` | 0/1 aircraft-on-ground spare |
| `connection_minutes` / `connection_tight` | MCT features |
| `belly_available` / `freighter_available` | capacity flags |
| `temp_sensitive` | 0/1 |
| `cargo_value_usd` | numeric |
| `delay_hours_p50` | numeric |
| `projected_delay_cost_usd` | money rollup for desk ticker |
| `expedite_aog` / `hold_for_connection` / `rebook_belly` | playbook gates |
| `miss_connection_risk` | label 0/1 |

## Playbook

expedite_aog → hold_for_connection → rebook_belly → monitor

## Regenerate

```bash
python scripts/gen_coda_packs.py --pack air-freight --n 600
```
