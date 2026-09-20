# Cloud Agent handoff — tabpfn-hack-core

**Role:** Domain-agnostic TabPFN-3.5 MCP + CLI core. Domain story is a pluggable pack (`domain.yaml` + CSV).

## Done in this tree

- `src/tabpfn_hack_core/` — backend (plus|thinking|fast|local|mock), pipeline, CLI, MCP, demo
- Root `domain.yaml` + `data/synthetic_table.csv` (generic messy table)
- Mock path is **default** without `TABPFN_TOKEN` — demo + pytest offline
- `examples/er-triage/` — optional thin domain pack (ER narrative stays there)
- Apache-2.0, judging 50/30/20 in README (no ER pitch as the core story)

## Verify

```bash
cd /workspace/tabpfn-hack-core
pip install -e ".[dev]"
tabpfn-hack demo          # no token → mock; writes artifacts/
pytest
```

## Env

- Official token name: **`TABPFN_TOKEN`** (see `.env.example`)

## Backend notes

- `mock`: sklearn HistGradientBoosting (fallback LogisticRegression); hashed cats + text length features
- `plus` / `fast` / `thinking`: `tabpfn_client.TabPFNClassifier.create_default_for_version(...)`; Thinking uses `group_col` / `group_time_col` from domain.yaml; falls back to mock with warning if no token
- `local`: `from tabpfn import TabPFNClassifier` — ImportError/OOM → mock
- Pass **raw pandas DataFrames** into TabPFN client/OSS paths

## Non-goals

- Do not register/submit the hackathon from agents
- Do not treat this as clinical software
- Do not rewrap Prior hosted MCP alone as the entry

## Related folders

- `/workspace/tabpfn-er-triage-scaffold/` — superseded by core + `examples/er-triage/` (see its `SUPERSEDED.md`)
- `/workspace/tabpfn-ops-mcp-scaffold/` — older ops scaffold; ignore for submission
