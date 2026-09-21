# Live small-n Thinking take (n=60) — **429 fallback**

**Status:** Prior Labs **HTTP 429** daily limit · fit fell back to **mock** · token was SET  
**Reset:** 2026-09-22 00:00:00 UTC (~5:00 PM PT Sep 21 if PDT; check local)  
**When:** 2026-09-21T23:30:59.326748+00:00

| | |
| --- | --- |
| sample_n | 60 / 1200 full |
| intended mode | Thinking (medium) |
| actual backend | mock (client fallback after 429) |
| fit wall | 2.219s |
| compare wall | 0.864s |
| metrics (mock) | `{"accuracy": 0.8333333333333334, "f1": 0.0, "roc_auc": 1.0, "avg_precision": 1.0}` |

**Preflight:** `--live-check` green (token + n=60).  
**Human:** not needed for re-paste — token OK. Retry live after Prior Labs daily reset.  
**VO:** still use [`mock_fulltable_metrics.md`](mock_fulltable_metrics.md) until a real live Thinking receipt lands.
