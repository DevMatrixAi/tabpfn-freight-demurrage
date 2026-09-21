"""Desk triage routes (ops board) — imports apply_triage from desk_triage_apply."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse

from tabpfn_hack_core.core.pipeline import PipelineSession

try:
    from apps.desk.desk_triage_apply import apply_triage
except ImportError:
    from desk_triage_apply import apply_triage  # type: ignore

try:
    from apps.desk.wow import run_what_if
except ImportError:
    try:
        from wow import run_what_if  # type: ignore
    except ImportError:
        run_what_if = None  # type: ignore

def register_triage_routes(
    app: FastAPI,
    *,
    state: dict[str, Any],
    pack_meta: Callable[[], dict[str, Any]],
    resolve_mode: Callable,
    metric_slice: Callable,
    money_total: Callable,
    build_risk_cards: Callable,
    load_default_csv: Callable,
    sample_ids: Callable,
) -> None:
    """Attach /run-triage and /what-if."""

    @app.post("/run-triage")
    async def run_triage(
        mode: str = Form("mock"),
        fast_ab: str | None = Form(None),
        thinking_effort: str | None = Form(None),
        sample_n: str | None = Form(None),
    ) -> RedirectResponse:
        """Run triage with judge-priority modes; always attach HistGBM baseline delta."""
        apply_triage(
            app,
            state,
            mode=mode,
            fast_ab=fast_ab,
            thinking_effort=thinking_effort,
            sample_n=sample_n,
            pack_meta=pack_meta,
            resolve_mode=resolve_mode,
            metric_slice=metric_slice,
            money_total=money_total,
            build_risk_cards=build_risk_cards,
            load_default_csv=load_default_csv,
            sample_ids=sample_ids,
        )
        return RedirectResponse(url="/desk", status_code=303)

    @app.post("/what-if")
    async def what_if(
        row_id: str = Form(...),
        free_days_left: str | None = Form(None),
        projected_demurrage_usd: str | None = Form(None),
        divert: str | None = Form(None),
        mode: str | None = Form(None),
    ) -> RedirectResponse:
        """Synthetic what-if simulation on a selected container row."""
        sess: PipelineSession = app.state.session
        tid = state.get("table_id")
        if not tid or tid not in sess.tables:
            load_default_csv(sess)
            tid = state["table_id"]
        overrides: dict[str, Any] = {}
        if free_days_left is not None and str(free_days_left).strip() != "":
            overrides["free_days_left"] = float(free_days_left)
        if projected_demurrage_usd is not None and str(projected_demurrage_usd).strip() != "":
            overrides["projected_demurrage_usd"] = float(projected_demurrage_usd)
        if divert in {"1", "on", "true", "yes"}:
            overrides["divert"] = 1
        backend_mode, resolve_warn = resolve_mode(mode or state.get("requested_mode") or "mock")
        try:
            result = run_what_if(sess, tid, row_id, overrides, backend_mode)
            if resolve_warn:
                result["warning"] = " · ".join(x for x in [resolve_warn, result.get("warning")] if x)
            state["what_if"] = result
        except Exception as exc:  # noqa: BLE001
            state["what_if"] = {
                "simulation": True,
                "label": "what-if simulation (synthetic)",
                "error": str(exc),
                "row_id": row_id,
            }
        return RedirectResponse(url="/desk#what-if", status_code=303)


    # Auto-wire stream re-score if not already mounted (e.g. older app.py)
    try:
        if not any(getattr(r, "path", None) == "/stream-rescore" for r in app.routes):
            from pathlib import Path as _P
            from fastapi.templating import Jinja2Templates as _T
            try:
                from apps.desk.stream_rescore import register_stream_routes as _reg_stream
            except ImportError:
                from stream_rescore import register_stream_routes as _reg_stream  # type: ignore
            try:
                from apps.desk.risk_board import human_action as _human_action
            except ImportError:
                from risk_board import human_action as _human_action  # type: ignore
            _desk = _P(__file__).resolve().parent
            _templates = getattr(app.state, "templates", None)
            if _templates is None:
                _templates = _T(directory=str(_desk / "templates"))
                _templates.env.filters["human_action"] = _human_action
                app.state.templates = _templates
            state.setdefault("stream_cursor", 0)
            state.setdefault("stream_log", [])
            state.setdefault("stream_last", [])
            _reg_stream(
                app,
                state=state,
                templates=_templates,
                pack_meta=pack_meta,
                resolve_mode=resolve_mode,
                metric_slice=metric_slice,
                money_total=money_total,
                build_risk_cards=build_risk_cards,
                load_default_csv=load_default_csv,
                sample_ids=sample_ids,
                primary_modes=("plus", "thinking", "mock"),
                metric_keys=("accuracy", "f1", "roc_auc", "avg_precision"),
            )
    except Exception:
        pass  # stream optional if templates/adapters missing
