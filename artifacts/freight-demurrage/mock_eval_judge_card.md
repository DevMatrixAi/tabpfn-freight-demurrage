# Frozen mock judge-card snapshot

**Purpose:** Video VO / repro when live TabPFN or `/eval` is unavailable.  
**Mode:** mock-only (`TABPFN_TOKEN` empty). Not a live capture.

## Headline

- **Judge card:** fast \u0394acc=+0.000 \u0394auc=+0.000 vs HistGBM
- **Latency:** Fast 0.11s vs Plus 0.141s (1.28\u00d7) \u00b7 Thinking 0.126s
- **Pack:** Freight demurrage (spine) (`freight-demurrage`)
- **Rows:** 200 (full 1200)

## VO crib

- Frozen mock /eval judge card \u2014 empty TABPFN_TOKEN.
- fast \u0394acc=+0.000 \u0394auc=+0.000 vs HistGBM
- Fast 0.11s vs Plus 0.141s (1.28\u00d7) \u00b7 Thinking 0.126s
- Text / high-card ablations + calibration bins for BeyondArena story.

## Files

- `artifacts/freight-demurrage/mock_eval_judge_card.json` \u2014 full structured `/eval` payload subset
- This markdown \u2014 human VO crib

## Repro

```bash
TABPFN_TOKEN= pytest -q tests/test_column_chips_shortcuts_artifact.py
# or: login \u2192 POST /eval/run \u2192 compare to frozen JSON keys judge_card / latency_panel
```
