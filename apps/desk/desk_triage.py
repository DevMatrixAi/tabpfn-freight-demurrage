"""Desk triage + what-if routes (ops board)."""
from __future__ import annotations

import time
from typing import Any, Callable

from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse

from tabpfn_hack_core.core.pipeline import PipelineSession

try:
    from apps.desk.wow import run_blank_head, run_what_if
    from apps.desk.risk_board import build_thinking_timeline, chart_stats
except ImportError:
    from wow import run_blank_head, run_what_if  # type: ignore
    from risk_board import build_thinking_timeline, chart_stats  # type: ignore


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
    async def run_triage(mode: str = Form("mock"), fast_ab: str | None = Form(None)) -> RedirectResponse:
        """Run triage with judge-priority modes; always attach HistGBM baseline delta."""
        sess: PipelineSession = app.state.session
        tid = state.get("table_id")
        if not tid or tid not in sess.tables:
            load_default_csv(sess)
            tid = state["table_id"]
        backend_mode, resolve_warn = resolve_mode(mode)
        n = len(sess.tables[tid])
        test_size = 0.3 if n >= 10 else 0.25
        if n < 4:
            import pandas as pd
            combined = pd.concat([pd.read_csv(pack_meta()["csv"]), sess.tables[tid]], ignore_index=True)
            sess.tables[tid] = combined
            state["n_rows"] = len(combined)
            state["demurrage_total"] = money_total(combined)
            state["sample_row_ids"] = sample_ids(combined, id_col=sess.domain.id_col or "container_id")
            test_size = 0.2
        t0 = time.perf_counter()
        cmp_ = sess.compare_baseline(tid, mode=backend_mode, baseline="sklearn_hist_gbm", test_size=test_size)
        elapsed = time.perf_counter() - t0
        actions = sess.suggest_actions(tid, max_rows=50)
        warnings: list[str] = []
        if resolve_warn:
            warnings.append(resolve_warn)
        if sess.last_warning:
            warnings.append(str(sess.last_warning))
        state["metrics"] = metric_slice(cmp_.tabpfn_metrics)
        state["baseline_metrics"] = metric_slice(cmp_.baseline_metrics)
        state["delta"] = metric_slice(cmp_.delta)
        state["baseline_narrative"] = cmp_.narrative
        state["backend"] = sess.last_backend
        effective = sess.last_mode
        state["mode"] = effective.value if hasattr(effective, "value") else str(effective)
        state["requested_mode"] = backend_mode.value if hasattr(backend_mode, "value") else str(backend_mode)
        state["warning"] = " · ".join(warnings) if warnings else None
        state["elapsed_s"] = round(elapsed, 3)
        state["group_col"] = sess.domain.group_col
        state["group_time_col"] = sess.domain.time_col
        state["actions"] = [
            {"row_id": a.row_id, "proba": round(float(a.proba), 4), "action": a.action, "reason": a.reason}
            for a in actions.items
        ]
        state["action_counts"] = dict(actions.counts)
        state["risk_cards"] = build_risk_cards(sess, tid, state["actions"])
        state["chart_stats"] = chart_stats(
            state["risk_cards"], float(state.get("demurrage_total") or 0.0)
        )
        # Thinking timeline: group × time path from table (or preview) when Thinking selected
        df = sess.tables[tid]
        preview = state.get("preview_rows") or []
        if not preview:
            preview = df.head(24).fillna("").to_dict(orient="records")
        else:
            # Prefer a slightly wider slice for the strip when Thinking
            preview = df.head(24).fillna("").to_dict(orient="records")
        gcol = state.get("group_col") or sess.domain.group_col or "vessel_id"
        tcol = state.get("group_time_col") or sess.domain.time_col or "event_ts"
        icol = sess.domain.id_col or pack_meta().get("id_hint") or "container_id"
        state["thinking_timeline"] = build_thinking_timeline(
            preview, group_col=gcol, time_col=tcol, id_col=icol, limit=24
        )
        state["money_label"] = pack_meta().get("money_label") or "Exposure"
        state["what_if"] = None
        if pack_meta().get("spine"):
            run_blank_head(sess, tid, backend_mode, test_size, state)
        else:
            state["blank_metrics"] = None
            state["blank_backend"] = None
            state["blank_warning"] = None
        if fast_ab in {"1", "on", "true", "yes"}:
            snap_pred = None if sess.last_predictions is None else sess.last_predictions.copy()
            snap = (sess.last_metrics, sess.last_backend, sess.last_mode, sess.last_warning, sess.last_baseline)
            t1 = time.perf_counter()
            fast_mode, fast_warn = resolve_mode("fast")
            fast_fit = sess.fit_predict(tid, mode=fast_mode, test_size=test_size)
            state["fast_ab"] = {
                "mode": "fast", "backend": fast_fit.backend, "metrics": metric_slice(fast_fit.metrics),
                "elapsed_s": round(time.perf_counter() - t1, 3), "warning": fast_warn or fast_fit.warning,
                "note": "Fast A/B stub — queue latency vs Thinking/Plus score (optional).",
            }
            if snap_pred is not None:
                sess.last_predictions = snap_pred
                sess.last_metrics, sess.last_backend, sess.last_mode, sess.last_warning, sess.last_baseline = snap
        else:
            state["fast_ab"] = None
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
