"""Preflight live-budget gate: token / DEV_N=60 / block full-table live."""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SPEC = importlib.util.spec_from_file_location(
    "preflight_live_budget",
    ROOT / "scripts" / "preflight_live_budget.py",
)
assert SPEC and SPEC.loader
_pre = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(_pre)


def test_script_and_wrapper_exist():
    assert (ROOT / "scripts" / "preflight_live_budget.py").is_file()
    assert (ROOT / "scripts" / "preflight.sh").is_file()


def test_mock_ok_empty_token(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    monkeypatch.delenv("TABPFN_DEV_N", raising=False)
    buf = io.StringIO()
    rc = _pre.run_preflight(mode="mock", stream=buf)
    assert rc == 0
    out = buf.getvalue()
    assert "unset/empty" in out
    assert "resolved n=60" in out
    assert "OK [--mock]" in out
    assert os_environ_dev_n_60()


def os_environ_dev_n_60() -> bool:
    import os

    return os.environ.get("TABPFN_DEV_N") == "60"


def test_mock_fail_when_token_set(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "fake-token-for-test")
    monkeypatch.setenv("TABPFN_DEV_N", "60")
    buf = io.StringIO()
    rc = _pre.run_preflight(mode="mock", stream=buf)
    assert rc == 2
    assert "FAIL [--mock]" in buf.getvalue()


def test_live_check_ok_token_and_safe_n(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "fake-token-for-test")
    monkeypatch.setenv("TABPFN_DEV_N", "60")
    buf = io.StringIO()
    rc = _pre.run_preflight(mode="live-check", stream=buf)
    assert rc == 0
    assert "OK [--live-check]" in buf.getvalue()


def test_live_check_fail_no_token(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    monkeypatch.setenv("TABPFN_DEV_N", "60")
    buf = io.StringIO()
    rc = _pre.run_preflight(mode="live-check", stream=buf)
    assert rc == 3


def test_block_full_table_live_missing_n(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "fake-token-for-test")
    monkeypatch.delenv("TABPFN_DEV_N", raising=False)
    buf = io.StringIO()
    # sample_n empty → full; --no-default so we don't force 60
    rc = _pre.run_preflight(
        mode="live-check",
        sample_n="",
        set_default=False,
        stream=buf,
    )
    assert rc == 4
    out = buf.getvalue()
    assert "full-table live BLOCKED" in out
    assert "sample_n 40–80" in out or "TABPFN_DEV_N=60" in out


def test_block_full_table_live_n_ge_fixture(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "fake-token-for-test")
    rows = _pre._fixture_rows()
    buf = io.StringIO()
    rc = _pre.run_preflight(
        mode="live-check",
        sample_n=str(rows),
        stream=buf,
    )
    assert rc == 4
    assert "full-table live BLOCKED" in buf.getvalue()


def test_is_full_table_live_helper():
    assert _pre.is_full_table_live(has_token=False, resolved_n=None) is False
    assert _pre.is_full_table_live(has_token=True, resolved_n=None) is True
    assert _pre.is_full_table_live(
        has_token=True, resolved_n=60, fixture_rows=1200
    ) is False
    assert _pre.is_full_table_live(
        has_token=True, resolved_n=1200, fixture_rows=1200
    ) is True


def test_chip_summary_importable(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    chip = _pre._chip_summary(sample_n=60, has_token=False)
    assert chip["mode"] == "mock"
    assert chip["sample_n"] == 60
    assert "Mock" in chip["label"]


def test_cli_main_mock(monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    monkeypatch.delenv("TABPFN_DEV_N", raising=False)
    assert _pre.main(["--mock"]) == 0


def test_docs_mention_preflight():
    judge = (ROOT / "docs" / "JUDGE_3MIN.md").read_text()
    readme = (ROOT / "README.md").read_text()
    blob = judge + "\n" + readme
    assert "preflight" in blob.lower()
