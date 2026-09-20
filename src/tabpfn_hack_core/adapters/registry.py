"""Registry of freight adapters (fixtures only)."""
from __future__ import annotations

from typing import Callable

from tabpfn_hack_core.adapters.base import BaseFreightAdapter, FreightAdapter
from tabpfn_hack_core.adapters.edi_315_fixture import Edi315FixtureAdapter
from tabpfn_hack_core.adapters.project44_fixture import Project44FixtureAdapter
from tabpfn_hack_core.adapters.terminal49_fixture import Terminal49FixtureAdapter

_REGISTRY: dict[str, Callable[[], BaseFreightAdapter]] = {
    "terminal49": Terminal49FixtureAdapter,
    "project44": Project44FixtureAdapter,
    "edi_315": Edi315FixtureAdapter,
}


def list_adapters() -> list[str]:
    return sorted(_REGISTRY.keys())


def get_adapter(name: str) -> FreightAdapter:
    key = name.strip().lower().replace("-", "_")
    if key not in _REGISTRY:
        raise KeyError(f"Unknown adapter '{name}'. Known: {list_adapters()}")
    return _REGISTRY[key]()


def load_adapter(name: str) -> FreightAdapter:
    """Alias for get_adapter (desk / CLI)."""
    return get_adapter(name)
