"""Polish fold: mode glossary + thinking_effort form + README raw-DF."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mode_glossary_partial_exists():
    text = (ROOT / "apps/desk/templates/partials_mode_glossary.html").read_text()
    assert "Mode glossary" in text
    assert "plus" in text and "thinking" in text and "hist_gbm" in text


def test_eval_includes_mode_glossary():
    text = (ROOT / "apps/desk/templates/eval.html").read_text()
    assert "partials_mode_glossary.html" in text


def test_readme_mentions_raw_dataframe():
    text = (ROOT / "README.md").read_text()
    assert "Raw DataFrame" in text or "raw DataFrame" in text
    assert "load_table" in text


def test_index_has_thinking_effort_select():
    text = (ROOT / "apps/desk/templates/index.html").read_text()
    text += (ROOT / "apps/desk/templates/partials_desk_main.html").read_text()
    assert 'name="thinking_effort"' in text
    assert "effort-chip" in text
