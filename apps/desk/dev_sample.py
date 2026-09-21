"""Small-n live TabPFN budget control (dev / overnight).

Env: TABPFN_DEV_N=60  → sample at most N rows before fit (live or mock).
When unset, default is **60** (keeps post-4 PM Thinking from blowing budget).
Form: sample_n on /run-triage overrides env for that run.
Full table stays available for mock demos; set sample_n empty / 0 for full.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd

# Default live budget when TABPFN_DEV_N is unset.
DEFAULT_DEV_N = 60

# Rough mock cost table — NOT Prior Labs billing. Estimate only.
# Formula: cents_per_row × n × live_modes (Plus+Thinking). Labeled est./rough.
_CENTS_PER_ROW = 0.15  # rough mock cents per row per live mode
_LIVE_MODES = 2  # Plus + Thinking typical live pair
_EST_TABLE = {
    40: 0.12,
    60: 0.18,
    80: 0.24,
}


def resolve_sample_n(
    form_value: str | None = None,
    *,
    default_env: str = "TABPFN_DEV_N",
    default_n: int = DEFAULT_DEV_N,
) -> int | None:
    """Return max rows to keep, or None for full table.

    Form empty string ("") means full table and overrides env.
    Form omitted (None) falls back to TABPFN_DEV_N, then default_n (60).
    """
    if form_value is not None:
        if str(form_value).strip() == "":
            return None  # explicit full-table choice
        raw = str(form_value).strip()
    else:
        raw = os.environ.get(default_env, "").strip() or None
        if raw is None:
            return int(default_n) if default_n and default_n > 0 else None
    if raw is None:
        return None
    try:
        n = int(str(raw).strip())
    except ValueError:
        return None
    if n <= 0:
        return None
    return n


def estimate_live_cost_usd(n: int | None, *, modes: int = _LIVE_MODES) -> float | None:
    """Rough USD estimate for a live Plus+Thinking pass at sample_n=n.

    Mock formula only — not Prior Labs billing. Returns None for full-table.
    """
    if n is None or n <= 0:
        return None
    if n in _EST_TABLE and modes == _LIVE_MODES:
        return float(_EST_TABLE[n])
    # cents_per_row × n × modes → dollars
    return round((_CENTS_PER_ROW * n * modes) / 100.0, 2)


def live_budget_chip(
    *,
    sample_n: int | None = None,
    has_token: bool | None = None,
) -> dict[str, Any]:
    """Nav / settings chip describing live budget (mock-safe).

    When mock (no token): ``Mock · no live spend`` + planned n for after-reset.
    When live: ``Live budget · n=60 · ~$0.18 est`` (estimate only).
    """
    if has_token is None:
        has_token = bool(os.environ.get("TABPFN_TOKEN", "").strip())
    n = sample_n if sample_n is not None else resolve_sample_n(None)
    planned = int(n) if n is not None else DEFAULT_DEV_N
    est = estimate_live_cost_usd(planned)
    est_str = f"${est:.2f}" if est is not None else "n/a"
    if not has_token:
        label = f"Mock · no live spend · planned n={planned}"
        short = "Mock · no live spend"
        mode = "mock"
    else:
        label = f"Live budget · n={planned} · ~{est_str} est"
        short = label
        mode = "live"
    return {
        "id": "live-budget",
        "mode": mode,
        "label": label,
        "short": short,
        "sample_n": planned,
        "est_usd": est,
        "est_label": f"~{est_str} est" if est is not None else "est. n/a",
        "formula_note": (
            "Rough estimate only (cents-per-row × n × Plus+Thinking) — "
            "not Prior Labs billing. Fixed table: n=40→~$0.12, n=60→~$0.18, n=80→~$0.24."
        ),
        "has_token": bool(has_token),
        "marker": "data-live-budget-chip",
    }


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
