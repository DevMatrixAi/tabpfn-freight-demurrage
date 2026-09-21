# Judge preview URL

Public HTTPS preview of the freight demurrage ops desk for hackathon judges.

## Credentials (demo stub)

| Field | Value |
| --- | --- |
| URL | [https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app) |
| Username | `demo` |
| Password | `demurrage` |

Robot/TMS JSON API (`/api/v1/*`) and OpenAPI (`/docs`) stay open without login.

## How judges demo in 3 minutes

Canonical: [`JUDGE_3MIN.md`](JUDGE_3MIN.md) · MCP: [`MCP_SMOKE.md`](MCP_SMOKE.md).

**Fastest honest path = local full desk** (deep panels live here). The public Vercel URL is a **mock stub only**.

| Min | Do this |
| --- | --- |
| 0:00 | `pip install -e ".[dev,desk]"` then `TABPFN_TOKEN= tabpfn-hack desk --host 127.0.0.1 --port 8765` |
| 0:30 | Open http://127.0.0.1:8765 → login `demo` / `demurrage` → **Run triage** (Mock) → risk cards + HistGBM Δ |
| 1:30 | Open **/eval** → **Run eval** → latency · Thinking · ablations · calibration · small-n learning curve |
| 2:30 | Optional: `TABPFN_TOKEN= python scripts/mcp_cookbook_demo.py` (7 MCP tools) · `TABPFN_TOKEN= pytest -q` · `tabpfn-hack demo --mode mock` |


**Deterministic mock path:** keep the inline `TABPFN_TOKEN=` on the local desk command.
The app loads a repo `.env` for convenience; an explicitly empty variable prevents an
unintended live request/rate limit and keeps the 3-minute walkthrough offline. Never
commit `.env`.

**Robot smoke (local):** `TABPFN_TOKEN= python scripts/robot_api_smoke.py` — health + mock triage without login.

**Live budget after reset:** desk `sample_n` 40–80 (or `TABPFN_DEV_N=60`); practice stays mock/full.

**Stub URL honesty:** [https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app) shows login + sample ticker only — **not** Jinja `/eval` or robot triage. Full TabPFN desk stays local (or Docker/Fly/Railway). Repo stays **private**. Never commit `.env`.


## Status

**Target:** public HTTPS preview (Vercel preferred; Fly / Railway fallback).

| Item | Value |
| --- | --- |
| GitHub repo | private `DevMatrixAi/tabpfn-freight-demurrage` (stays private) |
| Vercel project | `tabpfn-freight-demurrage` (`prj_zdy4NLl4FHlAkqDQaZsFA2mnnyf0`) |
| Preview URL | **[https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app)** (stub, mock-first) |
| Mode | mock-first (no `TABPFN_TOKEN` required) |


## What judges get on the live URL

Live Vercel production is a **lightweight preview stub** (`preview_stub.py`):

- Login `demo` / `demurrage` → ops board ticker + sample risk cards
- Open `/api/v1/health` without login
- Full TabPFN desk (Jinja ops board, `/eval`, robot API triage) is **not** on this serverless URL — run locally or deploy `Dockerfile` / Fly / Railway (see below). Stub exists so judges have a public HTTPS link while the private repo stays private and Hobby Vercel cannot pull the private GitHub source.

## One-command local

```bash
pip install -e ".[desk]"
# or: pip install -r requirements.txt && pip install -e .
tabpfn-hack desk --host 0.0.0.0 --port 8765
# open http://127.0.0.1:8765  → login demo / demurrage
```

## Deploy configs in-repo

| Path | Platform |
| --- | --- |
| `app.py` + `vercel.json` + `requirements.txt` | Vercel (FastAPI) |
| `Dockerfile` + `fly.toml` | Fly.io |
| `Dockerfile` + `railway.toml` | Railway |

Do **not** commit `.env` or `TABPFN_TOKEN`. Set Plus/Thinking later via host env if desired.

## Human steps (if agent deploy is blocked)

### Vercel (preferred — MCP already auth’d as `devmatrixai`)

1. If team scope `christopher-perciballis-projects` needs re-auth: open [Vercel dashboard](https://vercel.com/dashboard) → re-authorize the Cursor/MCP integration for that team.
2. Link GitHub repo **without making it public**: Project Settings → Git → connect `DevMatrixAi/tabpfn-freight-demurrage`.
3. Ensure Deployment Protection / Vercel Authentication is **off** for Production (judges must open the URL anonymously). This project was created with `ssoProtection` disabled.
4. Deploy production from `main`, then paste the `*.vercel.app` URL into this file and the README face block.

CLI alternative (after `vercel login`):

```bash
vercel link --project tabpfn-freight-demurrage
vercel --prod
```

### Fly.io

```bash
fly auth login
fly apps create tabpfn-freight-desk   # if name taken, change fly.toml app=
fly deploy
```

### Railway

```bash
railway login
railway init
railway up
```

## Smoke checks after URL is live

```bash
curl -sS "$URL/api/v1/health"
# expect JSON with ok/token/packs
# Browser: open $URL → login demo/demurrage → ops board /eval
```
