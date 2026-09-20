# Equipment size — synthetic bookings

**Pack:** `domains/equipment-size/`  
**File:** `data/bookings.csv` (~250 rows; regenerate with `--n 600` for full)  
**No real shipper PII.**

## Columns

| name | role |
| --- | --- |
| `booking_id` | id |
| `event_ts` | time (Thinking) |
| `trade_lane` | group (Thinking) |
| `pol` / `pod` | high-card ports |
| `shipper_id` | high-card |
| `commodity` | low-card |
| `booking_note` / `ops_note` | free text (often missing) |
| `weight_kg` / `volume_cbm` | numeric (missings) |
| `temp_min_c` | numeric (missings = ambient) |
| `hazmat` | 0/1 |
| `current_equip` | 20GP/40GP/40HC/20RF/40RF |
| `teu_request` | numeric |
| `cargo_value_usd` | numeric |
| `reefer_candidate` | 0/1 → reefer playbook gate |
| `hc_upsell` | 0/1 → 40HC upsell gate |
| `confirm_dry_ok` | 0/1 → confirm dry gate |
| `hold_reefer_slot` | 0/1 → reefer hold gate |
| `special_equip_fit` | label 0/1 |

## Playbook

reefer_hold → upsell_40hc → confirm_special → confirm_dry → monitor

## Regenerate

```bash
python scripts/gen_coda_packs.py --pack equipment-size --n 600
```
