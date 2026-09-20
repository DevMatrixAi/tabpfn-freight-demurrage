"""Freight feed adapters: normalize vendor payloads into domain CSV schema.

Fixtures only — no live API keys. Used by the web desk and tests.
"""
from __future__ import annotations

from tabpfn_hack_core.adapters.base import FREIGHT_COLUMNS, FreightAdapter
from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters, load_adapter

__all__ = [
    "FREIGHT_COLUMNS",
    "FreightAdapter",
    "get_adapter",
    "list_adapters",
    "load_adapter",
]
