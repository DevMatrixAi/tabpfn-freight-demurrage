"""Plain-English crib + robot smoke script presence."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_plain_english_partial():
    text = (ROOT / "apps/desk/templates/partials_plain_english.html").read_text()
    assert "Money at risk" in text
    assert "Late fee risk" in text
    assert "Suggested move" in text


def test_index_includes_plain_crib():
    text = (ROOT / "apps/desk/templates/index.html").read_text()
    assert "partials_plain_english.html" in text


def test_robot_api_smoke_script_runs(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "")
    import runpy

    rc = runpy.run_path(str(ROOT / "scripts" / "robot_api_smoke.py"), run_name="not_main")
    # execute main
    assert rc["main"]() == 0
