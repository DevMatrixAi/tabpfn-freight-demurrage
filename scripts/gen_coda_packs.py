#!/usr/bin/env python3
"""CLI wrapper for coda pack synthetic CSV generation."""
from __future__ import annotations
try:
    from tabpfn_hack_core.demo.gen_coda_packs import main
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from tabpfn_hack_core.demo.gen_coda_packs import main
if __name__ == "__main__":
    main()
