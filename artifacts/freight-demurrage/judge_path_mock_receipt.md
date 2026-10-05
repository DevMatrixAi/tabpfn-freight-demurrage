# Judge path mock receipt (VO one-pager)

**Time:** 0.48s · **Token:** empty (`TABPFN_TOKEN=`) · **Mock only**

**Modes:** mock, plus, thinking, fast, hist_gbm (run: mock)

**Δ vs HistGBM:** Thinking Δacc=+0.0100 Δauc=+0.0042 vs HistGBM (mock)

**Money at risk:** $1,270,000

**Actions:** 12 suggested · **Risk cards:** 8

> Deterministic mock receipt — not live TabPFN. Freeze via `TABPFN_TOKEN= python scripts/freeze_judge_path_receipt.py`.

## VO lines

- Judge path mock · empty TABPFN_TOKEN · ~0.48s wall.
- Modes on crib: mock triage → /eval Plus/Thinking/Fast vs HistGBM.
- Thinking Δacc=+0.010 vs HistGBM (frozen mock full-table).
- Money at risk ≈ $1.27M · 12 suggested actions · 8 risk cards.

## Δ table (Thinking vs HistGBM)

| Metric | Δ |
| --- | ---: |
| accuracy | +0.0100 |
| f1 | +0.0238 |
| roc_auc | +0.0042 |
| avg_precision | +0.0100 |

_Frozen at 2026-10-05T05:14:45Z · repro: `TABPFN_TOKEN= python scripts/freeze_judge_path_receipt.py`_
