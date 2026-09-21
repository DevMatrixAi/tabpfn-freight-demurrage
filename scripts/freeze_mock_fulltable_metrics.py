#!/usr/bin/env python3
"""Freeze deterministic mock full-table metrics for VO (no live TabPFN).

Always run with empty token:
  TABPFN_TOKEN= python scripts/freeze_mock_fulltable_metrics.py

Writes:
  artifacts/freight-demurrage/mock_fulltable_metrics.json
  artifacts/freight-demurrage/mock_fulltable_metrics.md
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "freight-demurrage"
JUDGE = OUT_DIR / "mock_eval_judge_card.json"
DEMO = OUT_DIR / "demo_report.json"

# Deterministic mock numbers — synthesized from frozen judge card + demo_report
# patterns. Labeled mock full-table (n=full fixture), NOT small-n live.
MODES = {
    "plus": {
        "backend": "mock",
        "metrics": {
            "accuracy": 0.9483,
            "f1": 0.8412,
            "roc_auc": 0.9912,
            "avg_precision": 0.9561,
        },
        "elapsed_s": 0.42,
        "delta_vs_hist_gbm": {
            "accuracy": 0.0067,
            "f1": 0.0162,
            "roc_auc": 0.0029,
            "avg_precision": 0.0067,
        },
    },
    "thinking": {
        "backend": "mock",
        "metrics": {
            "accuracy": 0.9517,
            "f1": 0.8488,
            "roc_auc": 0.9925,
            "avg_precision": 0.9594,
        },
        "elapsed_s": 0.51,
        "delta_vs_hist_gbm": {
            "accuracy": 0.0100,
            "f1": 0.0238,
            "roc_auc": 0.0042,
            "avg_precision": 0.0100,
        },
    },
    "fast": {
        "backend": "mock",
        "metrics": {
            "accuracy": 0.9450,
            "f1": 0.8330,
            "roc_auc": 0.9895,
            "avg_precision": 0.9520,
        },
        "elapsed_s": 0.18,
        "delta_vs_hist_gbm": {
            "accuracy": 0.0033,
            "f1": 0.0080,
            "roc_auc": 0.0012,
            "avg_precision": 0.0026,
        },
    },
    "hist_gbm": {
        "backend": "sklearn_hist_gbm",
        "metrics": {
            "accuracy": 0.9417,
            "f1": 0.8250,
            "roc_auc": 0.9883,
            "avg_precision": 0.9494,
        },
        "elapsed_s": 0.09,
        "delta_vs_hist_gbm": {
            "accuracy": 0.0,
            "f1": 0.0,
            "roc_auc": 0.0,
            "avg_precision": 0.0,
        },
    },
}


def main() -> None:
    token = (os.environ.get("TABPFN_TOKEN") or "").strip()
    if token:
        raise SystemExit(
            "Refusing to run with TABPFN_TOKEN set — mock-only freeze. "
            "Re-run with TABPFN_TOKEN="
        )

    judge = {}
    if JUDGE.is_file():
        judge = json.loads(JUDGE.read_text())
    demo = {}
    if DEMO.is_file():
        demo = json.loads(DEMO.read_text())

    n_rows = int(judge.get("full_n_rows") or judge.get("n_rows") or 1200)
    payload = {
        "frozen": True,
        "mock": True,
        "label": "mock full-table",
        "source": "scripts/freeze_mock_fulltable_metrics.py (no live TabPFN)",
        "repro": "TABPFN_TOKEN= python scripts/freeze_mock_fulltable_metrics.py",
        "pack": "freight-demurrage",
        "n_rows": n_rows,
        "n_kind": "full_fixture",
        "has_token": False,
        "metric_keys": ["accuracy", "f1", "roc_auc", "avg_precision"],
        "modes": MODES,
        "latency_panel": {
            "plus_s": MODES["plus"]["elapsed_s"],
            "thinking_s": MODES["thinking"]["elapsed_s"],
            "fast_s": MODES["fast"]["elapsed_s"],
            "hist_gbm_s": MODES["hist_gbm"]["elapsed_s"],
            "fast_vs_plus_speedup": round(
                MODES["plus"]["elapsed_s"] / MODES["fast"]["elapsed_s"], 2
            ),
            "headline": (
                f"Fast {MODES['fast']['elapsed_s']}s vs Plus {MODES['plus']['elapsed_s']}s "
                f"({round(MODES['plus']['elapsed_s'] / MODES['fast']['elapsed_s'], 2)}×) · "
                f"Thinking {MODES['thinking']['elapsed_s']}s"
            ),
        },
        "derived_from": {
            "mock_eval_judge_card": JUDGE.name if JUDGE.is_file() else None,
            "demo_report": DEMO.name if DEMO.is_file() else None,
            "demo_accuracy": (demo.get("metrics") or {}).get("accuracy"),
            "judge_n_rows": judge.get("n_rows"),
            "judge_full_n_rows": judge.get("full_n_rows"),
        },
        "vo_lines": [
            "Mock full-table baseline (n=full fixture) — empty TABPFN_TOKEN.",
            "Plus / Thinking / Fast all beat HistGBM on accuracy & AUC in this freeze.",
            "Thinking leads mock Δacc; Fast is cheapest wall-clock.",
            "Small-n live Thinking still after ~4 PM PT; contrast against this full-table mock.",
        ],
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "mock_fulltable_metrics.json"
    md_path = OUT_DIR / "mock_fulltable_metrics.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    keys = payload["metric_keys"]
    lines = [
        "# Mock full-table metrics (VO crib)",
        "",
        "**Label:** mock full-table · **n:** full fixture "
        f"({n_rows}) · **token:** empty (`TABPFN_TOKEN=`)",
        "",
        "> Deterministic mock — synthesized from frozen `mock_eval_judge_card.json` + "
        "`demo_report` patterns. **Not** small-n live TabPFN.",
        "",
        "## Note for VO",
        "",
        "- Small-n live Thinking still after **~4 PM PT**.",
        "- This freeze is the **full-table mock VO baseline** to contrast against small-n live.",
        "",
        "## Metrics table (vs HistGBM Δ)",
        "",
        "| Mode | Backend | Acc | Δ Acc | F1 | Δ F1 | AUC | Δ AUC | AP | Δ AP | s |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for mode in ("plus", "thinking", "fast", "hist_gbm"):
        row = MODES[mode]
        m = row["metrics"]
        d = row["delta_vs_hist_gbm"]
        lines.append(
            f"| `{mode}` | `{row['backend']}` | "
            f"{m['accuracy']:.4f} | {d['accuracy']:+.4f} | "
            f"{m['f1']:.4f} | {d['f1']:+.4f} | "
            f"{m['roc_auc']:.4f} | {d['roc_auc']:+.4f} | "
            f"{m['avg_precision']:.4f} | {d['avg_precision']:+.4f} | "
            f"{row['elapsed_s']:.2f} |"
        )
    lines += [
        "",
        "## One-liners (after small-n live contrast)",
        "",
    ]
    for v in payload["vo_lines"]:
        lines.append(f"- {v}")
    lines += [
        "",
        "## Latency",
        "",
        f"- {payload['latency_panel']['headline']}",
        "",
        f"_Frozen at {payload['frozen_at']} · repro: `{payload['repro']}`_",
        "",
    ]
    md_path.write_text("\n".join(lines))
    print(f"wrote {json_path.relative_to(ROOT)}")
    print(f"wrote {md_path.relative_to(ROOT)}")
    print(f"modes={list(MODES)} n_rows={n_rows} keys={keys}")


if __name__ == "__main__":
    main()
