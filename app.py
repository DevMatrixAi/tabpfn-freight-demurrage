"""Vercel / container ASGI entry — re-exports the freight demurrage desk app.

Mock-first: works without TABPFN_TOKEN. Demo login: demo / demurrage.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apps.desk.app import app  # noqa: E402

__all__ = ["app"]
