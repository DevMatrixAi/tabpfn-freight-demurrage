<!-- FREIGHT_FACE_START -->
# Freight demurrage triage (TabPFN-3.5)

**Demo open:** **$1.27M** projected demurrage sitting on the table — then divert / rebook / expedite / authorize_fee / cancel_booking before free days burn.

Predict which containers will blow free-time. Score a messy vessel/BOL table (terminal notes, weather text, high-card IDs, missing milestones, vessel groups + time) with TabPFN-3.5 Plus / Thinking / Fast. Show risk vs a GBDT baseline. Propose money moves via MCP.

Synthetic / public-derived demo only. Not a carrier system of record.

```bash
pip install -e ".[dev]"
tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --data domains/freight-demurrage/data/containers.csv
# opens artifacts/freight-demurrage/demo_report.md with the $1.27M line + action counts
```

Judging map, architecture, and engine docs are below. Pack: [`domains/freight-demurrage/`](domains/freight-demurrage/). Pitch: [`docs/FREIGHT_DEMURRAGE_PITCH_v0.md`](docs/FREIGHT_DEMURRAGE_PITCH_v0.md).

---
<!-- FREIGHT_FACE_END -->

# Engine: tabpfn-hack-core


**Domain-agnostic TabPFN-3.5 MCP + CLI engine** for the [Prior Labs TabPFN-3.5 Hackathon](https://platform.priorlabs.ai/hackathon-3.5) (deadline **6 Oct 2026 23:59 CEST**).

Swap the **story** with a thin domain pack (`domain.yaml` + CSV). The plumbing stays the same.

> **Non-goals:** This is **not** clinical software, not a medical device, and not production decisioning. Demo data is **synthetic**. Domain packs under `examples/` are optional narratives only.

---

## Judging map (50 / 30 / 20)

| Weight | Criterion | How this repo scores it |
| --- | --- | --- |
| **50%** | TabPFN-3.5 showcase | Plus / Thinking / Fast / local backends; raw DataFrames; text + high-card + missings + optional group/time; `predict_proba` uncertainty; baseline delta |
| **30%** | Creativity / practical value | Pluggable domain packs + MCP action hooks — pick any messy-table story without rewriting the core |
| **20%** | Repro / technical quality | Apache-2.0, one-command **mock** demo (no API key), in-repo synthetic CSV, pytest without network/GPU |

---

## Architecture

```
 domain.yaml + data/*.csv          (swap per idea)
            |
            v
   +--------------------+
   |  PipelineSession   |  load -> profile -> fit_predict
   |  (core/pipeline)   |         -> explain -> baseline
   +---------+----------+         -> suggest_actions -> report
             |
             v
   backend.py: plus | thinking | fast | local | mock
             |
     +-------+--------+
     v                v
  CLI (demo/gen)   MCP stdio (7 tools)
```

**Default without `TABPFN_TOKEN`:** `mock` (sklearn HistGradientBoosting / LogisticRegression) so CI and judges can run offline.

---

## Quickstart (mock first — no API key)

```bash
cd /workspace/tabpfn-hack-core
pip install -e ".[dev]"
# or: uv sync

tabpfn-hack demo              # -> artifacts/demo_report.md + predictions.json
tabpfn-hack demo --mode mock
tabpfn-hack gen --n 1000
pytest
```

With a token from [platform.priorlabs.ai](https://platform.priorlabs.ai):

```bash
cp .env.example .env   # set TABPFN_TOKEN=...
tabpfn-hack demo --mode plus
tabpfn-hack demo --mode thinking
tabpfn-hack demo --mode fast
tabpfn-hack demo --mode local   # needs optional tabpfn[local]
```

### MCP

```bash
tabpfn-hack mcp
```

Cursor example:

```json
{
  "mcpServers": {
    "tabpfn-hack-core": {
      "command": "uv",
      "args": ["run", "tabpfn-hack", "mcp"],
      "env": { "TABPFN_TOKEN": "${env:TABPFN_TOKEN}" }
    }
  }
}
```

---

## MCP tools (generic)

| Tool | Purpose |
| --- | --- |
| `load_table` | Load CSV / inline CSV into a session table |
| `profile` | Types, missingness, cardinality, text stats, group/time hints |
| `fit_predict` | `mode=plus|thinking|fast|local|mock` -> labels + probabilities |
| `explain` | Feature attributions (permutation / extensions fallback) |
| `export_report` | Markdown / HTML / JSON under `artifacts/` |
| `compare_baseline` | Delta vs sklearn HistGBM / logistic |
| `suggest_actions` | Domain-defined actions from score thresholds |

Contracts: `src/tabpfn_hack_core/tools_api.py`.

---

## How to add a domain pack

1. Copy `domain.yaml` and put a CSV under `data/` (or point `data_path`).
2. Set:

```yaml
name: my-idea
label_col: target
group_col: site_id          # optional — Thinking
time_col: event_ts          # optional — Thinking group_time_col
text_cols: [note_text]
high_card_cols: [entity_id]
action_thresholds: { high: 0.75, mid: 0.45 }
actions: { high: escalate, mid: review, low: monitor }
disclaimer: "Synthetic demo only."
```

3. Run `tabpfn-hack demo --domain path/to/domain.yaml --data path/to.csv`.
4. Put your pitch in a short README next to the pack — **not** in the core README.

Optional example: `examples/er-triage/` (thin pack; ER narrative lives there, not here).

---

## Env

| Variable | Meaning |
| --- | --- |
| `TABPFN_TOKEN` | Official Prior Labs API token (Plus / Thinking / Fast) |

---

## Web desk + freight adapters

Fixture-only ingest + FastAPI desk for demurrage triage demos:

- Adapters: `src/tabpfn_hack_core/adapters/` (Terminal49 / project44 / EDI 315 fixtures)
- Fixtures: `fixtures/adapters/*.json`
- Desk: `apps/desk/` — home, load adapter, run triage (mock default; honors `TABPFN_TOKEN` for plus)

```bash
pip install -e ".[dev,desk]"
tabpfn-hack desk --port 8765
# -> http://127.0.0.1:8765
pytest   # includes adapter unit tests
```

See [`apps/desk/README.md`](apps/desk/README.md).

## Layout

```
tabpfn-hack-core/
  LICENSE  README.md  CLOUD_AGENT_HANDOFF.md  pyproject.toml  .env.example
  domain.yaml
  data/synthetic_table.csv  data/DATA.md
  domains/freight-demurrage/
  fixtures/adapters/*.json
  apps/desk/                 # FastAPI demurrage desk
  scripts/gen_synthetic_table.py
  src/tabpfn_hack_core/
    cli.py  tools_api.py  domain.py
    adapters/                # fixture freight feeds
    core/{backend,pipeline}.py
    server/mcp_server.py
    demo/run_demo.py
  tests/
  examples/er-triage/
  artifacts/
```

---

## License

Apache-2.0 for **this repo's code**. TabPFN weights/API remain under Prior Labs terms and metering.

## Links

- Hackathon: https://platform.priorlabs.ai/hackathon-3.5
- Docs: https://docs.priorlabs.ai
