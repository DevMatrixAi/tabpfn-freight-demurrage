"""Contract tests for tools_api pydantic models."""
from __future__ import annotations

from tabpfn_hack_core.tools_api import (
    TOOL_SPECS,
    BackendMode,
    FitPredictArgs,
    FitPredictResult,
    LoadTableArgs,
    SuggestActionsArgs,
)


def test_seven_tools_registered():
    names = [t["name"] for t in TOOL_SPECS]
    assert names == [
        "load_table",
        "profile",
        "fit_predict",
        "explain",
        "export_report",
        "compare_baseline",
        "suggest_actions",
    ]


def test_backend_modes_include_mock():
    assert BackendMode.mock.value == "mock"
    assert {m.value for m in BackendMode} >= {
        "plus",
        "thinking",
        "fast",
        "local",
        "mock",
    }


def test_fit_predict_args_defaults():
    args = FitPredictArgs(table_id="t1")
    assert args.mode == BackendMode.mock
    assert 0 < args.test_size < 1


def test_fit_predict_result_shape():
    r = FitPredictResult(
        mode=BackendMode.mock,
        backend="mock",
        metrics={"accuracy": 0.9},
        n_train=80,
        n_test=20,
    )
    assert r.backend == "mock"
    dumped = r.model_dump()
    assert dumped["metrics"]["accuracy"] == 0.9


def test_load_and_suggest_validate():
    LoadTableArgs(path="data/x.csv")
    SuggestActionsArgs(table_id="t", max_rows=10)
