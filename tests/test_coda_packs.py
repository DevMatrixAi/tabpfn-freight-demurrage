"""Load + fit mock for equipment-size, inland-mode, and air-freight coda packs."""
from __future__ import annotations

from pathlib import Path

import pytest

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.demo.run_demo import run_demo
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode

ROOT = Path(__file__).resolve().parents[1]

PACKS = [
    (
        "equipment-size",
        ROOT / "domains" / "equipment-size" / "domain.yaml",
        ROOT / "domains" / "equipment-size" / "data" / "bookings.csv",
        "special_equip_fit",
        {"reefer_hold", "upsell_40hc", "confirm_special", "confirm_dry", "monitor"},
    ),
    (
        "inland-mode",
        ROOT / "domains" / "inland-mode" / "domain.yaml",
        ROOT / "domains" / "inland-mode" / "data" / "moves.csv",
        "prefer_rail",
        {"book_rail", "hold_for_ramp", "book_truck", "expedite_inland", "monitor"},
    ),
    (
        "air-freight",
        ROOT / "domains" / "air-freight" / "domain.yaml",
        ROOT / "domains" / "air-freight" / "data" / "shipments.csv",
        "miss_connection_risk",
        {"expedite_aog", "hold_for_connection", "rebook_belly", "monitor"},
    ),
]


def _ensure_csv(name: str, csv_path: Path) -> None:
    if csv_path.is_file():
        return
    from tabpfn_hack_core.demo.gen_coda_packs import (
        gen_air_freight,
        gen_equipment_size,
        gen_inland_mode,
    )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if name == "equipment-size":
        gen_equipment_size(n=250, seed=42).to_csv(csv_path, index=False)
    elif name == "inland-mode":
        gen_inland_mode(n=250, seed=43).to_csv(csv_path, index=False)
    else:
        gen_air_freight(n=250, seed=44).to_csv(csv_path, index=False)


@pytest.mark.parametrize("name,domain_path,csv_path,label,actions", PACKS, ids=[p[0] for p in PACKS])
def test_coda_pack_load_and_fit_mock(name, domain_path, csv_path, label, actions):
    assert domain_path.is_file(), domain_path
    _ensure_csv(name, csv_path)
    assert csv_path.is_file(), csv_path
    domain = load_domain(domain_path)
    assert domain.name == name
    assert domain.label_col == label
    assert domain.data_path
    assert domain.playbook, "playbook required"
    playbook_actions = {s.action for s in domain.playbook}
    assert playbook_actions & actions

    session = PipelineSession(domain=domain, root=ROOT)
    loaded = session.load_table(path=str(csv_path), table_id=name)
    assert loaded.n_rows >= 100
    df = session.tables[name]
    assert label in df.columns
    assert set(df[label].dropna().unique()).issubset({0, 1})

    fit = session.fit_predict(name, mode=BackendMode.mock)
    assert fit.backend == "mock"
    assert fit.n_train > 0 and fit.n_test > 0
    assert "accuracy" in fit.metrics

    suggested = session.suggest_actions(name, max_rows=30)
    assert suggested.items
    assert sum(suggested.counts.values()) == len(suggested.items)


@pytest.mark.parametrize("name,domain_path,csv_path,label,actions", PACKS, ids=[p[0] for p in PACKS])
def test_coda_pack_demo_uses_data_path(name, domain_path, csv_path, label, actions, tmp_path, monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    result = run_demo(
        root=ROOT,
        mode="mock",
        domain_path=domain_path,
        out_dir=tmp_path / f"art-{name}",
    )
    assert result["backend"] == "mock"
    assert result["n_rows"] >= 100
    assert Path(result["report_path"]).is_file()


def test_desk_packs_include_air():
    import importlib.util
    import sys

    packs_path = ROOT / "apps" / "desk" / "packs.py"
    spec = importlib.util.spec_from_file_location("desk_packs", packs_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["desk_packs"] = mod
    spec.loader.exec_module(mod)
    packs = mod.build_packs(ROOT)
    assert "air-freight" in packs
    assert packs["air-freight"]["csv"].name == "shipments.csv"
    assert packs["freight-demurrage"]["spine"] is True
    assert packs["air-freight"]["spine"] is False
    assert set(packs) >= {"freight-demurrage", "equipment-size", "inland-mode", "air-freight"}
