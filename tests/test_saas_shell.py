"""SaaS shell: demo auth, home, desk gate."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from apps.desk.app import app
from apps.desk.auth import SESSION_COOKIE


def test_login_gate_redirects():
    c = TestClient(app)
    r = c.get("/", follow_redirects=False)
    assert r.status_code in (303, 307)
    assert "/login" in r.headers.get("location", "")


def test_login_and_home():
    c = TestClient(app)
    r = c.post("/login", data={"username": "demo", "password": "demurrage"}, follow_redirects=False)
    assert r.status_code in (303, 307)
    c.cookies.set(SESSION_COOKIE, r.cookies.get(SESSION_COOKIE) or "1")
    home = c.get("/")
    assert home.status_code == 200
    assert b"Freight Money Desk" in home.content


def test_desk_after_login():
    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE, "1")
    r = c.get("/desk")
    assert r.status_code == 200


def test_robot_api_public():
    c = TestClient(app)
    r = c.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
