# DEEP TabPFN-3.5 showcase notes (overnight)

Shipped on the demurrage spine for Prior Labs judges (2026-09-21 PT).


## How judges demo in 3 minutes

**Fastest honest path = local full desk** (deep panels live here). The public Vercel URL is a **mock stub only**.

| Min | Do this |
| --- | --- |
| 0:00 | `pip install -e ".[dev,desk]"` then `tabpfn-hack desk --host 127.0.0.1 --port 8765` |
| 0:30 | Open http://127.0.0.1:8765 → login `demo` / `demurrage` → **Run triage** (Mock) → risk cards + HistGBM Δ |
| 1:30 | Open **/eval** → **Run eval** → latency · Thinking · ablations · calibration panels |
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
  still render Thinking params, latency, ablations, and calibration.
- Do not claim TabArena #1 as *our* result — cite Prior Labs; our Δ is vs HistGBM on
  *this* demurrage table.


## 2026-09-21 PT — DEEP UI unpack + stress fixtures (overnight continue)

- Desk `/eval` + index showcase HTML shipped via `ensure_deep_templates` + zlib blobs (`deep_template_blobs_*.py`); eval_dashboard imports ensure on load.
- Thinking / Fast-vs-Plus latency / text+high-card ablations / calibration / denser HistGBM judge card remain wired.
- Stress: `fixtures/stress/` packed CSV (`_csv_blob_{a,b}.py` + `_unpack_missing_wide.py`); test unpacks if CSV missing.
- pytest: 68 passed. Repo stays private. No `.env` commits.

## 2026-09-21 PT — overnight polish

- Prefer **readable** `templates/eval.html` + `index.html` for judge repro; zlib blobs are fallback-only (`ensure_deep_templates` keeps sources with deep markers).
- Readable desk sources pushed for `app.py` / `eval_dashboard.py` / `desk_triage.py` (no zlib loaders).
- Empty/loading UX on `/eval` + risk board; README/PREVIEW/DEEP 3-minute judge path.
- pytest green; `scripts/mcp_cookbook_demo.py` documented.
