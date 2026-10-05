"""Desk domain pack registry (spine + coda)."""
from __future__ import annotations
from pathlib import Path
from typing import Any

def build_packs(root: Path) -> dict[str, dict[str, Any]]:
    return {
        "freight-demurrage": {
            "label": "Late container fees",
            "gloss": "Late-container fee (demurrage) — money left on the dock",
            "domain": root / "domains" / "freight-demurrage" / "domain.yaml",
            "csv": root / "domains" / "freight-demurrage" / "data" / "containers.csv",
            "spine": True,
            "money_col": "projected_demurrage_usd",
            "money_label": "Money at risk",
            "id_hint": "container_id",
        },
        "equipment-size": {
            "label": "Which container size to book",
            "gloss": "Right box size for the booking",
            "domain": root / "domains" / "equipment-size" / "domain.yaml",
            "csv": root / "domains" / "equipment-size" / "data" / "bookings.csv",
            "spine": False,
            "money_col": "cargo_value_usd",
            "money_label": "Cargo value on book",
            "id_hint": "booking_id",
        },
        "inland-mode": {
            "label": "Truck or rail inland",
            "gloss": "Truck or rail to the inland dest",
            "domain": root / "domains" / "inland-mode" / "domain.yaml",
            "csv": root / "domains" / "inland-mode" / "data" / "moves.csv",
            "spine": False,
            "money_col": "truck_cost_usd",
            "money_label": "Truck cost rollup",
            "id_hint": "move_id",
        },
        "air-freight": {
            "label": "Air freight delays",
            "gloss": "Missed connection / delay cost on air",
            "domain": root / "domains" / "air-freight" / "domain.yaml",
            "csv": root / "domains" / "air-freight" / "data" / "shipments.csv",
            "spine": False,
            "money_col": "projected_delay_cost_usd",
            "money_label": "Projected delay cost",
            "id_hint": "awb_id",
        },
        "stow-fit": {
            "label": "Equipment and mode for a cargo load",
            "gloss": "Suggest the right container size or transport mode",
            "domain": root / "domains" / "stow-fit" / "domain.yaml",
            "csv": root / "domains" / "stow-fit" / "data" / "shipments.csv",
            "spine": False,
            "money_col": "cargo_value_usd",
            "money_label": "Cargo value",
            "id_hint": "shipment_id",
        },
    }

DEFAULT_PACK = "freight-demurrage"
