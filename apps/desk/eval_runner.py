"""Eval runner helpers — readable split for judge repro."""
from __future__ import annotations

import time
from typing import Any, Callable

from tabpfn_hack_core.core.ablations import run_feature_ablations
from tabpfn_hack_core.core.calibration import calibration_from_predictions
from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.tools_api import BackendMode


try:
    from ensure_deep_templates import ensure_deep_templates as _ensure_deep_tpl
    _ensure_deep_tpl()
except Exception:
    try:
        from apps.desk.ensure_deep_templates import ensure_deep_templates as _ensure_deep_tpl
        _ensure_deep_tpl()
    except Exception:
        pass

EVAL_MODES = ("plus", "thinking", "fast")
METRIC_KEYS = ("accuracy", "f1", "roc_auc", "avg_precision")
METRIC_LABELS = {
    "accuracy": "Accuracy",
    "f1": "F1",
    "roc_auc": "ROC-AUC",
    "avg_precision": "AP",
}


def _slice(metrics: dict[str, float] | None, keys: tuple[str, ...] = METRIC_KEYS) -> dict[str, float]:
    if not metrics:
        return {}
    return {
        k: float(metrics[k])
        for k in keys
        if k in metrics and isinstance(metrics[k], (int, float))
    }


def run_multi_mode_eval(
    sess: PipelineSession,
    table_id: str,
    *,
    resolve_mode: Callable[[str], tuple[BackendMode, str | None]],
    metric_slice: Callable[[dict[str, float] | None], dict[str, float]] | None = None,
    modes: tuple[str, ...] = EVAL_MODES,
    test_size: float | None = None,
) -> dict[str, Any]:
    """Run compare_baseline for Plus/Thinking/Fast vs sklearn HistGBM.

    Without TABPFN_TOKEN, cloud modes fall back to mock (still renders the board).
    With TABPFN_TOKEN set, live TabPFN backends populate metrics.
    """
    slice_fn = metric_slice or _slice
    full_n = len(sess.tables[table_id])
    # Cap rows for interactive dashboard latency / live TabPFN budget
    try:
        from apps.desk.dev_sample import resolve_sample_n
    except ImportError:
        from dev_sample import resolve_sample_n  # type: ignore
    _dev = resolve_sample_n(None)
    max_rows = int(_dev) if _dev else 200
    from tabpfn_hack_core.core import replay as _replay

    replay_on = _replay.covers(sess.tables[table_id], sess.domain.id_col)
    skipped: list[str] = []
    if replay_on:
        # Recorded scores: whole table, free. Fast was not part of the recorded run.
        max_rows = full_n
        skipped = [m for m in modes if m not in ("plus", "thinking")]
        modes = tuple(m for m in modes if m in ("plus", "thinking"))
    if full_n > max_rows:
        # stratified-ish: shuffle with fixed seed then head
        sess.tables[table_id] = (
            sess.tables[table_id].sample(n=max_rows, random_state=42).reset_index(drop=True)
        )
    n = len(sess.tables[table_id])
    ts = test_size if test_size is not None else (0.3 if n >= 10 else 0.25)
    rows: list[dict[str, Any]] = []
    baseline_metrics: dict[str, float] | None = None
    warnings: list[str] = []
    t0 = time.perf_counter()

    for mode_name in modes:
        backend_mode, resolve_warn = resolve_mode(mode_name)
        if resolve_warn:
            warnings.append(resolve_warn)
        t_mode = time.perf_counter()
        cmp_ = sess.compare_baseline(
            table_id,
            mode=backend_mode,
            baseline="sklearn_hist_gbm",
            test_size=ts,
        )
        elapsed_mode = round(time.perf_counter() - t_mode, 3)
        primary = slice_fn(cmp_.tabpfn_metrics)
        base = slice_fn(cmp_.baseline_metrics)
        delta = slice_fn(cmp_.delta)
        if baseline_metrics is None:
            baseline_metrics = base

        effective = sess.last_mode
        eff_s = effective.value if hasattr(effective, "value") else str(effective or mode_name)
        backend = sess.last_backend or "unknown"
        if sess.last_warning:
            warnings.append(f"{mode_name}: {sess.last_warning}")

        live = backend not in {"mock", "unknown", "tabpfn_replay"} and eff_s == mode_name
        rows.append(
            {
                "mode": mode_name,
                "requested_mode": (
                    backend_mode.value if hasattr(backend_mode, "value") else str(backend_mode)
                ),
                "effective_mode": eff_s,
                "backend": backend,
                "metrics": primary,
                "delta": delta,
                "elapsed_s": elapsed_mode,
                "narrative": cmp_.narrative,
                "live": live,
                "recorded": backend == "tabpfn_replay",
                "is_baseline": False,
            }
        )

    hist_row = {
        "mode": "hist_gbm",
        "requested_mode": "sklearn_hist_gbm",
        "effective_mode": "hist_gbm",
        "backend": "sklearn",
        "metrics": baseline_metrics or {},
        "delta": {k: 0.0 for k in METRIC_KEYS},
        "elapsed_s": None,
        "narrative": (
            "HistGBM scored on the same 5 folds as the recorded TabPFN run"
            if replay_on
            else "sklearn HistGradientBoosting baseline (shared compare_baseline split)"
        ),
        "live": False,
        "is_baseline": True,
    }

    all_vals: list[float] = []
    for r in rows + [hist_row]:
        all_vals.extend(float(v) for v in (r.get("metrics") or {}).values())
    bar_max = max(all_vals) if all_vals else 1.0
    if bar_max <= 0:
        bar_max = 1.0

    for r in rows + [hist_row]:
        m = r.get("metrics") or {}
        r["bars"] = {
            k: round(100.0 * float(m.get(k, 0.0)) / bar_max, 1) for k in METRIC_KEYS
        }

    # Alias keys for the Jinja template (eval.html)
    for r in rows + [hist_row]:
        r["is_baseline"] = r.get("is_baseline", False)
        r["effective_mode"] = r.get("effective_mode")
        r["elapsed_s"] = r.get("elapsed_s")

    # Fast vs Plus latency panel (elapsed_s already measured per mode)
    by_mode = {r["mode"]: r for r in rows}
    plus_s = by_mode.get("plus", {}).get("elapsed_s")
    fast_s = by_mode.get("fast", {}).get("elapsed_s")
    think_s = by_mode.get("thinking", {}).get("elapsed_s")
    speedup = None
    if isinstance(plus_s, (int, float)) and isinstance(fast_s, (int, float)) and fast_s > 0:
        speedup = round(float(plus_s) / float(fast_s), 2)
    latency_panel = {
        "plus_s": plus_s,
        "fast_s": fast_s,
        "thinking_s": think_s,
        "fast_vs_plus_speedup": speedup,
        "headline": (
            f"Fast {fast_s}s vs Plus {plus_s}s"
            + (f" ({speedup}×)" if speedup else "")
            + (f" · Thinking {think_s}s" if think_s is not None else "")
        ),
        "note": (
            "Wall-clock on this desk (mock or live). TabPFN-3.5-Fast is the "
            "latency path; Thinking spends fit-time compute for grouped/temporal quality."
        ),
    }

    # Text / high-card ablations on current (possibly capped) table
    ablations = None
    try:
        df = sess.tables[table_id]
        label = sess.domain.label_col
        X = sess._feature_frame(df, label)
        y = df[label].to_numpy()
        ablations = run_feature_ablations(X, y, sess.domain, test_size=ts)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"ablations skipped: {exc}")

    if replay_on:
        ablations = None  # would only retrain HistGBM; not a TabPFN result
    calibration = calibration_from_predictions(sess.last_predictions)

    # Denser judge card from last compare_baseline (thinking row preferred)
    judge_card = None
    if sess.last_baseline is not None:
        judge_card = getattr(sess.last_baseline, "judge_card", None) or {
            "narrative": sess.last_baseline.narrative,
            "delta": sess.last_baseline.delta,
        }
    # Prefer Thinking row narrative if present
    think_row = by_mode.get("thinking")
    thinking_showcase = None
    if think_row:
        thinking_showcase = {
            "mode": "thinking",
            "group_col": sess.domain.group_col,
            "group_time_col": sess.domain.time_col,
            "thinking_effort": (sess.last_fit or {}).get("thinking_effort") or "medium",
            "narrative": (sess.last_fit or {}).get("thinking_narrative")
            or think_row.get("narrative"),
            "elapsed_s": think_row.get("elapsed_s"),
            "metrics": think_row.get("metrics") or {},
            "delta": think_row.get("delta") or {},
            "live": think_row.get("live"),
        }

    try:
        from apps.desk.eval_lc import maybe_learning_curve
    except ImportError:
        from eval_lc import maybe_learning_curve  # type: ignore
    learning_curve = (
        _replay.recorded_learning_curve() if replay_on else None
    ) or maybe_learning_curve(sess, table_id, warnings)
    replay_meta = None
    if replay_on:
        latency_panel = None  # recorded scores load instantly; latency needs a live run
        replay_meta = {
            **_replay.replay_info(),
            "net_savings_300": _replay.recorded_net_savings(300.0),
            "skipped_modes": skipped,
        }

    return {
        "rows": rows,
        "learning_curve": learning_curve,
        "hist_gbm": hist_row,
        "display_rows": rows + [hist_row],
        "baseline_metrics": baseline_metrics or {},
        "metric_keys": list(METRIC_KEYS),
        "metric_labels": METRIC_LABELS,
        "warnings": warnings,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "test_size": ts,
        "n_rows": n,
        "full_n_rows": full_n,
        "bar_max": bar_max,
        "latency_panel": latency_panel,
        "ablations": ablations,
        "calibration": calibration,
        "judge_card": judge_card,
        "thinking_showcase": thinking_showcase,
        "replay": replay_meta,
    }


