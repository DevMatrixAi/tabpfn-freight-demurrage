"""Air-freight coda pack synthetic generator."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]


def gen_air_freight(n: int = 600, seed: int = 44) -> pd.DataFrame:
    """AWB rows: predict miss_connection_risk (delay / miss / AOG urgency).

    Multi-client and multi-carrier appear as fixture columns only (labels for demo
    slicing) — not live GSA/GHA systems.
    """
    rng = np.random.default_rng(seed)
    origins = ["HKG", "PVG", "ICN", "NRT", "SIN", "FRA", "AMS", "ORD", "LAX", "JFK", "DXB", "LHR"]
    dests = ["LAX", "JFK", "ORD", "MIA", "DFW", "SEA", "ATL", "SFO", "EWR", "BOS", "IAH", "DEN"]
    carriers = ["CX", "LH", "SQ", "KE", "UA", "AA", "EK", "QR", "CI", "NH"]
    clients = [f"CLT-{i:03d}" for i in range(1, 36)]
    commodities = [
        "pharma_cold", "semiconductor", "aog_spare", "apparel", "perishable",
        "electronics", "auto_parts", "docs_urgent", "live_animals", "machinery",
    ]
    notes = [
        "AOG spare — aircraft grounded; expedite requested.",
        "Tight MCT at hub — hold for connection?",
        "Belly capacity open on evening flight.",
        "Shipper OK with next-day if cheaper.",
        "Temp logger required; cold-chain break risk.",
        "",
        "Booking note incomplete.",
        "GHA flagged late acceptance cut-off.",
        "Rebook belly preferred over freighter premium.",
    ]
    rows = []
    base = pd.Timestamp("2026-08-01", tz="UTC")
    for i in range(n):
        origin = origins[int(rng.integers(0, len(origins)))]
        dest = dests[int(rng.integers(0, len(dests)))]
        while dest == origin:
            dest = dests[int(rng.integers(0, len(dests)))]
        carrier = carriers[int(rng.integers(0, len(carriers)))]
        client = clients[int(rng.integers(0, len(clients)))]
        commodity = commodities[int(rng.integers(0, len(commodities)))]
        pieces = int(rng.integers(1, 40))
        weight_kg = float(rng.uniform(5, 4500))
        volume_cbm = float(rng.uniform(0.02, 18))
        is_aog = int(commodity == "aog_spare" or rng.random() < 0.07)
        connection_minutes = float(rng.uniform(35, 240))
        connection_tight = int(connection_minutes < 75)
        belly_available = int(rng.random() < 0.55)
        freighter_available = int(rng.random() < 0.28)
        temp_sensitive = int(
            commodity in {"pharma_cold", "perishable", "live_animals"} or rng.random() < 0.12
        )
        cargo_value = float(rng.uniform(800, 420_000))
        delay_hours_p50 = float(rng.uniform(0, 18))
        projected_delay_cost = float(
            min(cargo_value * 0.08, 0.0 if delay_hours_p50 < 2 else delay_hours_p50 * (80 + cargo_value * 0.0004))
        )
        if is_aog:
            projected_delay_cost = max(projected_delay_cost, 12_000 + float(rng.uniform(0, 40_000)))
        score = (
            1.8 * is_aog
            + 1.2 * connection_tight
            + 0.9 * temp_sensitive
            + 0.7 * (delay_hours_p50 > 6)
            + 0.5 * (cargo_value > 80_000)
            - 0.8 * belly_available
            - 0.4 * freighter_available
            + float(rng.normal(0, 0.5))
        )
        label = int(score > 1.25)
        expedite_aog = int(is_aog and label == 1)
        hold_for_connection = int(connection_tight and not is_aog and label == 1)
        rebook_belly = int(belly_available and not is_aog and (label == 1 or delay_hours_p50 > 4))
        note = notes[int(rng.integers(0, len(notes)))]
        if is_aog and rng.random() < 0.7:
            note = "AOG spare — aircraft grounded; expedite requested."
        elif connection_tight and rng.random() < 0.45:
            note = "Tight MCT at hub — hold for connection?"
        elif belly_available and rng.random() < 0.35:
            note = "Belly capacity open on evening flight."
        flight_id = f"{carrier}{int(rng.integers(100, 999))}"
        rows.append(
            {
                "awb_id": f"AWB-{i + 1:06d}",
                "event_ts": (base + pd.to_timedelta(int(i * 9 + int(rng.integers(0, 6))), unit="min")).isoformat(),
                "flight_id": flight_id,
                "route_id": f"{origin}-{dest}",
                "origin": origin,
                "dest": dest,
                "carrier": carrier,
                "client_id": client,
                "commodity": commodity,
                "handling_note": note if rng.random() > 0.1 else "",
                "ops_note": "" if rng.random() > 0.4 else "Ops: verify ULD build / cut-off.",
                "pieces": pieces,
                "weight_kg": weight_kg if rng.random() > 0.07 else np.nan,
                "volume_cbm": volume_cbm if rng.random() > 0.09 else np.nan,
                "is_aog": is_aog,
                "connection_minutes": connection_minutes,
                "connection_tight": connection_tight,
                "belly_available": belly_available,
                "freighter_available": freighter_available,
                "temp_sensitive": temp_sensitive,
                "cargo_value_usd": cargo_value,
                "delay_hours_p50": delay_hours_p50,
                "projected_delay_cost_usd": round(projected_delay_cost, 2),
                "expedite_aog": expedite_aog,
                "hold_for_connection": hold_for_connection,
                "rebook_belly": rebook_belly,
                "miss_connection_risk": label,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=600)
    p.add_argument("--seed", type=int, default=44)
    args = p.parse_args()
    out = ROOT / "domains" / "air-freight" / "data" / "shipments.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = gen_air_freight(n=args.n, seed=args.seed)
    df.to_csv(out, index=False)
    print(f"Wrote {out} ({len(df)} rows, pos={df['miss_connection_risk'].mean():.2f})")
