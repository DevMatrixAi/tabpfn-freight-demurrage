"""MCP 7-tool mock smoke receipt freeze + artifact presence."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SPEC = importlib.util.spec_from_file_location(
    "freeze_mcp_mock_smoke_receipt",
    ROOT / "scripts" / "freeze_mcp_mock_smoke_receipt.py",
)
assert SPEC and SPEC.loader
_fr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_fr)

EXPECTED_TOOLS = [
    "load_table",
    "profile",
    "fit_predict",
    "explain",
    "export_report",
    "compare_baseline",
    "suggest_actions",
]


def test_freeze_script_exists():
    assert (ROOT / "scripts" / "freeze_mcp_mock_smoke_receipt.py").is_file()


def test_refuse_real_token(monkeypatch, tmp_path):
    monkeypatch.setenv("TABPFN_TOKEN", "not-empty-token")
    with pytest.raises(SystemExit) as ei:
        _fr.write_receipt(out_dir=tmp_path)
    assert "TABPFN_TOKEN" in str(ei.value)


def test_freeze_writes_json_and_md(monkeypatch, tmp_path):
    monkeypatch.setenv("TABPFN_TOKEN", "")
    jp, mp = _fr.write_receipt(out_dir=tmp_path)
    assert jp.is_file() and mp.is_file()
    data = json.loads(jp.read_text())
    assert data["tool_count"] == 7
    assert data["all_ok"] is True
    assert data["mock"] is True
    assert data["has_token"] is False
    assert [s["tool"] for s in data["steps"]] == EXPECTED_TOOLS
    assert all(s["ok"] for s in data["steps"])
    assert all("latency_ms_mock" in s for s in data["steps"])
    md = mp.read_text()
    assert "MCP 7-tool" in md
    assert "load_table" in md
    assert "suggest_actions" in md


def test_artifact_present_in_repo():
    jp = ROOT / "artifacts" / "freight-demurrage" / "mcp_mock_smoke_receipt.json"
    mp = ROOT / "artifacts" / "freight-demurrage" / "mcp_mock_smoke_receipt.md"
    assert jp.is_file(), "run freeze script to create artifact"
    assert mp.is_file()
    data = json.loads(jp.read_text())
    assert data["tool_count"] == 7
    assert data["all_ok"] is True


def test_mcp_smoke_md_links_receipt():
    text = (ROOT / "docs" / "MCP_SMOKE.md").read_text()
    assert "mcp_mock_smoke_receipt" in text
