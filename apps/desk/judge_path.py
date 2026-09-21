"""One-click Judge path (mock) — empty-token safe triage → /eval."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

try:
    from apps.desk.coach_strip import judge_path_payload
except ImportError:
    from coach_strip import judge_path_payload  # type: ignore

try:
    from apps.desk.desk_triage_apply import apply_triage
except ImportError:
    from desk_triage_apply import apply_triage  # type: ignore


def register_judge_path_routes(
    app: FastAPI,
    *,
    state: dict[str, Any],
    pack_meta: Callable[[], dict[str, Any]],
    resolve_mode: Callable,
    metric_slice: Callable,
    money_total: Callable,
    build_risk_cards: Callable,
    load_default_csv: Callable,
    sample_ids: Callable,
) -> None:
    """Attach POST /judge-path (always mock; redirects to /eval)."""

    @app.post("/judge-path")
    async def judge_path_mock() -> RedirectResponse:
        """Run mock triage then jump to /eval with frozen JUDGE_3MIN narrative."""
        apply_triage(
            app,
            state,
            mode="mock",
            fast_ab=None,
            thinking_effort="medium",
            sample_n=None,
            pack_meta=pack_meta,
            resolve_mode=resolve_mode,
            metric_slice=metric_slice,
            money_total=money_total,
            build_risk_cards=build_risk_cards,
            load_default_csv=load_default_csv,
            sample_ids=sample_ids,
        )
        cards = state.get("risk_cards") or []
        state["judge_path"] = judge_path_payload(
            triage_ok=bool(state.get("metrics") or cards),
            money_at_risk=float(state.get("demurrage_total") or 0.0),
            n_cards=len(cards),
        )
        state["coach_active_beat"] = "eval"
        return RedirectResponse(url="/eval?judge=1", status_code=303)
