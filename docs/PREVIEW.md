# Judge preview URL

Public HTTPS preview of the freight demurrage ops desk for hackathon judges.

## Credentials (demo stub)

| Field | Value |
| --- | --- |
| URL | [https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app) |
| Username | `demo` |
| Password | `demurrage` |

Robot/TMS JSON API (`/api/v1/*`) and OpenAPI (`/docs`) stay open without login.

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
| `preview_stub.py` | Live judge URL (lightweight serverless) |

Do **not** commit `.env` or `TABPFN_TOKEN`. Set Plus/Thinking later via host env if desired.

## Human steps (full desk on Vercel / Fly)

1. Link GitHub repo **without making it public**: Vercel Project Settings → Git → connect `DevMatrixAi/tabpfn-freight-demurrage` (needs GitHub App access to the private org repo).
2. Or: `fly auth login && fly deploy` / `railway up` using in-repo `Dockerfile`.
3. Keep Deployment Protection / Vercel Authentication **off** for judges.

CLI:

```bash
vercel link --project tabpfn-freight-demurrage
vercel --prod
```

## Smoke checks

```bash
URL=https://tabpfn-freight-demurrage.vercel.app
curl -sS "$URL/api/v1/health"
# Browser: open $URL → login demo/demurrage → board
```
