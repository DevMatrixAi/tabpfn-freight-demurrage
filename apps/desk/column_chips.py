"""Column-type chips for the ops board (BeyondArena / raw-DF story).

Mock-safe: built from domain.yaml schema (+ optional loaded DataFrame for
missing markers). Types: text / high-card / missing / group×time.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

CHIP_KINDS: tuple[str, ...] = ("text", "high_card", "missing", "group_time")

CHIP_META: dict[str, dict[str, str]] = {
    "text": {
        "label": "text",
        "title": "Messy text notes \u2014 TabPFN Plus, no NLP pipeline",
        "legend": "text notes",
    },
    "high_card": {
        "label": "high-card",
        "title": "High-cardinality IDs (BOL / container / ports)",
        "legend": "high-card IDs",
    },
    "missing": {
        "label": "missing",
        "title": "Columns with raw NaNs \u2014 not imputed away",
        "legend": "missing (raw)",
    },
    "group_time": {
        "label": "group\u00d7time",
        "title": "Thinking group_col \u00d7 group_time_col (vessel \u00d7 event_ts)",
        "legend": "group\u00d7time",
    },
}


def _as_list(val: Any) -> list[str]:
    if not val:
        return []
    if isinstance(val, str):
        return [val]
    return [str(x) for x in val if x is not None and str(x).strip()]


def column_chips_payload(
    domain: Any | None = None,
    df: pd.DataFrame | None = None,
    *,
    text_cols: list[str] | None = None,
    high_card_cols: list[str] | None = None,
    group_col: str | None = None,
    time_col: str | None = None,
    max_per_kind: int = 6,
) -> dict[str, Any]:
    """Build legend + chip rows from schema and/or fixture frame."""
    if domain is not None:
        text_cols = text_cols if text_cols is not None else list(getattr(domain, "text_cols", None) or [])
        high_card_cols = (
            high_card_cols
            if high_card_cols is not None
            else list(getattr(domain, "high_card_cols", None) or [])
        )
        group_col = group_col if group_col is not None else getattr(domain, "group_col", None)
        time_col = time_col if time_col is not None else getattr(domain, "time_col", None)

    text_cols = _as_list(text_cols)
    high_card_cols = _as_list(high_card_cols)
    group_cols = _as_list(group_col)
    time_cols = _as_list(time_col)
    group_time_cols = list(dict.fromkeys([*group_cols, *time_cols]))

    missing_cols: list[str] = []
    if df is not None and not getattr(df, "empty", True):
        rates = df.isna().mean()
        missing_cols = [str(c) for c, p in rates.items() if float(p) > 0]

    by_kind: dict[str, list[str]] = {
        "text": text_cols[:max_per_kind],
        "high_card": high_card_cols[:max_per_kind],
        "missing": missing_cols[:max_per_kind],
        "group_time": group_time_cols[:max_per_kind],
    }
    chips: list[dict[str, str]] = []
    for kind in CHIP_KINDS:
        meta = CHIP_META[kind]
        for col in by_kind[kind]:
            chips.append(
                {
                    "kind": kind,
                    "col": col,
                    "label": meta["label"],
                    "title": f"{meta['title']} \u00b7 {col}",
                }
            )

    legend = [
        {
            "kind": k,
            "label": CHIP_META[k]["legend"],
            "title": CHIP_META[k]["title"],
            "count": len(by_kind[k]),
        }
        for k in CHIP_KINDS
        if by_kind[k] or k in {"text", "high_card", "group_time"}
    ]

    return {
        "chips": chips,
        "legend": legend,
        "counts": {k: len(by_kind[k]) for k in CHIP_KINDS},
        "gloss": (
            "BeyondArena / raw-DF story \u2014 text, high-card IDs, missings, "
            "and group\u00d7time stay on the board (not cleaned away)."
        ),
        "markers": {
            "text": bool(text_cols),
            "high_card": bool(high_card_cols),
            "missing": bool(missing_cols),
            "group_time": bool(group_time_cols),
        },
    }


def apply_column_chips(state: dict[str, Any], domain: Any, df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Write column_chips onto desk state; return the payload."""
    payload = column_chips_payload(domain, df)
    state["column_chips"] = payload
    return payload
