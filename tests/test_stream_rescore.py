"""Streaming fixture ingest + desk re-score (partial refresh)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.stream_rescore import append_stream_events, _stream_pool
from tabpfn_hack_core.adapters.registry import get_adapter


def test_fixtures_are_richer():
    for name in ('edi_315', 'project44', 'terminal49'):
        events = get_adapter(name).fetch_events()
        assert len(events) >= 5, name
        notes = " ".join(str(e.get("terminal_note") or "") for e in events)
        assert len(notes) > 80, name


def test_stream_pool_nonempty():
    pool = _stream_pool()
    assert len(pool) >= 15


def test_desk_shows_stream_control():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        page = c.get("/desk")
        assert page.status_code == 200
        assert "btn-stream-rescore" in page.text
        assert "Stream event + re-score" in page.text
        assert "TODO: stream re-score" not in page.text
        assert 'id="live-board"' in page.text


def test_stream_rescore_partial_html():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        r = c.post(
            "/stream-rescore",
            data={"mode": "mock", "count": "1", "partial": "1"},
        )
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert 'id="live-board"' in r.text
        assert "risk-card" in r.text or "Risk board" in r.text


def test_stream_rescore_json_and_grows_rows():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        before = c.post(
            "/stream-rescore",
            data={"mode": "mock", "count": "1", "partial": "json"},
            headers={"Accept": "application/json"},
        ).json()
        after = c.post(
            "/stream-rescore",
            data={"mode": "mock", "count": "2", "partial": "json"},
            headers={"Accept": "application/json"},
        ).json()
        assert before["ok"] and after["ok"]
        assert after["n_rows"] >= before["n_rows"] + 2
        assert after["stream_cursor"] > before["stream_cursor"]
        assert after["n_risk_cards"] >= 1
        assert after["appended"]


def test_append_stream_events_unique_ids():
    from apps.desk.app import _STATE, _money_total, app as desk_app
    from apps.desk.wow import sample_ids

    with TestClient(desk_app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        sess = desk_app.state.session
        a1 = append_stream_events(sess, _STATE, money_total=_money_total, sample_ids=sample_ids, count=2)
        a2 = append_stream_events(sess, _STATE, money_total=_money_total, sample_ids=sample_ids, count=2)
        ids = [x["container_id"] for x in a1 + a2]
        assert len(ids) == len(set(ids))
