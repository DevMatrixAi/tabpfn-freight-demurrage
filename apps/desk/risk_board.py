"""Ops-board risk card helpers (dollar-first triage cards)."""
from __future__ import annotations

from typing import Any

from tabpfn_hack_core.core.pipeline import PipelineSession


def risk_tier(proba: float) -> str:
    if proba >= 0.65:
        return "red"
    if proba >= 0.40:
        return "amber"
    return "green"


def build_risk_cards(
    sess: PipelineSession,
    tid: str,
    actions: list[dict[str, Any]],
    pack_meta: dict[str, Any],
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Join suggested actions with table rows for dollar-first ops cards."""
    if tid not in sess.tables or not actions:
        return []
    df = sess.tables[tid]
    id_col = sess.domain.id_col or pack_meta.get("id_hint") or "container_id"
    money_col = pack_meta.get("money_col")
    cards: list[dict[str, Any]] = []
    for a in actions[:limit]:
        rid = str(a.get("row_id", ""))
        proba = float(a.get("proba") or 0.0)
        row = None
        if id_col in df.columns:
            hit = df.loc[df[id_col].astype(str) == rid]
            if len(hit):
                row = hit.iloc[0]
        money = None
        subtitle = ""
        if row is not None:
            if money_col and money_col in df.columns:
                try:
                    money = float(row[money_col]) if row[money_col] == row[money_col] else 0.0
                except (TypeError, ValueError):
                    money = 0.0
            bits = []
            for col in (
                "vessel_id", "flight_id", "pod", "dest", "pol", "origin",
                "carrier", "client_id", "trade_lane", "terminal",
            ):
                if col in df.columns and str(row.get(col, "") or ""):
                    bits.append(f"{col.split('_')[0]} {row[col]}")
            subtitle = " · ".join(bits[:3])
        cards.append({
            "row_id": rid,
            "proba": round(proba, 4),
            "action": a.get("action") or "monitor",
            "reason": a.get("reason") or "",
            "tier": risk_tier(proba),
            "money": money,
            "subtitle": subtitle,
        })
    order = {"red": 0, "amber": 1, "green": 2}
    cards.sort(key=lambda c: (order.get(c["tier"], 9), -(c["money"] or 0), -c["proba"]))
    return cards
