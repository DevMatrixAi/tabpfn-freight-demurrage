"""Small-n TABPFN_DEV_N / sample_frame budget helper."""
from __future__ import annotations

import pandas as pd

from apps.desk.dev_sample import (
    DEFAULT_DEV_N,
    estimate_live_cost_usd,
    live_budget_chip,
    resolve_sample_n,
    sample_frame,
)


def test_resolve_sample_n_env(monkeypatch):
    monkeypatch.setenv("TABPFN_DEV_N", "60")
    assert resolve_sample_n(None) == 60
    assert resolve_sample_n("80") == 80  # form wins
    assert resolve_sample_n("0") is None
    assert resolve_sample_n("") is None  # explicit full overrides env


def test_resolve_sample_n_default_60_when_unset(monkeypatch):
    monkeypatch.delenv("TABPFN_DEV_N", raising=False)
    assert DEFAULT_DEV_N == 60
    assert resolve_sample_n(None) == 60


def test_sample_frame_cuts_rows():
    df = pd.DataFrame({"y": [0, 1] * 50, "x": range(100)})
    out, meta = sample_frame(df, 40, label_col="y")
    assert meta is not None and meta["sampled"] is True
    assert len(out) == 40
    assert meta["full_n"] == 100


def test_sample_frame_noop_when_small():
    df = pd.DataFrame({"y": [0, 1, 0], "x": [1, 2, 3]})
    out, meta = sample_frame(df, 40, label_col="y")
    assert len(out) == 3
    assert meta is not None and meta["sampled"] is False


def test_estimate_and_chip_mock(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    monkeypatch.delenv("TABPFN_DEV_N", raising=False)
    assert estimate_live_cost_usd(60) == 0.18
    chip = live_budget_chip()
    assert chip["sample_n"] == 60
    assert chip["mode"] == "mock"
    assert "Mock" in chip["label"]
    assert "no live spend" in chip["label"]
    assert chip["marker"] == "data-live-budget-chip"
