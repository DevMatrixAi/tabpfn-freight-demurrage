"""Minimal judge preview stub — login demo/demurrage, health, simple board.
Full desk lives in apps.desk; this file is Vercel-deployable without the whole monorepo.
"""
from __future__ import annotations

import os
import secrets

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

USER = os.environ.get("DESK_DEMO_USER", "demo")
PASSWORD = os.environ.get("DESK_DEMO_PASSWORD", "demurrage")
COOKIE = "desk_preview_sess"

# Showcase chips mirroring desk story (no Jinja / heavy deps).
SHOWCASE_CHIPS: list[dict[str, str]] = [
    {"id": "mock", "label": "Mock", "hint": "empty TABPFN_TOKEN"},
    {"id": "modes", "label": "Plus / Thinking / Fast", "hint": "TabPFN-3.5 modes"},
    {"id": "histgbm", "label": "HistGBM Δ", "hint": "baseline lift"},
    {"id": "text", "label": "text", "hint": "messy notes"},
    {"id": "high_card", "label": "high-card", "hint": "BOL / container"},
    {"id": "missing", "label": "missing", "hint": "raw NaNs"},
    {"id": "group_time", "label": "group×time", "hint": "vessel + event_ts"},
    {"id": "robot", "label": "Robot API", "hint": "/api/v1"},
]

app = FastAPI(title="TabPFN Freight Demurrage Desk (preview)")
_sessions: set[str] = set()


def _authed(request: Request) -> bool:
    return request.cookies.get(COOKIE, "") in _sessions


def _chips_html() -> str:
    bits = []
    for c in SHOWCASE_CHIPS:
        bits.append(
            f'<span class="chip chip-{c["id"]}" title="{c["hint"]}">{c["label"]}</span>'
        )
    return '<div class="chip-row" aria-label="Showcase chips">' + "".join(bits) + "</div>"


LOGIN_HTML = """<!doctype html><html><head><meta charset=utf-8><title>Freight desk login</title>
<style>
body{font-family:system-ui,sans-serif;background:#0b1220;color:#e8eefc;display:grid;place-items:center;min-height:100vh;margin:0}
card{background:#141e33;padding:2rem;border-radius:12px;width:min(360px,92vw);box-shadow:0 8px 32px #0008}
h1{font-size:1.2rem;margin:0 0 .25rem}p{opacity:.75;margin:0 0 1.25rem;font-size:.9rem}
label{display:block;font-size:.8rem;margin:.6rem 0 .25rem}input{width:100%;padding:.55rem .7rem;border-radius:8px;border:1px solid #2a3b5c;background:#0b1220;color:#e8eefc;box-sizing:border-box}
button{margin-top:1rem;width:100%;padding:.65rem;border:0;border-radius:8px;background:#3b82f6;color:#fff;font-weight:600;cursor:pointer}
.err{color:#fca5a5;font-size:.85rem;margin-top:.75rem}
</style></head><body><card>
<h1>Freight demurrage ops desk</h1>
<p>Judge preview · mock-first · TabPFN-3.5</p>
<form method=post action=/login>
<label>Username</label><input name=username autocomplete=username value=demo>
<label>Password</label><input name=password type=password autocomplete=current-password>
<button type=submit>Sign in</button>
{err}
</form></card></body></html>"""

BOARD_HTML = """<!doctype html><html><head><meta charset=utf-8><title>Ops board</title>
<style>
body{font-family:system-ui,sans-serif;background:#0b1220;color:#e8eefc;margin:0}
header{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.5rem;border-bottom:1px solid #243045;flex-wrap:wrap;gap:.75rem}
.ticker{font-size:1.6rem;font-weight:700;color:#fbbf24}
main{padding:1.5rem;display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.card{background:#141e33;border-radius:12px;padding:1rem;border-left:4px solid var(--c,#3b82f6)}
.card.red{--c:#ef4444}.card.amber{--c:#f59e0b}.card.green{--c:#22c55e}
a{color:#93c5fd} .muted{opacity:.7;font-size:.85rem}
.chip-row{display:flex;flex-wrap:wrap;gap:.4rem;padding:.85rem 1.5rem 0}
.chip{display:inline-flex;align-items:center;padding:.2rem .55rem;border-radius:999px;border:1px solid #2a3b5c;font-size:.72rem;background:#121a26;color:#c7d2e5}
.chip-mock{border-color:rgba(59,130,246,.45);color:#93c5fd}
.chip-modes{border-color:rgba(167,139,250,.45);color:#ddd6fe}
.chip-histgbm{border-color:rgba(251,191,36,.45);color:#fde68a}
.chip-text{border-color:rgba(167,139,250,.45);color:#e8dfff}
.chip-high_card{border-color:rgba(56,189,248,.45);color:#bae6fd}
.chip-missing{border-color:rgba(251,191,36,.45);color:#fde68a}
.chip-group_time{border-color:rgba(52,211,153,.45);color:#a7f3d0}
.chip-robot{border-color:rgba(34,211,238,.45);color:#a5f3fc}
</style></head><body>
<header>
  <div><strong>Freight demurrage triage</strong><div class=muted>Preview stub · full desk via local / Fly</div></div>
  <div class=ticker>$1.27M projected</div>
  <div><a href=/eval>Eval</a> · <a href=/settings>Settings</a> · <a href=/api/v1/health>Health</a> · <a href=/logout>Logout</a></div>
</header>
__CHIPS__
<main>
  <div class="card red"><h3>MSCUred101</h3><p>divert · $48.2k at risk</p></div>
  <div class="card amber"><h3>COSUamb202</h3><p>expedite · $12.4k</p></div>
  <div class="card green"><h3>MAEUOK303</h3><p>hold · free days OK</p></div>
  <div class="card"><h3>Mock mode</h3><p class=muted>No TABPFN_TOKEN. Full board: <code>tabpfn-hack desk</code></p></div>
</main>
</body></html>""".replace("__CHIPS__", _chips_html())


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if _authed(request):
        return RedirectResponse("/board", status_code=303)
    return HTMLResponse(LOGIN_HTML.replace("{err}", ""))


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == USER and password == PASSWORD:
        token = secrets.token_urlsafe(24)
        _sessions.add(token)
        resp = RedirectResponse("/board", status_code=303)
        resp.set_cookie(COOKIE, token, httponly=True, samesite="lax")
        return resp
    return HTMLResponse(LOGIN_HTML.replace('{err}', '<div class=err>Invalid credentials (try demo / demurrage)</div>'), status_code=401)


@app.get("/board", response_class=HTMLResponse)
def board(request: Request):
    if not _authed(request):
        return RedirectResponse("/", status_code=303)
    return HTMLResponse(BOARD_HTML)


@app.get("/eval", response_class=HTMLResponse)
def eval_page(request: Request):
    if not _authed(request):
        return RedirectResponse("/", status_code=303)
    return HTMLResponse(
        "<!doctype html><html><body style='font-family:system-ui;background:#0b1220;color:#e8eefc;padding:2rem'>"
        "<h1>/eval preview</h1><p>Full Jinja eval dashboard ships in the repo desk. "
        "Run locally: <code>tabpfn-hack desk</code> → open /eval</p>"
        + _chips_html()
        + "<p style='margin-top:1rem'><a href=/board style='color:#93c5fd'>← board</a></p></body></html>"
    )


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    """Tiny stub — full settings on local desk."""
    if not _authed(request):
        return RedirectResponse("/", status_code=303)
    return HTMLResponse(
        "<!doctype html><html><head><meta charset=utf-8><title>Settings (stub)</title>"
        "<style>body{font-family:system-ui;background:#0b1220;color:#e8eefc;padding:2rem}"
        "a{color:#93c5fd}.muted{opacity:.7}</style></head><body>"
        "<h1>Settings (preview stub)</h1>"
        "<p class=muted>Full settings live on the local desk: "
        "<code>TABPFN_TOKEN= tabpfn-hack desk</code> → <code>/settings</code>.</p>"
        "<p>Demo prefs: sample_n 40/60/80 · Thinking effort · mode badge · judge crib.</p>"
        + _chips_html()
        + "<p style='margin-top:1rem'><a href=/board>← board</a></p></body></html>"
    )


@app.get("/logout")
def logout(request: Request):
    tok = request.cookies.get(COOKIE)
    if tok:
        _sessions.discard(tok)
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie(COOKIE)
    return resp


@app.get("/api/v1/health")
def health():
    return JSONResponse(
        {
            "ok": True,
            "preview": "stub",
            "mode": "mock",
            "auth": {"user": USER},
            "packs": ["freight-demurrage"],
            "chips": [{"id": c["id"], "label": c["label"], "hint": c["hint"]} for c in SHOWCASE_CHIPS],
            "chip_flags": {c["id"]: True for c in SHOWCASE_CHIPS},
            "note": "Full desk: pip install -e '.[desk]' && tabpfn-hack desk",
        }
    )


@app.get("/docs", include_in_schema=False)
def docs_redirect():
    return RedirectResponse("/api/v1/health")
