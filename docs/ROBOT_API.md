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
```

## Run

```bash
pip install -e ".[dev,desk]"
tabpfn-hack desk --host 127.0.0.1 --port 8765
# OpenAPI UI: http://127.0.0.1:8765/docs
```
