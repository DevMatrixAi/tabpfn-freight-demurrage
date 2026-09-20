"""project44-shaped fixture adapter (no live API)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tabpfn_hack_core.adapters.base import BaseFreightAdapter
from tabpfn_hack_core.domain import find_project_root


def _default_fixture() -> Path:
    return find_project_root() / "fixtures" / "adapters" / "project44.json"


class Project44FixtureAdapter(BaseFreightAdapter):
    def __init__(self, fixture_path: Path | str | None = None):
        self._path = Path(fixture_path) if fixture_path else _default_fixture()

    @property
    def name(self) -> str:
        return "project44"

    def fetch_events(self) -> list[dict[str, Any]]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        shipments = raw.get("shipments") or raw.get("data") or raw
        if isinstance(shipments, dict):
            shipments = [shipments]
        out: list[dict[str, Any]] = []
        for s in shipments:
            container = (s.get("identifiers") or {}).get("containerId") or s.get("container_id")
            route = s.get("routeInfo") or s.get("route") or {}
            states = s.get("states") or {}
            costs = s.get("costs") or {}
            free_days = float(states.get("freeDaysLeft", s.get("free_days_left", 0)))
            dwell = float(states.get("dwellDays", s.get("dwell_days_so_far", 0)))
            daily = float(costs.get("dailyDemurrageUsd", s.get("daily_demurrage_usd", 150)))
            projected = float(costs.get("projectedDemurrageUsd", s.get("projected_demurrage_usd", 0)))
            flags = s.get("flags") or {}
            out.append(
                {
                    "container_id": container,
                    "event_ts": s.get("eventTime") or s.get("event_ts"),
                    "vessel_id": (s.get("identifiers") or {}).get("vesselId") or s.get("vessel_id"),
                    "bol_id": (s.get("identifiers") or {}).get("bol") or s.get("bol_id"),
                    "pol": route.get("origin") or s.get("pol"),
                    "pod": route.get("destination") or s.get("pod"),
                    "terminal_note": s.get("terminalNote") or s.get("terminal_note") or "",
                    "weather_alert": s.get("weatherAlert") or s.get("weather_alert") or "",
                    "free_days_left": free_days,
                    "dwell_days_so_far": dwell,
                    "teu": int(s.get("teu", 1)),
                    "cargo_value_usd": float(costs.get("cargoValueUsd", s.get("cargo_value_usd", 30000))),
                    "daily_demurrage_usd": daily,
                    "blank_sailing": int(flags.get("blankSailing", s.get("blank_sailing", 0))),
                    "inland_can_beat_freedays": int(
                        flags.get("inlandCanBeatFreedays", s.get("inland_can_beat_freedays", 0))
                    ),
                    "fee_inevitable": int(flags.get("feeInevitable", s.get("fee_inevitable", 0))),
                    "cargo_vs_fee_collapse": int(
                        flags.get("cargoVsFeeCollapse", s.get("cargo_vs_fee_collapse", 0))
                    ),
                    "projected_demurrage_usd": projected,
                    "demurrage_risk": int(s.get("demurrage_risk", 1 if free_days < 2 or projected > 500 else 0)),
                }
            )
        return out
