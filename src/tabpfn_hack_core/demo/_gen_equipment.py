"""Coda pack synthetic generators."""
from __future__ import annotations
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]

def gen_equipment_size(n: int = 600, seed: int = 42) -> pd.DataFrame:
    """Booking rows: predict special_equip_fit (reefer/40HC/special vs dry box)."""
    rng = np.random.default_rng(seed)
    pols = ["CNSHA", "CNNGB", "KRPUS", "JPYOK", "SGSIN", "HKHKG", "TWKHH", "VNSGN"]
    pods = ["USLAX", "USLGB", "USNYC", "NLRTM", "DEHAM", "GBFXT", "BEANR", "ITGOA"]
    commodity = [
        "electronics", "apparel", "frozen_seafood", "pharma_cold", "furniture",
        "auto_parts", "chemicals_dg", "produce_chilled", "machinery", "toys",
    ]
    notes = [
        "Shipper requests high-cube for cubing out.",
        "Temp-sensitive cargo — reefer preferred.",
        "Standard dry OK; no special handling.",
        "Overheight / awkward dims — check 40HC.",
        "Cold chain break risk if dry used.",
        "",
        "Booking note incomplete.",
        "Customer asked about reefer hold slot.",
    ]
    rows = []
    base = pd.Timestamp("2026-06-01", tz="UTC")
    for i in range(n):
        commodity_i = commodity[int(rng.integers(0, len(commodity)))]
        weight_kg = float(rng.uniform(800, 28000))
        volume_cbm = float(rng.uniform(2, 76))
        temp_min_c = float(rng.choice([np.nan, -25, -18, 2, 5, 15, 25], p=[0.45, 0.05, 0.08, 0.12, 0.1, 0.1, 0.1]))
        hazmat = int(rng.random() < 0.08)
        current_equip = rng.choice(["20GP", "40GP", "40HC", "20RF", "40RF"], p=[0.25, 0.35, 0.2, 0.08, 0.12])
        cargo_value = float(rng.uniform(2_000, 250_000))
        teu_request = float(rng.choice([1.0, 2.0], p=[0.4, 0.6]))
        cube_ratio = volume_cbm / max(teu_request * 28.0, 1.0)
        cold = commodity_i in {"frozen_seafood", "pharma_cold", "produce_chilled"} or (
            not np.isnan(temp_min_c) and temp_min_c <= 5
        )
        cube_out = cube_ratio > 0.85 and volume_cbm > 55
        score = (
            1.6 * int(cold)
            + 1.1 * int(cube_out)
            + 0.7 * int(hazmat)
            + 0.4 * (cargo_value > 80_000)
            + 0.5 * (current_equip in {"20GP", "40GP"} and (cold or cube_out))
            + float(rng.normal(0, 0.55))
        )
        label = int(score > 1.35)
        reefer_candidate = int(cold or (not np.isnan(temp_min_c) and temp_min_c <= 5))
        hc_upsell = int(cube_out or (volume_cbm > 58 and current_equip in {"20GP", "40GP"}))
        confirm_dry_ok = int(not cold and not cube_out and not hazmat and cargo_value < 60_000)
        hold_reefer_slot = int(reefer_candidate and label == 1)
        note = notes[int(rng.integers(0, len(notes)))]
        if cold and rng.random() < 0.4:
            note = "Temp-sensitive cargo — reefer preferred."
        if cube_out and rng.random() < 0.35:
            note = "Shipper requests high-cube for cubing out."
        rows.append(
            {
                "booking_id": f"BK-{i + 1:06d}",
                "event_ts": (base + pd.to_timedelta(int(i * 11 + int(rng.integers(0, 8))), unit="min")).isoformat(),
                "trade_lane": f"{pols[i % len(pols)]}-{pods[i % len(pods)]}",
                "pol": pols[int(rng.integers(0, len(pols)))],
                "pod": pods[int(rng.integers(0, len(pods)))],
                "shipper_id": f"SHP-{int(rng.integers(1, 220)):04d}",
                "commodity": commodity_i,
                "booking_note": note if rng.random() > 0.12 else "",
                "ops_note": "" if rng.random() > 0.35 else "Ops: verify equipment availability.",
                "weight_kg": weight_kg if rng.random() > 0.08 else np.nan,
                "volume_cbm": volume_cbm if rng.random() > 0.1 else np.nan,
                "temp_min_c": temp_min_c,
                "hazmat": hazmat,
                "current_equip": current_equip,
                "teu_request": teu_request,
                "cargo_value_usd": cargo_value,
                "reefer_candidate": reefer_candidate,
                "hc_upsell": hc_upsell,
                "confirm_dry_ok": confirm_dry_ok,
                "hold_reefer_slot": hold_reefer_slot,
                "special_equip_fit": label,
            }
        )
    return pd.DataFrame(rows)
