# 3-minute judge runbook (mock OK)

**Login:** http://127.0.0.1:8765 · `demo` / `demurrage`  
**Preview stub:** https://tabpfn-freight-demurrage.vercel.app (prefer local for full desk)  
**Token:** empty = mock; after reset use `sample_n` 40–80 for live Thinking.

| Time | Click | Say / show |
| --- | --- | --- |
| 0:00 | Login | Shipper money desk — stop late fees before the invoice. |
| 0:20 | Home → late-fee desk | Crib: money at risk / late-fee risk / moves / Δ |
| 0:40 | Fixture → Plus → Thinking → run | Messy table → TabPFN |
| 1:10 | Charts + HistGBM Δ | Better than a normal model. |
| 1:30 | Thinking timeline + effort | Vessel over time. |
| 1:50 | Risk card → action drawer | Money move (move / rebook / pay fee / cancel / watch). |
| 2:10 | Stream + re-score (optional) | Live update. |
| 2:25 | Compare `/eval` | Plus / Thinking / Fast vs HistGBM + ablations + calibration. |
| 2:50 | Robot / MCP note | Same actions for humans or robots. |
| 3:00 | Stop | |

Long form: `docs/DEMO_90S_AND_FORM_v2.md`.
