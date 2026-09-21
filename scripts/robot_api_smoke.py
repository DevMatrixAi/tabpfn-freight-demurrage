#!/usr/bin/env python3
"""Mock-only robot/TMS API smoke (no TABPFN_TOKEN / no live calls).

Usage (repo root):
  TABPFN_TOKEN= python scripts/robot_api_smoke.py

Exits 0 when /api/v1/health + /api/v1/triage (mock) succeed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["TABPFN_TOKEN"] = ""  # force mock
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient


def main() -> int:
    from apps.desk.app import app

    with TestClient(app) as client:
        h = client.get("/api/v1/health")
        if h.status_code != 200:
            print("FAIL health", h.status_code, h.text[:200])
            return 1
        health = h.json()
        print("OK health", json.dumps({k: health.get(k) for k in ("status", "has_token", "packs")}, default=str))

        t = client.post(
            "/api/v1/triage",
            json={"pack": "freight-demurrage", "mode": "mock", "max_rows": 10},
        )
        if t.status_code != 200:
            print("FAIL triage", t.status_code, t.text[:300])
            return 1
        body = t.json()
        print(
            "OK triage",
            json.dumps(
                {
                    "n_rows": body.get("n_rows"),
                    "mode": body.get("mode"),
                    "action_counts": body.get("action_counts"),
                    "has_metrics": bool(body.get("metrics")),
                },
                default=str,
            ),
        )
    print("robot_api_smoke OK (mock)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
