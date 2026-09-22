"""TabPFN backends: plus | thinking | fast | local | mock.

Mock uses sklearn and always works without TABPFN_TOKEN / GPU.
"""
from __future__ import annotations

import hashlib
import os
import warnings
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder

from tabpfn_hack_core.tools_api import BackendMode

BackendKind = Literal["tabpfn_client", "tabpfn_oss", "mock"]


@dataclass
class BackendResult:
    mode: BackendMode
    backend: BackendKind
    y_pred: np.ndarray
    y_proba: np.ndarray
    metrics: dict[str, float]
    model: Any = None
    feature_names: list[str] = field(default_factory=list)
    warning: str | None = None
    n_train: int = 0
    n_test: int = 0
    thinking_effort: str | None = None
    group_col: str | None = None
    group_time_col: str | None = None
    thinking_narrative: str | None = None


def _has_token() -> bool:
    return bool(os.environ.get("TABPFN_TOKEN", "").strip())


def _hash_series(s: pd.Series, n_buckets: int = 64) -> np.ndarray:
    out = np.zeros(len(s), dtype=np.float64)
    for i, v in enumerate(s.astype(str).fillna("__NA__")):
        h = int(hashlib.md5(v.encode("utf-8")).hexdigest(), 16)
        out[i] = float(h % n_buckets)
    return out


def _prepare_mock_matrix(
    X: pd.DataFrame,
    text_cols: list[str] | None = None,
    high_card_cols: list[str] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Numeric + simple hashed categoricals / text length for mock sklearn."""
    text_cols = text_cols or []
    high_card_cols = high_card_cols or []
    parts: list[np.ndarray] = []
    names: list[str] = []

    for col in X.columns:
        series = X[col]
        if col in text_cols or (
            series.dtype == object
            and series.dropna().astype(str).str.len().mean() > 40
        ):
            lengths = series.fillna("").astype(str).str.len().to_numpy(dtype=np.float64)
            parts.append(lengths.reshape(-1, 1))
            names.append(f"{col}__len")
            # crude token count
            tokens = (
                series.fillna("")
                .astype(str)
                .str.split()
                .str.len()
                .fillna(0)
                .to_numpy(dtype=np.float64)
            )
            parts.append(tokens.reshape(-1, 1))
            names.append(f"{col}__tokens")
        elif pd.api.types.is_numeric_dtype(series):
            arr = pd.to_numeric(series, errors="coerce").to_numpy(dtype=np.float64)
            parts.append(arr.reshape(-1, 1))
            names.append(col)
        else:
            hashed = _hash_series(series)
            parts.append(hashed.reshape(-1, 1))
            names.append(f"{col}__hash")

    if not parts:
        mat = np.zeros((len(X), 1), dtype=np.float64)
        return mat, ["_const"]
    mat = np.hstack(parts)
    # fill NaN with column median
    for j in range(mat.shape[1]):
        col = mat[:, j]
        mask = np.isnan(col)
        if mask.any():
            med = np.nanmedian(col) if (~mask).any() else 0.0
            col[mask] = med
            mat[:, j] = col
    return mat, names


def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> dict[str, float]:
    metrics: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    try:
        if len(np.unique(y_true)) > 1:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
            metrics["avg_precision"] = float(average_precision_score(y_true, y_proba))
        else:
            metrics["roc_auc"] = float("nan")
            metrics["avg_precision"] = float("nan")
    except ValueError:
        metrics["roc_auc"] = float("nan")
        metrics["avg_precision"] = float("nan")
    return metrics


def fit_mock(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    *,
    text_cols: list[str] | None = None,
    high_card_cols: list[str] | None = None,
    prefer: Literal["hist_gbm", "logistic"] = "hist_gbm",
) -> BackendResult:
    Xt, names = _prepare_mock_matrix(X_train, text_cols, high_card_cols)
    Xv, _ = _prepare_mock_matrix(X_test, text_cols, high_card_cols)

    le = LabelEncoder()
    yt = le.fit_transform(y_train)
    yv = le.transform(y_test) if len(y_test) else np.array([], dtype=int)

    model: Any
    try:
        if prefer == "hist_gbm":
            model = HistGradientBoostingClassifier(max_depth=4, max_iter=80, random_state=42)
            model.fit(Xt, yt)
        else:
            raise ValueError("force logistic")
    except Exception:
        model = LogisticRegression(max_iter=500, random_state=42)
        # replace nan already handled; clip extreme
        model.fit(np.nan_to_num(Xt), yt)
        Xt = np.nan_to_num(Xt)
        Xv = np.nan_to_num(Xv)

    proba = model.predict_proba(Xv)
    # binary positive class index
    if proba.shape[1] == 1:
        y_proba = proba[:, 0]
    else:
        # prefer class "1" if present
        classes = list(getattr(model, "classes_", range(proba.shape[1])))
        pos_idx = classes.index(1) if 1 in classes else int(np.argmax(classes))
        y_proba = proba[:, pos_idx]
    y_pred = (y_proba >= 0.5).astype(int)
    # map back if needed
    if set(le.classes_) != {0, 1} and len(le.classes_) == 2:
        # keep 0/1 as encoded labels for metrics vs yv
        pass

    metrics = _compute_metrics(yv, y_pred, y_proba) if len(yv) else {}
    return BackendResult(
        mode=BackendMode.mock,
        backend="mock",
        y_pred=y_pred,
        y_proba=y_proba,
        metrics=metrics,
        model=model,
        feature_names=names,
        n_train=len(yt),
        n_test=len(yv),
    )


def _thinking_narrative(
    mode: BackendMode,
    *,
    group_col: str | None,
    group_time_col: str | None,
    thinking_effort: str | None,
) -> str | None:
    if mode != BackendMode.thinking:
        return None
    effort = thinking_effort or "medium"
    bits = [
        "TabPFN-3.5-Thinking",
        f"thinking_mode=True",
        f"thinking_effort={effort}",
    ]
    if group_col:
        bits.append(f"group_col={group_col}")
    if group_time_col:
        bits.append(f"group_time_col={group_time_col}")
    bits.append(
        "non-i.i.d. vessel/time context visible to the fit "
        "(Prior Labs Thinking docs: grouped + temporal rows)."
    )
    return " · ".join(bits)


def _try_tabpfn_client(
    mode: BackendMode,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    *,
    group_col: str | None = None,
    group_time_col: str | None = None,
    thinking_effort: str | None = None,
) -> BackendResult | None:
    if not _has_token():
        return None
    try:
        from tabpfn_client import TabPFNClassifier  # type: ignore
    except ImportError:
        warnings.warn("tabpfn_client not installed; falling back to mock", stacklevel=2)
        return None

    try:
        # Constructor accepts thinking_mode / group_col / time_col / group_time_col.
        # Setting attributes after fit is a no-op for inference — must pass at init.
        overrides: dict[str, Any] = {}
        effort = thinking_effort or "medium"
        if mode == BackendMode.thinking:
            overrides["thinking_mode"] = True
            overrides["thinking_effort"] = effort
            if group_col:
                overrides["group_col"] = group_col
            if group_time_col:
                # Client: group_time_col requires group_col; cannot combine with time_col.
                overrides["group_time_col"] = group_time_col

        if mode == BackendMode.fast:
            clf = TabPFNClassifier.create_default_for_version("v3.5-fast", **overrides)
        else:
            # plus + thinking share v3.5 weights; thinking differs via overrides
            clf = TabPFNClassifier.create_default_for_version("v3.5", **overrides)

        clf.fit(X_train, y_train)

        proba = clf.predict_proba(X_test)
        if proba.ndim == 1:
            y_proba = np.asarray(proba, dtype=float)
        else:
            classes = list(getattr(clf, "classes_", range(proba.shape[1])))
            pos_idx = classes.index(1) if 1 in classes else -1
            y_proba = np.asarray(proba[:, pos_idx], dtype=float)
        y_pred = (y_proba >= 0.5).astype(int)
        metrics = _compute_metrics(np.asarray(y_test), y_pred, y_proba)
        return BackendResult(
            mode=mode,
            backend="tabpfn_client",
            y_pred=y_pred,
            y_proba=y_proba,
            metrics=metrics,
            model=clf,
            feature_names=list(X_train.columns),
            n_train=len(y_train),
            n_test=len(y_test),
            thinking_effort=effort if mode == BackendMode.thinking else None,
            group_col=group_col if mode == BackendMode.thinking else None,
            group_time_col=group_time_col if mode == BackendMode.thinking else None,
            thinking_narrative=_thinking_narrative(
                mode,
                group_col=group_col,
                group_time_col=group_time_col,
                thinking_effort=effort,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        warnings.warn(f"tabpfn_client failed ({exc}); falling back to mock", stacklevel=2)
        return None


def _try_local_tabpfn(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
) -> BackendResult | None:
    try:
        from tabpfn import TabPFNClassifier  # type: ignore
    except ImportError:
        return None
    try:
        clf = TabPFNClassifier()
        clf.fit(X_train, y_train)
        proba = clf.predict_proba(X_test)
        classes = list(getattr(clf, "classes_", range(proba.shape[1])))
        pos_idx = classes.index(1) if 1 in classes else -1
        y_proba = np.asarray(proba[:, pos_idx], dtype=float)
        y_pred = (y_proba >= 0.5).astype(int)
        metrics = _compute_metrics(np.asarray(y_test), y_pred, y_proba)
        return BackendResult(
            mode=BackendMode.local,
            backend="tabpfn_oss",
            y_pred=y_pred,
            y_proba=y_proba,
            metrics=metrics,
            model=clf,
            feature_names=list(X_train.columns),
            n_train=len(y_train),
            n_test=len(y_test),
        )
    except Exception as exc:  # noqa: BLE001 — OOM etc.
        warnings.warn(f"local tabpfn failed ({exc}); falling back to mock", stacklevel=2)
        return None


def resolve_backend(mode: BackendMode | str | None = None) -> BackendMode:
    """Choose effective mode. Default: mock when no token / explicit mock."""
    if mode is None or mode == "" or str(mode) == "auto":
        return BackendMode.plus if _has_token() else BackendMode.mock
    return BackendMode(mode)


def fit_predict_backend(
    mode: BackendMode | str,
    X_train: pd.DataFrame,
    y_train: np.ndarray | pd.Series,
    X_test: pd.DataFrame,
    y_test: np.ndarray | pd.Series,
    *,
    group_col: str | None = None,
    group_time_col: str | None = None,
    text_cols: list[str] | None = None,
    high_card_cols: list[str] | None = None,
    thinking_effort: str | None = None,
) -> BackendResult:
    """Fit and predict with the requested backend; fall back to mock as needed."""
    mode = resolve_backend(mode)
    y_train_a = np.asarray(y_train)
    y_test_a = np.asarray(y_test)
    warning: str | None = None
    effort = thinking_effort or "medium"

    def _annotate_mock(mock: BackendResult) -> BackendResult:
        if mode == BackendMode.thinking:
            mock.thinking_effort = effort
            mock.group_col = group_col
            mock.group_time_col = group_time_col
            mock.thinking_narrative = _thinking_narrative(
                mode,
                group_col=group_col,
                group_time_col=group_time_col,
                thinking_effort=effort,
            )
        return mock

    if mode == BackendMode.mock:
        return fit_mock(
            X_train, y_train_a, X_test, y_test_a,
            text_cols=text_cols, high_card_cols=high_card_cols,
        )

    if mode == BackendMode.local:
        result = _try_local_tabpfn(X_train, y_train_a, X_test, y_test_a)
        if result is not None:
            return result
        warning = "local tabpfn unavailable; using mock backend"
        mock = fit_mock(
            X_train, y_train_a, X_test, y_test_a,
            text_cols=text_cols, high_card_cols=high_card_cols,
        )
        mock.warning = warning
        mock.mode = BackendMode.local
        return mock

    # plus / thinking / fast via client
    if not _has_token():
        warning = f"TABPFN_TOKEN not set; mode={mode.value} falling back to mock"
        warnings.warn(warning, stacklevel=2)
        mock = fit_mock(
            X_train, y_train_a, X_test, y_test_a,
            text_cols=text_cols, high_card_cols=high_card_cols,
        )
        mock.warning = warning
        mock.mode = mode
        return _annotate_mock(mock)

    result = _try_tabpfn_client(
        mode, X_train, y_train_a, X_test, y_test_a,
        group_col=group_col, group_time_col=group_time_col,
        thinking_effort=effort,
    )
    if result is not None:
        return result
    warning = f"tabpfn_client failed for mode={mode.value}; using mock"
    mock = fit_mock(
        X_train, y_train_a, X_test, y_test_a,
        text_cols=text_cols, high_card_cols=high_card_cols,
    )
    mock.warning = warning
    mock.mode = mode
    return _annotate_mock(mock)
