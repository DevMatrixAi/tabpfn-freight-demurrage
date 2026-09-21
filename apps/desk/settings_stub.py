"""SaaS /settings stub — demo prefs + judge crib (mock-only; not IAM)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

SAMPLE_COOKIE = "desk_sample_n"
EFFORT_COOKIE = "desk_thinking_effort"
SAMPLE_CHOICES = (40, 60, 80)
EFFORT_CHOICES = ("low", "medium", "high")

JUDGE_CRIB = (
    "Plain English for judges: this is a shipper late-fee money desk. "
    "Empty TABPFN_TOKEN = mock offline path. sample_n 40–80 keeps live Thinking cheap after API reset. "
    "Walk Login → Desks → Ops board triage → /eval → Robot API. "
    "Not production IAM — demo/demurrage only."
)


def _has_token() -> bool:
    return bool(os.environ.get("TABPFN_TOKEN", "").strip())


def _mode_badge() -> dict[str, str]:
    if _has_token():
        return {
            "id": "live-small-n",
            "label": "Live small-n",
            "gloss": "TABPFN_TOKEN set — prefer sample_n 40–80 for Plus/Thinking.",
        }
    return {
        "id": "mock",
        "label": "Mock",
        "gloss": "No TABPFN_TOKEN — deterministic offline mock (judge-safe).",
    }


def settings_payload(
    request: Request | None = None,
    *,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build template context for /settings (demo-only)."""
    try:
        from apps.desk.clients import DEFAULT_CLIENT, client_meta, list_clients
    except ImportError:
        from clients import DEFAULT_CLIENT, client_meta, list_clients  # type: ignore

    try:
        from apps.desk.auth import demo_credentials
    except ImportError:
        from auth import demo_credentials  # type: ignore

    try:
        from apps.desk.dev_sample import resolve_sample_n
    except ImportError:
        from dev_sample import resolve_sample_n  # type: ignore

    user, _pw = demo_credentials()
    env_n = os.environ.get("TABPFN_DEV_N", "").strip() or None
    resolved = resolve_sample_n(None)

    cookie_n = None
    cookie_effort = None
    if request is not None:
        raw_n = (request.cookies.get(SAMPLE_COOKIE) or "").strip()
        if raw_n.isdigit() and int(raw_n) in SAMPLE_CHOICES:
            cookie_n = int(raw_n)
        raw_e = (request.cookies.get(EFFORT_COOKIE) or "").strip().lower()
        if raw_e in EFFORT_CHOICES:
            cookie_effort = raw_e

    cid = None
    clabel = None
    cgloss = None
    if state:
        cid = state.get("client_id")
        clabel = state.get("client_label")
        if cid:
            meta = client_meta(str(cid))
            clabel = clabel or meta.get("label")
            cgloss = meta.get("gloss", "")
    if not cid:
        cid = DEFAULT_CLIENT
        meta = client_meta(cid)
        clabel = meta.get("label")
        cgloss = meta.get("gloss", "")

    effort = cookie_effort or (state or {}).get("thinking_effort") or "medium"
    if effort not in EFFORT_CHOICES:
        effort = "medium"

    display_n = cookie_n if cookie_n is not None else resolved
    no_client = not cid or cid in ("", "NONE", "none")

    return {
        "auth_note": (
            f"Demo auth stub · user `{user}` / demurrage · cookie session only — not IAM."
        ),
        "demo_user": user,
        "active_client": cid,
        "active_client_label": clabel,
        "active_client_gloss": cgloss or "",
        "clients": list_clients(),
        "no_client": no_client,
        "mode": _mode_badge(),
        "has_token": _has_token(),
        "sample_n": display_n,
        "sample_n_env": env_n,
        "sample_n_resolved": resolved,
        "sample_n_cookie": cookie_n,
        "sample_choices": list(SAMPLE_CHOICES),
        "thinking_effort": effort,
        "effort_choices": list(EFFORT_CHOICES),
        "judge_crib": JUDGE_CRIB,
        "links": [
            {"href": "/judge-path", "label": "Judge path (mock)", "method": "post"},
            {"href": "/eval", "label": "/eval", "method": "get"},
            {"href": "/anti-wrapper", "label": "Anti-wrapper", "method": "get"},
            {"href": "/docs", "label": "Robot API /docs", "method": "get"},
            {"href": "/desk", "label": "Ops board", "method": "get"},
        ],
        "saas_home": "/",
    }


def register_settings_routes(
    app: FastAPI,
    *,
    templates: Jinja2Templates | None = None,
    state: dict[str, Any] | None = None,
) -> None:
    """Attach GET/POST /settings (auth-gated by DemoAuthMiddleware)."""
    desk = Path(__file__).resolve().parent
    tpl = templates or getattr(app.state, "templates", None)
    if tpl is None:
        tpl = Jinja2Templates(directory=str(desk / "templates"))
        app.state.templates = tpl

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request) -> HTMLResponse:
        ctx = settings_payload(request, state=state)
        return tpl.TemplateResponse(request, "settings.html", ctx)

    @app.post("/settings")
    async def settings_save(
        request: Request,
        sample_n: str = Form(""),
        thinking_effort: str = Form("medium"),
    ) -> RedirectResponse:
        resp = RedirectResponse(url="/settings", status_code=303)
        raw = (sample_n or "").strip()
        if raw.isdigit() and int(raw) in SAMPLE_CHOICES:
            resp.set_cookie(SAMPLE_COOKIE, raw, httponly=False, samesite="lax")
            if state is not None:
                # Surface preference for desk forms that read state
                state["settings_sample_n"] = int(raw)
        elif raw in ("", "full", "0"):
            resp.delete_cookie(SAMPLE_COOKIE)
            if state is not None:
                state.pop("settings_sample_n", None)
        eff = (thinking_effort or "medium").strip().lower()
        if eff not in EFFORT_CHOICES:
            eff = "medium"
        resp.set_cookie(EFFORT_COOKIE, eff, httponly=False, samesite="lax")
        if state is not None:
            state["thinking_effort"] = eff
        return resp
