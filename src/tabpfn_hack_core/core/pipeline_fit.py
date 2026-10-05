from __future__ import annotations
"""Fit/load/profile half of PipelineSession (split for GitHub MCP push size)."""
"""In-memory table session + pipeline steps for MCP / demo."""

import json
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from tabpfn_hack_core.core import replay as _replay
from tabpfn_hack_core.core.backend import (
    BackendResult,
    _compute_metrics,
    fit_mock,
    fit_predict_backend,
    resolve_backend,
)
from tabpfn_hack_core.core.jsonutil import jsonable
from tabpfn_hack_core.domain import DomainConfig, load_domain
from tabpfn_hack_core.tools_api import (
    ActionItem,
    BackendMode,
    ColumnProfile,
    CompareBaselineResult,
    ExplainResult,
    ExportReportResult,
    FitPredictResult,
    LoadTableResult,
    ProfileResult,
    SuggestActionsResult,
)


class _FitMixin:
    """Holds loaded tables, last fit results, and domain config."""

    def __init__(self, domain: DomainConfig | None = None, root: Path | None = None):
        self.domain = domain or load_domain()
        self.root = root or Path.cwd()
        self.tables: dict[str, pd.DataFrame] = {}
        self.last_fit: dict[str, Any] = {}
        self.last_predictions: pd.DataFrame | None = None
        self.last_metrics: dict[str, float] = {}
        self.last_backend: str | None = None
        self.last_mode: BackendMode | None = None
        self.last_explain: ExplainResult | None = None
        self.last_baseline: CompareBaselineResult | None = None
        self.last_actions: SuggestActionsResult | None = None
        self.last_warning: str | None = None
        self._feature_names: list[str] = []
        self._model: Any = None

    # ------------------------------------------------------------------ load
    def load_table(
        self,
        path: str | None = None,
        csv_text: str | None = None,
        table_id: str | None = None,
    ) -> LoadTableResult:
        if csv_text:
            df = pd.read_csv(StringIO(csv_text))
        elif path:
            p = Path(path)
            if not p.is_file():
                # try relative to root / data
                alt = self.root / path
                if alt.is_file():
                    p = alt
                else:
                    data_alt = self.root / "data" / Path(path).name
                    if data_alt.is_file():
                        p = data_alt
                    else:
                        raise FileNotFoundError(f"CSV not found: {path}")
            df = pd.read_csv(p)
        else:
            default = self.root / "data" / "synthetic_table.csv"
            if self.domain.data_path:
                default = self.root / self.domain.data_path
            if not default.is_file():
                raise FileNotFoundError(
                    f"No path/csv_text and default missing: {default}"
                )
            df = pd.read_csv(default)

        tid = table_id or f"tbl_{uuid.uuid4().hex[:8]}"
        self.tables[tid] = df
        return LoadTableResult(
            table_id=tid,
            n_rows=len(df),
            n_cols=len(df.columns),
            columns=list(df.columns.astype(str)),
        )

    def _get(self, table_id: str) -> pd.DataFrame:
        if table_id not in self.tables:
            raise KeyError(f"Unknown table_id: {table_id}")
        return self.tables[table_id]

    # --------------------------------------------------------------- profile
    def profile(self, table_id: str, sample_rows: int = 5) -> ProfileResult:
        df = self._get(table_id)
        cols: list[ColumnProfile] = []
        high_card_hint = set(self.domain.high_card_cols)
        text_hint = set(self.domain.text_cols)

        for name in df.columns:
            s = df[name]
            n_unique = int(s.nunique(dropna=True))
            missing_rate = float(s.isna().mean())
            inferred: str
            text_avg_len: float | None = None
            high_card = False

            if name in text_hint or (
                s.dtype == object
                and s.dropna().astype(str).str.len().mean() > 40
            ):
                inferred = "text"
                text_avg_len = float(s.fillna("").astype(str).str.len().mean())
            elif pd.api.types.is_datetime64_any_dtype(s) or name.endswith("_ts"):
                inferred = "datetime"
            elif pd.api.types.is_numeric_dtype(s):
                inferred = "numeric"
            elif n_unique > max(50, int(0.3 * len(df))) or name in high_card_hint:
                inferred = "categorical"
                high_card = True
            else:
                inferred = "categorical"
                high_card = n_unique > 50 or name in high_card_hint

            examples = [
                str(v)
                for v in s.dropna().astype(str).head(sample_rows).tolist()
            ]
            cols.append(
                ColumnProfile(
                    name=str(name),
                    inferred_type=inferred,  # type: ignore[arg-type]
                    missing_rate=missing_rate,
                    n_unique=n_unique,
                    high_cardinality=high_card,
                    text_avg_len=text_avg_len,
                    examples=examples,
                )
            )

        return ProfileResult(
            table_id=table_id,
            n_rows=len(df),
            columns=cols,
            suggested_group_col=self.domain.group_col,
            suggested_time_col=self.domain.time_col,
            suggested_label=self.domain.label_col,
        )

    # ----------------------------------------------------------- fit_predict
    def _feature_frame(
        self,
        df: pd.DataFrame,
        label_col: str,
        feature_cols: list[str] | None = None,
    ) -> pd.DataFrame:
        exclude = set(self.domain.feature_exclude) | {label_col, "row_id"}
        # When fitting a non-primary head, drop the primary label so it is not a feature.
        if label_col != self.domain.label_col:
            exclude.add(self.domain.label_col)
        sec = getattr(self.domain, "secondary_label_col", None)
        if sec and label_col != sec:
            # Primary head may keep secondary as a feature (e.g. blank_sailing → demurrage).
            pass
        if feature_cols:
            cols = [c for c in feature_cols if c in df.columns and c != label_col]
        else:
            cols = [c for c in df.columns if c not in exclude]
        return df[cols].copy()

    def _fit_predict_replay(
        self, df, X, y, table_id, label, req_mode, effort, gcol, tcol, predictions_path
    ) -> FitPredictResult:
        """Score every row from recorded TabPFN-3.5 out-of-fold probabilities (no API call)."""
        shown_mode = BackendMode.thinking if req_mode == BackendMode.mock else req_mode
        col = _replay.proba_column(shown_mode.value)  # Fast was not recorded; it never reaches here
        proba, est = _replay.score_table(
            df, X, y, self.domain.id_col, col,
            text_cols=self.domain.text_cols, high_card_cols=self.domain.high_card_cols,
        )
        y_a = np.asarray(y)
        y_pred = (proba >= 0.5).astype(int)
        metrics = _compute_metrics(y_a, y_pred, proba)
        info = _replay.replay_info()
        pred_df = df.copy().reset_index(drop=True)
        pred_df["y_true"] = y_a
        pred_df["y_pred"] = y_pred
        pred_df["proba_1"] = proba
        pred_df["score_source"] = np.where(est, "estimate", "tabpfn_replay")
        n = len(df)
        n_est = int(est.sum())
        self.last_predictions = pred_df
        self.last_metrics = metrics
        self.last_backend = "tabpfn_replay"
        self.last_mode = shown_mode
        self.last_warning = None
        self._feature_names = list(X.columns)
        self._model = None
        rec = _replay.load_receipt()
        think = rec.get("thinking") or {}
        narrative = None
        if shown_mode == BackendMode.thinking:
            narrative = (
                f"{info['label']}: Thinking mode, effort {think.get('effort', effort)}, "
                f"grouped by {think.get('group_col', gcol)}, ordered by {think.get('group_time_col', tcol)}. "
                "Each container was scored by a model that never saw it (5-fold, split by vessel)."
            )
        self.last_fit = {
            "table_id": table_id,
            "label_col": label,
            "mode": shown_mode.value,
            "backend": "tabpfn_replay",
            "metrics": metrics,
            "n_train": int(round(n * 0.8)),
            "n_test": n,
            "thinking_effort": think.get("effort", effort) if shown_mode == BackendMode.thinking else None,
            "group_col": gcol,
            "group_time_col": tcol,
            "thinking_narrative": narrative,
            "replay": {**info, "n_scored": n, "n_estimated": n_est, "column": col},
        }
        out_path: str | None = None
        if predictions_path is not None:
            p = Path(predictions_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            clean = [{k: jsonable(v) for k, v in row.items()} for row in pred_df.to_dict(orient="records")]
            p.write_text(json.dumps(clean, indent=2), encoding="utf-8")
            out_path = str(p)
        preview = [
            {
                "row_id": str(row.get("row_id", row.get(self.domain.id_col or "row_id", i))),
                "y_true": jsonable(row["y_true"]),
                "y_pred": jsonable(row["y_pred"]),
                "proba_1": float(row["proba_1"]),
            }
            for i, row in pred_df.head(5).iterrows()
        ]
        return FitPredictResult(
            mode=shown_mode,
            backend="tabpfn_replay",  # type: ignore[arg-type]
            metrics=metrics,
            n_train=int(round(n * 0.8)),
            n_test=n,
            predictions_path=out_path,
            preview=preview,
            warning=None,
            thinking_effort=self.last_fit["thinking_effort"],
            group_col=gcol,
            group_time_col=tcol,
            thinking_narrative=narrative,
        )

    def fit_predict(
        self,
        table_id: str,
        label_col: str | None = None,
        feature_cols: list[str] | None = None,
        mode: BackendMode | str = BackendMode.mock,
        test_size: float = 0.2,
        group_col: str | None = None,
        group_time_col: str | None = None,
        thinking_effort: str | None = None,
        random_state: int = 42,
        predictions_path: str | Path | None = None,
    ) -> FitPredictResult:
        df = self._get(table_id)
        label = label_col or self.domain.label_col
        if label not in df.columns:
            raise ValueError(f"label_col {label!r} not in table")

        gcol = group_col if group_col is not None else self.domain.group_col
        tcol = group_time_col if group_time_col is not None else self.domain.time_col
        effort = thinking_effort or "medium"

        X = self._feature_frame(df, label, feature_cols)
        y = df[label].to_numpy()

        id_col = self.domain.id_col
        req_mode = resolve_backend(mode)
        if (
            label == self.domain.label_col
            and req_mode in (BackendMode.mock, BackendMode.plus, BackendMode.thinking)
            and _replay.covers(df, id_col)
        ):
            return self._fit_predict_replay(
                df, X, y, table_id, label, req_mode, effort, gcol, tcol, predictions_path
            )

        X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
            X, y, df.index.to_numpy(), test_size=test_size, random_state=random_state,
            stratify=y if len(np.unique(y)) > 1 else None,
        )

        result = fit_predict_backend(
            mode,
            X_train.reset_index(drop=True),
            y_train,
            X_test.reset_index(drop=True),
            y_test,
            group_col=gcol,
            group_time_col=tcol,
            text_cols=self.domain.text_cols,
            high_card_cols=self.domain.high_card_cols,
            thinking_effort=effort,
        )

        # Build predictions frame
        pred_df = df.loc[idx_test].copy()
        pred_df = pred_df.reset_index(drop=True)
        pred_df["y_true"] = y_test
        pred_df["y_pred"] = result.y_pred
        pred_df["proba_1"] = result.y_proba

        self.last_predictions = pred_df
        self.last_metrics = result.metrics
        self.last_backend = result.backend
        self.last_mode = result.mode
        self.last_warning = result.warning
        self._feature_names = result.feature_names
        self._model = result.model
        self.last_fit = {
            "table_id": table_id,
            "label_col": label,
            "mode": result.mode.value,
            "backend": result.backend,
            "metrics": result.metrics,
            "n_train": result.n_train,
            "n_test": result.n_test,
            "thinking_effort": result.thinking_effort,
            "group_col": result.group_col,
            "group_time_col": result.group_time_col,
            "thinking_narrative": result.thinking_narrative,
        }

        out_path: str | None = None
        if predictions_path is not None:
            p = Path(predictions_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            records = pred_df.to_dict(orient="records")
            # JSON-serializable
            clean = []
            for row in records:
                clean.append({k: (jsonable(v)) for k, v in row.items()})
            p.write_text(json.dumps(clean, indent=2), encoding="utf-8")
            out_path = str(p)

        preview = []
        for _, row in pred_df.head(5).iterrows():
            preview.append(
                {
                    "row_id": str(row.get("row_id", row.name)),
                    "y_true": jsonable(row["y_true"]),
                    "y_pred": jsonable(row["y_pred"]),
                    "proba_1": float(row["proba_1"]),
                }
            )

        return FitPredictResult(
            mode=result.mode,
            backend=result.backend,  # type: ignore[arg-type]
            metrics=result.metrics,
            n_train=result.n_train,
            n_test=result.n_test,
            predictions_path=out_path,
            preview=preview,
            warning=result.warning,
            thinking_effort=result.thinking_effort,
            group_col=result.group_col,
            group_time_col=result.group_time_col,
            thinking_narrative=result.thinking_narrative,
        )
