"""Readable desk FastAPI implementation (judge repro).

Loads ``app_impl_part_a`` then ``app_impl_part_b`` into this module globals
so MCP pushes stay under size limits while remaining fully readable.
"""
from __future__ import annotations

from pathlib import Path

_DIR = Path(__file__).resolve().parent
for _name in ("app_impl_part_a.py", "app_impl_part_b.py"):
    _path = _DIR / _name
    exec(compile(_path.read_text(encoding="utf-8"), str(_path), "exec"), globals())
del _DIR, _name, _path
