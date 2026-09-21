"""Stow-fit coda pack synthetic generator (tabular suggest head, not 3D packer)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
MODES = ["dry20", "dry40", "hc40", "reefer", "air_belly", "ltl_truck"]


def gen_stow_fit(n: int = 600, seed: int = 45) -> pd.DataFrame:
    """Cargo rows: predict fit_risk. Multi-client/carrier are fixture labels."""
    rng = np.random.default_rng(seed)
    origins = ["CNSHA", "CNNGB", "KRPUS", "SGSIN", "NLRTM", "USLAX", "USCHI", "DEHAM"]
    dests = ["USLAX", "USNYC", "USCHI", "NLRTM", "GBFXT", "DEHAM", "USDFW", "USATL"]
    carriers = ["MSK", "MSC", "COSCO", "HPL", "ONE", "YML", "EMC", "ZIM", "FDX", "UPS"]
    clients = [f"CLT-{i:03d}" for i in range(1, 42)]
    commodities = [
        "electronics", "apparel", "frozen_seafood", "pharma_cold", "furniture",
        "auto_parts", "chemicals_dg", "produce_chilled", "machinery", "parcels",
        "aog_spare", "retail_replen",
    ]
    notes = [
        "Dims look tight for dry40 -- check HC.",
        "Temp-sensitive; reefer slot preferred.",
        "Overweight for single 20GP -- split load?",
        "High value + urgent -- air belly candidate.",
        "Domestic short haul -- LTL truck OK.",
        "Standard dry OK; no special handling.",
        "",
        "Booking note incomplete.",
        "Shipper asked about 40HC upsell.",
        "Hazmat -- verify mode / segregation.",
    ]
    rows = []
    base = pd.Timestamp("2026-07-01", tz="UTC")
    for i in range(n):
        origin = origins[int(rng.integers(0, len(origins)))]
        dest = dests[int(rng.integers(0, len(dests)))]
        while dest == origin:
            dest = dests[int(rng.integers(0, len(dests)))]
        carrier = carriers[int(rng.integers(0, len(carriers)))]
        client = clients[int(rng.integers(0, len(clients)))]
        commodity = commodities[int(rng.integers(0, len(commodities)))]
        pieces = int(rng.integers(1, 48))
        length_cm = float(rng.uniform(30, 620))
        width_cm = float(rng.uniform(20, 240))
        height_cm = float(rng.uniform(15, 280))
        weight_kg = float(rng.uniform(40, 26000))
        pack_factor = float(rng.uniform(0.35, 0.95)) if pieces <= 8 else float(rng.uniform(0.45, 1.0))
        volume_cbm = float(
            max(0.01, (length_cm * width_cm * height_cm) / 1e6 * max(1, pieces * 0.35) * pack_factor)
        )
        temp_min_c = float(
            rng.choice([np.nan, -25, -18, 2, 5, 15, 25], p=[0.55, 0.04, 0.06, 0.08, 0.07, 0.1, 0.1])
        )
        hazmat = int(commodity == "chemicals_dg" or rng.random() < 0.07)
        cargo_value = float(rng.uniform(500, 380_000))
        urgency = int(commodity in {"aog_spare", "pharma_cold"} or rng.random() < 0.22)
        domestic_short = int(
            (origin.startswith("US") and dest.startswith("US")) or (rng.random() < 0.12)
        )
        requested_mode = rng.choice(MODES, p=[0.18, 0.38, 0.16, 0.10, 0.08, 0.10])
        cold = commodity in {"frozen_seafood", "pharma_cold", "produce_chilled"} or (
            not np.isnan(temp_min_c) and temp_min_c <= 5
        )
        cold = bool(cold and (commodity in {"frozen_seafood", "pharma_cold"} or rng.random() < 0.55))
        cube_out = volume_cbm > 58 or (height_cm > 240 and volume_cbm > 40)
        overweight_20 = weight_kg > 18000 and volume_cbm < 28
        oversize_piece = length_cm > 580 or width_cm > 230 or height_cm > 255
        air_candidate = (
            not cold
            and weight_kg < 5000
            and volume_cbm < 16
            and (
                commodity == "aog_spare"
                or urgency
                or (cargo_value > 20_000 and rng.random() < 0.35)
                or rng.random() < 0.10
            )
        )
        ltl_candidate = (
            not cold
            and not air_candidate
            and weight_kg < 10000
            and volume_cbm < 28
            and (
                domestic_short
                or commodity in {"parcels", "retail_replen", "apparel"}
                or rng.random() < 0.15
            )
        )
        if cold:
            suggested = "reefer"
        elif air_candidate:
            suggested = "air_belly"
        elif ltl_candidate and not hazmat:
            suggested = "ltl_truck"
        elif cube_out or oversize_piece:
            suggested = "hc40"
        elif weight_kg < 8000 and volume_cbm < 22 and not hazmat:
            suggested = "dry20"
        else:
            suggested = "dry40"
        mismatch = int(suggested != requested_mode)
        score = (
            1.5 * int(cold and requested_mode not in {"reefer"})
            + 1.2 * int(cube_out and requested_mode in {"dry20", "dry40"})
            + 1.1 * int(overweight_20 or oversize_piece)
            + 1.0 * int(air_candidate and requested_mode != "air_belly")
            + 0.8 * int(ltl_candidate and requested_mode not in {"ltl_truck", "dry20"})
            + 0.6 * mismatch
            + 0.5 * hazmat
            + 0.4 * (cargo_value > 100_000)
            + float(rng.normal(0, 0.45))
        )
        label = int(score > 1.45)
        reefer_hold = int(cold and label == 1)
        upsell_40hc = int((cube_out or oversize_piece) and not cold and label == 1)
        split_load = int((overweight_20 or (pieces > 30 and volume_cbm > 65)) and label == 1)
        air_expedite = int(air_candidate and label == 1)
        book_ltl = int(ltl_candidate and not cold and label == 1)
        note = notes[int(rng.integers(0, len(notes)))]
        if cold and rng.random() < 0.4:
            note = "Temp-sensitive; reefer slot preferred."
        if cube_out and rng.random() < 0.35:
            note = "Dims look tight for dry40 -- check HC."
        if air_candidate and rng.random() < 0.4:
            note = "High value + urgent -- air belly candidate."
        if split_load and rng.random() < 0.35:
            note = "Overweight for single 20GP -- split load?"
        rows.append(
            {
                "shipment_id": f"STW-{i + 1:06d}",
                "event_ts": (base + pd.to_timedelta(int(i * 13 + int(rng.integers(0, 9))), unit="min")).isoformat(),
                "lane_id": f"{origin}-{dest}",
                "origin": origin,
                "dest": dest,
                "carrier": carrier,
                "client_id": client,
                "commodity": commodity,
                "booking_note": note if rng.random() > 0.12 else "",
                "ops_note": "" if rng.random() > 0.4 else "Ops: verify equipment / mode fit (suggest head only).",
                "pieces": pieces,
                "length_cm": length_cm if rng.random() > 0.06 else np.nan,
                "width_cm": width_cm if rng.random() > 0.06 else np.nan,
                "height_cm": height_cm if rng.random() > 0.08 else np.nan,
                "weight_kg": weight_kg if rng.random() > 0.07 else np.nan,
                "volume_cbm": volume_cbm if rng.random() > 0.08 else np.nan,
                "temp_min_c": temp_min_c,
                "hazmat": hazmat,
                "cargo_value_usd": cargo_value,
                "urgency": urgency,
                "requested_mode": requested_mode,
                "suggested_mode": suggested,
                "reefer_hold": reefer_hold,
                "upsell_40hc": upsell_40hc,
                "split_load": split_load,
                "air_expedite": air_expedite,
                "book_ltl": book_ltl,
                "fit_risk": label,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = ROOT / "domains" / "stow-fit" / "data" / "shipments.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = gen_stow_fit(n=250, seed=45)
    df.to_csv(out, index=False)
    print(f"Wrote {out} ({len(df)} rows, pos={df['fit_risk'].mean():.2f})")
