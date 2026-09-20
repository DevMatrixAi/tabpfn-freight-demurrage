"""End-to-end pipeline tests with mock backend (no network/GPU/token)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.demo.run_demo import generate_synthetic_table, run_demo
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def tiny_csv(tmp_path: Path) -> Path:
    return generate_synthetic_table(n=200, out=tmp_path / "t.csv", seed=0)


@pytest.fixture()
def session(tiny_csv: Path) -> PipelineSession:
    domain = load_domain(ROOT / "domain.yaml")
    s = PipelineSession(domain=domain, root=ROOT)
    s.load_table(path=str(tiny_csv), table_id="t")
    return s


def test_load_profile_fit_explain_actions(session: PipelineSession, tmp_path: Path):
    prof = session.profile("t")
    assert prof.n_rows == 200
    assert prof.suggested_label == "target"
    assert any(c.name == "note_text" for c in prof.columns)

    fit = session.fit_predict(
        "t",
        mode=BackendMode.mock,
        predictions_path=tmp_path / "predictions.json",
    )
    assert fit.backend == "mock"
    assert fit.n_train > 0 and fit.n_test > 0
    assert "accuracy" in fit.metrics
    assert (tmp_path / "predictions.json").is_file()

    expl = session.explain("t", mode=BackendMode.mock)
    assert expl.importances
    assert expl.method in {"permutation_importance", "unavailable"}

    actions = session.suggest_actions("t", max_rows=20)
    assert actions.items
    assert sum(actions.counts.values()) == len(actions.items)
    assert "Synthetic" in actions.disclaimer

    report = session.export_report("t", out_dir=str(tmp_path / "art"))
    md = Path(report.paths["markdown"])
    text = md.read_text(encoding="utf-8")
    assert "Metrics" in text
    assert "accuracy" in text


def test_compare_baseline(session: PipelineSession):
    cmp_ = session.compare_baseline("t", mode=BackendMode.mock)
    assert "accuracy" in cmp_.tabpfn_metrics
    assert "accuracy" in cmp_.baseline_metrics
    assert cmp_.narrative


def test_plus_without_token_falls_back(session: PipelineSession, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    fit = session.fit_predict("t", mode=BackendMode.plus)
    assert fit.backend == "mock"
    assert fit.warning


def test_run_demo_no_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TABPFN_TOKEN", raising=False)
    # Use a copy of domain + generated data under tmp
    domain_src = (ROOT / "domain.yaml").read_text(encoding="utf-8")
    (tmp_path / "domain.yaml").write_text(domain_src, encoding="utf-8")
    generate_synthetic_table(n=300, out=tmp_path / "data" / "synthetic_table.csv")
    result = run_demo(root=tmp_path, mode="mock", out_dir=tmp_path / "artifacts")
    assert result["backend"] == "mock"
    assert Path(result["report_path"]).is_file()
    report = Path(result["report_path"]).read_text(encoding="utf-8")
    assert "metric" in report.lower() or "accuracy" in report
    preds = json.loads(Path(result["predictions_path"]).read_text(encoding="utf-8"))
    assert isinstance(preds, list) and len(preds) > 0
