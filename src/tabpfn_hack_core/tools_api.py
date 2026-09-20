"""Typed contracts for the seven MCP tools — domain-agnostic.

Apache-2.0. Synthetic demos only; not clinical software.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class BackendMode(str, Enum):
    plus = "plus"
    thinking = "thinking"
    fast = "fast"
    local = "local"
    mock = "mock"


class OpsErrorCode(str, Enum):
    not_found = "not_found"
    invalid_argument = "invalid_argument"
    missing_token = "missing_token"
    backend_failed = "backend_failed"
    not_fitted = "not_fitted"


class OpsError(BaseModel):
    code: OpsErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class LoadTableArgs(BaseModel):
    path: str | None = None
    csv_text: str | None = None
    table_id: str | None = None


class LoadTableResult(BaseModel):
    table_id: str
    n_rows: int
    n_cols: int
    columns: list[str]


class ProfileArgs(BaseModel):
    table_id: str
    sample_rows: int = Field(5, ge=0, le=50)


class ColumnProfile(BaseModel):
    name: str
    inferred_type: Literal["numeric", "categorical", "text", "datetime", "other"]
    missing_rate: float
    n_unique: int
    high_cardinality: bool
    text_avg_len: float | None = None
    examples: list[str] = Field(default_factory=list)


class ProfileResult(BaseModel):
    table_id: str
    n_rows: int
    columns: list[ColumnProfile]
    suggested_group_col: str | None = None
    suggested_time_col: str | None = None
    suggested_label: str | None = None


class FitPredictArgs(BaseModel):
    table_id: str
    label_col: str | None = None
    feature_cols: list[str] | None = None
    mode: BackendMode = BackendMode.mock
    test_size: float = Field(0.2, gt=0.0, lt=0.9)
    group_col: str | None = None
    group_time_col: str | None = None
    thinking_effort: Literal["medium", "high"] = "medium"
    random_state: int = 42


class FitPredictResult(BaseModel):
    mode: BackendMode
    backend: Literal["tabpfn_client", "tabpfn_oss", "mock"]
    metrics: dict[str, float]
    n_train: int
    n_test: int
    predictions_path: str | None = None
    preview: list[dict[str, Any]] = Field(default_factory=list)
    warning: str | None = None


class ExplainArgs(BaseModel):
    table_id: str
    label_col: str | None = None
    mode: BackendMode = BackendMode.mock
    max_features: int = Field(10, ge=1, le=50)
    row_index: int | None = None


class ExplainResult(BaseModel):
    method: str
    importances: list[dict[str, float | str]]
    notes: str = ""


class ExportReportArgs(BaseModel):
    table_id: str
    title: str = "tabpfn-hack-core demo report (synthetic)"
    formats: list[Literal["markdown", "html", "json"]] = Field(
        default_factory=lambda: ["markdown", "json"]
    )
    out_dir: str = "artifacts"


class ExportReportResult(BaseModel):
    paths: dict[str, str]


class CompareBaselineArgs(BaseModel):
    table_id: str
    label_col: str | None = None
    mode: BackendMode = BackendMode.mock
    baseline: Literal["sklearn_hist_gbm", "logistic"] = "sklearn_hist_gbm"


class CompareBaselineResult(BaseModel):
    tabpfn_metrics: dict[str, float]
    baseline_metrics: dict[str, float]
    delta: dict[str, float]
    narrative: str


class SuggestActionsArgs(BaseModel):
    table_id: str
    proba_col: str = "proba_1"
    threshold_high: float | None = None
    threshold_mid: float | None = None
    max_rows: int = Field(50, ge=1, le=500)


class ActionItem(BaseModel):
    row_id: str
    action: str
    proba: float
    reason: str


class SuggestActionsResult(BaseModel):
    items: list[ActionItem]
    counts: dict[str, int]
    disclaimer: str = "Synthetic demo only."


TOOL_SPECS: list[dict[str, Any]] = [
    {"name": "load_table", "args": LoadTableArgs, "result": LoadTableResult},
    {"name": "profile", "args": ProfileArgs, "result": ProfileResult},
    {"name": "fit_predict", "args": FitPredictArgs, "result": FitPredictResult},
    {"name": "explain", "args": ExplainArgs, "result": ExplainResult},
    {"name": "export_report", "args": ExportReportArgs, "result": ExportReportResult},
    {
        "name": "compare_baseline",
        "args": CompareBaselineArgs,
        "result": CompareBaselineResult,
    },
    {
        "name": "suggest_actions",
        "args": SuggestActionsArgs,
        "result": SuggestActionsResult,
    },
]
