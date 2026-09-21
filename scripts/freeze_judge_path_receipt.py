#!/usr/bin/env python3
"""CLI: freeze Judge-path mock receipt (TABPFN_TOKEN= required empty)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.desk.judge_path_receipt import main, write_receipt  # noqa: F401

if __name__ == "__main__":
    main()
