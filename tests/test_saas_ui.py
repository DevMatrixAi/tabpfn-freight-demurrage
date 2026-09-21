"""SaaS shell chrome (login/home) — mock-only visual density."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_saas_shell_css_exists():
    css = (ROOT / "apps/desk/static/saas_shell.css").read_text()
    assert "app-nav" in css and "login-card" in css


def test_login_uses_saas_shell():
    text = (ROOT / "apps/desk/templates/login.html").read_text()
    assert "saas_shell.css" in text
    assert "Sign in to your desks" in text


def test_home_has_primary_nav():
    text = (ROOT / "apps/desk/templates/home_saas.html").read_text()
    assert "app-nav" in text
    assert 'href="/eval"' in text


def test_desk_nav_includes_saas_shell():
    text = (ROOT / "apps/desk/templates/index.html").read_text()
    assert "saas_shell.css" in text
    assert "app-nav" in text
