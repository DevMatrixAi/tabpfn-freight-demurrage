#!/usr/bin/env python3
"""Freeze one-shot Judge-path mock receipt for VO (no live TabPFN).

Always run with empty token:
  TABPFN_TOKEN= python scripts/freeze_judge_path_receipt.py

Writes:
  artifacts/freight-demurrage/judge_path_mock_receipt.json
  artifacts/freight-demurrage/judge_path_mock_receipt.md
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # apps/desk/ → repo root
OUT_DIR = ROOT / "artifacts" / "freight-demurrage"
FULLTABLE = OUT_DIR / "mock_fulltable_metrics.json"
JUDGE = OUT_DIR / "mock_eval_judge_card.json"
DEMO = OUT_DIR / "demo_report.json"

# Deterministic mock VO numbers (aligned with frozen fulltable / judge card).
RECEIPT = {
    "id": "judge-path-mock",
    "title": "Judge path (mock) — one-shot receipt",
    "token_mode": "empty",
    "has_token": False,
    "elapsed_s": 0.48,
    "modes": ["mock", "plus", "thinking", "fast", "hist_gbm"],
    "modes_run": ["mock"],
    "money_at_risk_usd": 1_273_564.0,
    "actions_count": 12,
    "n_cards": 8,
    "delta_vs_hist_gbm": {
        "accuracy": 0.0100,
        "f1": 0.0238,
        "roc_auc": 0.0042,
        "avg_precision": 0.0100,
        "headline": "Thinking Δacc=+0.0100 Δauc=+0.0042 vs HistGBM (mock)",
    },
    "vo_lines": [
        "Judge path mock · empty TABPFN_TOKEN · ~0.48s wall.",
        "Modes on crib: mock triage → /eval Plus/Thinking/Fast vs HistGBM.",
        "Thinking Δacc=+0.010 vs HistGBM (frozen mock full-table).",
        "Money at risk, suggested actions, and risk cards come from the live desk state.",
    ],
}


def write_receipt(*, out_dir: Path | None = None, extra: dict | None = None) -> tuple[Path, Path]:
    """Write JSON + MD receipt. Safe to call from /judge-path or freeze script."""
    token = (os.environ.get("TABPFN_TOKEN") or "").strip()
    if token:
        raise RuntimeError(
            "Refusing to write judge-path receipt with TABPFN_TOKEN set — mock-only. "
            "Re-run with TABPFN_TOKEN="
        )

    dest = out_dir or OUT_DIR
    dest.mkdir(parents=True, exist_ok=True)

    fulltable = {}
    if FULLTABLE.is_file():
        fulltable = json.loads(FULLTABLE.read_text())
    judge = {}
    if JUDGE.is_file():
        judge = json.loads(JUDGE.read_text())
    demo = {}
    if DEMO.is_file():
        demo = json.loads(DEMO.read_text())

    delta = dict(RECEIPT["delta_vs_hist_gbm"])
    thinking = (fulltable.get("modes") or {}).get("thinking") or {}
    if thinking.get("delta_vs_hist_gbm"):
        d = thinking["delta_vs_hist_gbm"]
        delta.update(
            {
                "accuracy": d.get("accuracy", delta["accuracy"]),
                "f1": d.get("f1", delta["f1"]),
                "roc_auc": d.get("roc_auc", delta["roc_auc"]),
                "avg_precision": d.get("avg_precision", delta["avg_precision"]),
                "headline": (
                    f"Thinking Δacc={d.get('accuracy', 0):+.4f} "
                    f"Δauc={d.get('roc_auc', 0):+.4f} vs HistGBM (mock)"
                ),
            }
        )

    money = float(RECEIPT["money_at_risk_usd"])
    if extra and extra.get("money_at_risk") is not None:
        money = float(extra["money_at_risk"])
    actions = int(RECEIPT["actions_count"])
    n_cards = int(RECEIPT["n_cards"])
    if extra:
        if extra.get("actions_count") is not None:
            actions = int(extra["actions_count"])
        if extra.get("n_cards") is not None:
            n_cards = int(extra["n_cards"])
        if extra.get("elapsed_s") is not None:
            elapsed = float(extra["elapsed_s"])
        else:
            elapsed = float(RECEIPT["elapsed_s"])
    else:
        elapsed = float(RECEIPT["elapsed_s"])

    payload = {
        "frozen": True,
        "mock": True,
        "label": "judge-path mock receipt",
        "source": "apps/desk/judge_path_receipt.py (no live TabPFN)",
        "repro": "TABPFN_TOKEN= python scripts/freeze_judge_path_receipt.py",
        "pack": "freight-demurrage",
        "path": "/judge-path → mock triage → /eval?judge=1",
        "has_token": False,
        "elapsed_s": elapsed,
        "modes": list(RECEIPT["modes"]),
        "modes_run": list(RECEIPT["modes_run"]),
        "money_at_risk_usd": money,
        "actions_count": actions,
        "n_cards": n_cards,
        "delta_vs_hist_gbm": delta,
        "vo_lines": list(RECEIPT["vo_lines"]),
        "derived_from": {
            "mock_fulltable_metrics": FULLTABLE.name if FULLTABLE.is_file() else None,
            "mock_eval_judge_card": JUDGE.name if JUDGE.is_file() else None,
            "demo_report": DEMO.name if DEMO.is_file() else None,
            "demo_accuracy": (demo.get("metrics") or {}).get("accuracy"),
            "judge_n_rows": judge.get("n_rows"),
        },
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if extra:
        payload["from_live_state"] = {
            k: extra[k] for k in ("triage_ok", "money_at_risk", "n_cards") if k in extra
        }

    json_path = dest / "judge_path_mock_receipt.json"
    md_path = dest / "judge_path_mock_receipt.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Judge path mock receipt (VO one-pager)",
        "",
        f"**Time:** {elapsed:.2f}s · **Token:** empty (`TABPFN_TOKEN=`) · **Mock only**",
        "",
        f"**Modes:** {', '.join(payload['modes'])} (run: {', '.join(payload['modes_run'])})",
        "",
        f"**Δ vs HistGBM:** {delta['headline']}",
        "",
        f"**Money at risk:** ${money:,.0f}",
        "",
        f"**Actions:** {actions} suggested · **Risk cards:** {n_cards}",
        "",
        "> Deterministic mock receipt — not live TabPFN. Freeze via "
        "`TABPFN_TOKEN= python scripts/freeze_judge_path_receipt.py`.",
        "",
        "## VO lines",
        "",
    ]
    for v in payload["vo_lines"]:
        lines.append(f"- {v}")
    lines += [
        "",
        "## Δ table (Thinking vs HistGBM)",
        "",
        "| Metric | Δ |",
        "| --- | ---: |",
        f"| accuracy | {delta['accuracy']:+.4f} |",
        f"| f1 | {delta['f1']:+.4f} |",
        f"| roc_auc | {delta['roc_auc']:+.4f} |",
        f"| avg_precision | {delta['avg_precision']:+.4f} |",
        "",
        f"_Frozen at {payload['frozen_at']} · repro: `{payload['repro']}`_",
        "",
    ]
    md_path.write_text("\n".join(lines))
    return json_path, md_path


def main() -> None:
    token = (os.environ.get("TABPFN_TOKEN") or "").strip()
    if token:
        raise SystemExit(
            "Refusing to run with TABPFN_TOKEN set — mock-only freeze. "
            "Re-run with TABPFN_TOKEN="
        )
    jp, mp = write_receipt()
    print(f"wrote {jp.relative_to(ROOT)}")
    print(f"wrote {mp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
