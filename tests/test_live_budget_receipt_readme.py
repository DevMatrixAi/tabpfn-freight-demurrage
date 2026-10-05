"""Live-budget chip · judge-path mock receipt · README/JUDGE tip pins."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.dev_sample import DEFAULT_DEV_N, live_budget_chip, resolve_sample_n


def _client() -> TestClient:
    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE, "1")
    return c


def test_default_dev_n_is_60(monkeypatch):
    monkeypatch.delenv("TABPFN_DEV_N", raising=False)
    assert DEFAULT_DEV_N == 60
    assert resolve_sample_n(None) == 60


def test_live_budget_chip_markers_in_desk_and_settings(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    c = _client()
    desk = c.get("/desk")
    assert desk.status_code == 200
    assert 'data-live-budget-chip' in desk.text
    assert "Mock" in desk.text and "no live spend" in desk.text
    assert "n=60" in desk.text or "60 (default live)" in desk.text

    settings = c.get("/settings")
    assert settings.status_code == 200
    assert 'data-live-budget-chip' in settings.text
    assert "Live budget" in settings.text or "no live spend" in settings.text

    home = c.get("/")
    assert home.status_code == 200
    assert 'data-live-budget-chip' in home.text


def test_chip_helper_planned_n():
    chip = live_budget_chip(sample_n=60, has_token=False)
    assert chip["sample_n"] == 60
    assert "planned n=60" in chip["label"] or chip["sample_n"] == 60
    live = live_budget_chip(sample_n=60, has_token=True)
    assert live["mode"] == "live"
    assert "est" in live["label"].lower()
    assert "~$" in live["label"] or "est" in live["label"]


def test_judge_path_receipt_artifacts(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    env = {**os.environ, "TABPFN_TOKEN": ""}
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "freeze_judge_path_receipt.py")],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    jp = ROOT / "artifacts" / "freight-demurrage" / "judge_path_mock_receipt.json"
    mp = ROOT / "artifacts" / "freight-demurrage" / "judge_path_mock_receipt.md"
    assert jp.is_file()
    assert mp.is_file()
    data = json.loads(jp.read_text())
    assert data.get("frozen") is True
    assert data.get("mock") is True
    assert data.get("has_token") is False
    assert "delta_vs_hist_gbm" in data
    assert data.get("money_at_risk_usd", 0) > 0
    assert data.get("actions_count", 0) > 0
    md = mp.read_text()
    assert "Judge path mock receipt" in md
    assert "HistGBM" in md
    assert "Money at risk" in md
    assert "Actions" in md


def test_readme_and_judge_tip_pins():
    readme = (ROOT / "README.md").read_text()
    assert "TIP_SHA_PIN_START" in readme
    assert "TIP_SHA_PIN_END" in readme
    assert "docs/images/judge/login.svg" in readme
    assert "docs/images/judge/home.svg" in readme
    assert "docs/images/judge/desk.svg" in readme
    assert "docs/images/judge/eval.svg" in readme
    assert "Judged version:" in readme
    head = readme.split("FREIGHT_FACE_START")[0]
    assert "images/judge/login.svg" in head

    judge = (ROOT / "docs" / "JUDGE_3MIN.md").read_text()
    assert "TIP_SHA_PIN_START" in judge
    assert "images/judge/login.svg" in judge
    assert "images/judge/eval.svg" in judge
    assert "judge_path_mock_receipt" in judge
    head_j = judge.split("# Judge path")[0]
    assert "TIP_SHA_PIN_START" in head_j
    assert "images/judge/desk.svg" in head_j


def test_desk_select_default_60_marker():
    html = (ROOT / "apps" / "desk" / "templates" / "partials_desk_main.html").read_text()
    assert "60 (default live)" in html
    assert "data-live-budget-chip" in html or "live-budget" in html
