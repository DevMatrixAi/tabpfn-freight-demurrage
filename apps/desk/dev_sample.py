"""Small-n live TabPFN budget control (dev / overnight).

Env: TABPFN_DEV_N=60  → sample at most N rows before fit (live or mock).
Form: sample_n on /run-triage overrides env for that run.
Full table stays available for mock demos; set sample_n empty / 0 for full.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd


def resolve_sample_n(form_value: str | None = None, *, default_env: str = "TABPFN_DEV_N") -> int | None:
    """Return max rows to keep, or None for full table.

    Form empty string ("") means full table and overrides env.
    Form omitted (None) falls back to TABPFN_DEV_N.
    """
    if form_value is not None:
        if str(form_value).strip() == "":
            return None  # explicit full-table choice
        raw = str(form_value).strip()
    else:
        raw = os.environ.get(default_env, "").strip() or None
    if raw is None:
        return None
    try:
        n = int(str(raw).strip())
    except ValueError:
        return None
    if n <= 0:
        return None
    return n


def sample_frame(
    df: pd.DataFrame,
    n: int | None,
    *,
    label_col: str | None = None,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict[str, Any] | None]:
    """Return (possibly sampled) frame + meta describing the cut."""
    if df is None or df.empty or n is None:
        return df, None
    full = int(len(df))
    if full <= n:
        return df, {
            "sample_n": full,
            "full_n": full,
            "sampled": False,
            "gloss": f"Full table ({full} rows) — under TABPFN_DEV_N={n}.",
        }
    out = df
    if label_col and label_col in df.columns:
        try:
            # Stratified sample when both classes exist and n is large enough
            vc = df[label_col].value_counts()
            if len(vc) >= 2 and n >= 2 * len(vc):
                frac = n / full
                parts = []
                for _, g in df.groupby(label_col, sort=False):
                    k = max(1, int(round(len(g) * frac)))
                    parts.append(g.sample(n=min(k, len(g)), random_state=random_state))
                out = pd.concat(parts, ignore_index=True)
                if len(out) > n:
                    out = out.sample(n=n, random_state=random_state).reset_index(drop=True)
            else:
                out = df.sample(n=n, random_state=random_state).reset_index(drop=True)
        except Exception:
            out = df.sample(n=n, random_state=random_state).reset_index(drop=True)
    else:
        out = df.sample(n=n, random_state=random_state).reset_index(drop=True)
    meta = {
        "sample_n": int(len(out)),
        "full_n": full,
        "sampled": True,
        "gloss": f"Dev sample {len(out)} of {full} rows (budget control for live TabPFN).",
    }
    return out, meta
