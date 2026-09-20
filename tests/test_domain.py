"""Tests for domain.yaml loading."""
from __future__ import annotations

from pathlib import Path

from tabpfn_hack_core.domain import DomainConfig, load_domain


ROOT = Path(__file__).resolve().parents[1]


def test_load_default_domain_yaml():
    cfg = load_domain(ROOT / "domain.yaml")
    assert cfg.name == "generic-messy-table"
    assert cfg.label_col == "target"
    assert cfg.group_col == "group_id"
    assert cfg.time_col == "event_ts"
    assert cfg.group_time_col == "event_ts"
    assert "note_text" in cfg.text_cols
    assert cfg.action_thresholds.high == 0.75
    assert cfg.actions["high"] == "escalate"
    assert "Synthetic" in cfg.disclaimer


def test_domain_defaults_when_missing(tmp_path: Path):
    cfg = load_domain(tmp_path / "nope.yaml")
    # missing file → defaults
    assert isinstance(cfg, DomainConfig)
    assert cfg.label_col == "target"


def test_custom_domain_roundtrip(tmp_path: Path):
    p = tmp_path / "domain.yaml"
    p.write_text(
        "name: custom\nlabel_col: y\ntext_cols: [t]\nactions:\n  high: go\n  mid: maybe\n  low: stop\n",
        encoding="utf-8",
    )
    cfg = load_domain(p)
    assert cfg.name == "custom"
    assert cfg.label_col == "y"
    assert cfg.actions["high"] == "go"
