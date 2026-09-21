"""Desk explain helpers — mock permutation importance → plain-English drawer copy.

Reuses PipelineSession.explain (sklearn permutation on mock path). No live TabPFN / SHAP.
"""
from __future__ import annotations

from typing import Any

# Technical mock-feature suffixes / names → shipper language
_FEATURE_PLAIN: dict[str, str] = {
    "terminal_note__len": "Terminal note length",
    "terminal_note__tokens": "Terminal note detail",
    "weather_alert__len": "Weather alert length",
    "weather_alert__tokens": "Weather alert detail",
    "bol_id__hash": "Bill of lading ID",
    "container_id__hash": "Container ID",
    "pol__hash": "Load port",
    "pod__hash": "Discharge port",
    "vessel_id__hash": "Vessel ID",
    "event_ts__hash": "Event time bucket",
    "client_id__hash": "Client ID",
    "free_days_left": "Free days left",
    "dwell_days_so_far": "Days already dwelling",
    "projected_demurrage_usd": "Projected late fee $",
    "daily_demurrage_usd": "Daily late fee rate",
    "cargo_value_usd": "Cargo value",
    "blank_sailing": "Blank sailing flag",
    "inland_can_beat_freedays": "Inland can beat free days",
    "fee_inevitable": "Fee already inevitable",
    "cargo_vs_fee_collapse": "Cargo vs fee collapse",
    "teu": "TEU size",
}

_KIND_PLAIN: dict[str, str] = {
    "text": "messy text",
    "high_card": "high-card ID",
    "missing_derived": "missing / derived",
    "money": "money / dwell",
    "other": "table signal",
}


def feature_kind(name: str, *, text_cols: list[str] | None = None, high_card_cols: list[str] | None = None) -> str:
    """Classify a mock feature name for the drawer legend."""
    text_cols = text_cols or []
    high_card_cols = high_card_cols or []
    base = name.split("__", 1)[0]
    if name.endswith("__len") or name.endswith("__tokens") or base in text_cols:
        return "text"
    if name.endswith("__hash") or base in high_card_cols:
        return "high_card"
    if base in {
        "free_days_left",
        "dwell_days_so_far",
        "projected_demurrage_usd",
        "daily_demurrage_usd",
        "cargo_value_usd",
    }:
        return "money"
    # Gate / flag cols and anything with NaN-driven mock fill → missing/derived bucket
    if base in {
        "blank_sailing",
        "inland_can_beat_freedays",
        "fee_inevitable",
        "cargo_vs_fee_collapse",
    } or "__missing" in name or name.endswith("_isna"):
        return "missing_derived"
    return "other"


def human_feature(name: str) -> str:
    """Map technical feature → desk phrase."""
    if name in _FEATURE_PLAIN:
        return _FEATURE_PLAIN[name]
    base = name.split("__", 1)[0]
    if name.endswith("__len"):
        return f"{base.replace('_', ' ').title()} length"
    if name.endswith("__tokens"):
        return f"{base.replace('_', ' ').title()} detail"
    if name.endswith("__hash"):
        return f"{base.replace('_', ' ').title()} ID"
    return name.replace("_", " ").replace("__", " · ")


def why_this_move(
    *,
    action: str | None = None,
    reason: str | None = None,
    top_labels: list[str] | None = None,
) -> str:
    """One plain-English paragraph for the action drawer."""
    bits: list[str] = []
    if reason and str(reason).strip():
        bits.append(str(reason).strip().rstrip("."))
    elif action:
        bits.append(f"Suggested move: {action.replace('_', ' ')}")
    if top_labels:
        shown = ", ".join(top_labels[:3])
        bits.append(f"Top drivers on this table: {shown}")
    if not bits:
        return "Run triage to see why the model ranked this move."
    return ". ".join(bits) + "."


def format_explain(
    expl: Any,
    *,
    text_cols: list[str] | None = None,
    high_card_cols: list[str] | None = None,
    max_bars: int = 6,
    action_reason: str | None = None,
    action: str | None = None,
) -> dict[str, Any]:
    """Turn ExplainResult (or dict-like) into drawer payload with bar widths."""
    if expl is None:
        return {}
    if hasattr(expl, "model_dump"):
        raw = expl.model_dump()
    elif isinstance(expl, dict):
        raw = expl
    else:
        raw = {
            "method": getattr(expl, "method", "unknown"),
            "importances": list(getattr(expl, "importances", []) or []),
            "notes": getattr(expl, "notes", ""),
        }
    items = list(raw.get("importances") or [])
    vals = []
    for it in items:
        try:
            vals.append(abs(float(it.get("importance") or 0.0)))
        except (TypeError, ValueError):
            vals.append(0.0)
    vmax = max(vals) if vals else 0.0
    bars: list[dict[str, Any]] = []
    for it, v in zip(items[:max_bars], vals[:max_bars]):
        feat = str(it.get("feature") or "feature")
        kind = feature_kind(feat, text_cols=text_cols, high_card_cols=high_card_cols)
        label = human_feature(feat)
        pct = round(100.0 * v / vmax, 1) if vmax > 1e-12 else 0.0
        bars.append({
            "feature": feat,
            "label": label,
            "importance": round(float(it.get("importance") or 0.0), 5),
            "pct": pct,
            "kind": kind,
            "kind_label": _KIND_PLAIN.get(kind, kind),
        })
    top_labels = [b["label"] for b in bars[:3]]
    narrative = why_this_move(action=action, reason=action_reason, top_labels=top_labels)
    return {
        "method": raw.get("method") or "permutation_importance",
        "notes": raw.get("notes") or "Mock permutation importance (offline).",
        "bars": bars,
        "top_labels": top_labels,
        "why": narrative,
        "n": len(bars),
    }
