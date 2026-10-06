<!-- TIP_SHA_PIN_START -->
**Judged version:** git tag `submit` · clean12 Late Fee Control face · CONT-000121 showcase · [video](https://youtu.be/_aIq96WwLF0) · [judge_path_mock_receipt.md](../artifacts/freight-demurrage/judge_path_mock_receipt.md)

**First-screen gallery:**

| Login | Home | Desk | Eval |
| --- | --- | --- | --- |
| ![login](images/judge/login.svg) | ![home](images/judge/home.svg) | ![desk](images/judge/desk.svg) | ![eval](images/judge/eval.svg) |
<!-- TIP_SHA_PIN_END -->
**Dry-run timing (mock):** [`artifacts/freight-demurrage/judge_path_dryrun_timing.md`](../artifacts/freight-demurrage/judge_path_dryrun_timing.md) — wall login→eval ~0.34s (feature freeze).


# Judge path — 3 minutes (offline mock)

**Honest path = local full desk.** The Vercel URL is a login + sample-ticker stub only.

Credentials: `demo` / `demurrage`. Never commit `.env`. Keep `TABPFN_TOKEN=` empty on these commands so mock stays deterministic (no live 429s).

| Min | Do this |
| --- | --- |
| 0:00 | `pip install -e ".[dev,desk]"` then `TABPFN_TOKEN= tabpfn-hack desk --host 127.0.0.1 --port 8765` |
| 0:30 | http://127.0.0.1:8765 → login → **Run triage** (Mock) → money-at-risk cards + HistGBM Δ · star **CONT-000121** |
| 1:30 | Open **/eval** → **Run eval** → Plus/Thinking/Fast vs HistGBM, latency, ablations, calibration, **small-n learning curve** |
| 2:20 | Optional: `TABPFN_TOKEN= python scripts/robot_api_smoke.py` (robot/TMS health+triage) |
| 2:30 | Optional: `TABPFN_TOKEN= python scripts/mcp_cookbook_demo.py` (7 tools) · see [`MCP_SMOKE.md`](MCP_SMOKE.md) · `TABPFN_TOKEN= pytest -q` |

## Clean12 numbers (reported face)

Method: **12 kept columns**, 5 folds grouped by vessel, seed 42. Columns that nearly gave the answer away are removed from what the models see.

| | AUC | Net saved at $300/action |
| --- | ---: | ---: |
| TabPFN-3.5 Plus | **0.911** | **$595,310** |
| HistGBM (scikit-learn's standard gradient-boosting model) | 0.873 | $435,587 |
| Perfect foresight | | $914,480 |

At $300 per action, Plus saves **$595,310** vs HistGBM **$435,587** — **65.1%** vs **47.6%** of the $914,480 perfect forecast.

**What the desk flags:** 195 actions hold **$708,152** of the **$1,273,564** in possible late fees (total possible fees, not a savings claim).

**Star container:** CONT-000121 — 26.80% chance, $11,308 fee, $3,031 likely cost, desk says **Push for early pickup**.

**What to point at (50% showcase):** text / high-card / missings on vessel tables · Thinking group/time narrative · Plus Δ vs HistGBM · playbook money moves · robot API same actions.

**Stress missingness (optional):** load `fixtures/stress/missing_wide_demurrage.csv` (or unpack via `fixtures/stress/_unpack_missing_wide.py`) — desk shows a missingness panel when NaNs are present.

More depth: [`DEEP_SHOWCASE.md`](DEEP_SHOWCASE.md) · preview honesty: [`PREVIEW.md`](PREVIEW.md).

## Live budget (after API reset)

Prefer **small-n live** Thinking/Plus: desk `sample_n` 40–80, or env `TABPFN_DEV_N=60`.
Full-table mock anytime (`TABPFN_TOKEN=`). One full live Thinking pass near shoot/submit only.

**Preflight:** `TABPFN_TOKEN= python scripts/preflight_live_budget.py --mock` (or `--live-check` after API reset) before small-n Thinking — blocks full-table live.

**VO artifacts:** `artifacts/freight-demurrage/` (`mock_fulltable_metrics`, `judge_path_mock_receipt`, `mcp_mock_smoke_receipt`).


## First-screen screenshots (mock UI frames)

Labeled **mock UI frames** for the 3-minute path (not live browser captures). Dark theme matches the desk crib.

| Screen | Image |
| --- | --- |
| Login | ![Login](images/judge/login.svg) |
| Home desks | ![Home](images/judge/home.svg) |
| Ops board | ![Desk](images/judge/desk.svg) |
| /eval pre-run | ![Eval](images/judge/eval.svg) |

Also: Settings at `/settings` (demo prefs · mode badge · judge crib).
