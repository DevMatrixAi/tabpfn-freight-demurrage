"""DEEP showcase: Thinking narrative, ablations, calibration, MCP cookbook."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tabpfn_hack_core.core.ablations import run_feature_ablations
from tabpfn_hack_core.core.calibration import calibration_from_predictions, calibration_summary
from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode

DOMAIN = ROOT / "domains" / "freight-demurrage" / "domain.yaml"
CSV = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"


@pytest.fixture()
def freight_session() -> PipelineSession:
    domain = load_domain(DOMAIN)
    s = PipelineSession(domain=domain, root=ROOT)
    df = pd.read_csv(CSV).head(80)
    s.load_table(csv_text=df.to_csv(index=False), table_id="freight")
    return s


def test_thinking_effort_and_narrative_on_fallback(freight_session, monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    fit = freight_session.fit_predict(
        "freight",
        mode=BackendMode.thinking,
        thinking_effort="high",
        test_size=0.3,
    )
    assert fit.mode == BackendMode.thinking
    assert fit.thinking_effort == "high"
    assert fit.group_col == "vessel_id"
    assert fit.group_time_col == "event_ts"
    assert fit.thinking_narrative
    assert "thinking_effort=high" in fit.thinking_narrative
    assert "group_col=vessel_id" in fit.thinking_narrative
    assert freight_session.last_fit.get("thinking_effort") == "high"


def test_compare_baseline_dense_judge_card(freight_session, monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    cmp_ = freight_session.compare_baseline("freight", mode=BackendMode.mock)
    assert "Judge card" in cmp_.narrative or "Δ accuracy=" in cmp_.narrative
    assert isinstance(cmp_.judge_card, dict)
    assert cmp_.judge_card.get("headline")
    assert "delta" in cmp_.judge_card
    assert cmp_.judge_card.get("text_cols")


def test_feature_ablations_variants(freight_session):
    df = freight_session.tables["freight"]
    X = freight_session._feature_frame(df, freight_session.domain.label_col)
    y = df[freight_session.domain.label_col].to_numpy()
    out = run_feature_ablations(X, y, freight_session.domain, test_size=0.3)
    variants = [r["variant"] for r in out["rows"]]
    assert "full" in variants
    assert "drop_text" in variants
    assert "drop_high_card" in variants
    assert out["text_cols"]
    assert out["high_card_cols"]
    assert out["headline"]


def test_calibration_summary_and_from_preds(freight_session, monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    freight_session.fit_predict("freight", mode=BackendMode.mock, test_size=0.3)
    cal = calibration_from_predictions(freight_session.last_predictions)
    assert cal["n"] > 0
    assert cal["brier"] is not None
    assert cal["ece"] is not None
    assert isinstance(cal["bins"], list)
    y = np.array([0, 1, 1, 0, 1, 0, 1, 1])
    p = np.array([0.1, 0.8, 0.7, 0.2, 0.9, 0.3, 0.6, 0.55])
    s = calibration_summary(y, p, n_bins=4)
    assert s["n"] == 8
    assert 0 <= s["brier"] <= 1


def test_eval_includes_new_panels(monkeypatch):
    from apps.desk.app import DEFAULT_PACK, PACKS, _metric_slice, _resolve_mode, _session
    from apps.desk.eval_dashboard import run_multi_mode_eval

    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    sess = _session(DEFAULT_PACK)
    df = pd.read_csv(PACKS[DEFAULT_PACK]["csv"]).head(40)
    sess.load_table(csv_text=df.to_csv(index=False), table_id="eval_deep")
    result = run_multi_mode_eval(
        sess, "eval_deep", resolve_mode=_resolve_mode, metric_slice=_metric_slice
    )
    assert "latency_panel" in result
    assert result["latency_panel"]["plus_s"] is not None
    assert result["ablations"] and result["ablations"]["rows"]
    assert result["calibration"]["n"] > 0
    assert result["thinking_showcase"]
    assert result["thinking_showcase"]["group_col"] == "vessel_id"
    assert result.get("judge_card") is not None


def test_eval_page_shows_new_sections():
    from fastapi.testclient import TestClient
    from apps.desk.app import DEFAULT_PACK, app
    from apps.desk.auth import SESSION_COOKIE

    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE, "1")
    r = c.post("/eval/run", data={"pack": DEFAULT_PACK}, follow_redirects=False)
    assert r.status_code in (303, 307)
    page = c.get("/eval")
    assert page.status_code == 200
    body = page.text
    assert 'id="eval-latency"' in body
    assert 'id="eval-ablations"' in body
    assert 'id="eval-calibration"' in body
    assert 'id="eval-thinking"' in body
    assert "thinking_effort" in body or "effort=" in body


def test_mcp_cookbook_script(tmp_path, monkeypatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "mcp_cookbook_demo", ROOT / "scripts" / "mcp_cookbook_demo.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rc = mod.main()
    assert rc == 0
    receipt = ROOT / "artifacts" / "mcp_cookbook" / "cookbook_receipt.json"
    assert receipt.is_file()
    data = json.loads(receipt.read_text())
    assert data["tool_count"] == 7
    assert [s["tool"] for s in data["steps"]] == data["tools"]


def test_stress_fixture_exists():
    # Prefer checked-in CSV; unpack packed blob if missing (MCP size limits).
    path = ROOT / "fixtures" / "stress" / "missing_wide_demurrage.csv"
    if not path.is_file():
        import runpy
        runpy.run_path(str(ROOT / "fixtures" / "stress" / "_unpack_missing_wide.py"))
    assert path.is_file()
    df = pd.read_csv(path)
    assert df.shape[1] >= 50
    assert df.isna().any().any()
