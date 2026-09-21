from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from tabpfn_hack_core.core.backend import fit_mock, fit_predict_backend
from tabpfn_hack_core.tools_api import (
    ActionItem,
    BackendMode,
    CompareBaselineResult,
    SuggestActionsResult,
)

class _BaselineActionsMixin:
    # ---------------------------------------------------- compare_baseline
    def compare_baseline(
        self,
        table_id: str,
        label_col: str | None = None,
        mode: BackendMode | str = BackendMode.mock,
        baseline: str = "sklearn_hist_gbm",
        test_size: float = 0.2,
        random_state: int = 42,
        thinking_effort: str | None = None,
    ) -> CompareBaselineResult:
        # Run primary (requested mode) then a dedicated baseline mock
        primary = self.fit_predict(
            table_id,
            label_col=label_col,
            mode=mode,
            test_size=test_size,
            random_state=random_state,
            thinking_effort=thinking_effort,
        )
        df = self._get(table_id)
        label = label_col or self.domain.label_col
        X = self._feature_frame(df, label)
        y = df[label].to_numpy()
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state,
            stratify=y if len(np.unique(y)) > 1 else None,
        )
        prefer = "hist_gbm" if baseline == "sklearn_hist_gbm" else "logistic"
        base = fit_mock(
            X_train.reset_index(drop=True),
            y_train,
            X_test.reset_index(drop=True),
            y_test,
            text_cols=self.domain.text_cols,
            high_card_cols=self.domain.high_card_cols,
            prefer=prefer,  # type: ignore[arg-type]
        )

        tabpfn_metrics = primary.metrics
        baseline_metrics = base.metrics
        delta = {
            k: float(tabpfn_metrics.get(k, 0) - baseline_metrics.get(k, 0))
            for k in set(tabpfn_metrics) | set(baseline_metrics)
            if isinstance(tabpfn_metrics.get(k), (int, float))
            and isinstance(baseline_metrics.get(k), (int, float))
        }
        mode_s = primary.mode.value if hasattr(primary.mode, "value") else str(primary.mode)
        gcol = getattr(self.domain, "group_col", None)
        tcol = getattr(self.domain, "time_col", None)
        text_n = len(getattr(self.domain, "text_cols", []) or [])
        high_n = len(getattr(self.domain, "high_card_cols", []) or [])
        think_bits = []
        if mode_s == "thinking":
            think_bits.append(f"thinking_effort={primary.thinking_effort or 'medium'}")
            if primary.group_col or gcol:
                think_bits.append(f"group_col={primary.group_col or gcol}")
            if primary.group_time_col or tcol:
                think_bits.append(f"group_time_col={primary.group_time_col or tcol}")
        think_s = (" · " + " · ".join(think_bits)) if think_bits else ""
        wins = [k for k, v in delta.items() if isinstance(v, float) and v > 0.0005]
        narrative = (
            f"Judge card — `{primary.backend}` mode={mode_s}{think_s} vs `{baseline}` "
            f"on the same split. "
            f"Δ accuracy={delta.get('accuracy', float('nan')):+.4f}, "
            f"Δ f1={delta.get('f1', float('nan')):+.4f}, "
            f"Δ roc_auc={delta.get('roc_auc', float('nan')):+.4f}, "
            f"Δ AP={delta.get('avg_precision', float('nan')):+.4f}. "
            f"Domain hints: text_cols={text_n}, high_card_cols={high_n}, "
            f"group={gcol or '—'}, time={tcol or '—'}. "
            + (
                f"Primary leads on: {', '.join(wins)}."
                if wins
                else "No clear positive Δ on this mock/live split."
            )
        )
        if primary.thinking_narrative:
            narrative = narrative + " Thinking: " + primary.thinking_narrative
        judge_card = {
            "mode": mode_s,
            "backend": primary.backend,
            "baseline": baseline,
            "thinking_effort": primary.thinking_effort,
            "group_col": primary.group_col or gcol,
            "group_time_col": primary.group_time_col or tcol,
            "text_cols": list(getattr(self.domain, "text_cols", []) or []),
            "high_card_cols": list(getattr(self.domain, "high_card_cols", []) or []),
            "delta": {k: round(float(v), 4) for k, v in delta.items()},
            "wins": wins,
            "thinking_narrative": primary.thinking_narrative,
            "headline": (
                f"{mode_s} Δacc={delta.get('accuracy', float('nan')):+.3f} "
                f"Δauc={delta.get('roc_auc', float('nan')):+.3f} vs HistGBM"
            ),
        }
        result = CompareBaselineResult(
            tabpfn_metrics=tabpfn_metrics,
            baseline_metrics=baseline_metrics,
            delta=delta,
            narrative=narrative,
            judge_card=judge_card,
        )
        self.last_baseline = result
        return result

    # ---------------------------------------------------- suggest_actions
    def suggest_actions(
        self,
        table_id: str,
        proba_col: str = "proba_1",
        threshold_high: float | None = None,
        threshold_mid: float | None = None,
        max_rows: int = 50,
    ) -> SuggestActionsResult:
        if self.last_predictions is None or proba_col not in self.last_predictions.columns:
            self.fit_predict(table_id, mode=BackendMode.mock)

        assert self.last_predictions is not None
        pred = self.last_predictions
        items: list[ActionItem] = []
        counts: dict[str, int] = {}
        id_col = self.domain.id_col or "row_id"

        playbook = list(self.domain.playbook)
        if playbook:
            # First matching step wins — preserve YAML order (author controls priority).
            ordered = playbook
        else:
            ordered = None
            thr_high = (
                threshold_high
                if threshold_high is not None
                else self.domain.action_thresholds.high
            )
            thr_mid_high = self.domain.action_thresholds.mid_high
            thr_mid = (
                threshold_mid
                if threshold_mid is not None
                else self.domain.action_thresholds.mid
            )
            thr_mid_low = self.domain.action_thresholds.mid_low
            actions_map = self.domain.actions

        for _, row in pred.head(max_rows).iterrows():
            proba = float(row[proba_col])
            action = "monitor"
            reason = f"proba {proba:.3f}"

            if ordered is not None:
                for step in ordered:
                    if proba < step.min_proba:
                        continue
                    if step.when_col is not None:
                        val = row.get(step.when_col)
                        if str(val) != str(step.when_equals):
                            continue
                    action = step.action
                    reason = step.reason or (
                        f"proba {proba:.3f} >= {step.min_proba} → {step.action}"
                    )
                    break
            else:
                if proba >= thr_high:
                    action = actions_map.get("high", "escalate")
                    reason = f"proba {proba:.3f} >= high {thr_high}"
                elif thr_mid_high is not None and proba >= thr_mid_high:
                    action = actions_map.get("mid_high", actions_map.get("mid", "review"))
                    reason = f"proba {proba:.3f} >= mid_high {thr_mid_high}"
                elif proba >= thr_mid:
                    action = actions_map.get("mid", "review")
                    reason = f"proba {proba:.3f} >= mid {thr_mid}"
                elif thr_mid_low is not None and proba >= thr_mid_low:
                    action = actions_map.get("mid_low", actions_map.get("low", "monitor"))
                    reason = f"proba {proba:.3f} >= mid_low {thr_mid_low}"
                else:
                    action = actions_map.get("low", "monitor")
                    reason = f"proba {proba:.3f} < mid {thr_mid}"

            rid = str(row.get(id_col, row.get("row_id", row.name)))
            items.append(ActionItem(row_id=rid, action=action, proba=proba, reason=reason))
            counts[action] = counts.get(action, 0) + 1

        result = SuggestActionsResult(
            items=items,
            counts=counts,
            disclaimer=self.domain.disclaimer,
        )
        self.last_actions = result
        return result
