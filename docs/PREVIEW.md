# Judge preview URL

Public HTTPS preview of the freight demurrage ops desk for hackathon judges.

## Credentials (demo stub)

| Field | Value |
| --- | --- |
| URL | _see status below_ |
| Username | `demo` |
| Password | `demurrage` |

Robot/TMS JSON API (`/api/v1/*`) and OpenAPI (`/docs`) stay open without login.

## Status

**Target:** public HTTPS preview (Vercel preferred; Fly / Railway fallback).

| Item | Value |
| --- | --- |
| GitHub repo | private `DevMatrixAi/tabpfn-freight-demurrage` (stays private) |
| Vercel project | `tabpfn-freight-demurrage` (`prj_zdy4NLl4FHlAkqDQaZsFA2mnnyf0`) |
| Preview URL | _pending first successful deployment_ |
| Mode | mock-first (no `TABPFN_TOKEN` required) |

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
