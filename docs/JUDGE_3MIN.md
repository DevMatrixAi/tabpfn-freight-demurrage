# Judge path — 3 minutes (offline mock)

**Honest path = local full desk.** The Vercel URL is a login + sample-ticker stub only.

Credentials: `demo` / `demurrage`. Never commit `.env`. Keep `TABPFN_TOKEN=` empty on these commands so mock stays deterministic (no live 429s).

| Min | Do this |
| --- | --- |
| 0:00 | `pip install -e ".[dev,desk]"` then `TABPFN_TOKEN= tabpfn-hack desk --host 127.0.0.1 --port 8765` |
| 0:30 | http://127.0.0.1:8765 → login → **Run triage** (Mock) → money-at-risk cards + HistGBM Δ |
| 1:30 | Open **/eval** → **Run eval** → Plus/Thinking/Fast vs HistGBM, latency, ablations, calibration, **small-n learning curve** |
| 2:30 | Optional: `TABPFN_TOKEN= python scripts/mcp_cookbook_demo.py` (7 tools) · see [`MCP_SMOKE.md`](MCP_SMOKE.md) · `TABPFN_TOKEN= pytest -q` |

**What to point at (50% showcase):** text / high-card / missings on vessel tables · Thinking group/time narrative · Plus Δacc vs HistGBM · playbook money moves · robot API same actions.

**Stress missingness (optional):** load `fixtures/stress/missing_wide_demurrage.csv` (or unpack via `fixtures/stress/_unpack_missing_wide.py`) — desk shows a missingness panel when NaNs are present.

More depth: [`DEEP_SHOWCASE_v0.md`](DEEP_SHOWCASE_v0.md) · preview honesty: [`PREVIEW.md`](PREVIEW.md).
