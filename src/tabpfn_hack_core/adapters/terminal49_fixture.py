"""Terminal49-shaped fixture adapter (no live API)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tabpfn_hack_core.adapters.base import BaseFreightAdapter
from tabpfn_hack_core.domain import find_project_root


def _default_fixture() -> Path:
    return find_project_root() / "fixtures" / "adapters" / "terminal49.json"


class Terminal49FixtureAdapter(BaseFreightAdapter):
    def __init__(self, fixture_path: Path | str | None = None):
        self._path = Path(fixture_path) if fixture_path else _default_fixture()

    @property
    def name(self) -> str:
        return "terminal49"

    def fetch_events(self) -> list[dict[str, Any]]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        shipments = raw.get("shipments") or raw.get("data") or raw
        if isinstance(shipments, dict):
            shipments = [shipments]
        out: list[dict[str, Any]] = []
        for s in shipments:
            attrs = s.get("attributes") or s
            loc = attrs.get("location") or {}
            risk_flags = attrs.get("risk_flags") or {}
            free_days = float(attrs.get("free_days_remaining", attrs.get("free_days_left", 0)))
            dwell = float(attrs.get("dwell_days", attrs.get("dwell_days_so_far", 0)))
            daily = float(attrs.get("demurrage_rate_usd", attrs.get("daily_demurrage_usd", 100)))
            projected = max(0.0, -min(free_days, 0) * daily + max(0.0, dwell - 7) * daily * 0.25)
            if "projected_demurrage_usd" in attrs:
                projected = float(attrs["projected_demurrage_usd"])
            demurrage_risk = int(attrs.get("demurrage_risk", 1 if free_days < 2 or projected > 500 else 0))
            out.append(
                {
                    "container_id": attrs.get("container_number") or attrs.get("container_id"),
                    "event_ts": attrs.get("event_timestamp") or attrs.get("event_ts"),
                    "vessel_id": attrs.get("vessel_imo") or attrs.get("vessel_id") or attrs.get("vessel_name"),
                    "bol_id": attrs.get("bill_of_lading") or attrs.get("bol_id"),
                    "pol": attrs.get("port_of_lading") or attrs.get("pol") or loc.get("pol"),
                    "pod": attrs.get("port_of_discharge") or attrs.get("pod") or loc.get("pod"),
                    "terminal_note": attrs.get("terminal_remarks") or attrs.get("terminal_note") or "",
                    "weather_alert": attrs.get("weather") or attrs.get("weather_alert") or "",
                    "free_days_left": free_days,
                    "dwell_days_so_far": dwell,
                    "teu": int(attrs.get("teu", 1)),
                    "cargo_value_usd": float(attrs.get("cargo_value_usd", 25000)),
                    "daily_demurrage_usd": daily,
                    "blank_sailing": int(risk_flags.get("blank_sailing", attrs.get("blank_sailing", 0))),
                    "inland_can_beat_freedays": int(
                        risk_flags.get("inland_can_beat_freedays", attrs.get("inland_can_beat_freedays", 0))
                    ),
                    "fee_inevitable": int(risk_flags.get("fee_inevitable", attrs.get("fee_inevitable", 0))),
                    "cargo_vs_fee_collapse": int(
                        risk_flags.get("cargo_vs_fee_collapse", attrs.get("cargo_vs_fee_collapse", 0))
                    ),
                    "projected_demurrage_usd": projected,
                    "demurrage_risk": demurrage_risk,
                }
            )
        return out
