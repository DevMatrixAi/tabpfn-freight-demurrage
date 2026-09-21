"""Eval dashboard routes — readable; logic in eval_runner."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.tools_api import BackendMode

try:
    from apps.desk.eval_runner import (
        EVAL_MODES,
        METRIC_KEYS,
        METRIC_LABELS,
        _slice,
        run_multi_mode_eval,
    )
except ImportError:
    from eval_runner import (  # type: ignore
        EVAL_MODES,
        METRIC_KEYS,
        METRIC_LABELS,
        _slice,
        run_multi_mode_eval,
    )

__all__ = [
    "EVAL_MODES",
    "METRIC_KEYS",
    "METRIC_LABELS",
    "run_multi_mode_eval",
    "register_eval_routes",
]


def register_eval_routes(
    app: FastAPI,
    *,
    state: dict[str, Any],
    templates: Jinja2Templates,
    packs: dict[str, dict[str, Any]],
    default_pack: str,
    session_factory: Callable[[str | None], PipelineSession],
    load_pack_csv: Callable[..., None],
    resolve_mode: Callable[[str], tuple[BackendMode, str | None]],
    metric_slice: Callable[[dict[str, float] | None], dict[str, float]],
    has_token: Callable[[], bool],
) -> None:
    """Mount GET /eval and POST /eval/run (auth-gated like /desk)."""

    def _ensure_pack(pack: str | None) -> tuple[str, PipelineSession]:
        pid = pack if pack in packs else (state.get("pack") or default_pack)
        if pid not in packs:
            pid = default_pack
        need_reload = (
            pid != state.get("pack")
            or not state.get("table_id")
            or getattr(app.state, "session", None) is None
        )
        if need_reload:
            state["pack"] = pid
            state["pack_label"] = packs[pid]["label"]
            state["pack_gloss"] = packs[pid].get("gloss")
            sess = session_factory(pid)
            load_pack_csv(sess)
        return pid, app.state.session

    @app.get("/eval", response_class=HTMLResponse)
    async def eval_page(request: Request, pack: str | None = None) -> HTMLResponse:
        pid, _sess = _ensure_pack(pack)
        result = state.get("eval_result")
        if result and result.get("pack") and result["pack"] != pid:
            result = None
        return templates.TemplateResponse(
            request,
            "eval.html",
            {
                "packs": [
                    {
                        "id": k,
                        "label": v["label"],
                        "spine": v["spine"],
                        "gloss": v.get("gloss"),
                    }
                    for k, v in packs.items()
                ],
                "active_pack": pid,
                "pack_label": packs[pid]["label"],
                "pack_gloss": packs[pid].get("gloss"),
                "n_rows": state.get("n_rows") or 0,
                "has_token": has_token(),
                "result": result,
                "eval_modes": list(EVAL_MODES),
                "metric_keys": list(METRIC_KEYS),
                "metric_labels": METRIC_LABELS,
                "saas_home": "/",
            },
        )

    @app.post("/eval/run")
    async def eval_run(pack: str = Form(default_pack)) -> RedirectResponse:
        pid, sess = _ensure_pack(pack)
        tid = state.get("table_id")
        if not tid or tid not in sess.tables:
            load_pack_csv(sess)
            tid = state["table_id"]
            sess = app.state.session
        result = run_multi_mode_eval(
            sess, tid, resolve_mode=resolve_mode, metric_slice=metric_slice
        )
        if not result.get("learning_curve"):
            try:
                from apps.desk.eval_lc import maybe_learning_curve
            except ImportError:
                from eval_lc import maybe_learning_curve  # type: ignore
            warns = list(result.get("warnings") or [])
            lc = maybe_learning_curve(sess, tid, warns)
            result["warnings"] = warns
            if lc is not None:
                result["learning_curve"] = lc
        result["pack"] = pid
        result["pack_label"] = packs[pid]["label"]
        result["has_token"] = has_token()
        state["eval_result"] = result
        return RedirectResponse(url=f"/eval?pack={pid}", status_code=303)
