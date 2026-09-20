"""Desk domain pack registry (spine + coda)."""
from __future__ import annotations
from pathlib import Path
from typing import Any

def build_packs(root: Path) -> dict[str, dict[str, Any]]:
    return {
        "freight-demurrage": {
            "label": "Freight demurrage (spine)",
            "domain": root / "domains" / "freight-demurrage" / "domain.yaml",
            "csv": root / "domains" / "freight-demurrage" / "data" / "containers.csv",
            "spine": True,
            "money_col": "projected_demurrage_usd",
            "money_label": "Projected demurrage",
            "id_hint": "container_id",
        },
        "equipment-size": {
            "label": "Equipment size (coda)",
            "domain": root / "domains" / "equipment-size" / "domain.yaml",
            "csv": root / "domains" / "equipment-size" / "data" / "bookings.csv",
            "spine": False,
            "money_col": "cargo_value_usd",
            "money_label": "Cargo value on book",
            "id_hint": "booking_id",
        },
        "inland-mode": {
            "label": "Inland truck vs rail (coda)",
            "domain": root / "domains" / "inland-mode" / "domain.yaml",
            "csv": root / "domains" / "inland-mode" / "data" / "moves.csv",
            "spine": False,
            "money_col": "truck_cost_usd",
            "money_label": "Truck cost rollup",
            "id_hint": "move_id",
        },
        "air-freight": {
            "label": "Air freight (coda)",
            "domain": root / "domains" / "air-freight" / "domain.yaml",
            "csv": root / "domains" / "air-freight" / "data" / "shipments.csv",
            "spine": False,
            "money_col": "projected_delay_cost_usd",
            "money_label": "Projected delay cost",
            "id_hint": "awb_id",
        },
    }

DEFAULT_PACK = "freight-demurrage"
