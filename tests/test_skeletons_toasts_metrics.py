"""Skeletons, toasts, eval partial, mock fulltable metrics, preview chips."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_partials_eval_results_present_and_wired():
    partial = ROOT / "apps/desk/templates/partials_eval_results.html"
    eval_html = ROOT / "apps/desk/templates/eval.html"
    assert partial.is_file()
    assert partial.stat().st_size > 8_000
    text = eval_html.read_text()
    assert "partials_eval_results.html" in text
    body = partial.read_text()
    for marker in (
        'id="eval-results"',
        'id="eval-latency"',
        "Thinking",
        'id="eval-ablations"',
        'id="eval-calibration"',
    ):
        assert marker in body


def test_toast_js_css_linked():
    js = (ROOT / "apps/desk/static/desk_toasts.js").read_text()
    css = (ROOT / "apps/desk/static/saas_density.css").read_text()
    assert "function deskToast" in js or "deskToast" in js
    assert "aria-live" in js
    assert ".desk-toasts" in css
    assert ".desk-toast-error" in css
    assert "desk-toast-in" in css
    for rel in (
        "apps/desk/templates/index.html",
        "apps/desk/templates/eval.html",
        "apps/desk/templates/settings.html",
    ):
        text = (ROOT / rel).read_text()
        assert "desk_toasts.js" in text
        assert 'id="desk-toasts"' in text or "desk-toasts" in text


def test_skeleton_markers():
    css = (ROOT / "apps/desk/static/saas_density.css").read_text()
    assert "chart-skeleton" in css
    assert "desk-skeleton" in css
    assert "triage-board" in css
    assert "eval-running" in css
    assert "drawer-apply" in css
    assert "saas-shimmer" in css

    main = (ROOT / "apps/desk/templates/partials_desk_main.html").read_text()
    assert 'data-skeleton="triage-board"' in main

    eval_html = (ROOT / "apps/desk/templates/eval.html").read_text()
    assert 'data-skeleton="eval-running"' in eval_html
    assert 'data-empty="eval-prerun"' in eval_html

    drawer = (ROOT / "apps/desk/templates/polish_drawer.html").read_text()
    assert 'data-skeleton="drawer-apply"' in drawer


def test_mock_fulltable_metrics_artifact_schema():
    path = ROOT / "artifacts/freight-demurrage/mock_fulltable_metrics.json"
    md = ROOT / "artifacts/freight-demurrage/mock_fulltable_metrics.md"
    assert path.is_file()
    assert md.is_file()
    data = json.loads(path.read_text())
    assert data.get("frozen") is True
    assert data.get("mock") is True
    assert data.get("label") == "mock full-table"
    assert data.get("has_token") is False
    assert data.get("n_kind") == "full_fixture"
    assert "accuracy" in data["metric_keys"]
    for mode in ("plus", "thinking", "fast", "hist_gbm"):
        assert mode in data["modes"]
        m = data["modes"][mode]["metrics"]
        for k in data["metric_keys"]:
            assert k in m
            assert isinstance(m[k], (int, float))
    assert "latency_panel" in data
    md_text = md.read_text()
    assert "mock full-table" in md_text.lower()
    assert "4 PM" in md_text or "4 pm" in md_text.lower()
    assert "HistGBM" in md_text or "hist_gbm" in md_text


def test_preview_stub_showcase_chips():
    stub = (ROOT / "preview_stub.py").read_text()
    assert "SHOWCASE_CHIPS" in stub
    assert '"mock"' in stub or "'mock'" in stub
    assert "Plus / Thinking / Fast" in stub
    assert "chip_flags" in stub
    assert "/settings" in stub
    assert "/api/v1/health" in stub


def test_freeze_script_exists_and_mock_only():
    script = ROOT / "scripts/freeze_mock_fulltable_metrics.py"
    assert script.is_file()
    text = script.read_text()
    assert "TABPFN_TOKEN" in text
    assert "Refusing to run with TABPFN_TOKEN set" in text
