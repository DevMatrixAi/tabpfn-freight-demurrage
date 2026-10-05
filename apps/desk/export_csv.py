"""Export triage rows + suggested actions as CSV (desk download)."""
from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import FastAPI
from fastapi.responses import Response

def _expected(proba: Any, money: Any) -> Any:
    try:
        return round(float(proba) * float(money), 2)
    except (TypeError, ValueError):
        return ""


def _label(key: Any, fallback: Any = "") -> str:
    try:
        try:
            from apps.desk.risk_board import human_action
        except ImportError:  # pragma: no cover
            from risk_board import human_action  # type: ignore

        return human_action(str(key)) if key else str(fallback or "")
    except Exception:  # pragma: no cover
        return str(fallback or key or "")


CSV_COLUMNS = (
    "row_id",
    "proba",
    "action",
    "action_label",
    "reason",
    "tier",
    "risk_label",
    "money_usd",
    "expected_usd",
)


def build_triage_csv(state: dict[str, Any]) -> str:
    """Serialize state['actions'] joined with risk_cards into CSV text."""
    actions = list(state.get("actions") or [])
    cards = {str(c.get("row_id")): c for c in (state.get("risk_cards") or []) if c.get("row_id") is not None}
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(CSV_COLUMNS), extrasaction="ignore")
    w.writeheader()
    if not actions and cards:
        # Fall back to cards alone if actions cleared
        for rid, c in cards.items():
            w.writerow(_row_from_card(rid, c))
    else:
        for a in actions:
            rid = str(a.get("row_id", ""))
            c = cards.get(rid) or {}
            w.writerow(
                {
                    "row_id": rid,
                    "proba": a.get("proba", c.get("proba", "")),
                    "action": a.get("action", c.get("action", "")),
                    "action_label": _label(a.get("action") or c.get("action"), c.get("action_label")),
                    "reason": a.get("reason") or c.get("reason") or "",
                    "tier": c.get("tier") or "",
                    "risk_label": c.get("risk_label") or "",
                    "money_usd": c.get("money") if c.get("money") is not None else "",
                    "expected_usd": _expected(a.get("proba", c.get("proba")), c.get("money")),
                }
            )
    return buf.getvalue()


def _row_from_card(rid: str, c: dict[str, Any]) -> dict[str, Any]:
    return {
        "row_id": rid,
        "proba": c.get("proba", ""),
        "action": c.get("action", ""),
        "action_label": c.get("action_label") or "",
        "reason": c.get("reason") or "",
        "tier": c.get("tier") or "",
        "risk_label": c.get("risk_label") or "",
        "money_usd": c.get("money") if c.get("money") is not None else "",
        "expected_usd": _expected(c.get("proba"), c.get("money")),
    }


def register_export_csv_routes(app: FastAPI, *, state: dict[str, Any]) -> None:
    """Attach GET /export-triage.csv."""

    @app.get("/export-triage.csv")
    async def export_triage_csv() -> Response:
        body = build_triage_csv(state)
        return Response(
            content=body,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="triage_actions.csv"',
                "Cache-Control": "no-store",
            },
        )
