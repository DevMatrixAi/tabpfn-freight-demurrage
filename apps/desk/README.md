# Freight demurrage web desk

Lean FastAPI + Jinja shell that wraps `PipelineSession` for judges and SaaS demos.
Fixture adapters under `fixtures/adapters/` normalize vendor-shaped JSON into the
`domains/freight-demurrage` CSV schema — **no live API keys**.

## Run

From the repo root (with the package editable-installed):

```bash
cd /workspace/tabpfn-hack-core
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
6. **Backlog** — stream re-score remains a TODO chip.

Missing or failing `TABPFN_TOKEN` falls back to mock with a visible warning banner.

## Adapters

| Name | Fixture | Module |
| --- | --- | --- |
| `terminal49` | `fixtures/adapters/terminal49.json` | `adapters/terminal49_fixture.py` |
| `project44` | `fixtures/adapters/project44.json` | `adapters/project44_fixture.py` |
| `edi_315` | `fixtures/adapters/edi_315.json` | `adapters/edi_315_fixture.py` |

Brain remains `tabpfn_hack_core` / MCP. This desk is presentation + ingest only.
