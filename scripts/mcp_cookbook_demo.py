#!/usr/bin/env python3
"""Exercise all 7 MCP tools on the freight-demurrage spine (mock-first).

Usage (from repo root):
  python scripts/mcp_cookbook_demo.py
  python -m scripts.mcp_cookbook_demo

Does not need TABPFN_TOKEN. Writes a short JSON receipt under artifacts/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tabpfn_hack_core.core.calibration import calibration_from_predictions
from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode, TOOL_SPECS
import os

def _prefer_mock() -> BackendMode:
    """Avoid live Thinking spam when TABPFN_TOKEN is unset/empty."""
    if os.environ.get("TABPFN_TOKEN", "").strip():
        return BackendMode.thinking
    return BackendMode.mock


def main() -> int:
    domain_path = ROOT / "domains" / "freight-demurrage" / "domain.yaml"
    csv_path = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"
    domain = load_domain(domain_path)
    sess = PipelineSession(domain=domain, root=ROOT)

    receipt: dict = {"tools": [t["name"] for t in TOOL_SPECS], "steps": []}

    # 1 load_table
    load = sess.load_table(path=str(csv_path), table_id="freight")
    receipt["steps"].append({"tool": "load_table", "ok": True, "n_rows": load.n_rows})

    # 2 profile
    prof = sess.profile("freight", sample_rows=3)
    receipt["steps"].append(
        {
            "tool": "profile",
            "ok": True,
            "n_cols": len(prof.columns),
            "suggested_group_col": prof.suggested_group_col,
            "suggested_time_col": prof.suggested_time_col,
        }
    )

    # 3 fit_predict (Thinking kwargs visible even on mock fallback)
    fit = sess.fit_predict(
        "freight",
        mode=BackendMode.mock,
        test_size=0.25,
        group_col=domain.group_col,
        group_time_col=domain.time_col,
        thinking_effort="high",
    )
    # Force thinking narrative path for showcase receipt
    think_mode = _prefer_mock()
    fit_think = sess.fit_predict(
        "freight",
        mode=think_mode,
        test_size=0.25,
        group_col=domain.group_col,
        group_time_col=domain.time_col,
        thinking_effort="high",
    )
    receipt["steps"].append(
        {
            "tool": "fit_predict",
            "ok": True,
            "mode": fit_think.mode.value,
            "backend": fit_think.backend,
            "thinking_effort": fit_think.thinking_effort,
            "group_col": fit_think.group_col or domain.group_col,
            "group_time_col": fit_think.group_time_col or domain.time_col,
            "thinking_narrative": fit_think.thinking_narrative,
            "metrics": fit_think.metrics,
        }
    )

    # 4 explain
    expl = sess.explain("freight", mode=BackendMode.mock, max_features=8)
    receipt["steps"].append(
        {
            "tool": "explain",
            "ok": True,
            "method": expl.method,
            "top": [i.get("feature") for i in expl.importances[:5]],
        }
    )

    # 5 export_report (TOOL_SPECS order)
    out = ROOT / "artifacts" / "mcp_cookbook"
    out.mkdir(parents=True, exist_ok=True)
    rep = sess.export_report("freight", title="MCP cookbook demurrage demo", out_dir=str(out))
    receipt["steps"].append({"tool": "export_report", "ok": True, "paths": rep.paths})

    # 6 compare_baseline
    cmp_ = sess.compare_baseline("freight", mode=BackendMode.mock)
    receipt["steps"].append(
        {
            "tool": "compare_baseline",
            "ok": True,
            "narrative": cmp_.narrative,
            "judge_card": cmp_.judge_card,
            "delta": cmp_.delta,
        }
    )

    # 7 suggest_actions
    acts = sess.suggest_actions("freight", max_rows=20)
    receipt["steps"].append(
        {
            "tool": "suggest_actions",
            "ok": True,
            "counts": acts.counts,
            "n_items": len(acts.items),
        }
    )

    receipt["calibration"] = calibration_from_predictions(sess.last_predictions)
    receipt["tool_count"] = len(receipt["steps"])
    assert receipt["tool_count"] == 7, receipt["tool_count"]
    assert [s["tool"] for s in receipt["steps"]] == [t["name"] for t in TOOL_SPECS]

    dest = out / "cookbook_receipt.json"
    dest.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    print(f"OK — exercised {receipt['tool_count']} tools → {dest}")
    print(f"Thinking narrative: {fit_think.thinking_narrative}")
    print(f"Judge headline: {(cmp_.judge_card or {}).get('headline')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
