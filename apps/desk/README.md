# Freight demurrage web desk

Lean FastAPI + Jinja shell that wraps `PipelineSession` for judges and SaaS demos.
Fixture adapters under `fixtures/adapters/` normalize vendor-shaped JSON into the
`domains/freight-demurrage` CSV schema — **no live API keys**.

## Run

From the repo root (with the package editable-installed):

```bash
cd /workspace/tabpfn-hack-core
pip install -e ".[dev,desk]"
# mock by default; set TABPFN_TOKEN for Plus
tabpfn-hack desk --host 127.0.0.1 --port 8765
# or:
uvicorn apps.desk.app:app --app-dir . --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765

## Flows

1. **Home** — loads domain CSV; shows projected demurrage $.
2. **Load adapter** — Terminal49 / project44 / EDI 315 fixtures → domain columns.
3. **Run triage** — `PipelineSession.fit_predict` (mock unless `TABPFN_TOKEN` + plus) + action table.

## Adapters

| Name | Fixture | Module |
| --- | --- | --- |
| `terminal49` | `fixtures/adapters/terminal49.json` | `adapters/terminal49_fixture.py` |
| `project44` | `fixtures/adapters/project44.json` | `adapters/project44_fixture.py` |
| `edi_315` | `fixtures/adapters/edi_315.json` | `adapters/edi_315_fixture.py` |

Brain remains `tabpfn_hack_core` / MCP. This desk is presentation + ingest only.
