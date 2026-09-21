# DEEP TabPFN-3.5 showcase notes (overnight)

Shipped on the demurrage spine for Prior Labs judges (2026-09-21 PT).

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
