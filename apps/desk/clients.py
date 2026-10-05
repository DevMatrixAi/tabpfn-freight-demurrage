"""Fixture multi-tenant clients for the SaaS shell (demo only)."""
from __future__ import annotations

from typing import Any

# Demo clients — labels only; filter rows when client_id column exists.
CLIENTS: dict[str, dict[str, Any]] = {
    "CLT-ACME": {
        "label": "Acme Imports",
        "gloss": "Consumer goods shipper — late-fee desk",
    },
    "CLT-GLOBEX": {
        "label": "Globex Logistics",
        "gloss": "3PL running multiple carriers",
    },
    "CLT-NORTH": {
        "label": "Northwoods Trading",
        "gloss": "Seasonal reefer + dry mix",
    },
    "ALL": {
        "label": "All clients (demo)",
        "gloss": "All clients",
    },
}

DEFAULT_CLIENT = "ALL"


def list_clients() -> list[dict[str, str]]:
    return [
        {"id": cid, "label": meta["label"], "gloss": meta.get("gloss", "")}
        for cid, meta in CLIENTS.items()
    ]


def client_meta(client_id: str) -> dict[str, Any]:
    return CLIENTS.get(client_id) or CLIENTS[DEFAULT_CLIENT]
