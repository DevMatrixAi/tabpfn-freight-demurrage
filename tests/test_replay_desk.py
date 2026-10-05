"""Recorded TabPFN-3.5 replay: desk and /eval show real model scores with no token."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from fastapi.testclient import TestClient

from apps.desk.act_first import build_act_first
from tabpfn_hack_core.core import replay
from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain


@pytest.fixture
def replay_on(monkeypatch):
    monkeypatch.setenv("DESK_REPLAY", "1")
    assert replay.replay_enabled()


def _sess():
    dom = load_domain(ROOT / "domains" / "freight-demurrage" / "domain.yaml")
    s = PipelineSession(domain=dom, root=ROOT)
    s.load_table(path=str(ROOT / dom.data_path), table_id="t")
    return s


def test_replay_off_by_default_in_tests():
    assert not replay.replay_enabled()


def test_token_disables_replay_unless_forced(monkeypatch):
    monkeypatch.setenv("TABPFN_TOKEN", "x")
    monkeypatch.setenv("DESK_REPLAY", "1")
    assert not replay.replay_enabled()
    monkeypatch.setenv("DESK_REPLAY", "force")
    assert replay.replay_enabled()


def test_fit_predict_uses_recorded_scores(replay_on):
    s = _sess()
    fit = s.fit_predict("t", mode="thinking")
    assert fit.backend == "tabpfn_replay"
    assert fit.n_test == 1200
    assert fit.metrics["roc_auc"] == pytest.approx(0.987, abs=0.002)
    cmp_ = s.compare_baseline("t", mode="plus")
    assert cmp_.tabpfn_metrics["roc_auc"] == pytest.approx(0.986, abs=0.002)
    assert cmp_.baseline_metrics["roc_auc"] == pytest.approx(0.957, abs=0.002)
    assert "proba_hist_gbm" in s.last_predictions.columns


def test_fast_and_local_never_use_replay(replay_on):
    s = _sess()
    assert s.fit_predict("t", mode="fast").backend == "mock"


def test_unknown_rows_get_marked_estimate(replay_on):
    s = _sess()
    df = s.tables["t"]
    extra = df.head(5).copy()
    extra["container_id"] = [f"NEW-{i}" for i in range(5)]
    s.tables["t"] = pd.concat([df, extra], ignore_index=True)
    s.fit_predict("t", mode="thinking")
    src = s.last_predictions["score_source"]
    assert (src == "estimate").sum() == 5
    assert s.last_fit["replay"]["n_estimated"] == 5


def test_act_first_matches_receipt(replay_on):
    s = _sess()
    s.compare_baseline("t", mode="plus")
    af = build_act_first(s.last_predictions, id_col="container_id", money_col="projected_demurrage_usd")
    assert af["model"]["net_savings"] == replay.recorded_net_savings(300)["plus"]
    assert af["baseline"]["net_savings"] == replay.recorded_net_savings(300)["hist_gbm"]
    assert len(af["items"]) == 5
    exp = [it["expected"] for it in af["items"]]
    assert exp == sorted(exp, reverse=True)


def test_act_first_rule_small():
    pred = pd.DataFrame({
        "container_id": ["A", "B", "C"],
        "proba_1": [0.9, 0.5, 0.99],
        "projected_demurrage_usd": [1000, 10000, 100],
        "y_true": [1, 0, 1],
    })
    af = build_act_first(pred, id_col="container_id", money_col="projected_demurrage_usd")
    assert [i["row_id"] for i in af["items"]] == ["B", "A"]  # C: 0.99*100 < $300
    assert af["model"]["net_savings"] == 1000 - 600
    assert af["top_risk"]["row_id"] == "C" and not af["top_risk"]["in_top"]


def test_desk_and_eval_show_replay(replay_on):
    from apps.desk.app import app
    from apps.desk.auth import SESSION_COOKIE

    with TestClient(app) as c:
        c.cookies.set(SESSION_COOKIE, "1")
        c.post("/load-domain-csv", follow_redirects=False)
        r = c.post("/run-triage", data={"mode": "thinking"}, follow_redirects=True)
        t = r.text
        assert 'id="replay-banner"' in t and 'id="act-first"' in t
        assert "Real TabPFN-3.5 scores" in t
        assert "$898,376" in t and "$877,962" in t
        assert "mock fallback" not in t
        c.post("/eval/run", data={"pack": "freight-demurrage"}, follow_redirects=False)
        e = c.get("/eval?pack=freight-demurrage").text
        assert "recorded TabPFN-3.5" in e
        assert "$900,610" in e
        assert "tabpfn_replay" in e
        assert 'id="lc-table"' in e
        assert "requested mode=plus will fall back" not in e
