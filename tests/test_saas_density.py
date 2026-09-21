"""SaaS density wave: empty states, drawer foot, mobile + chart markers."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_saas_shell_has_empty_and_mobile():
    css = (ROOT / "apps/desk/static/saas_density.css").read_text()
    shell = (ROOT / "apps/desk/static/saas_shell.css").read_text()
    assert "app-nav" in shell
    assert ".saas-empty" in css
    assert "data-empty" not in css  # attribute lives in HTML; class is enough
    assert ".drawer-foot" in css
    assert "@media (max-width:768px)" in css
    assert "@media (max-width:420px)" in css
    assert "chart-skeleton" in css
    assert "saas-shimmer" in css
    assert "zero-risk" in css
    assert "no-selection" in css


def test_drawer_has_sticky_foot_and_empty_markers():
    text = (ROOT / "apps/desk/templates/polish_drawer.html").read_text()
    assert 'id="drawer-foot"' in text
    assert "drawer-foot" in text
    assert 'data-empty="no-selection"' in text
    assert "Suggested move" in text
    assert "Late fee risk" in text
    assert "money at risk" in text.lower() or "Money at risk" in text


def test_charts_pre_triage_empty_state():
    text = (ROOT / "apps/desk/templates/polish_charts.html").read_text()
    assert 'data-empty="charts"' in text
    assert 'data-chart-state="pre-triage"' in text
    assert "chart-skeleton" in text
    assert 'data-empty="zero-risk"' in text


def test_live_board_empty_cta():
    text = (ROOT / "apps/desk/templates/live_board.html").read_text()
    assert 'data-empty="risk-board"' in text
    assert 'href="#triage-panel"' in text
    assert "empty-cta" in text


def test_home_empty_desks_marker():
    text = (ROOT / "apps/desk/templates/home_saas.html").read_text()
    assert 'data-empty="home-desks"' in text


def test_index_triage_panel_and_snapshot_empty():
    text = (ROOT / "apps/desk/templates/index.html").read_text()
    assert 'id="triage-panel"' in text
    assert 'data-empty="board-snapshot"' in text
    assert 'data-empty="what-if-noselect"' in text


def test_templates_link_saas_density():
    for rel in (
        "apps/desk/templates/login.html",
        "apps/desk/templates/home_saas.html",
        "apps/desk/templates/index.html",
    ):
        text = (ROOT / rel).read_text()
        assert "saas_density.css" in text
