"""Settings stub + preview_stub chips + JUDGE_3MIN screenshot links (mock-only)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE


def _client() -> TestClient:
    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE, "1")
    return c


def test_settings_route_mock():
    c = _client()
    r = c.get("/settings")
    assert r.status_code == 200
    body = r.text
    assert "Settings" in body
    assert "Auth stub" in body or "auth stub" in body.lower() or "Demo auth" in body
    assert "Mock" in body
    assert "sample_n" in body
    assert "Thinking effort" in body or "thinking_effort" in body
    assert 'id="settings-page"' in body or 'data-settings="1"' in body
    assert "/eval" in body and "/anti-wrapper" in body


def test_settings_post_demo_prefs_cookie():
    c = _client()
    r = c.post(
        "/settings",
        data={"sample_n": "60", "thinking_effort": "high"},
        follow_redirects=False,
    )
    assert r.status_code in (303, 307)
    assert "desk_sample_n" in r.cookies or r.headers.get("set-cookie", "")
    c.cookies.update(r.cookies)
    page = c.get("/settings")
    assert page.status_code == 200
    assert "60" in page.text
    assert "high" in page.text


def test_nav_includes_settings():
    for rel in (
        "apps/desk/templates/home_saas.html",
        "apps/desk/templates/index.html",
        "apps/desk/templates/eval.html",
    ):
        text = (ROOT / rel).read_text()
        assert 'href="/settings"' in text
        assert "Settings" in text


def test_settings_module_and_css():
    assert (ROOT / "apps/desk/settings_stub.py").is_file()
    assert (ROOT / "apps/desk/templates/settings.html").is_file()
    css = (ROOT / "apps/desk/static/settings_stub.css").read_text()
    assert "settings-mode-badge" in css


def test_preview_stub_chips():
    from preview_stub import SHOWCASE_CHIPS, app as stub_app

    labels = {c["label"] for c in SHOWCASE_CHIPS}
    assert "Mock" in labels
    assert any("Plus" in L or "Thinking" in L for L in labels)
    assert "HistGBM Δ" in labels
    assert "text" in labels and "high-card" in labels
    assert "missing" in labels
    assert any("group" in L for L in labels)
    assert "Robot API" in labels

    c = TestClient(stub_app)
    health = c.get("/api/v1/health")
    assert health.status_code == 200
    data = health.json()
    assert data.get("ok") is True
    assert "chips" in data
    assert data.get("chip_flags", {}).get("mock") is True
    ids = {x["id"] for x in data["chips"]}
    for need in ("mock", "histgbm", "text", "high_card", "missing", "group_time", "robot"):
        assert need in ids

    login = c.post("/login", data={"username": "demo", "password": "demurrage"}, follow_redirects=False)
    assert login.status_code in (303, 307)
    c.cookies.update(login.cookies)
    board = c.get("/board")
    assert board.status_code == 200
    assert "chip-row" in board.text
    assert "HistGBM" in board.text or "HistGBM Δ" in board.text

    settings = c.get("/settings")
    assert settings.status_code == 200
    assert "full settings" in settings.text.lower() or "local desk" in settings.text.lower()


def test_judge_screenshots_exist_and_linked():
    img_dir = ROOT / "docs/images/judge"
    for name in ("login", "home", "desk", "eval"):
        # Prefer PNG; SVG mock frames also OK for JUDGE_3MIN first screens
        png = img_dir / f"{name}.png"
        svg = img_dir / f"{name}.svg"
        assert png.is_file() or svg.is_file(), name
        hit = png if png.is_file() else svg
        assert hit.stat().st_size < 300_000
        assert hit.stat().st_size > 200

    for doc in (
        ROOT / "docs/JUDGE_3MIN.md",
        ROOT / "docs/JUDGE_3MIN_RUNBOOK.md",
        ROOT / "README.md",
    ):
        text = doc.read_text()
        assert "images/judge/login." in text or "docs/images/judge/login." in text
        assert "desk." in text and "eval." in text


def test_empty_state_ctas():
    login = (ROOT / "apps/desk/templates/login.html").read_text()
    assert 'data-empty="login-error"' in login

    eval_t = (ROOT / "apps/desk/templates/eval.html").read_text()
    assert 'data-empty="eval-prerun"' in eval_t
    assert "empty-cta" in eval_t

    drawer = (ROOT / "apps/desk/templates/polish_drawer.html").read_text()
    assert "empty-cta" in drawer
    assert "Load freight fixture" in drawer or "Run triage" in drawer

    home = (ROOT / "apps/desk/templates/home_saas.html").read_text()
    assert "Load freight fixture" in home or "empty-cta" in home
