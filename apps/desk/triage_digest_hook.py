"""Hook: attach morning digest + coach beat after triage (mock)."""
from __future__ import annotations
from typing import Any

def after_triage(state: dict[str, Any]) -> None:
    try:
        from apps.desk.morning_digest import build_morning_digest
    except ImportError:
        from morning_digest import build_morning_digest  # type: ignore
    state["morning_digest"] = build_morning_digest(
        state.get("risk_cards"),
        state.get("action_counts"),
        money_at_risk=float(state.get("demurrage_total") or 0.0),
        top_n=5,
    )
    state["coach_active_beat"] = "drawer" if state.get("risk_cards") else "triage"
