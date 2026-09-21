"""Column-type chips, keyboard shortcuts, frozen mock /eval judge-card artifact."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["TABPFN_TOKEN"] = ""

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE
from apps.desk.column_chips import CHIP_KINDS, column_chips_payload
from tabpfn_hack_core.domain import load_domain


def test_column_chips_from_domain_schema():
    domain = load_domain(ROOT / "domains" / "freight-demurrage" / "domain.yaml")
    payload = column_chips_payload(domain)
    assert payload["markers"]["text"] is True
    assert payload["markers"]["high_card"] is True
    assert payload["markers"]["group_time"] is True
    kinds = {c["kind"] for c in payload["chips"]}
    assert "text" in kinds and "high_card" in kinds and "group_time" in kinds
    cols = {c["col"] for c in payload["chips"]}
    assert "terminal_note" in cols or "weather_alert" in cols
    assert "bol_id" in cols or "container_id" in cols
    assert "vessel_id" in cols and "event_ts" in cols
    assert all(k in CHIP_KINDS for k in kinds)


def test_column_chips_missing_from_dataframe():
    domain = load_domain(ROOT / "domains" / "freight-demurrage" / "domain.yaml")
    df = pd.DataFrame(
        {
            "terminal_note": ["ok", None],
            "bol_id": ["B1", "B2"],
            "vessel_id": ["V1", "V1"],
            "event_ts": ["2024-01-01", "2024-01-02"],
            "dwell_days": [1.0, None],
        }
    )
    payload = column_chips_payload(domain, df)
    assert payload["markers"]["missing"] is True
    miss_cols = {c["col"] for c in payload["chips"] if c["kind"] == "missing"}
    assert "terminal_note" in miss_cols or "dwell_days" in miss_cols


def test_desk_renders_column_chips_markers():
    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        page = c.get("/desk")
        assert page.status_code == 200
        body = page.text
        assert 'id="column-chips-panel"' in body or 'data-column-chips="1"' in body
        assert "data-chip-kind" in body
        assert "high-card" in body or "high_card" in body
        assert "group\u00d7time" in body or "group_time" in body or "group\u00d7time" in body
        assert "text" in body.lower()


def test_keyboard_shortcuts_cheatsheet_and_handlers():
    js = (ROOT / "apps/desk/static/desk_keys.js").read_text()
    assert "desk-keys-cheatsheet" in js or "data-desk-keys-cheatsheet" in js
    assert 'key: "t"' in js or 'e.key === "t"' in js
    assert 'e.key === "e"' in js or 'key: "e"' in js
    assert 'e.key === "/"' in js or 'key: "/"' in js
    assert 'e.key === "?"' in js or 'key: "?"' in js
    assert "typingTarget" in js or "isContentEditable" in js
    assert "board-filter" in js or "desk-search" in js

    index = (ROOT / "apps/desk/templates/index.html").read_text()
    assert "desk_keys.js" in index
    live = (ROOT / "apps/desk/templates/live_board.html").read_text()
    assert 'id="board-filter"' in live or 'data-desk-filter="1"' in live

    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        page = c.get("/desk")
        assert page.status_code == 200
        assert "desk_keys.js" in page.text
        static = c.get("/static/desk_keys.js")
        assert static.status_code == 200
        assert b"cheatsheet" in static.content.lower() or b"cheat" in static.content.lower()


def test_frozen_mock_eval_judge_card_artifact_exists():
    json_path = ROOT / "artifacts" / "freight-demurrage" / "mock_eval_judge_card.json"
    md_path = ROOT / "artifacts" / "freight-demurrage" / "mock_eval_judge_card.md"
    assert json_path.is_file(), f"missing frozen artifact {json_path}"
    assert md_path.is_file(), f"missing frozen VO crib {md_path}"
    data = json.loads(json_path.read_text())
    assert data.get("frozen") is True
    assert data.get("mock") is True
    assert isinstance(data.get("judge_card"), dict)
    assert data["judge_card"].get("headline")
    assert "latency_panel" in data
    md = md_path.read_text()
    assert "VO" in md or "judge" in md.lower()
    assert "TABPFN_TOKEN" in md
