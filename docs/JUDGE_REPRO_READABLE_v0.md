# Judge repro — readable desk sources

Overnight continue (2026-09-21 PT): replace zlib-packed `apps/desk/app.py`, `eval_dashboard.py`, `desk_triage.py` with readable modules (split when MCP size requires).

- Prefer checked-in Python over `exec(zlib.decompress(...))` loaders.
- Demurrage spine intact; repo stays **private**; never commit `.env`.
- Local verify: `pytest` + `tabpfn-hack desk`.
