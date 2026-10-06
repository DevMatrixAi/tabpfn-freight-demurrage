# Freight ops board (web desk)

Lean FastAPI + Jinja **ops board** wrapping `PipelineSession` for judges and SaaS demos.
Opens on a **projected-$ ticker**, paints container/shipment **risk cards** (green / amber / red by score),
and keeps the Plus | Thinking | Mock + HistGBM Δ panel as the judge card.
Fixture adapters under `fixtures/adapters/` normalize vendor-shaped JSON into the
`domains/freight-demurrage` CSV schema — **no live API keys**.

## Run

From the repo root (with the package editable-installed):

```bash
cd tabpfn-freight-demurrage
pip install -e ".[dev,desk]"
# mock by default; set TABPFN_TOKEN for Plus / Thinking / Fast
tabpfn-hack desk --host 127.0.0.1 --port 8765
# or:
uvicorn apps.desk.app:app --app-dir . --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765

## Judge-priority flows

1. **Mode toggle (must-have)** — segmented **Plus | Thinking | Mock**.
   - Plus: messy terminal/weather text cols (no NLP pipeline).
   - Thinking: constructor overrides `thinking_mode` + `group_col=vessel_id` +
     `group_time_col=event_ts` (never `time_col` together with `group_col`).
   - Mock: offline HistGBM-style path; always works without `TABPFN_TOKEN`.
2. **Baseline Δ** — every triage calls `compare_baseline` vs sklearn HistGBM and
   shows accuracy / f1 / roc_auc / AP plus Δ on the metrics panel.
3. **Fast A/B (optional stub)** — checkbox; latency vs score side-by-side, not required.
4. **Second head (blank sailing)** — after triage, desk also fits `label_col=blank_sailing`
   via the same `PipelineSession.fit_predict` (no stack fork). Metrics shown under the
   primary demurrage + HistGBM Δ card.
5. **What-if panel** — tweak `free_days_left` / `projected_demurrage_usd` / divert on a
   sample container; hold-out re-score shows before/after proba + suggested action
   (labeled synthetic simulation).
6. **Stream re-score** — desk button appends a synthetic Terminal49 / project44 / EDI fixture event, re-runs triage, and refreshes risk cards via fetch (no full reload). Optional 5s auto-poll. Endpoints: `POST /stream-rescore`, `GET /partials/live-board`.

Missing or failing `TABPFN_TOKEN` falls back to mock with a visible warning banner.

## Adapters

| Name | Fixture | Module |
| --- | --- | --- |
| `terminal49` | `fixtures/adapters/terminal49.json` | `adapters/terminal49_fixture.py` |
| `project44` | `fixtures/adapters/project44.json` | `adapters/project44_fixture.py` |
| `edi_315` | `fixtures/adapters/edi_315.json` | `adapters/edi_315_fixture.py` |

Brain remains `tabpfn_hack_core` / MCP. This desk is presentation + ingest only.


## Coda packs

Desk home includes a **pack selector** (spine demurrage + equipment-size + inland-mode + air-freight + stow-fit).
Coda packs are fixtures only; blank-sailing second head and what-if stay demurrage-spine features.
Stow-fit is a tabular equip/mode suggestion head — not a 3D bin packer.

CLI:

```bash
tabpfn-hack demo --domain domains/equipment-size/domain.yaml
tabpfn-hack demo --domain domains/inland-mode/domain.yaml
tabpfn-hack demo --domain domains/air-freight/domain.yaml --mode mock
tabpfn-hack demo --domain domains/stow-fit/domain.yaml --mode mock
```

## Robot / TMS consumer API

Same FastAPI process exposes **decisions** endpoints for robots/TMS:

- `GET /api/v1/health`
- `POST /api/v1/triage` — pack / fixture / rows → metrics + actions
- `POST /api/v1/actions` — score rows → playbook actions

OpenAPI tag: **robot/TMS consumer API** (`/docs`). Docs: [`docs/ROBOT_API.md`](../../docs/ROBOT_API.md).
Does not replace the ops board UI — both share `PipelineSession` + domain playbooks.

## SaaS shell (demo)

1. Open http://127.0.0.1:8765 → sign in with `demo` / `demurrage` (or `DESK_DEMO_USER` / `DESK_DEMO_PASSWORD`).
2. Multi-desk home + client switcher → open a desk (spine = late-fee board).
3. Robot/TMS API at `/api/v1` stays **without** login.

Demo auth stub — not production IAM.
