"""Explain-in-drawer + p90 fee-band on risk cards (mock-only)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.explain_ui import feature_kind, format_explain, human_feature, why_this_move
from apps.desk.risk_board import fee_band


def test_human_feature_and_kinds():
    assert "Terminal" in human_feature("terminal_note__len")
    assert feature_kind("terminal_note__len") == "text"
    assert feature_kind("bol_id__hash") == "high_card"
    assert feature_kind("free_days_left") == "money"
    assert feature_kind("blank_sailing") == "missing_derived"


def test_format_explain_bars():
    raw = {
        "method": "permutation_importance",
        "notes": "mock",
        "importances": [
            {"feature": "terminal_note__len", "importance": 0.08},
            {"feature": "bol_id__hash", "importance": 0.05},
            {"feature": "free_days_left", "importance": 0.03},
        ],
    }
    out = format_explain(raw, text_cols=["terminal_note"], high_card_cols=["bol_id"], action_reason="Divert — burn")
    assert out["n"] == 3
    assert out["bars"][0]["pct"] == 100.0
    assert out["bars"][0]["kind"] == "text"
    assert "Why" not in out["why"] or "Divert" in out["why"] or "Top drivers" in out["why"]
    assert "Divert" in out["why"] or "Top drivers" in out["why"]


def test_why_this_move_plain():
    s = why_this_move(reason="Rebook — blank sailing", top_labels=["Vessel ID", "Free days left"])
    assert "Rebook" in s
    assert "Vessel ID" in s


def test_fee_band_p90_ge_expected():
    band = fee_band(
        expected_usd=1000.0,
        daily_usd=200.0,
        free_days_left=1.0,
        dwell_days=8.0,
        proba=0.8,
    )
    assert band["expected_usd"] == 1000.0
    assert band["p90_usd"] >= band["expected_usd"]


def test_fee_band_zero_safe():
    band = fee_band(expected_usd=None, daily_usd=None, proba=0.2)
    assert band["expected_usd"] == 0.0
    assert band["p90_usd"] >= 0.0


def test_desk_explain_and_fee_band_after_triage():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        r = c.post("/run-triage", data={"mode": "mock"}, follow_redirects=False)
        assert r.status_code in (303, 307)
        page = c.get("/desk")
        assert page.status_code == 200
        body = page.text
        assert 'id="drawer-explain"' in body
        assert "Why this move" in body
        assert 'id="explain-bars"' in body or "explain-bar" in body
        assert "Expected $" in body
        assert "p90 $" in body
        assert 'class="fee-band"' in body
        assert 'data-expected="' in body
        assert 'data-p90="' in body


def test_pitch_docs_present():
    docs = ROOT / "docs"
    for name in (
        "JUDGE_3MIN_RUNBOOK.md",
        "ANTI_WRAPPER_CHECKLIST.md",
        "IN_DESK_COACH_STRIP.md",
    ):
        text = (docs / name).read_text()
        assert len(text) > 200
    assert "Anti-wrapper" in (docs / "ANTI_WRAPPER_CHECKLIST.md").read_text()
    assert "Control" in (docs / "IN_DESK_COACH_STRIP.md").read_text()
    assert "Login" in (docs / "JUDGE_3MIN_RUNBOOK.md").read_text()
