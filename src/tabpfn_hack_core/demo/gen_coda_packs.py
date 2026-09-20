"""Coda pack generators (equipment-size + inland-mode)."""
from __future__ import annotations
from tabpfn_hack_core.demo._gen_equipment import gen_equipment_size
from tabpfn_hack_core.demo._gen_inland import gen_inland_mode
from tabpfn_hack_core.demo._gen_equipment import ROOT
import argparse

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", choices=["equipment-size", "inland-mode", "all"], default="all")
    parser.add_argument("--n", type=int, default=600)
    args = parser.parse_args()
    if args.pack in ("equipment-size", "all"):
        out = ROOT / "domains" / "equipment-size" / "data" / "bookings.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        df = gen_equipment_size(n=args.n, seed=42)
        df.to_csv(out, index=False)
        print(f"Wrote {out} ({len(df)} rows, pos={df['special_equip_fit'].mean():.2f})")
    if args.pack in ("inland-mode", "all"):
        out = ROOT / "domains" / "inland-mode" / "data" / "moves.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        df = gen_inland_mode(n=args.n, seed=43)
        df.to_csv(out, index=False)
        print(f"Wrote {out} ({len(df)} rows, pos={df['prefer_rail'].mean():.2f})")

if __name__ == "__main__":
    main()
