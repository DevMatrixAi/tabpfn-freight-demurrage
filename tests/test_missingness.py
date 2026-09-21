"""Missingness panel helper (stress fixture / messy tables)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from apps.desk.missingness import missingness_summary

ROOT = Path(__file__).resolve().parents[1]


def test_missingness_none_when_complete():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    assert missingness_summary(df) is None


def test_missingness_reports_top_cols():
    df = pd.DataFrame({"a": [1, None, 3], "b": [None, None, 1], "c": [1, 2, 3]})
    summary = missingness_summary(df, top_n=2)
    assert summary is not None
    assert summary["n_cols_with_missing"] == 2
    assert summary["top"][0]["col"] == "b"
    assert summary["top"][0]["pct"] == 66.7


def test_stress_fixture_has_missingness():
    path = ROOT / "fixtures" / "stress" / "missing_wide_demurrage.csv"
    if not path.exists():
        import runpy

        runpy.run_path(str(ROOT / "fixtures" / "stress" / "_unpack_missing_wide.py"))
    df = pd.read_csv(path)
    summary = missingness_summary(df)
    assert summary is not None
    assert summary["n_cols_with_missing"] >= 3
    assert summary["overall_pct"] > 0
