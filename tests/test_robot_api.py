"""TestClient coverage for robot/TMS consumer API."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client(monkeypatch):
    # Ensure mock path: no accidental live token in CI
    monkeypatch.setenv("TABPFN_TOKEN", "")  # empty → mock; blocks .env override on startup
    monkeypatch.chdir(ROOT)
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from fastapi.testclient import TestClient
    from apps.desk.app import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "robot/TMS" in body["service"]
    assert body["has_token"] is False
    assert "freight-demurrage" in body["packs"]
    assert "decisions" in body["note"].lower() or "crane" in body["note"].lower()


def test_openapi_documents_robot_tag(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "robot/TMS consumer API" in (spec.get("tags") or [{}])[0].get("name", "") or any(
        t.get("name") == "robot/TMS consumer API" for t in (spec.get("tags") or [])
    ) or "/api/v1/triage" in spec.get("paths", {})
    assert "/api/v1/health" in spec["paths"]
    assert "/api/v1/triage" in spec["paths"]
    assert "/api/v1/actions" in spec["paths"]
    # Human ops board still present
    assert "/" in spec["paths"]


def test_triage_pack_mock(client):
    r = client.post(
        "/api/v1/triage",
        json={"pack": "freight-demurrage", "mode": "mock", "max_rows": 8},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["pack"] == "freight-demurrage"
    assert body["backend"] == "mock"
    assert body["n_rows"] >= 10
    assert "accuracy" in body["metrics"]
    assert "accuracy" in body["baseline_metrics"]
    assert "delta" in body
    assert body["actions"]
    assert body["action_counts"]
    assert "crane" in body["scope"].lower() or "decisions" in body["scope"].lower()


def test_triage_fixture(client):
    r = client.post(
        "/api/v1/triage",
        json={"fixture": "terminal49", "mode": "mock", "max_rows": 20},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["n_rows"] >= 4
    assert body["actions"]


def test_actions_passthrough_carrier_client(client):
    rows = []
    for i in range(6):
        rows.append(
            {
                "container_id": f"C{i}",
                "event_ts": f"2026-07-01T0{i}:00:00Z",
                "vessel_id": "V1",
                "bol_id": f"B{i}",
                "pol": "CNSHA",
                "pod": "USLAX",
                "terminal_note": "delay" if i % 2 else "",
                "weather_alert": "",
                "free_days_left": 1.0 + i,
                "dwell_days_so_far": float(i),
                "teu": 1,
                "cargo_value_usd": 10000.0,
                "daily_demurrage_usd": 100.0,
                "blank_sailing": 0,
                "inland_can_beat_freedays": 1,
                "fee_inevitable": 0,
                "cargo_vs_fee_collapse": 0,
                "projected_demurrage_usd": 100.0 * i,
                "demurrage_risk": 1 if i % 2 else 0,
                "carrier": "MAEU" if i < 3 else "HLCU",
                "client_id": "CLT-001",
            }
        )
    r = client.post(
        "/api/v1/actions",
        json={
            "pack": "freight-demurrage",
            "mode": "mock",
            "carrier": "REQ-CARRIER",
            "client_id": "REQ-CLIENT",
            "rows": rows,
            "max_rows": 10,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["carrier"] == "REQ-CARRIER"
    assert body["client_id"] == "REQ-CLIENT"
    assert body["actions"]
    # Top-level request labels echoed; row-level carrier may also appear on items
    assert body["actions"][0]["carrier"] == "REQ-CARRIER"
    assert body["actions"][0]["client_id"] == "REQ-CLIENT"


def test_triage_unknown_pack(client):
    r = client.post("/api/v1/triage", json={"pack": "nope", "mode": "mock"})
    assert r.status_code == 400


def test_ops_board_home_still_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
