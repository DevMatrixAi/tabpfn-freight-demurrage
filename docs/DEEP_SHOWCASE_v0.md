# DEEP TabPFN-3.5 showcase notes (overnight)

Shipped on the demurrage spine for Prior Labs judges (2026-09-21 PT).


## How judges demo in 3 minutes

**Fastest honest path = local full desk** (deep panels live here). The public Vercel URL is a **mock stub only**.

| Min | Do this |
| --- | --- |
| 0:00 | `pip install -e ".[dev,desk]"` then `tabpfn-hack desk --host 127.0.0.1 --port 8765` |
| 0:30 | Open http://127.0.0.1:8765 → login `demo` / `demurrage` → **Run triage** (Mock) → risk cards + HistGBM Δ |
| 1:30 | Open **/eval** → **Run eval** → latency · Thinking · ablations · calibration · small-n curve |
| 2:30 | Optional: `python scripts/mcp_cookbook_demo.py` (7 MCP tools) · `pytest` · `tabpfn-hack demo --mode mock` |

**Stub URL honesty:** [https://tabpfn-freight-demurrage.vercel.app](https://tabpfn-freight-demurrage.vercel.app) shows login + sample ticker only — **not** Jinja `/eval` or robot triage. Full TabPFN desk stays local (or Docker/Fly/Railway). Repo stays **private**. Never commit `.env`.

## Surfaces (2–4 strongest)

1. **Thinking group/time narrative** — `thinking_effort` wired through client/MCP;
   desk + `/eval` show `group_col=vessel_id`, `group_time_col=event_ts`, effort badge,
   and a Thinking showcase strip. Mock still emits the narrative when token is absent.
2. **Text / high-card ablations on `/eval`** — full vs drop-text vs drop-high-card vs both
   under the same HistGBM mock split (`core/ablations.py`).
3. **Fast vs Plus latency panel + denser HistGBM judge card** — wall-clock per mode on
   `/eval`; `compare_baseline` returns a richer `narrative` + structured `judge_card`.
4. **Calibration display + MCP cookbook** — Brier/ECE reliability bins from `proba_1`
   (`core/calibration.py`); `scripts/mcp_cookbook_demo.py` exercises all **7** tools.
5. **Small-n learning curve (new)** — Acc@n mock HistGBM curve on demurrage features
   (`core/learning_curve.py`); frames TabPFN few-shot when `TABPFN_TOKEN` is set.

Bonus: `fixtures/stress/missing_wide_demurrage.csv` (missingness + 40 noise cols).

## Run

```bash
pip install -e ".[dev,desk]"
pytest
python scripts/mcp_cookbook_demo.py
tabpfn-hack desk --host 127.0.0.1 --port 8765   # /eval → Run eval
```

## Honesty

- Live Plus/Thinking/Fast need `TABPFN_TOKEN`; without it modes fall back to mock but
  still render Thinking params, latency, ablations, calibration, and the small-n curve.
- Do not claim TabArena #1 as *our* result — cite Prior Labs; our Δ is vs HistGBM on
  *this* demurrage table.

## 2026-09-21 PT overnight continue — judge repro + small-n curve

- Replaced zlib-packed remote desk modules with **readable** sources (split for MCP size):
  `desk_triage.py` + `desk_triage_apply.py`, `eval_dashboard.py` + `eval_runner.py`.
  Prefer checked-in HTML over zlib blob fallbacks.
- New TabPFN-deep surface: **small-n learning curve** on `/eval`.
- pytest green; demurrage spine intact; repo stays **private**; never commit `.env`.
