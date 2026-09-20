"""EDI 315 (ocean status) fixture adapter (no live API / VAN)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tabpfn_hack_core.adapters.base import BaseFreightAdapter
from tabpfn_hack_core.domain import find_project_root


def _default_fixture() -> Path:
    return find_project_root() / "fixtures" / "adapters" / "edi_315.json"


class Edi315FixtureAdapter(BaseFreightAdapter):
    def __init__(self, fixture_path: Path | str | None = None):
        self._path = Path(fixture_path) if fixture_path else _default_fixture()

    @property
    def name(self) -> str:
        return "edi_315"

    def fetch_events(self) -> list[dict[str, Any]]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        segments = raw.get("status_messages") or raw.get("messages") or raw
        if isinstance(segments, dict):
            segments = [segments]
        out: list[dict[str, Any]] = []
        for m in segments:
            free_days = float(m.get("free_days_left", m.get("QTY_free_days", 0)))
            dwell = float(m.get("dwell_days_so_far", m.get("QTY_dwell", 0)))
            daily = float(m.get("daily_demurrage_usd", 100))
            projected = float(m.get("projected_demurrage_usd", max(0.0, -min(free_days, 0) * daily)))
            out.append(
                {
                    "container_id": m.get("container_id") or m.get("N9_CN"),
                    "event_ts": m.get("event_ts") or m.get("DTM_event"),
                    "vessel_id": m.get("vessel_id") or m.get("N9_VN"),
                    "bol_id": m.get("bol_id") or m.get("N9_BM"),
                    "pol": m.get("pol") or m.get("R4_L"),
                    "pod": m.get("pod") or m.get("R4_D"),
                    "terminal_note": m.get("terminal_note") or m.get("K1_note") or "",
                    "weather_alert": m.get("weather_alert") or "",
                    "free_days_left": free_days,
                    "dwell_days_so_far": dwell,
                    "teu": int(m.get("teu", 1)),
                    "cargo_value_usd": float(m.get("cargo_value_usd", 20000)),
                    "daily_demurrage_usd": daily,
                    "blank_sailing": int(m.get("blank_sailing", 0)),
                    "inland_can_beat_freedays": int(m.get("inland_can_beat_freedays", 0)),
                    "fee_inevitable": int(m.get("fee_inevitable", 0)),
                    "cargo_vs_fee_collapse": int(m.get("cargo_vs_fee_collapse", 0)),
                    "projected_demurrage_usd": projected,
                    "demurrage_risk": int(m.get("demurrage_risk", 1 if free_days < 2 or projected > 500 else 0)),
                }
            )
        return out
