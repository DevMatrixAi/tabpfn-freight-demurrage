"""Ops-board risk card helpers (dollar-first triage cards).

Display labels are plain-English for the desk UI only; robot API field names
stay technical (divert / rebook / …).
"""
from __future__ import annotations

from typing import Any

from tabpfn_hack_core.core.pipeline import PipelineSession

# Desk UI copy — keep API / playbook keys unchanged.
ACTION_LABELS: dict[str, str] = {
    "divert": "Move to another terminal",
    "rebook": "Book on the next ship",
    "authorize_fee": "Pay the known fee",
    "cancel_booking": "Cancel booking",
    "cancel": "Cancel booking",
    "monitor": "Watch only",
    "call_terminal": "Push for early pickup",
    "expedite": "Speed up inland move",
}

# Late fee risk cards: Low / Med / High (tier colors stay red/amber/green).
TIER_RISK_LABELS: dict[str, str] = {
    "red": "High",
    "amber": "Med",
    "green": "Low",
}


def human_action(action: str | None) -> str:
    """Map playbook action key → desk phrase (fallback: raw key)."""
    key = (action or "monitor").strip()
    return ACTION_LABELS.get(key, key.replace("_", " "))


def risk_tier(proba: float) -> str:
    if proba >= 0.65:
        return "red"
    if proba >= 0.40:
        return "amber"
    return "green"


def risk_label(tier: str) -> str:
    """Late fee risk band for cards (High / Med / Low)."""
    return TIER_RISK_LABELS.get(tier, tier)


def fee_band(
    *,
    expected_usd: float | None,
    daily_usd: float | None = None,
    free_days_left: float | None = None,
    dwell_days: float | None = None,
    proba: float = 0.0,
) -> dict[str, float | None]:
    """Mock expected $ + p90 $ fee band (no live predictive distribution).

    Expected = projected demurrage on the row. p90 stretches with late-fee
    probability and remaining free-day burn using the daily rate — same
    dollar story judges see when live TabPFN full-dist is available.
    """
    try:
        expected = float(expected_usd) if expected_usd is not None else 0.0
    except (TypeError, ValueError):
        expected = 0.0
    try:
        daily = float(daily_usd) if daily_usd is not None else 0.0
    except (TypeError, ValueError):
        daily = 0.0
    try:
        free = float(free_days_left) if free_days_left is not None else 0.0
    except (TypeError, ValueError):
        free = 0.0
    try:
        dwell = float(dwell_days) if dwell_days is not None else 0.0
    except (TypeError, ValueError):
        dwell = 0.0
    p = max(0.0, min(1.0, float(proba or 0.0)))
    # Mock upper-tail dwell days past free window
    burn = max(0.0, dwell + 2.0 + 6.0 * p - max(0.0, free))
    tail = burn * daily if daily > 0 else expected * (0.25 + 0.55 * p)
    p90 = max(expected, expected + tail * 0.35, expected * (1.0 + 0.45 * p))
    return {
        "expected_usd": round(expected, 2),
        "p90_usd": round(float(p90), 2),
    }


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
        action_key = a.get("action") or "monitor"
        tier = risk_tier(proba)
        daily = None
        free = None
        dwell = None
        if row is not None:
            for col, dest in (
                ("daily_demurrage_usd", "daily"),
                ("free_days_left", "free"),
                ("dwell_days_so_far", "dwell"),
            ):
                if col in df.columns:
                    try:
                        val = row[col]
                        fval = float(val) if val == val else None
                    except (TypeError, ValueError):
                        fval = None
                    if dest == "daily":
                        daily = fval
                    elif dest == "free":
                        free = fval
                    else:
                        dwell = fval
        band = fee_band(
            expected_usd=money if money is not None else 0.0,
            daily_usd=daily,
            free_days_left=free,
            dwell_days=dwell,
            proba=proba,
        )
        cards.append({
            "row_id": rid,
            "proba": round(proba, 4),
            "action": action_key,  # technical key (API / debug)
            "action_label": human_action(action_key),
            "reason": a.get("reason") or "",
            "tier": tier,
            "risk_label": risk_label(tier),  # High / Med / Low
            "money": money,
            "expected_usd": band["expected_usd"],
            "p90_usd": band["p90_usd"],
            "subtitle": subtitle,
        })
    order = {"red": 0, "amber": 1, "green": 2}
    cards.sort(key=lambda c: (order.get(c["tier"], 9), -(c["money"] or 0), -c["proba"]))
    return cards


def chart_stats(cards: list[dict[str, Any]], demurrage_total: float = 0.0) -> dict[str, Any]:
    """Aggregate risk-card tiers for ops-board charts (counts + money)."""
    counts = {"high": 0, "med": 0, "low": 0}
    money = {"high": 0.0, "med": 0.0, "low": 0.0}
    for c in cards or []:
        tier = c.get("tier") or "green"
        band = {"red": "high", "amber": "med", "green": "low"}.get(tier, "low")
        counts[band] += 1
        try:
            money[band] += float(c.get("money") or 0.0)
        except (TypeError, ValueError):
            pass
    total_n = sum(counts.values()) or 1
    money_r = {k: round(v, 2) for k, v in money.items()}
    return {
        "counts": counts,
        "money": money_r,
        "money_max": max(money_r.values()) if money_r else 0.0,
        "money_total": round(float(demurrage_total or sum(money.values())), 2),
        "pct": {k: round(100.0 * counts[k] / total_n, 1) for k in ("high", "med", "low")},
        "n_cards": sum(counts.values()),
    }


def build_thinking_timeline(
    rows: list[dict[str, Any]] | None,
    *,
    group_col: str = "vessel_id",
    time_col: str = "event_ts",
    id_col: str = "container_id",
    limit: int = 24,
) -> list[dict[str, Any]]:
    """Readable vessel/flight × time strip for Thinking mode (from preview or sample rows)."""
    if not rows:
        return []
    gcol = group_col or "vessel_id"
    tcol = time_col or "event_ts"
    icol = id_col or "container_id"
    events: list[dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        gid = str(r.get(gcol) or r.get("vessel_id") or r.get("flight_id") or "—")
        ts = str(r.get(tcol) or r.get("event_ts") or "")
        rid = str(r.get(icol) or r.get("container_id") or r.get("awb_id") or r.get("row_id") or "—")
        pod = str(r.get("pod") or r.get("dest") or r.get("terminal") or "")
        money = r.get("projected_demurrage_usd")
        if money is None:
            money = r.get("projected_delay_cost_usd")
        try:
            money_f = float(money) if money not in (None, "") else None
        except (TypeError, ValueError):
            money_f = None
        # short time label
        ts_short = ts.replace("T", " ").replace("+00:00", "Z")
        if len(ts_short) > 16:
            ts_short = ts_short[:16]
        events.append({
            "group": gid,
            "ts": ts,
            "ts_label": ts_short or "—",
            "row_id": rid,
            "pod": pod,
            "money": money_f,
        })
    events.sort(key=lambda e: (e["group"], e["ts"] or "", e["row_id"]))
    return events[:limit]
