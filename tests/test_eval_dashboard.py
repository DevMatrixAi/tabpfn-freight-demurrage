"""Eval dashboard: auth gate, home link, multi-mode vs HistGBM (mock OK)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import DEFAULT_PACK, app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.eval_dashboard import EVAL_MODES, METRIC_KEYS, run_multi_mode_eval


def _authed() -> TestClient:
    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE, "1")
    return c


def test_eval_requires_auth():
    c = TestClient(app)
    r = c.get("/eval", follow_redirects=False)
    assert r.status_code in (303, 307)
    assert "/login" in r.headers.get("location", "")


def test_home_links_eval():
    c = _authed()
    home = c.get("/")
    assert home.status_code == 200
    assert b'href="/eval"' in home.content
    assert b"HistGBM" in home.content or b"hist_gbm" in home.content


def test_eval_page_renders():
    c = _authed()
    r = c.get("/eval")
    assert r.status_code == 200
    body = r.text
    assert "HistGBM" in body or "hist_gbm" in body
    assert "Run eval" in body
    assert "plus" in body and "thinking" in body and "fast" in body


def test_eval_run_mock_table_and_bars():
    c = _authed()
    r = c.post("/eval/run", data={"pack": DEFAULT_PACK}, follow_redirects=False)
    assert r.status_code in (303, 307)
    assert "/eval" in r.headers.get("location", "")
    page = c.get("/eval")
    assert page.status_code == 200
    body = page.text
    assert 'id="eval-table"' in body
    assert 'id="eval-bars"' in body
    for mode in EVAL_MODES:
        assert mode in body
    assert "hist_gbm" in body
    for key in ("Accuracy", "F1", "ROC-AUC", "AP"):
        assert key in body
    assert "Δ" in body


def test_run_multi_mode_eval_unit(monkeypatch):
    from apps.desk.app import PACKS, _metric_slice, _resolve_mode, _session
    import pandas as pd

    sess = _session(DEFAULT_PACK)
    df = pd.read_csv(PACKS[DEFAULT_PACK]["csv"]).head(36)
    sess.load_table(csv_text=df.to_csv(index=False), table_id="eval_unit")

    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    result = run_multi_mode_eval(
        sess, "eval_unit", resolve_mode=_resolve_mode, metric_slice=_metric_slice
    )
    assert result["n_rows"] == 36
    assert len(result["display_rows"]) == 4  # 3 modes + hist_gbm
    modes = [r["mode"] for r in result["display_rows"]]
    assert modes[:3] == list(EVAL_MODES)
    assert modes[-1] == "hist_gbm"
    for row in result["display_rows"]:
        for k in METRIC_KEYS:
            assert k in row["metrics"]
            assert k in row["bars"]
        assert "delta" in row
