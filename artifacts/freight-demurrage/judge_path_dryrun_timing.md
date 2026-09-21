# Judge-path mock dry-run timing (feature freeze)

**Mode:** mock (`TABPFN_TOKEN=` empty) · **not** a live Thinking take · tip freeze `db42e97`.

| Step | seconds |
| --- | ---: |
| Login | 0.004 |
| POST `/judge-path` (mock triage) | 0.321 |
| GET `/eval` | 0.015 |
| **Wall (login→eval)** | **0.34** |

- Redirect: `/eval?judge=1`
- Live budget: default `TABPFN_DEV_N=60`; preflight blocks full-table live.
- Post-4 human: token → `scripts/preflight.sh --live-check` → one small-n Thinking take → VO from `mock_fulltable_metrics.md`.
- Recorded: 2026-09-21T21:24:13.848906+00:00
