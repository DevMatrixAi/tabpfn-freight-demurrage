"""Desk domain pack registry (spine + coda)."""
from __future__ import annotations
from pathlib import Path
from typing import Any

def build_packs(root: Path) -> dict[str, dict[str, Any]]:
    return {
        "freight-demurrage": {
            "label": "Freight desk: late container fees",
            "gloss": "Which containers will run up port late fees (demurrage), and what to do",
            "domain": root / "domains" / "freight-demurrage" / "domain.yaml",
            "csv": root / "domains" / "freight-demurrage" / "data" / "containers.csv",
            "spine": True,
            "money_col": "projected_demurrage_usd",
            "money_label": "Possible late fees",
            "id_hint": "container_id",
        },
        "equipment-size": {
            "label": "Which container size to book",
            "gloss": "Pick the container size each booking needs",
            "domain": root / "domains" / "equipment-size" / "domain.yaml",
            "csv": root / "domains" / "equipment-size" / "data" / "bookings.csv",
            "spine": False,
            "money_col": "cargo_value_usd",
            "money_label": "Cargo value on book",
            "id_hint": "booking_id",
        },
        "inland-mode": {
            "label": "Truck or rail inland",
            "gloss": "Choose truck or rail for the inland leg",
            "domain": root / "domains" / "inland-mode" / "domain.yaml",
            "csv": root / "domains" / "inland-mode" / "data" / "moves.csv",
            "spine": False,
            "money_col": "truck_cost_usd",
            "money_label": "Truck cost rollup",
            "id_hint": "move_id",
        },
        "air-freight": {
            "label": "Air freight delays",
            "gloss": "Which air shipments will miss a connection",
            "domain": root / "domains" / "air-freight" / "domain.yaml",
            "csv": root / "domains" / "air-freight" / "data" / "shipments.csv",
            "spine": False,
            "money_col": "projected_delay_cost_usd",
            "money_label": "Projected delay cost",
            "id_hint": "awb_id",
        },
        "stow-fit": {
            "label": "Equipment and mode for a load",
            "gloss": "Pick equipment and transport mode together",
            "domain": root / "domains" / "stow-fit" / "domain.yaml",
            "csv": root / "domains" / "stow-fit" / "data" / "shipments.csv",
            "spine": False,
            "money_col": "cargo_value_usd",
            "money_label": "Cargo value",
            "id_hint": "shipment_id",
        },
    }

DEFAULT_PACK = "freight-demurrage"
