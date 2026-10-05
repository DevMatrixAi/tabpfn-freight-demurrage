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
        "label": f"Real TabPFN-3.5 scores, recorded {when}" if when else "Real TabPFN-3.5 scores",
        "banner": (
            "Synthetic benchmark data. A few columns nearly give away the answer, so read these "
            "scores as a benchmark, not real-world shipper accuracy."
            if leaky
            else "Synthetic benchmark data; scores from a clean run with answer-revealing columns removed."
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
