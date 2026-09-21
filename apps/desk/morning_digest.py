"""Morning digest strip — top-N moves + $ at risk + action counts (mock).

Pitch claim (FREIGHT_DEMURRAGE_PITCH): suggest_actions + morning digest.
"""
from __future__ import annotations

from typing import Any

try:
    from apps.desk.risk_board import human_action
except ImportError:
    from risk_board import human_action  # type: ignore


def build_morning_digest(
    risk_cards: list[dict[str, Any]] | None,
    action_counts: dict[str, Any] | None,
    *,
    money_at_risk: float = 0.0,
    top_n: int = 5,
) -> dict[str, Any] | None:
    """Compact digest after triage. None when no cards yet."""
    cards = list(risk_cards or [])
    if not cards and not action_counts:
        return None
    ranked = sorted(
        cards,
        key=lambda c: float(c.get("money") or c.get("expected_usd") or 0.0),
        reverse=True,
    )
    top: list[dict[str, Any]] = []
    for c in ranked[: max(1, int(top_n))]:
        money = c.get("money")
        if money is None:
            money = c.get("expected_usd")
        try:
            money_f = float(money) if money is not None else 0.0
        except (TypeError, ValueError):
            money_f = 0.0
        action = c.get("action") or "monitor"
        top.append(
            {
                "row_id": str(c.get("row_id") or ""),
                "action": action,
                "action_label": c.get("action_label") or human_action(action),
                "money": round(money_f, 2),
                "proba": float(c.get("proba") or 0.0),
                "tier": c.get("risk_label") or c.get("tier") or "",
            }
        )
    counts_raw = dict(action_counts or {})
    counts = [
        {"action": k, "label": human_action(k), "n": int(v)}
        for k, v in sorted(counts_raw.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    ]
    try:
        total = float(money_at_risk or 0.0)
    except (TypeError, ValueError):
        total = 0.0
    return {
        "money_at_risk": round(total, 2),
        "top_moves": top,
        "action_counts": counts,
        "n_cards": len(cards),
        "top_n": len(top),
    }
