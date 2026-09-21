"""Streaming fixture ingest + re-score without full page reload."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from tabpfn_hack_core.adapters.base import FREIGHT_COLUMNS
from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters
from tabpfn_hack_core.core.pipeline import PipelineSession

try:
    from apps.desk.desk_triage import apply_triage
except ImportError:
    from desk_triage import apply_triage  # type: ignore


def _stream_pool() -> list[dict[str, Any]]:
    """Flatten all fixture adapters into a rotating synthetic event pool."""
    pool: list[dict[str, Any]] = []
    for name in list_adapters():
        adapter = get_adapter(name)
        for ev in adapter.fetch_events():
            row = {c: ev.get(c) for c in FREIGHT_COLUMNS}
            row["_stream_src"] = name
            pool.append(row)
    return pool


def append_stream_events(
    sess: PipelineSession,
    state: dict[str, Any],
    *,
    money_total: Callable,
    sample_ids: Callable,
    count: int = 1,
) -> list[dict[str, Any]]:
    """Append ``count`` synthetic fixture events to the live desk table."""
    tid = state.get("table_id")
    if not tid or tid not in sess.tables:
        raise RuntimeError("No desk table loaded")
    pool = _stream_pool()
    if not pool:
        return []
    cursor = int(state.get("stream_cursor") or 0)
    df = sess.tables[tid]
    id_col = sess.domain.id_col or "container_id"
    existing = set(df[id_col].astype(str)) if id_col in df.columns else set()
    appended: list[dict[str, Any]] = []
    for _ in range(max(1, min(int(count), 5))):
        base = dict(pool[cursor % len(pool)])
        src = base.pop("_stream_src", "fixture")
        cid = str(base.get("container_id") or f"STREAM-{cursor}")
        stamp = cursor % 1000
        new_id = f"{cid}-S{stamp}"
        while new_id in existing:
            stamp = (stamp + 1) % 10000
            new_id = f"{cid}-S{stamp}"
        base["container_id"] = new_id
        base["event_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        existing.add(new_id)
        note = str(base.get("terminal_note") or "")[:120]
        appended.append({"container_id": new_id, "source": src, "terminal_note": note})
        df = pd.concat([df, pd.DataFrame([base])[FREIGHT_COLUMNS]], ignore_index=True)
        cursor += 1
    sess.tables[tid] = df
    state["stream_cursor"] = cursor
    state["n_rows"] = len(df)
    state["demurrage_total"] = money_total(df)
    state["preview_rows"] = df.tail(8).fillna("").to_dict(orient="records")
    state["sample_row_ids"] = sample_ids(df, id_col=id_col)
    state["source"] = f"stream:{appended[-1]['source']}" if appended else state.get("source")
    log = list(state.get("stream_log") or [])
    log.extend(appended)
    state["stream_log"] = log[-12:]
    state["stream_last"] = appended
    return appended


def register_stream_routes(
    app: FastAPI,
    *,
    state: dict[str, Any],
    templates: Jinja2Templates,
    pack_meta: Callable[[], dict[str, Any]],
    resolve_mode: Callable,
    metric_slice: Callable,
    money_total: Callable,
    build_risk_cards: Callable,
    load_default_csv: Callable,
    sample_ids: Callable,
    primary_modes: tuple[str, ...] | list[str],
    metric_keys: tuple[str, ...] | list[str],
) -> None:
    """Attach stream re-score endpoints (redirect + partial HTML + JSON)."""
    state.setdefault("stream_cursor", 0)
    state.setdefault("stream_log", [])
    state.setdefault("stream_last", [])

    def _ensure_table() -> None:
        sess: PipelineSession = app.state.session
        tid = state.get("table_id")
        if not tid or tid not in sess.tables:
            load_default_csv(sess)

    def _run(mode: str, count: int) -> list[dict[str, Any]]:
        _ensure_table()
        sess: PipelineSession = app.state.session
        appended = append_stream_events(
            sess, state, money_total=money_total, sample_ids=sample_ids, count=count
        )
        apply_triage(
            app,
            state,
            mode=mode or state.get("requested_mode") or "mock",
            fast_ab=None,
            pack_meta=pack_meta,
            resolve_mode=resolve_mode,
            metric_slice=metric_slice,
            money_total=money_total,
            build_risk_cards=build_risk_cards,
            load_default_csv=load_default_csv,
            sample_ids=sample_ids,
        )
        return appended

    def _ctx(request: Request) -> dict[str, Any]:
        meta = pack_meta()
        return {
            "request": request,
            "state": state,
            "is_spine": bool(meta.get("spine")),
            "metric_keys": metric_keys,
            "primary_modes": primary_modes,
        }

    @app.post("/stream-rescore")
    async def stream_rescore(
        request: Request,
        mode: str = Form("mock"),
        count: int = Form(1),
        partial: str | None = Form(None),
    ):
        """Append fixture adapter event(s) and re-run triage.

        ``partial=1`` → HTML fragment for #live-board (fetch-friendly).
        ``Accept: application/json`` → JSON summary.
        Else → redirect to /desk#live-board.
        """
        appended = _run(mode, int(count or 1))
        accept = (request.headers.get("accept") or "").lower()
        wants_json = "application/json" in accept and "text/html" not in accept
        if partial in {"1", "true", "yes", "on"} or request.headers.get("HX-Request"):
            return templates.TemplateResponse(request, "live_board.html", _ctx(request))
        if wants_json or partial == "json":
            return JSONResponse(
                {
                    "ok": True,
                    "appended": appended,
                    "n_rows": state.get("n_rows"),
                    "demurrage_total": state.get("demurrage_total"),
                    "stream_cursor": state.get("stream_cursor"),
                    "action_counts": state.get("action_counts"),
                    "n_risk_cards": len(state.get("risk_cards") or []),
                    "elapsed_s": state.get("elapsed_s"),
                    "mode": state.get("mode"),
                    "backend": state.get("backend"),
                }
            )
        return RedirectResponse(url="/desk#live-board", status_code=303)

    @app.get("/partials/live-board", response_class=HTMLResponse)
    async def live_board_partial(request: Request) -> HTMLResponse:
        """Poll-friendly HTML fragment of charts + risk cards + stream status."""
        return templates.TemplateResponse(request, "live_board.html", _ctx(request))
