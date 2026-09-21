"""Anti-wrapper page, triage CSV export, /eval reliability chart (mock-only)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import DEFAULT_PACK, app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.anti_wrapper import CHECKLIST_ITEMS, checklist_payload
from apps.desk.export_csv import CSV_COLUMNS, build_triage_csv


def _authed() -> TestClient:
    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE, "1")
    return c


def test_checklist_mirrors_doc():
    payload = checklist_payload()
    assert payload["total"] == 8
    assert payload["target"] == 6
    assert len(CHECKLIST_ITEMS) == 8
    assert CHECKLIST_ITEMS[0]["surface"].startswith("Messy text")
    assert CHECKLIST_ITEMS[7]["href"] == "/docs"
    doc = (ROOT / "docs/ANTI_WRAPPER_CHECKLIST.md").read_text()
    assert "≥6/8" in doc or ">=6/8" in doc or "≥6" in doc


def test_anti_wrapper_page_requires_auth():
    c = TestClient(app)
    r = c.get("/anti-wrapper", follow_redirects=False)
    assert r.status_code in (303, 307)
    assert "/login" in r.headers.get("location", "")


def test_anti_wrapper_page_renders_and_nav():
    c = _authed()
    r = c.get("/anti-wrapper")
    assert r.status_code == 200
    body = r.text
    assert 'id="anti-wrapper-page"' in body or 'data-anti-wrapper="1"' in body
    assert "Anti-wrapper checklist" in body
    assert "Messy text" in body
    assert "HistGBM" in body or "Baseline" in body
    assert 'data-aw-check="1"' in body
    home = c.get("/")
    assert home.status_code == 200
    assert b'href="/anti-wrapper"' in home.content
    desk = c.get("/desk")
    assert desk.status_code == 200
    assert b'href="/anti-wrapper"' in desk.content or b"anti-wrapper" in desk.content


def test_export_csv_empty_headers():
    text = build_triage_csv({})
    header = text.strip().splitlines()[0]
    for col in CSV_COLUMNS:
        assert col in header


def test_export_csv_rows_and_route():
    state = {
        "actions": [
            {"row_id": "C1", "proba": 0.91, "action": "divert", "reason": "high risk"},
            {"row_id": "C2", "proba": 0.4, "action": "monitor", "reason": "watch"},
        ],
        "risk_cards": [
            {
                "row_id": "C1",
                "proba": 0.91,
                "action": "divert",
                "action_label": "Divert",
                "reason": "high risk",
                "tier": "red",
                "risk_label": "High",
                "money": 1200.0,
                "expected_usd": 1100.0,
            }
        ],
    }
    text = build_triage_csv(state)
    assert "C1" in text and "divert" in text and "1200" in text
    assert "C2" in text

    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.get("/export-triage.csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "row_id" in r.text
        assert "attachment" in r.headers.get("content-disposition", "").lower()

        desk = c.get("/desk")
        assert desk.status_code == 200
        assert "export-triage" in desk.text
        tr = c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        assert tr.status_code in (303, 307, 200)
        r2 = c.get("/export-triage.csv")
        assert r2.status_code == 200
        lines = [ln for ln in r2.text.strip().splitlines() if ln.strip()]
        assert len(lines) >= 2


def test_reliability_chart_partial_and_eval():
    partial = (ROOT / "apps/desk/templates/partials_reliability_chart.html").read_text()
    assert 'id="eval-reliability-chart"' in partial
    assert "Reliability diagram" in partial
    assert "mean_proba" in partial

    eval_html = (ROOT / "apps/desk/templates/eval.html").read_text()
    assert "partials_reliability_chart.html" in eval_html

    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.post("/eval/run", data={"pack": DEFAULT_PACK}, follow_redirects=False)
        assert r.status_code in (303, 307)
        page = c.get("/eval")
        assert page.status_code == 200
        body = page.text
        assert "eval-calibration" in body or "eval-reliability-chart" in body or "Uncertainty" in body
        if "calibration" in body.lower():
            assert "eval-reliability-chart" in body or "Reliability" in body
