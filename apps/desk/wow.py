"""Desk wow-layer: blank-sailing second head + synthetic what-if."""
from __future__ import annotations

from typing import Any

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.tools_api import BackendMode

BLANK_LABEL = "blank_sailing"
METRIC_KEYS = ("accuracy", "f1", "roc_auc", "avg_precision")


def metric_slice(metrics: dict[str, float] | None) -> dict[str, float]:
    if not metrics:
        return {}
    return {
        k: float(metrics[k])
        for k in METRIC_KEYS
        if k in metrics and isinstance(metrics[k], (int, float))
    }


def sample_ids(df, id_col: str | None = "container_id", limit: int = 18) -> list[str]:
    candidates = [c for c in (id_col, "container_id", "booking_id", "move_id", "row_id") if c]
    col = next((c for c in candidates if c in df.columns), None)
    if not col:
        return []
    ids = [str(x) for x in df[col].head(12).tolist()]
    if "blank_sailing" in df.columns:
        for p in df.loc[df["blank_sailing"].astype(int) == 1, col].astype(str).head(6):
            if p not in ids:
                ids.append(p)
    return ids[:limit]


def run_blank_head(
    sess: PipelineSession,
    tid: str,
    mode: BackendMode,
    test_size: float,
    state: dict[str, Any],
) -> None:
    """Fit blank_sailing second head via label_col override; restore demurrage preds."""
    label = getattr(sess.domain, "secondary_label_col", None) or BLANK_LABEL
    state["blank_label"] = label
    if tid not in sess.tables or label not in sess.tables[tid].columns:
        state["blank_metrics"] = None
        state["blank_backend"] = None
        state["blank_warning"] = f"Column {label!r} missing — blank-sailing head skipped"
        return

    snap_pred = None if sess.last_predictions is None else sess.last_predictions.copy()
    snap = (
        sess.last_metrics,
        sess.last_backend,
        sess.last_mode,
        sess.last_warning,
        sess.last_baseline,
        dict(sess.last_fit) if getattr(sess, "last_fit", None) else None,
    )
    try:
        blank_fit = sess.fit_predict(tid, label_col=label, mode=mode, test_size=test_size)
        state["blank_metrics"] = metric_slice(blank_fit.metrics)
        state["blank_backend"] = blank_fit.backend
        state["blank_warning"] = blank_fit.warning
    except Exception as exc:  # noqa: BLE001
        state["blank_metrics"] = None
        state["blank_backend"] = None
        state["blank_warning"] = f"Blank-sailing head failed: {exc}"
    finally:
        if snap_pred is not None:
            sess.last_predictions = snap_pred
            (
                sess.last_metrics,
                sess.last_backend,
                sess.last_mode,
                sess.last_warning,
                sess.last_baseline,
            ) = snap[:5]
            if snap[5] is not None:
                sess.last_fit = snap[5]


def run_what_if(
    sess: PipelineSession,
    tid: str,
    row_id: str,
    overrides: dict[str, Any],
    mode: BackendMode,
) -> dict[str, Any]:
    """Synthetic what-if wrapper around PipelineSession.what_if."""
    return sess.what_if(tid, row_id=row_id, overrides=overrides, mode=mode)
