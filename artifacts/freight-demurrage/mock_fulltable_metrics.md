# Mock full-table metrics (VO crib)

**Label:** mock full-table · **n:** full fixture (1200) · **token:** empty (`TABPFN_TOKEN=`)

> Deterministic mock — synthesized from frozen `mock_eval_judge_card.json` + `demo_report` patterns. **Not** small-n live TabPFN.

## Note for VO

- Small-n live Thinking still after **~4 PM PT**.
- This freeze is the **full-table mock VO baseline** to contrast against small-n live.

## Metrics table (vs HistGBM Δ)

| Mode | Backend | Acc | Δ Acc | F1 | Δ F1 | AUC | Δ AUC | AP | Δ AP | s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `plus` | `mock` | 0.9483 | +0.0067 | 0.8412 | +0.0162 | 0.9912 | +0.0029 | 0.9561 | +0.0067 | 0.42 |
| `thinking` | `mock` | 0.9517 | +0.0100 | 0.8488 | +0.0238 | 0.9925 | +0.0042 | 0.9594 | +0.0100 | 0.51 |
| `fast` | `mock` | 0.9450 | +0.0033 | 0.8330 | +0.0080 | 0.9895 | +0.0012 | 0.9520 | +0.0026 | 0.18 |
| `hist_gbm` | `sklearn_hist_gbm` | 0.9417 | +0.0000 | 0.8250 | +0.0000 | 0.9883 | +0.0000 | 0.9494 | +0.0000 | 0.09 |

## One-liners (after small-n live contrast)

- Mock full-table baseline (n=full fixture) — empty TABPFN_TOKEN.
- Plus / Thinking / Fast all beat HistGBM on accuracy & AUC in this freeze.
- Thinking leads mock Δacc; Fast is cheapest wall-clock.
- Small-n live Thinking still after ~4 PM PT; contrast against this full-table mock.

## Latency

- Fast 0.18s vs Plus 0.42s (2.33×) · Thinking 0.51s

_Frozen at 2026-09-21T20:40:51Z · repro: `TABPFN_TOKEN= python scripts/freeze_mock_fulltable_metrics.py`_
