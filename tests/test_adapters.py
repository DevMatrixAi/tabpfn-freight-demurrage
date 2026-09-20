"""Unit tests for fixture freight adapters."""
from __future__ import annotations

from pathlib import Path

import pytest

from tabpfn_hack_core.adapters.base import FREIGHT_COLUMNS
from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters, load_adapter
from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode

ROOT = Path(__file__).resolve().parents[1]


def test_list_adapters():
    names = list_adapters()
    assert set(names) == {"terminal49", "project44", "edi_315"}


@pytest.mark.parametrize("name", ["terminal49", "project44", "edi_315"])
def test_adapter_fetch_and_schema(name: str):
    adapter = get_adapter(name)
    assert adapter.name == name
    events = adapter.fetch_events()
    assert len(events) >= 2
    df = adapter.to_dataframe()
    assert list(df.columns) == FREIGHT_COLUMNS
    assert len(df) == len(events)
    assert df["container_id"].notna().all()
    assert "demurrage_risk" in df.columns


def test_load_adapter_alias():
    a = load_adapter("terminal49")
    assert a.name == "terminal49"


def test_unknown_adapter():
    with pytest.raises(KeyError):
        get_adapter("not-a-real-vendor")


def test_adapter_into_pipeline_mock():
    """At least one fixture adapter loads into PipelineSession and runs triage."""
    domain = load_domain(ROOT / "domains" / "freight-demurrage" / "domain.yaml")
    import pandas as pd

    adapter = get_adapter("terminal49")
    fixture_df = adapter.to_dataframe()
    domain_df = pd.read_csv(ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv")
    combined = pd.concat([domain_df.head(40), fixture_df], ignore_index=True)

    sess = PipelineSession(domain=domain, root=ROOT)
    tmp = ROOT / "artifacts" / "_adapter_test.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(tmp, index=False)
    loaded = sess.load_table(path=str(tmp), table_id="adapter_t")
    assert loaded.n_rows == len(combined)

    fit = sess.fit_predict("adapter_t", mode=BackendMode.mock)
    assert fit.backend == "mock"
    assert "accuracy" in fit.metrics
    actions = sess.suggest_actions("adapter_t", max_rows=10)
    assert actions.items
    tmp.unlink(missing_ok=True)
