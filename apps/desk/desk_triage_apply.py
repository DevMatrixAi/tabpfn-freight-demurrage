"""apply_triage core — readable split for judge repro / MCP-sized pushes."""
from __future__ import annotations

import time
from typing import Any, Callable

import pandas as pd
from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse

from tabpfn_hack_core.core.pipeline import PipelineSession

try:
    from apps.desk.dev_sample import resolve_sample_n, sample_frame
except ImportError:
    from dev_sample import resolve_sample_n, sample_frame  # type: ignore

try:
    from apps.desk.wow import run_blank_head, run_what_if
    from apps.desk.risk_board import build_thinking_timeline, chart_stats
except ImportError:
    from wow import run_blank_head, run_what_if  # type: ignore
    from risk_board import build_thinking_timeline, chart_stats  # type: ignore


def _apply_triage_impl(
    app: FastAPI,
    state: dict[str, Any],
    *,
    mode: str = "mock",
    fast_ab: str | None = None,
    thinking_effort: str | None = None,
    sample_n: str | None = None,
    pack_meta: Callable[[], dict[str, Any]],
    resolve_mode: Callable,
    metric_slice: Callable,
    money_total: Callable,
    build_risk_cards: Callable,
    load_default_csv: Callable,
    sample_ids: Callable,
    keep_rows: bool = False,
) -> None:
    """Run triage into ``state`` (shared by /run-triage and stream re-score)."""
    sess: PipelineSession = app.state.session
    tid = state.get("table_id")
    if not tid or tid not in sess.tables:
        load_default_csv(sess)
        tid = state["table_id"]
    backend_mode, resolve_warn = resolve_mode(mode)
    # Budget control: optional small-n sample before fit (live TabPFN cost)
    want_n = resolve_sample_n(sample_n)
    _df0 = sess.tables[tid]
    _label = getattr(sess.domain, "label_col", None)
    from tabpfn_hack_core.core import replay as _replay

    if keep_rows or _replay.covers(_df0, sess.domain.id_col):
        # keep_rows: stream re-score already holds the sampled table plus new arrivals.
        # Recorded TabPFN scores cost nothing, so score the full table instead of a sample.
        _sampled, _smeta = _df0, None
    else:
        _sampled, _smeta = sample_frame(_df0, want_n, label_col=_label)
    if _smeta and _smeta.get("sampled"):
        sess.tables[tid] = _sampled
        state["n_rows"] = int(len(_sampled))
        state["demurrage_total"] = money_total(_sampled)
        state["sample_row_ids"] = sample_ids(_sampled, id_col=sess.domain.id_col or "container_id")
        state["dev_sample"] = _smeta
    else:
        state["dev_sample"] = _smeta  # may be under-cap note or None
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
    effort = (thinking_effort or "medium").strip().lower()
    if effort not in {"low", "medium", "high"}:
        effort = "medium"
    state["thinking_effort"] = effort
    cmp_ = sess.compare_baseline(
        tid, mode=backend_mode, baseline="sklearn_hist_gbm", test_size=test_size, thinking_effort=effort
    )
    elapsed = time.perf_counter() - t0
    actions = sess.suggest_actions(tid, max_rows=100_000)
    _push_reason = (
        "No reroute or rebooking fits this container, so the quickest fix is to get it collected: push the "
        "terminal or trucker to pick it up before its free days run out. Its likely cost is far above the $300 cost of acting."
    )
    # Containers whose likely cost (chance x fee) beats the action cost are "flagged" and
    # counted as acted-on in the savings, so they must never read "Watch only" / "pay the fee".
    _flag_ids: set[str] = set()
    try:
        from apps.desk.act_first import action_cost as _action_cost
    except ImportError:
        from act_first import action_cost as _action_cost  # type: ignore
    try:
        _mc = pack_meta().get("money_col")
        _pred = sess.last_predictions
        _icol = sess.domain.id_col or pack_meta().get("id_hint") or "container_id"
        if _pred is not None and _mc and _mc in _pred.columns and "proba_1" in _pred.columns and _icol in _pred.columns:
            _exp = _pred["proba_1"].astype(float) * _pred[_mc].astype(float)
            _flag_ids = {str(r) for r in _pred.loc[_exp > _action_cost(), _icol]}
    except Exception:
        _flag_ids = set()
    for a in actions.items:
        if a.action == "authorize_fee" or (a.action == "monitor" and str(a.row_id) in _flag_ids):
            try:
                a.action, a.reason = "call_terminal", _push_reason
            except Exception:
                pass
    _action_of = {str(a.row_id): (a.action, a.reason) for a in actions.items}
    _rank_actions_by_expected_fee(sess, actions, pack_meta().get("money_col"), keep=50)
    # Keep the demo showcase container visible on the board (not buried by rank).
    try:
        from tabpfn_hack_core.core import replay as _replay_pin
        _sid = str((_replay_pin.replay_info() or {}).get("showcase_container_id") or "CONT-000121")
        _items = list(actions.items or [])
        _hit = [a for a in _items if str(a.row_id) == _sid]
        if not _hit and sess.last_predictions is not None:
            _pred = sess.last_predictions
            _icol = sess.domain.id_col or "container_id"
            if _icol in _pred.columns and "proba_1" in _pred.columns:
                _row = _pred.loc[_pred[_icol].astype(str) == _sid]
                if len(_row):
                    from types import SimpleNamespace
                    _r0 = _row.iloc[0]
                    _hit = [SimpleNamespace(
                        row_id=_sid,
                        proba=float(_r0["proba_1"]),
                        action=_action_of.get(_sid, ("call_terminal", _push_reason))[0],
                        reason=_action_of.get(_sid, ("call_terminal", _push_reason))[1],
                    )]
                    _action_of[_sid] = (_hit[0].action, _hit[0].reason)
        if _hit:
            actions.items = _hit + [a for a in _items if str(a.row_id) != _sid]
            actions.items = actions.items[:50]
    except Exception:
        pass
    # Mock explain → action drawer ("Why this move" + importance bars)
    try:
        from apps.desk.explain_ui import format_explain
    except ImportError:
        from explain_ui import format_explain  # type: ignore
    try:
        expl = sess.explain(tid, mode=backend_mode, max_features=8)
        top_reason = actions.items[0].reason if actions.items else None
        top_action = actions.items[0].action if actions.items else None
        state["explain"] = format_explain(
            expl,
            text_cols=list(getattr(sess.domain, "text_cols", None) or []),
            high_card_cols=list(getattr(sess.domain, "high_card_cols", None) or []),
            action_reason=top_reason,
            action=top_action,
        )
    except Exception as exc:  # noqa: BLE001
        state["explain"] = {
            "method": "unavailable",
            "notes": f"Explain skipped: {exc}",
            "bars": [],
            "top_labels": [],
            "why": "Explain unavailable on this run.",
            "n": 0,
        }
    warnings: list[str] = []
    if resolve_warn:
        warnings.append(resolve_warn)
    if sess.last_warning:
        warnings.append(str(sess.last_warning))
    state["metrics"] = metric_slice(cmp_.tabpfn_metrics)
    state["baseline_metrics"] = metric_slice(cmp_.baseline_metrics)
    state["delta"] = metric_slice(cmp_.delta)
    state["baseline_narrative"] = cmp_.narrative
    state["judge_card"] = getattr(cmp_, "judge_card", None) or {}
    state["thinking_effort"] = (sess.last_fit or {}).get("thinking_effort")
    state["thinking_narrative"] = (sess.last_fit or {}).get("thinking_narrative")
    try:
        from tabpfn_hack_core.core.calibration import calibration_from_predictions
        state["calibration"] = calibration_from_predictions(sess.last_predictions)
    except Exception:
        state["calibration"] = None
    state["backend"] = sess.last_backend
    state["replay"] = (sess.last_fit or {}).get("replay")
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
    _af = state["action_counts"].pop("authorize_fee", 0)
    if _af:
        state["action_counts"]["call_terminal"] = state["action_counts"].get("call_terminal", 0) + _af
    state["risk_cards"] = build_risk_cards(sess, tid, state["actions"])
    state["chart_stats"] = chart_stats(
        state["risk_cards"], float(state.get("demurrage_total") or 0.0)
    )
    try:
        from apps.desk.act_first import build_act_first
    except ImportError:
        from act_first import build_act_first  # type: ignore
    _pm = pack_meta()
    state["act_first"] = (
        build_act_first(
            sess.last_predictions,
            id_col=sess.domain.id_col or _pm.get("id_hint") or "container_id",
            money_col=_pm.get("money_col"),
        )
        if _pm.get("spine")
        else None
    )
    if state["act_first"]:
        _by_id = {str(a["row_id"]): a for a in state["actions"]}
        for it in state["act_first"].get("items", []):
            a = _by_id.get(str(it["row_id"])) or {}
            it.setdefault("action", a.get("action") or "Act before free time runs out")
            it.setdefault("reason", a.get("reason") or "")
        try:
            from apps.desk.act_first import group_by_move
        except ImportError:
            from act_first import group_by_move  # type: ignore
        state["act_first"]["by_move"] = group_by_move(
            state["act_first"].get("flagged") or [], _action_of
        )
        state["act_first"].pop("flagged", None)

    try:
        from apps.desk.triage_digest_hook import after_triage
    except ImportError:
        from triage_digest_hook import after_triage  # type: ignore
    after_triage(state)
    df = sess.tables[tid]
    preview = df.head(24).fillna("").to_dict(orient="records")
    state["preview_rows"] = df.head(8).fillna("").to_dict(orient="records")
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
            "mode": "fast",
            "backend": fast_fit.backend,
            "metrics": metric_slice(fast_fit.metrics),
            "elapsed_s": round(time.perf_counter() - t1, 3),
            "warning": fast_warn or fast_fit.warning,
            "note": "Fast A/B stub — queue latency vs Thinking/Plus score (optional).",
        }
        if snap_pred is not None:
            sess.last_predictions = snap_pred
            sess.last_metrics, sess.last_backend, sess.last_mode, sess.last_warning, sess.last_baseline = snap
    else:
        state["fast_ab"] = None


def _rank_actions_by_expected_fee(sess: Any, actions: Any, money_col: str | None, keep: int = 50) -> None:
    """Order the board like the Act-first strip: chance of a fee times the fee at stake."""
    pred = getattr(sess, "last_predictions", None)
    id_col = getattr(sess.domain, "id_col", None) or "container_id"
    items = list(getattr(actions, "items", []) or [])
    if pred is not None and money_col and money_col in pred.columns and id_col in pred.columns:
        fee = dict(zip(pred[id_col].astype(str), pd.to_numeric(pred[money_col], errors="coerce").fillna(0.0)))
        items.sort(key=lambda a: float(a.proba) * float(fee.get(str(a.row_id), 0.0)), reverse=True)
    actions.items = items[:keep]


def apply_triage(app: FastAPI, state: dict[str, Any], **kwargs: Any) -> None:
    """Run triage; if a live TabPFN call is refused, keep the previous results and show why."""
    from tabpfn_hack_core.core.backend import TabPFNLiveError

    sess = getattr(app.state, "session", None)
    saved_state = dict(state)
    saved_tables = dict(sess.tables) if sess is not None else None
    attrs = ("last_predictions", "last_metrics", "last_backend", "last_mode", "last_warning",
             "last_baseline", "last_fit")
    saved_attrs = {a: getattr(sess, a, None) for a in attrs} if sess is not None else {}
    try:
        _apply_triage_impl(app, state, **kwargs)
        state["live_error"] = None
    except TabPFNLiveError as exc:
        state.clear()
        state.update(saved_state)
        sess = getattr(app.state, "session", None)
        if sess is not None and saved_tables is not None:
            sess.tables.clear()
            sess.tables.update(saved_tables)
            for a, v in saved_attrs.items():
                setattr(sess, a, v)
        state["live_error"] = str(exc)
