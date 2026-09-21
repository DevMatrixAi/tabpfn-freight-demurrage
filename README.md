<!-- FREIGHT_FACE_START -->
# Freight demurrage triage (TabPFN-3.5)

**Demo open:** **$1.27M** projected demurrage — then divert / rebook / expedite / authorize_fee / cancel_booking before free days burn.

Messy vessel/BOL tables → TabPFN-3.5 Plus / Thinking / Fast → baseline vs HistGBM → MCP money moves. **Web ops board:** projected-$ ticker + risk cards; load Terminal49 / project44 / EDI-315 fixtures and triage in the browser.

```bash
pip install -e ".[dev,desk]"
tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --data domains/freight-demurrage/data/containers.csv
tabpfn-hack desk --host 127.0.0.1 --port 8765   # http://127.0.0.1:8765
```

**Judge preview:** [https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app) — login `demo` / `demurrage` (mock stub). Full desk: [`docs/PREVIEW.md`](docs/PREVIEW.md). Deploy configs: `app.py` + `vercel.json`, `Dockerfile` + `fly.toml` / `railway.toml`.

Synthetic / public-derived demo only. Fixture adapters only — not live carrier APIs. Pack: [`domains/freight-demurrage/`](domains/freight-demurrage/). Pitch: [`docs/FREIGHT_DEMURRAGE_PITCH_v0.md`](docs/FREIGHT_DEMURRAGE_PITCH_v0.md). 90s: [`docs/DEMO_90S_AND_FORM_v1.md`](docs/DEMO_90S_AND_FORM_v1.md).

---
<!-- FREIGHT_FACE_END -->

## How judges demo in 3 minutes

**Fastest honest path = local full desk** (deep panels live here). The public Vercel URL is a **mock stub only**.

| Min | Do this |
| --- | --- |
| 0:00 | `pip install -e ".[dev,desk]"` then `TABPFN_TOKEN= tabpfn-hack desk --host 127.0.0.1 --port 8765` |
| 0:30 | Open http://127.0.0.1:8765 → login `demo` / `demurrage` → **Run triage** (Mock) → risk cards + HistGBM Δ |
| 1:30 | Open **/eval** → **Run eval** → latency · Thinking · ablations · calibration · small-n learning curve |
| 2:30 | Optional: `TABPFN_TOKEN= python scripts/mcp_cookbook_demo.py` (7 MCP tools) · `TABPFN_TOKEN= pytest -q` · `tabpfn-hack demo --mode mock` |
|


**Deterministic mock path:** keep the inline `TABPFN_TOKEN=` on the local desk command.
The app loads a repo `.env` for convenience; an explicitly empty variable prevents an
unintended live request/rate limit and keeps the 3-minute walkthrough offline. Never
commit `.env`.

**Stub URL honesty:** [https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app) shows login + sample ticker only — **not** Jinja `/eval` or robot triage. Full TabPFN desk stays local (or Docker/Fly/Railway). Repo stays **private**. Never commit `.env`.



## Robot / TMS consumer API

**Humans or robots call the same action API.** Desk serves JSON under `/api/v1/*` that wraps TabPFN `suggest_actions` / triage (honest: **decisions API**, not crane control). Mock works without a token; Plus/Thinking when `TABPFN_TOKEN` is set. See [`docs/ROBOT_API.md`](docs/ROBOT_API.md) and OpenAPI at `/docs`.

```bash
tabpfn-hack desk --host 127.0.0.1 --port 8765
curl -s http://127.0.0.1:8765/api/v1/health
curl -s -X POST http://127.0.0.1:8765/api/v1/triage \
  -H 'content-type: application/json' \
  -d '{"pack":"freight-demurrage","mode":"mock"}'
```

## Multi-desk note

**Spine:** `domains/freight-demurrage/` — demurrage triage is the default desk story.  
**Coda packs** (same engine, fixtures only — not live TOS):

| Pack | Path | Mock demo (no token) |
| --- | --- | --- |
| Equipment size (box / TEU / reefer vs dry) | [`domains/equipment-size/`](domains/equipment-size/) | `tabpfn-hack demo --domain domains/equipment-size/domain.yaml` |
| Inland truck vs rail | [`domains/inland-mode/`](domains/inland-mode/) | `tabpfn-hack demo --domain domains/inland-mode/domain.yaml` |
| Air freight (AOG / connection / belly) | [`domains/air-freight/`](domains/air-freight/) | `tabpfn-hack demo --domain domains/air-freight/domain.yaml --mode mock` |
| Stow-fit (equip/mode suggest head) | [`domains/stow-fit/`](domains/stow-fit/) | `tabpfn-hack demo --domain domains/stow-fit/domain.yaml --mode mock` |

**Ops board desk:** dollar ticker + green/amber/red risk cards; Plus | Thinking | Mock + HistGBM Δ stays the judge card. Pack selector includes demurrage (spine) + coda packs (equipment-size, inland-mode, air-freight, stow-fit). Chargeback remains an extra story under `domains/chargeback-desk/`. Stow-fit is a tabular suggestion head — **not** a 3D bin packer.

# Engine: tabpfn-hack-core

**Domain-agnostic TabPFN-3.5 MCP + CLI** — mock demo / pytest / MCP cookbook:

```bash
pip install -e ".[dev,desk]"
tabpfn-hack demo --domain domains/freight-demurrage/domain.yaml --mode mock
pytest
python scripts/mcp_cookbook_demo.py
tabpfn-hack desk --host 127.0.0.1 --port 8765
```

Deep panels: [`docs/DEEP_SHOWCASE_v0.md`](docs/DEEP_SHOWCASE_v0.md). Preview honesty: [`docs/PREVIEW.md`](docs/PREVIEW.md).
