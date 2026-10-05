"""Coach strip, Judge path (mock), morning digest markers — empty TABPFN_TOKEN."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["TABPFN_TOKEN"] = ""

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.coach_strip import (
    COACH_BEATS,
    COACH_CRIBS,
    active_beat_for_path,
    coach_beats,
    coach_crib,
    judge_path_payload,
)
from apps.desk.morning_digest import build_morning_digest


def test_coach_beats_and_cribs_match_pitch():
    beats = coach_beats()
    assert [b["id"] for b in beats] == ["login", "ticker", "triage", "drawer", "stream", "eval"]
    assert len(COACH_BEATS) == 6
    assert "shipper" in coach_crib("login").lower() or "late fees" in coach_crib("login").lower()
    assert "HistGBM" in coach_crib("compare-eval") or "HistGBM" in COACH_CRIBS["compare-eval"]
    assert "money move" in coach_crib("risk-drawer").lower()
    assert active_beat_for_path("/login") == "login"
    assert active_beat_for_path("/eval") == "eval"
    assert active_beat_for_path("/desk", has_triage=True) == "drawer"


def test_morning_digest_top_n_and_counts():
    cards = [
        {"row_id": "A", "action": "divert", "money": 9000, "proba": 0.9, "tier": "red"},
        {"row_id": "B", "action": "rebook", "money": 1000, "proba": 0.5, "tier": "amber"},
        {"row_id": "C", "action": "monitor", "money": 5000, "proba": 0.3, "tier": "green"},
    ]
    dig = build_morning_digest(cards, {"divert": 2, "rebook": 1}, money_at_risk=15000.0, top_n=2)
    assert dig is not None
    assert dig["top_n"] == 2
    assert dig["top_moves"][0]["row_id"] == "A"
    assert dig["money_at_risk"] == 15000.0
    assert dig["action_counts"][0]["action"] == "divert"
    assert build_morning_digest([], None) is None


def test_judge_path_payload_frozen():
    p = judge_path_payload(triage_ok=True, money_at_risk=1234.5, n_cards=3)
    assert p["frozen"] is True
    assert p["mock"] is True
    assert p["n_cards"] == 3
    assert len(p["beats"]) >= 5


def test_templates_have_coach_and_digest_markers():
    index = (ROOT / "apps/desk/templates/index.html").read_text()
    assert "partials_coach_strip.html" in index
    assert 'id="judge-path-btn"' in index or 'data-judge-path="1"' in index
    main = (ROOT / "apps/desk/templates/partials_desk_main.html").read_text()
    assert "partials_morning_digest.html" in main
    assert 'data-coach="run-triage"' in main
    assert 'data-coach="histgbm-delta"' in main
    strip = (ROOT / "apps/desk/templates/partials_coach_strip.html").read_text()
    assert 'id="coach-strip"' in strip
    assert 'data-coach-strip="1"' in strip
    assert "Login" in strip and "/eval" in strip
    digest = (ROOT / "apps/desk/templates/partials_morning_digest.html").read_text()
    assert 'id="morning-digest"' in digest
    assert "data-morning-digest" in digest
    login = (ROOT / "apps/desk/templates/login.html").read_text()
    assert 'data-coach="login"' in login
    assert "coach-strip" in login or "partials_coach_strip" in login
    css = (ROOT / "apps/desk/static/ops_board.css").read_text()
    css += (ROOT / "apps/desk/static/coach_strip.css").read_text()
    assert ".coach-strip" in css
    assert ".morning-digest" in css
    assert ".judge-path-btn" in css


def test_desk_coach_strip_and_digest_after_triage():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        assert r.status_code in (303, 307)
        page = c.get("/desk")
        assert page.status_code == 200
        body = page.text
        assert 'id="coach-strip"' in body
        assert 'data-coach-strip="1"' in body
        assert 'id="judge-path-btn"' in body or 'data-judge-path="1"' in body
        assert 'id="morning-digest"' in body
        assert "data-morning-digest" in body
        assert "at risk" in body.lower()
        assert 'data-coach="run-triage"' in body
        assert 'data-coach="risk-drawer"' in body or 'data-coach-hint="risk-drawer"' in body


def test_judge_path_route_mock_to_eval():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.post("/judge-path", follow_redirects=False)
        assert r.status_code in (303, 307)
        loc = r.headers.get("location") or ""
        assert "/eval" in loc
        page = c.get("/eval?judge=1")
        assert page.status_code == 200
        body = page.text
        assert 'id="judge-path-banner"' in body or "data-judge-path-banner" in body
        assert "Judge path" in body
        assert "frozen" in body.lower() or "mock" in body.lower()
        assert 'id="coach-strip"' in body
