"""Coda pack synthetic generators."""
from __future__ import annotations
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[3]

def gen_inland_mode(n: int = 600, seed: int = 43) -> pd.DataFrame:
    """Drayage/inland rows: predict prefer_rail (rail vs truck mode choice)."""
    rng = np.random.default_rng(seed)
    terminals = ["USLAX", "USLGB", "USNYC", "USSAV", "USORF", "USHOU", "USSEA", "USOAK"]
    destinations = [
        "Chicago IL", "Dallas TX", "Atlanta GA", "Columbus OH", "Memphis TN",
        "Kansas City MO", "Denver CO", "Phoenix AZ", "Detroit MI", "Nashville TN",
    ]
    notes = [
        "Customer needs door by Friday — truck may win.",
        "Rail ramp has capacity this week.",
        "Chassis shortage near terminal.",
        "Expedite inland requested by BCO.",
        "Cost-sensitive; OK with longer transit.",
        "",
        "Appointment window tight at warehouse.",
        "Weather advisory on I-40 corridor.",
    ]
    rows = []
    base = pd.Timestamp("2026-07-15", tz="UTC")
    for i in range(n):
        terminal = terminals[int(rng.integers(0, len(terminals)))]
        dest = destinations[int(rng.integers(0, len(destinations)))]
        distance_mi = float(rng.uniform(80, 2200))
        free_days_left = float(rng.uniform(-2, 12))
        truck_transit_h = distance_mi / float(rng.uniform(38, 55))
        rail_transit_h = distance_mi / float(rng.uniform(18, 32)) + float(rng.uniform(12, 48))
        truck_cost = 2.2 * distance_mi + float(rng.uniform(150, 600))
        rail_cost = 1.1 * distance_mi + float(rng.uniform(200, 900))
        cargo_value = float(rng.uniform(5_000, 180_000))
        dwell_at_terminal = float(rng.uniform(0, 9))
        appointment_tight = int(rng.random() < 0.28)
        chassis_ok = int(rng.random() < 0.72)
        expedite_flag = int(rng.random() < 0.22)
        score = (
            1.2 * (distance_mi > 700)
            + 1.0 * ((truck_cost - rail_cost) / max(truck_cost, 1) > 0.25)
            + 0.8 * (free_days_left > 4)
            - 1.3 * int(expedite_flag)
            - 0.9 * int(appointment_tight)
            - 0.5 * (cargo_value > 120_000 and free_days_left < 3)
            + 0.4 * int(chassis_ok == 0)
            + float(rng.normal(0, 0.5))
        )
        prefer_rail = int(score > 1.45)
        book_rail = int(prefer_rail == 1 and free_days_left > 3 and not expedite_flag)
        book_truck = int(prefer_rail == 0 or expedite_flag or appointment_tight)
        expedite_inland = int(expedite_flag or (free_days_left < 2 and cargo_value > 40_000))
        hold_for_ramp = int(prefer_rail and not chassis_ok and free_days_left > 2)
        note = notes[int(rng.integers(0, len(notes)))]
        if expedite_flag and rng.random() < 0.5:
            note = "Expedite inland requested by BCO."
        if distance_mi > 900 and rng.random() < 0.35:
            note = "Rail ramp has capacity this week."
        rows.append(
            {
                "move_id": f"IM-{i + 1:06d}",
                "event_ts": (base + pd.to_timedelta(int(i * 9 + int(rng.integers(0, 6))), unit="min")).isoformat(),
                "lane_id": f"LN-{terminal}-{dest.split()[0].upper()[:3]}",
                "terminal": terminal,
                "destination": dest,
                "container_id": f"CONT-{int(rng.integers(1, 9000)):05d}",
                "shipper_note": note if rng.random() > 0.15 else "",
                "ops_note": "" if rng.random() > 0.4 else "Check ramp cut-off vs free days.",
                "distance_mi": distance_mi if rng.random() > 0.06 else np.nan,
                "free_days_left": free_days_left,
                "truck_transit_h": truck_transit_h if rng.random() > 0.08 else np.nan,
                "rail_transit_h": rail_transit_h if rng.random() > 0.08 else np.nan,
                "truck_cost_usd": truck_cost,
                "rail_cost_usd": rail_cost,
                "cargo_value_usd": cargo_value,
                "dwell_at_terminal_d": dwell_at_terminal,
                "appointment_tight": appointment_tight,
                "chassis_ok": chassis_ok,
                "expedite_flag": expedite_flag,
                "book_rail": book_rail,
                "book_truck": book_truck,
                "expedite_inland": expedite_inland,
                "hold_for_ramp": hold_for_ramp,
                "prefer_rail": prefer_rail,
            }
        )
    return pd.DataFrame(rows)
