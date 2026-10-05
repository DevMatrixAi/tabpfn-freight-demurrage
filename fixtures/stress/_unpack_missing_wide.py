"""Regenerate fixtures/stress/missing_wide_demurrage.csv (plain CSV, checked in).

The fixture used to be shipped as a zlib blob split across Python modules; that
blob was corrupted (adler32 mismatch), so the CSV is now committed as plain text
and this script deterministically rebuilds it from the freight-demurrage table:

* first 20 rows of domains/freight-demurrage/data/containers.csv
* elevated missingness on notes / dwell / free days / cargo value
* 40 synthetic ``noise_f*`` columns (wide-table stress; shape[1] >= 50)

Run: ``python fixtures/stress/_unpack_missing_wide.py``
Only writes when the CSV is absent (or ``--force`` is passed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"
OUT = HERE / "missing_wide_demurrage.csv"

N_ROWS = 20
N_NOISE = 40
MISSING_RATES = {
    "terminal_note": 0.35,
    "weather_alert": 0.5,
    "dwell_days_so_far": 0.25,
    "free_days_left": 0.25,
    "cargo_value_usd": 0.3,
}


def build(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.read_csv(SRC).head(N_ROWS).copy()
    for col, rate in MISSING_RATES.items():
        if col in df.columns:
            mask = rng.random(len(df)) < rate
            df.loc[mask, col] = np.nan
    noise = rng.normal(0, 1, size=(len(df), N_NOISE)).round(6)
    noise[rng.random(noise.shape) < 0.1] = np.nan
    for i in range(N_NOISE):
        df[f"noise_f{i + 1:02d}"] = noise[:, i]
    return df


def main(force: bool = False) -> Path:
    if force or not OUT.is_file():
        build().to_csv(OUT, index=False, lineterminator="\n")
    return OUT


main(force="--force" in sys.argv[1:])
