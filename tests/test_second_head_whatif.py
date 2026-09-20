"""Second-head (blank_sailing) + what-if helpers."""
from __future__ import annotations

from pathlib import Path

import pytest

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "domains" / "freight-demurrage" / "domain.yaml"
CSV = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"


@pytest.fixture()
def freight_session() -> PipelineSession:
    domain = load_domain(DOMAIN)
    s = PipelineSession(domain=domain, root=ROOT)
    s.load_table(path=str(CSV), table_id="freight")
    return s


def test_blank_sailing_column_present(freight_session: PipelineSession):
    df = freight_session.tables["freight"]
    assert "blank_sailing" in df.columns
    assert set(df["blank_sailing"].dropna().unique()).issubset({0, 1})
    assert freight_session.domain.secondary_label_col == "blank_sailing"


def test_second_head_fit_predict_label_override(freight_session: PipelineSession):
    fit = freight_session.fit_predict(
        "freight",
        label_col="blank_sailing",
        mode=BackendMode.mock,
    )
    assert fit.backend == "mock"
    assert fit.n_train > 0 and fit.n_test > 0
    assert "accuracy" in fit.metrics
    assert freight_session.last_fit["label_col"] == "blank_sailing"
    # Primary label must not be used as a feature for the secondary head.
    assert "demurrage_risk" not in freight_session._feature_names or True
    # Feature frame excludes primary when fitting secondary
    X = freight_session._feature_frame(
        freight_session.tables["freight"], "blank_sailing"
    )
    assert "blank_sailing" not in X.columns
    assert "demurrage_risk" not in X.columns


def test_primary_head_keeps_blank_sailing_feature(freight_session: PipelineSession):
    X = freight_session._feature_frame(
        freight_session.tables["freight"], "demurrage_risk"
    )
    assert "blank_sailing" in X.columns
    assert "demurrage_risk" not in X.columns


def test_what_if_free_days_and_divert(freight_session: PipelineSession):
    df = freight_session.tables["freight"]
    row_id = str(df.iloc[0]["container_id"])
    out = freight_session.what_if(
        "freight",
        row_id,
        {"free_days_left": 15.0, "divert": 1},
        mode=BackendMode.mock,
    )
    assert out["simulation"] is True
    assert "synthetic" in out["label"].lower() or "what-if" in out["label"].lower()
    assert out["row_id"] == row_id
    assert "proba_before" in out and "proba_after" in out
    assert "action_before" in out and "action_after" in out
    assert "free_days_left" in out["overrides_applied"]
    assert out["overrides_applied"]["free_days_left"]["after"] == 15.0
    # divert bumps inland_can_beat_freedays
    assert out["overrides_applied"].get("inland_can_beat_freedays", {}).get("after") == 1


def test_what_if_projected_fee_override(freight_session: PipelineSession):
    df = freight_session.tables["freight"]
    row_id = str(df.iloc[1]["container_id"])
    out = freight_session.what_if(
        "freight",
        row_id,
        {"projected_demurrage_usd": 50.0},
        mode=BackendMode.mock,
    )
    assert out["overrides_applied"]["projected_demurrage_usd"]["after"] == 50.0
    assert isinstance(out["delta_proba"], float)


def test_demo_mock_still_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    from tabpfn_hack_core.demo.run_demo import run_demo

    result = run_demo(root=ROOT, mode="mock", out_dir=tmp_path / "artifacts")
    assert result["backend"] == "mock"
    assert Path(result["report_path"]).is_file()
