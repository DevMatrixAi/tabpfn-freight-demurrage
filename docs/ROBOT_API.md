# Robot / TMS consumer API

HTTP endpoints a **robot or TMS** can call that wrap the same TabPFN `suggest_actions` / triage path as the human ops board.

**Honest scope:** this is a **decisions API**, not crane control and not a live TOS. Humans or robots call the **same action playbook**.

Served by the desk FastAPI app (`tabpfn-hack desk`). OpenAPI: http://127.0.0.1:8765/docs (tag **robot/TMS consumer API**).

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Liveness + whether `TABPFN_TOKEN` is set + pack list |
| `POST` | `/api/v1/triage` | Fit + HistGBM baseline Δ + playbook actions |
| `POST` | `/api/v1/actions` | Fit + suggested actions on inline rows |

## Modes

- **`mock`** — works offline without a token (default; CI / demos).
- **`plus` / `thinking` / `fast`** — when `TABPFN_TOKEN` is set; otherwise fall back to mock with a warning.

## Multi-client / multi-carrier

Optional top-level `client_id` and `carrier` on the request are echoed on the response. If those columns exist on input rows (e.g. air-freight fixtures), they **pass through** onto each action item.

## curl examples

```bash
# Health
curl -s http://127.0.0.1:8765/api/v1/health | jq .

# Triage spine pack (mock)
curl -s -X POST http://127.0.0.1:8765/api/v1/triage \
  -H 'content-type: application/json' \
  -d '{"pack":"freight-demurrage","mode":"mock","max_rows":10}' | jq '.metrics,.action_counts,.actions[0]'

# Triage Terminal49 fixture
curl -s -X POST http://127.0.0.1:8765/api/v1/triage \
  -H 'content-type: application/json' \
  -d '{"fixture":"terminal49","mode":"mock"}' | jq '.n_rows,.action_counts'

# Actions on inline rows (carrier / client_id pass-through)
curl -s -X POST http://127.0.0.1:8765/api/v1/actions \
  -H 'content-type: application/json' \
  -d '{
    "pack":"freight-demurrage",
    "mode":"mock",
    "carrier":"MAEU",
    "client_id":"CLT-001",
    "rows":[
      {"container_id":"C1","event_ts":"2026-07-01T00:00:00Z","vessel_id":"V1","bol_id":"B1","pol":"CNSHA","pod":"USLAX","terminal_note":"delay","weather_alert":"","free_days_left":1,"dwell_days_so_far":8,"teu":1,"cargo_value_usd":10000,"daily_demurrage_usd":100,"blank_sailing":0,"inland_can_beat_freedays":0,"fee_inevitable":1,"cargo_vs_fee_collapse":0,"projected_demurrage_usd":800,"demurrage_risk":1,"carrier":"MAEU","client_id":"CLT-001"},
      {"container_id":"C2","event_ts":"2026-07-01T01:00:00Z","vessel_id":"V1","bol_id":"B2","pol":"CNSHA","pod":"USLAX","terminal_note":"","weather_alert":"","free_days_left":5,"dwell_days_so_far":1,"teu":1,"cargo_value_usd":9000,"daily_demurrage_usd":100,"blank_sailing":0,"inland_can_beat_freedays":1,"fee_inevitable":0,"cargo_vs_fee_collapse":0,"projected_demurrage_usd":0,"demurrage_risk":0,"carrier":"MAEU","client_id":"CLT-001"},
      {"container_id":"C3","event_ts":"2026-07-01T02:00:00Z","vessel_id":"V2","bol_id":"B3","pol":"KRPUS","pod":"NLRTM","terminal_note":"pile","weather_alert":"storm","free_days_left":2,"dwell_days_so_far":6,"teu":2,"cargo_value_usd":20000,"daily_demurrage_usd":150,"blank_sailing":1,"inland_can_beat_freedays":0,"fee_inevitable":0,"cargo_vs_fee_collapse":0,"projected_demurrage_usd":900,"demurrage_risk":1,"carrier":"HLCU","client_id":"CLT-002"},
      {"container_id":"C4","event_ts":"2026-07-01T03:00:00Z","vessel_id":"V2","bol_id":"B4","pol":"KRPUS","pod":"NLRTM","terminal_note":"","weather_alert":"","free_days_left":4,"dwell_days_so_far":2,"teu":1,"cargo_value_usd":8000,"daily_demurrage_usd":75,"blank_sailing":0,"inland_can_beat_freedays":1,"fee_inevitable":0,"cargo_vs_fee_collapse":0,"projected_demurrage_usd":0,"demurrage_risk":0,"carrier":"HLCU","client_id":"CLT-002"}
    ]
  }' | jq '.actions[0],.carrier,.client_id'
```

## Mock smoke (no token)

```bash
TABPFN_TOKEN= python scripts/robot_api_smoke.py
```

Expect: `robot_api_smoke OK (mock)` after health + triage.

## Run

```bash
pip install -e ".[dev,desk]"
tabpfn-hack desk --host 127.0.0.1 --port 8765
# OpenAPI UI: http://127.0.0.1:8765/docs
```
