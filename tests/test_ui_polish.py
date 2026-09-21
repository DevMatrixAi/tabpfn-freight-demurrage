"""UI polish: chart_stats, thinking timeline, desk after triage."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.risk_board import build_thinking_timeline, chart_stats


def test_chart_stats_tiers():
    cards = [
        {"tier": "red", "money": 1000},
        {"tier": "red", "money": 500},
        {"tier": "amber", "money": 200},
        {"tier": "green", "money": 0},
    ]
    s = chart_stats(cards, demurrage_total=9999)
    assert s["counts"]["high"] == 2
    assert s["counts"]["med"] == 1
    assert s["counts"]["low"] == 1
    assert s["money"]["high"] == 1500.0
    assert s["money_max"] == 1500.0
    assert s["money_total"] == 9999.0


def test_thinking_timeline_orders_by_group_time():
    rows = [
        {"vessel_id": "VSL-B", "event_ts": "2026-07-02T10:00:00Z", "container_id": "C2", "pod": "DEHAM"},
        {"vessel_id": "VSL-A", "event_ts": "2026-07-01T03:00:00Z", "container_id": "C1", "pod": "NLRTM", "projected_demurrage_usd": 100},
        {"vessel_id": "VSL-A", "event_ts": "2026-07-01T06:00:00Z", "container_id": "C3", "pod": "NLRTM"},
    ]
    ev = build_thinking_timeline(rows, group_col="vessel_id", time_col="event_ts", id_col="container_id")
    assert [e["row_id"] for e in ev] == ["C1", "C3", "C2"]
    assert ev[0]["group"] == "VSL-A"
    assert ev[0]["money"] == 100.0


def test_desk_charts_and_drawer_after_triage():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        assert r.status_code in (303, 307)
        page = c.get("/desk")
        assert page.status_code == 200
        body = page.text
        assert 'id="ops-charts"' in body
        assert "Late fee risk mix" in body
        assert 'id="action-drawer"' in body
        assert "openActionDrawer" in body
        assert "clickable" in body


def test_desk_thinking_timeline_when_thinking_mode():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.post("/run-triage", data={"mode": "thinking"}, follow_redirects=False)
        assert r.status_code in (303, 307)
        page = c.get("/desk")
        assert page.status_code == 200
        body = page.text
        # Without token, mode falls back to mock but requested_mode stays thinking → strip still shows
        assert 'id="thinking-timeline"' in body
        assert "Thinking timeline" in body
