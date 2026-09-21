"""Coda pack generators (equipment-size + inland-mode + air-freight + stow-fit)."""
from __future__ import annotations

import argparse

from tabpfn_hack_core.demo._gen_air import gen_air_freight
from tabpfn_hack_core.demo._gen_equipment import ROOT, gen_equipment_size
from tabpfn_hack_core.demo._gen_inland import gen_inland_mode
from tabpfn_hack_core.demo._gen_stow import gen_stow_fit

# Re-exports for tests / scripts
__all__ = [
    "gen_equipment_size",
    "gen_inland_mode",
    "gen_air_freight",
    "gen_stow_fit",
    "main",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pack",
        choices=["equipment-size", "inland-mode", "air-freight", "stow-fit", "all"],
        default="all",
    )
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
    if args.pack in ("air-freight", "all"):
        out = ROOT / "domains" / "air-freight" / "data" / "shipments.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        df = gen_air_freight(n=args.n, seed=44)
        df.to_csv(out, index=False)
        print(f"Wrote {out} ({len(df)} rows, pos={df['miss_connection_risk'].mean():.2f})")
    if args.pack in ("stow-fit", "all"):
        out = ROOT / "domains" / "stow-fit" / "data" / "shipments.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        df = gen_stow_fit(n=args.n, seed=45)
        df.to_csv(out, index=False)
        print(f"Wrote {out} ({len(df)} rows, pos={df['fit_risk'].mean():.2f})")


if __name__ == "__main__":
    main()
