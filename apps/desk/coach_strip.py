"""In-desk coach strip — DEMO_90S / JUDGE_3MIN beats + IN_DESK_COACH_STRIP cribs.

Mock-only UI helpers. No live TabPFN.
"""
from __future__ import annotations

from typing import Any

# Judge / 90s demo beat chips (login → … → /eval). Order matches JUDGE_3MIN_RUNBOOK.
COACH_BEATS: list[dict[str, str]] = [
    {
        "id": "login",
        "label": "Login",
        "target": "#coach-login",
        "href": "/login",
        "line": "You're the shipper — stop late fees before the invoice.",
    },
    {
        "id": "ticker",
        "label": "Money at risk",
        "target": "#ticker-dollars",
        "href": "/desk#ticker-dollars",
        "line": "Dollars that burn if boxes sit past grace days.",
    },
    {
        "id": "triage",
        "label": "Triage",
        "target": "#triage-panel",
        "href": "/desk#triage-panel",
        "line": "Score late-fee risk on this messy table.",
    },
    {
        "id": "drawer",
        "label": "Drawer",
        "target": "#risk-board",
        "href": "/desk#risk-board",
        "line": "Click a container to see the suggested move.",
    },
    {
        "id": "stream",
        "label": "Stream",
        "target": "#btn-stream-rescore",
        "href": "/desk#stream-panel",
        "line": "New event — score and move can change.",
    },
    {
        "id": "eval",
        "label": "/eval",
        "target": "#eval-link",
        "href": "/eval",
        "line": "Plus / Thinking / Fast vs HistGBM for judges.",
    },
]

# Control → one-liner crib (docs/IN_DESK_COACH_STRIP.md). Keys = data-coach ids.
COACH_CRIBS: dict[str, str] = {
    "login": "You're the shipper — stop late fees before the invoice.",
    "client-switcher": "Switch between client accounts.",
    "money-at-risk": "Dollars that burn if boxes sit past grace days.",
    "sample-n": "Small slice for live Thinking (saves API). Full table = mock or final numbers.",
    "plus": "Reads messy text — no NLP pipeline.",
    "thinking": "Follows each vessel over time.",
    "run-triage": "Score late-fee risk on this messy table.",
    "histgbm-delta": "Lift vs a normal model on the same data.",
    "thinking-timeline": "Vessel across time — story, not just a score.",
    "risk-drawer": "Click a container to see the suggested move.",
    "stream-rescore": "New event — score and move can change.",
    "compare-eval": "Plus / Thinking / Fast vs HistGBM for judges.",
    "pack-selector": "Same engine — equipment, inland, air, stow-fit.",
    "robot-api": "Humans or robots call the same actions.",
}

# Frozen narrative when Judge path (mock) lands on /eval (JUDGE_3MIN_RUNBOOK).
JUDGE_PATH_NARRATIVE: dict[str, Any] = {
    "id": "judge-3min-mock",
    "title": "Judge path (mock) — frozen crib",
    "token_mode": "empty",
    "beats": [
        "Login — shipper money desk; stop late fees before the invoice.",
        "Home → late-fee desk — money at risk / late-fee risk / moves / Δ.",
        "Fixture → Plus → Thinking → run (mock) — messy table → TabPFN stand-in.",
        "Charts + HistGBM Δ — better than a normal model.",
        "Thinking timeline + effort — vessel over time.",
        "Risk card → action drawer — money move (move / rebook / pay fee / watch).",
        "Stream + re-score (optional) — live update.",
        "Compare /eval — Plus / Thinking / Fast vs HistGBM + ablations + calibration.",
        "Robot / MCP — same actions for humans or robots.",
    ],
    "say": "Shipper money desk — stop late fees before the invoice. Mock path; empty TABPFN_TOKEN.",
}


def coach_beats() -> list[dict[str, str]]:
    """Return judge-path step chips (copy-safe list)."""
    return [dict(b) for b in COACH_BEATS]


def coach_crib(control_id: str) -> str:
    """One-liner under a control, or empty if unknown."""
    return COACH_CRIBS.get(control_id, "")


def active_beat_for_path(path: str, *, has_triage: bool = False) -> str:
    """Pick highlighted chip from request path / triage state."""
    p = (path or "").rstrip("/") or "/"
    if p.endswith("/login") or p == "/login":
        return "login"
    if p.endswith("/eval") or p == "/eval":
        return "eval"
    if p in {"/", ""}:
        return "login"  # home after login → nudge toward ticker/desk
    if "desk" in p:
        if has_triage:
            return "drawer"
        return "triage"
    return "ticker"


def judge_path_payload(*, triage_ok: bool, money_at_risk: float, n_cards: int) -> dict[str, Any]:
    """Frozen judge-path banner payload after mock triage."""
    return {
        **JUDGE_PATH_NARRATIVE,
        "triage_ok": bool(triage_ok),
        "money_at_risk": float(money_at_risk or 0.0),
        "n_cards": int(n_cards or 0),
        "frozen": True,
        "mock": True,
    }
