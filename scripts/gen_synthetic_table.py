#!/usr/bin/env python3
"""Generate synthetic_table.csv for the generic domain pack."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--out", type=Path, default=Path("data/synthetic_table.csv"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Prefer installed package; fall back to path injection for raw script use
    try:
        from tabpfn_hack_core.demo.run_demo import generate_synthetic_table
    except ImportError:
        import sys

        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "src"))
        from tabpfn_hack_core.demo.run_demo import generate_synthetic_table

    path = generate_synthetic_table(n=args.n, out=args.out, seed=args.seed)
    print(f"Wrote {path} ({args.n} rows)")


if __name__ == "__main__":
    main()
