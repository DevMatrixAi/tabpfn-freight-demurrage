"""Missingness summary for messy tabular showcase (TabPFN strength)."""
from __future__ import annotations

from typing import Any

import pandas as pd


def missingness_summary(df: pd.DataFrame | None, *, top_n: int = 8) -> dict[str, Any] | None:
    """Return a compact missingness panel payload, or None if nothing missing."""
    if df is None or df.empty:
        return None
    rates = df.isna().mean()
    hit = rates[rates > 0].sort_values(ascending=False)
    if hit.empty:
        return None
    top = [
        {"col": str(c), "pct": round(float(p) * 100.0, 1)}
        for c, p in hit.head(top_n).items()
    ]
    return {
        "n_rows": int(len(df)),
        "n_cols": int(df.shape[1]),
        "n_cols_with_missing": int(len(hit)),
        "overall_pct": round(float(df.isna().mean().mean()) * 100.0, 2),
        "top": top,
        "gloss": "TabPFN-3.5 handles missings natively — stress fixture shows NaN rate by column.",
    }
