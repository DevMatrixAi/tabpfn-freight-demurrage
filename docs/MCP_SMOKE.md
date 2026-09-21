# MCP stdio smoke (7 tools, mock-first)

Exercises the full MCP cookbook spine without a live TabPFN call.

```bash
# from repo root — empty token forces mock / no 429
TABPFN_TOKEN= python scripts/mcp_cookbook_demo.py
```

Expect: `OK — exercised 7 tools → artifacts/mcp_cookbook/cookbook_receipt.json`

| # | Tool | What the receipt proves |
| --- | --- | --- |
| 1 | `load_table` | Freight CSV loaded |
| 2 | `profile` | Cols + suggested group/time |
| 3 | `fit_predict` | Thinking kwargs + mock fallback metrics |
| 4 | `explain` | Top features |
| 5 | `export_report` | Report paths under `artifacts/` |
| 6 | `compare_baseline` | Judge card + Δ vs HistGBM |
| 7 | `suggest_actions` | Playbook counts (divert/rebook/…) |

Pytest: `tests/test_deep_showcase.py::test_mcp_cookbook_script` (also covered by `TABPFN_TOKEN= pytest -q`).

MCP server entry: `tabpfn-hack mcp` (stdio). Cookbook script calls the same `PipelineSession` / `TOOL_SPECS` the server exposes.

Frozen VO receipt: [`artifacts/freight-demurrage/mcp_mock_smoke_receipt.md`](../artifacts/freight-demurrage/mcp_mock_smoke_receipt.md) (`TABPFN_TOKEN= python scripts/freeze_mcp_mock_smoke_receipt.py`).
