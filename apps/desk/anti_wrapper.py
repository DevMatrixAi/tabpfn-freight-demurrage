"""In-desk anti-wrapper checklist — honest judge surface from docs/ANTI_WRAPPER_CHECKLIST.md."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Mirrors docs/ANTI_WRAPPER_CHECKLIST.md — one path should hit ≥6/8.
CHECKLIST_ITEMS: list[dict[str, str]] = [
    {
        "n": "1",
        "surface": "Messy text (Plus)",
        "where": "notes / weather",
        "href": "/desk",
        "hint": "Free-text notes and weather strings — not cleaned categorical wrappers.",
    },
    {
        "n": "2",
        "surface": "High-cardinality IDs",
        "where": "BOL / container / ports",
        "href": "/desk",
        "hint": "Container / BOL / port IDs stay high-card — TabPFN handles them raw.",
    },
    {
        "n": "3",
        "surface": "Missings (raw frames)",
        "where": "milestones / missingness panel",
        "href": "/desk#missingness",
        "hint": "Raw missing milestones — missingness panel, not imputed-to-hide.",
    },
    {
        "n": "4",
        "surface": "Thinking + group/time",
        "where": "vessel_id + event_ts + effort chip",
        "href": "/desk",
        "hint": "Group/time columns + Thinking effort chip on triage.",
    },
    {
        "n": "5",
        "surface": "Fast vs Plus latency",
        "where": "/eval",
        "href": "/eval",
        "hint": "Side-by-side latency on the eval dashboard.",
    },
    {
        "n": "6",
        "surface": "Probabilities → money moves",
        "where": "action drawer",
        "href": "/desk",
        "hint": "Calibrated proba drives divert / rebook / monitor — not labels alone.",
    },
    {
        "n": "7",
        "surface": "Baseline Δ vs HistGBM",
        "where": "charts + /eval",
        "href": "/eval",
        "hint": "TabPFN vs HistGBM delta on desk charts and /eval.",
    },
    {
        "n": "8",
        "surface": "MCP / robot API",
        "where": "cookbook + scripts/robot_api_smoke.py",
        "href": "/docs",
        "hint": "Same suggest_actions path for humans or robots (/api/v1).",
    },
]

BONUS = "Bonus: calibration, ablations, learning curve, stream re-score, packs."
INTRO = (
    "Not a thin rewrap of Prior hosted MCP. One path should hit ≥6/8. "
    "Check boxes as you walk the desk — local only, not persisted."
)


def checklist_payload() -> dict[str, Any]:
    return {
        "entries": CHECKLIST_ITEMS,
        "bonus": BONUS,
        "intro": INTRO,
        "target": 6,
        "total": len(CHECKLIST_ITEMS),
        "source_doc": "docs/ANTI_WRAPPER_CHECKLIST.md",
    }


def register_anti_wrapper_routes(
    app: FastAPI,
    *,
    templates: Jinja2Templates | None = None,
) -> None:
    """Attach GET /anti-wrapper (auth-gated by DemoAuthMiddleware)."""
    desk = Path(__file__).resolve().parent
    tpl = templates or getattr(app.state, "templates", None)
    if tpl is None:
        tpl = Jinja2Templates(directory=str(desk / "templates"))
        app.state.templates = tpl

    @app.get("/anti-wrapper", response_class=HTMLResponse)
    async def anti_wrapper_page(request: Request) -> HTMLResponse:
        return tpl.TemplateResponse(
            request,
            "anti_wrapper.html",
            {
                "checklist": checklist_payload(),
                "saas_home": "/",
            },
        )
