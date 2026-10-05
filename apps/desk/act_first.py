"""Cost-based flagging: act on a container when expected fee (risk x fee) beats the action cost.

``DESK_ACTION_COST`` (default $300) is the assumed cost of one intervention
(rebook, expedite, call the terminal). Same rule as the recorded replay receipt.
"""
from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd


def action_cost() -> float:
    try:
        v = float(os.environ.get("DESK_ACTION_COST", "300"))
        return v if v > 0 else 300.0
    except ValueError:
        return 300.0


def _net(y: np.ndarray, p: np.ndarray, fee: np.ndarray, cost: float) -> dict[str, float]:
    flag = p * fee > cost
    caught = float(fee[flag & (y == 1)].sum())
    spent = float(cost * flag.sum())
    return {
        "n_flagged": int(flag.sum()),
        "fees_avoided": round(caught),
        "action_spend": round(spent),
        "net_savings": round(caught - spent),
        "missed_fees": round(float(fee[(~flag) & (y == 1)].sum())),
    }


def build_act_first(
    pred: pd.DataFrame | None,
    *,
    id_col: str,
    money_col: str | None,
    top_n: int = 5,
) -> dict[str, Any] | None:
    """Top containers by expected fee, plus net savings for the model and HistGBM."""
    if pred is None or "proba_1" not in pred.columns or not money_col or money_col not in pred.columns:
        return None
    cost = action_cost()
    p = pred["proba_1"].astype(float).to_numpy()
    fee = pd.to_numeric(pred[money_col], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    exp = p * fee
    order = np.argsort(-exp)
    items = []
    for i in order[:top_n]:
        if exp[i] <= cost:
            break
        row = pred.iloc[int(i)]
        items.append({
            "row_id": str(row.get(id_col, i)),
            "proba": round(float(p[i]), 4),
            "fee": round(float(fee[i])),
            "expected": round(float(exp[i])),
            "estimate": str(row.get("score_source", "")) == "estimate",
        })
    flagged = []
    for i in order:
        if exp[i] <= cost:
            break
        row = pred.iloc[int(i)]
        flagged.append({
            "row_id": str(row.get(id_col, i)),
            "proba": round(float(p[i]), 4),
            "fee": round(float(fee[i])),
            "expected": round(float(exp[i])),
            "estimate": str(row.get("score_source", "")) == "estimate",
        })
    top_risk = None
    if len(p):
        j = int(np.argmax(p))
        top_risk = {
            "row_id": str(pred.iloc[j].get(id_col, j)),
            "proba": round(float(p[j]), 4),
            "fee": round(float(fee[j])),
            "in_top": any(it["row_id"] == str(pred.iloc[j].get(id_col, j)) for it in items),
        }
    out: dict[str, Any] = {
        "top_risk": top_risk,
        "action_cost": round(cost),
        "items": items,
        "flagged": flagged,
        "n_rows": int(len(pred)),
        "n_flagged": int((exp > cost).sum()),
        "model": None,
        "baseline": None,
    }
    if "y_true" in pred.columns:
        y = pd.to_numeric(pred["y_true"], errors="coerce").fillna(0).astype(int).to_numpy()
        out["model"] = _net(y, p, fee, cost)
        if "proba_hist_gbm" in pred.columns:
            pb = pred["proba_hist_gbm"].astype(float).to_numpy()
            out["baseline"] = _net(y, pb, fee, cost)
    return out


def group_by_move(
    flagged: list[dict[str, Any]], action_of: dict[str, tuple[str, str]]
) -> list[dict[str, Any]]:
    """Group flagged containers by suggested move; biggest expected fee first.

    ``action_of`` maps row_id -> (action key, reason). Each group carries its top
    container so the desk can show one example per move.
    """
    groups: dict[str, dict[str, Any]] = {}
    for it in flagged:
        act, reason = action_of.get(str(it["row_id"]), ("monitor", ""))
        if act in ("monitor", "", "authorize_fee"):
            # Flagged = likely fee beats the action cost and the savings count it as avoided,
            # so "watch" undersells it and "pay the fee" would contradict the savings math.
            act = "call_terminal"
            reason = (
                "No reroute or rebooking fits this container, so the quickest fix is to get it collected: push the "
                "terminal or trucker to pick it up before its free days run out. Its likely cost is far above the $300 cost of acting."
            )
        g = groups.setdefault(act, {"action": act, "n": 0, "at_stake": 0, "expected": 0, "top": None})
        g["n"] += 1
        g["at_stake"] += int(it["fee"])
        g["expected"] += int(it["expected"])
        if g["top"] is None:
            g["top"] = dict(it, action=act, reason=reason)
    return sorted(groups.values(), key=lambda g: -g["expected"])
