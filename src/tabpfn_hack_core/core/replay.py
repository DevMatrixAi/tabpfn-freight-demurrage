"""Recorded TabPFN-3.5 scores ("replay") so the desk shows real model output with no token.

The replay file holds out-of-fold probabilities from one live run (5-fold, grouped by vessel):
``container_id, fold, label, p_tabpfn_plus, p_tabpfn_thinking, p_hist_gbm``.
Every container's score came from a model that never saw that container, so scoring the
whole table from it is honest. Rows not in the file get a local estimate and are marked.

Disable with ``DESK_REPLAY=0``; ``DESK_REPLAY=force`` uses it even with a token; point elsewhere with ``DESK_REPLAY_PATH``.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
DEFAULT_REPLAY = _REPO / "artifacts" / "freight-demurrage" / "replay_tabpfn_oof.csv"
MIN_COVERAGE = 0.8


def replay_path() -> Path:
    return Path(os.environ.get("DESK_REPLAY_PATH") or DEFAULT_REPLAY)


def replay_enabled() -> bool:
    flag = os.environ.get("DESK_REPLAY", "1").strip().lower()
    if flag in {"0", "false", "off", "no"}:
        return False
    if flag != "force" and os.environ.get("TABPFN_TOKEN", "").strip():
        return False  # live token present: call the real API instead
    return replay_path().is_file()


@lru_cache(maxsize=4)
def _load(path_s: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path_s)
    return df.drop_duplicates("container_id").set_index("container_id")


def load_replay() -> pd.DataFrame | None:
    p = replay_path()
    if not p.is_file():
        return None
    return _load(str(p), p.stat().st_mtime)


def load_receipt() -> dict[str, Any]:
    p = replay_path()
    r = p.with_name(p.stem + "_receipt.json")
    if not r.is_file():
        return {}
    try:
        return json.loads(r.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def replay_info() -> dict[str, Any]:
    """Small dict for UI labels and banners."""
    rec = load_receipt()
    leaky = bool(rec.get("leaky", True))
    when = str(rec.get("recorded_at") or "")[:10]
    return {
        "active": replay_enabled(),
        "recorded_at": when,
        "leaky": leaky,
        "feature_set": rec.get("feature_set") or ("all columns" if leaky else "clean"),
        "label": f"Real TabPFN-3.5 scores from a saved run ({when})" if when else "Real TabPFN-3.5 scores from a saved run",
        "banner": (
            "The containers are made up for this demo, and a few columns make the answer easy, "
            "so expect lower accuracy on real shipments."
            if leaky
            else "The containers are made up for this demo; answer-revealing columns were removed before scoring."
        ),
    }


def proba_column(mode: str) -> str:
    m = (mode or "").lower()
    if m in {"plus", "fast"}:
        return "p_tabpfn_plus"
    return "p_tabpfn_thinking"


def coverage(df: pd.DataFrame, id_col: str | None) -> float:
    rep = load_replay()
    if rep is None or not id_col or id_col not in df.columns or len(df) == 0:
        return 0.0
    return float(df[id_col].astype(str).isin(rep.index).mean())


def covers(df: pd.DataFrame, id_col: str | None) -> bool:
    return replay_enabled() and coverage(df, id_col) >= MIN_COVERAGE


def lookup(df: pd.DataFrame, id_col: str, column: str) -> pd.Series:
    """Replay probabilities aligned to ``df`` rows (NaN where missing)."""
    rep = load_replay()
    ids = df[id_col].astype(str)
    if rep is None or column not in rep.columns:
        return pd.Series([float("nan")] * len(df), index=df.index)
    return ids.map(rep[column]).astype(float)


def score_table(
    df: pd.DataFrame,
    X: pd.DataFrame,
    y,
    id_col: str,
    column: str,
    *,
    text_cols: list[str] | None = None,
    high_card_cols: list[str] | None = None,
):
    """Return (proba, is_estimate) for every row of ``df``.

    Rows in the replay use the recorded out-of-fold score. Rows not in it (e.g. streamed-in
    containers) get a HistGBM estimate trained on the recorded rows, flagged ``is_estimate``.
    """
    import numpy as np

    from tabpfn_hack_core.core.backend import fit_mock

    proba = lookup(df, id_col, column)
    missing = proba.isna().to_numpy()
    out = proba.to_numpy(dtype=float).copy()
    if missing.any():
        y_a = np.asarray(y)
        have = ~missing
        if have.sum() >= 4 and len(np.unique(y_a[have])) > 1:
            est = fit_mock(
                X[have].reset_index(drop=True), y_a[have],
                X[missing].reset_index(drop=True), y_a[missing],
                text_cols=text_cols, high_card_cols=high_card_cols,
            )
            out[missing] = np.asarray(est.y_proba, dtype=float)
        else:
            out[missing] = float(np.nanmean(out[have])) if have.any() else 0.5
    return out, missing


def recorded_learning_curve() -> dict[str, Any] | None:
    """Learning curve recorded with the replay (TabPFN Plus/Thinking vs HistGBM by training size)."""
    p = replay_path().with_name("learning_curve_summary.csv")
    meta_p = replay_path().with_name("learning_curve_meta.json")
    if not p.is_file():
        return None
    try:
        df = pd.read_csv(p, header=[0, 1], index_col=[0, 1])
        meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.is_file() else {}
    except (OSError, ValueError):
        return None
    rows: dict[int, dict[str, Any]] = {}
    for (n, model), r in df.iterrows():
        try:
            n_i = int(n)
        except (TypeError, ValueError):
            continue
        d = rows.setdefault(n_i, {"n_train": n_i})
        d[str(model)] = {
            "roc_auc": float(r[("roc_auc", "mean")]),
            "net_savings": float(r[("net_savings_300", "mean")]),
        }
    out = [rows[k] for k in sorted(rows)]
    return {
        "recorded": True,
        "rows": out,
        "ns": [r["n_train"] for r in out],
        "n_test": meta.get("test_rows"),
        "headline": (
            "Recorded TabPFN-3.5 runs at each training size, scored on the same held-out vessels. "
            "TabPFN ranks risk better at every size; HistGBM saves slightly more dollars at 30 and 60 rows."
        ),
        "note": (
            f"{meta.get('test_rows', '?')} held-out containers from vessels never seen in training; "
            f"average of {meta.get('repeats', 'several')} draws. Savings assume a $300 action cost."
        ),
    }


def recorded_oracle_net(action_cost: float = 300.0) -> int | None:
    """Net savings a perfect forecast would get at this action cost (same for every model)."""
    rec = load_receipt()
    for v in (rec.get("metrics") or {}).values():
        for c in v.get("cost") or []:
            if float(c.get("action_cost", -1)) == float(action_cost) and c.get("oracle_net") is not None:
                return int(c["oracle_net"])
    return None


def recorded_net_savings(action_cost: float = 300.0) -> dict[str, int]:
    rec = load_receipt()
    out: dict[str, int] = {}
    for k, v in (rec.get("metrics") or {}).items():
        for c in v.get("cost") or []:
            if float(c.get("action_cost", -1)) == float(action_cost):
                out[k] = int(c["net_savings"])
    return out
