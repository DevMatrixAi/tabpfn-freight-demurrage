"""A refused live TabPFN call shows a clear error instead of quietly using mock numbers.

No network: the tabpfn_client constructor is patched to raise a fake HTTP 429.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tabpfn_hack_core.core.backend import TabPFNLiveError, fit_predict_backend

CSV = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"


@pytest.fixture
def refused(monkeypatch):
    import tabpfn_client

    def _boom(*_a, **_k):
        raise RuntimeError("Fail to call fit: [HTTP 429] Daily usage limit reached. Your daily limit is 5000000 tokens.")

    monkeypatch.setenv("TABPFN_TOKEN", "fake-token-for-test")
    monkeypatch.setenv("DESK_REPLAY", "0")
    monkeypatch.delenv("TABPFN_ALLOW_MOCK_FALLBACK", raising=False)
    monkeypatch.setattr(tabpfn_client.TabPFNClassifier, "create_default_for_version", _boom)


def _xy():
    X = pd.DataFrame({"a": np.arange(20.0), "b": np.arange(20.0) % 3})
    y = np.array([0, 1] * 10)
    return X.iloc[:14], y[:14], X.iloc[14:], y[14:]


@pytest.mark.parametrize("mode", ["plus", "thinking", "fast"])
def test_backend_raises_clear_429(refused, mode):
    Xtr, ytr, Xte, yte = _xy()
    with pytest.raises(TabPFNLiveError) as ei:
        fit_predict_backend(mode, Xtr, ytr, Xte, yte)
    assert ei.value.status == 429
    msg = str(ei.value)
    assert "daily usage limit" in msg and "no offline numbers" in msg


def test_opt_in_fallback_still_available(refused, monkeypatch):
    monkeypatch.setenv("TABPFN_ALLOW_MOCK_FALLBACK", "1")
    Xtr, ytr, Xte, yte = _xy()
    with pytest.warns(UserWarning):
        r = fit_predict_backend("plus", Xtr, ytr, Xte, yte)
    assert r.backend == "mock" and r.warning


def test_robot_api_returns_429(refused):
    from fastapi.testclient import TestClient
    from apps.desk.app import app

    rows = pd.read_csv(CSV).head(40).fillna("").to_dict(orient="records")
    with TestClient(app) as c:
        r = c.post("/api/v1/actions", json={"rows": rows, "mode": "plus", "max_rows": 5})
    assert r.status_code == 429
    body = r.json()
    assert body["error"] == "tabpfn_live_failed"
    assert "daily usage limit" in body["detail"]


def test_desk_shows_banner_and_keeps_previous_results(refused):
    from fastapi.testclient import TestClient
    from apps.desk import app_impl
    from apps.desk.app import app
    from apps.desk.auth import SESSION_COOKIE

    with TestClient(app) as c:
        r = c.post("/login", data={"username": "demo", "password": "demurrage"}, follow_redirects=False)
        c.cookies.set(SESSION_COOKIE, r.cookies.get(SESSION_COOKIE) or "1")
        before = dict(app_impl._STATE)
        try:
            r = c.post("/run-triage", data={"mode": "plus", "sample_n": "40"}, follow_redirects=False)
            assert r.status_code == 303
            assert "daily usage limit" in (app_impl._STATE.get("live_error") or "")
            assert app_impl._STATE.get("n_rows") == before.get("n_rows")
            assert app_impl._STATE.get("metrics") == before.get("metrics")
            page = c.get("/desk").text
            assert "Live TabPFN call failed." in page
            assert "previous results" in page
        finally:
            app_impl._STATE["live_error"] = None
