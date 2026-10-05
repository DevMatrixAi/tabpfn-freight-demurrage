"""Test defaults: never call the live TabPFN API, and test the plain mock path unless a test opts in."""
import pytest


@pytest.fixture(autouse=True)
def _offline_defaults(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    monkeypatch.setenv("DESK_REPLAY", "0")
    yield
