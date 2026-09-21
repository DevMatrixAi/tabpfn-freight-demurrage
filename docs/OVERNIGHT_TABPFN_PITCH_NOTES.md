# Overnight TabPFN-3.5 pitch notes (2026-09-21)

Sources: priorlabs.ai TabPFN-3.5 report, BeyondArena/TabArena claims, Thinking docs.

## Honest “whoa” surfaces we already show (keep naming these)

| Surface | Why Prior Labs cares | Where in our entry |
| --- | --- | --- |
| Plus / native messy text | BeyondArena text-rich lead; STRABLE/messy strings | terminal notes, weather text |
| High-cardinality IDs | BeyondArena high-card strength | BOL, container, ports |
| Missing values / raw frames | “data as-is” story | incomplete milestones |
| Thinking + group/time | non-i.i.d. / grouped / temporal | vessel_id + event_ts |
| Fast | latency path / A/B | Fast mode + eval page (when live) |
| Full predictive / risk scores | action thresholds from proba | late-fee risk → money moves |
| Baseline Δ | anti-wrapper | HistGBM comparison |
| Agent/MCP/robot API | not a thin hosted-MCP rewrap | suggest_actions + api_robot |

## Do not claim overnight (would get us dinged)

- Robots driving cranes / TOS control
- Live carrier APIs
- “#1 on TabArena” as *our* result (cite Prior Labs; our claim is Δ vs HistGBM on *this* table)
- 3D bin packing physics (stow-fit is a suggest head only)

## Pitch upgrades for v2.0 form (ship when eval unlocks)

Lead with: messy ERP-style freight table → TabPFN-3.5 family (Plus/Thinking/Fast) → $ action, with eval page showing all three vs HistGBM.

Judge one-liner: “We use TabPFN-3.5 the way BeyondArena says real tables look: text, high-card, missings, vessel groups over time — then we spend the prediction.”

## Optional Build asks (offline queue — no human ping)

1. Eval page labels: Plus / Thinking / Fast / HistGBM with one sentence each matching Prior docs  
2. One “raw DataFrame in” screenshot or log line for README  
3. thinking_effort visible when Thinking runs (if API exposes it)

## Shipped overnight (DEEP)

See [`docs/DEEP_SHOWCASE_v0.md`](DEEP_SHOWCASE_v0.md): Thinking effort + group/time narrative, `/eval` ablations + Fast/Plus latency + denser judge card, calibration bins, MCP 7-tool cookbook, stress missing/wide fixture.

## Overnight smoke note (2026-09-21 PT)

- `/eval` smoked locally through login → Run eval; the deep panels and small-n learning curve render.
- Deep-template fallback now preserves the learning-curve include when a clean checkout unpacks the zlib blob.
- Judge docs use `TABPFN_TOKEN=` for a deterministic mock path; repo remains private and `.env` stays untracked.
