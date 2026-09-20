"""Protocol / ABC for freight feed adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

import pandas as pd

# Columns expected by domains/freight-demurrage (domain.yaml + containers.csv).
FREIGHT_COLUMNS: list[str] = [
    "container_id",
    "event_ts",
    "vessel_id",
    "bol_id",
    "pol",
    "pod",
    "terminal_note",
    "weather_alert",
    "free_days_left",
    "dwell_days_so_far",
    "teu",
    "cargo_value_usd",
    "daily_demurrage_usd",
    "blank_sailing",
    "inland_can_beat_freedays",
    "fee_inevitable",
    "cargo_vs_fee_collapse",
    "projected_demurrage_usd",
    "demurrage_risk",
]


@runtime_checkable
class FreightAdapter(Protocol):
    """Normalize an external freight feed into the demurrage domain schema."""

    @property
    def name(self) -> str: ...

    def fetch_events(self) -> list[dict[str, Any]]: ...

    def to_dataframe(self) -> pd.DataFrame: ...


class BaseFreightAdapter(ABC):
    """Shared helpers for fixture adapters."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def fetch_events(self) -> list[dict[str, Any]]: ...

    def to_dataframe(self) -> pd.DataFrame:
        rows = self.fetch_events()
        df = pd.DataFrame(rows)
        for col in FREIGHT_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA
        return df[FREIGHT_COLUMNS]
