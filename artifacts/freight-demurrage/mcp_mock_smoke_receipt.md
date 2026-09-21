# MCP 7-tool mock smoke receipt (VO crib)

**Token:** empty (`TABPFN_TOKEN=`) · **Mock only** · **All ok:** True

**Wall:** 0.583s · **Mock latency sum:** 272 ms

| # | Tool | ok | latency_ms (mock) |
| --- | --- | --- | ---: |
| 1 | `load_table` | ✅ | 12 |
| 2 | `profile` | ✅ | 18 |
| 3 | `fit_predict` | ✅ | 95 |
| 4 | `explain` | ✅ | 42 |
| 5 | `export_report` | ✅ | 28 |
| 6 | `compare_baseline` | ✅ | 55 |
| 7 | `suggest_actions` | ✅ | 22 |

## VO lines

- MCP 7-tool mock smoke · empty TABPFN_TOKEN · all ok.
- Tools: load_table → profile → fit_predict → explain → export_report → compare_baseline → suggest_actions.
- Mock latency sum ≈ 272 ms (VO crib; wall ~0.583s).
- Same PipelineSession / TOOL_SPECS the MCP stdio server exposes.

> Deterministic mock receipt — not live TabPFN. Freeze via `TABPFN_TOKEN= python scripts/freeze_mcp_mock_smoke_receipt.py`.

_Frozen at 2026-09-21T21:13:00Z · repro: `TABPFN_TOKEN= python scripts/freeze_mcp_mock_smoke_receipt.py`_
