from __future__ import annotations
"""What-if simulation helpers for PipelineSession (synthetic desk sandbox)."""

from typing import Any

import pandas as pd

from tabpfn_hack_core.core.backend import fit_predict_backend
from tabpfn_hack_core.core.jsonutil import jsonable
from tabpfn_hack_core.tools_api import BackendMode


class _WhatIfMixin:

    def _action_for_proba(self, row: pd.Series, proba: float) -> tuple[str, str]:
        """Map a single row + proba through domain playbook / thresholds."""
        playbook = list(self.domain.playbook)
        if playbook:
            for step in playbook:
                if proba < step.min_proba:
                    continue
                if step.when_col is not None:
                    val = row.get(step.when_col)
                    if str(val) != str(step.when_equals):
                        continue
                return step.action, step.reason or (
                    f"proba {proba:.3f} >= {step.min_proba} → {step.action}"
                )
            return "monitor", f"proba {proba:.3f}"
        thr = self.domain.action_thresholds
        actions_map = self.domain.actions
        if proba >= thr.high:
            return actions_map.get("high", "escalate"), f"proba {proba:.3f} >= high {thr.high}"
        if thr.mid_high is not None and proba >= thr.mid_high:
            return actions_map.get("mid_high", actions_map.get("mid", "review")), (
                f"proba {proba:.3f} >= mid_high {thr.mid_high}"
            )
        if proba >= thr.mid:
            return actions_map.get("mid", "review"), f"proba {proba:.3f} >= mid {thr.mid}"
        if thr.mid_low is not None and proba >= thr.mid_low:
            return actions_map.get("mid_low", actions_map.get("low", "monitor")), (
                f"proba {proba:.3f} >= mid_low {thr.mid_low}"
            )
        return actions_map.get("low", "monitor"), f"proba {proba:.3f} < mid {thr.mid}"

    def what_if(
        self,
        table_id: str,
        row_id: str,
        overrides: dict[str, Any] | None = None,
        *,
        label_col: str | None = None,
        mode: BackendMode | str = BackendMode.mock,
        id_col: str | None = None,
        random_state: int = 42,
    ) -> dict[str, Any]:
        """Synthetic what-if: hold out one row, score before/after feature tweaks.

        Does not mutate the stored table. Label as simulation in UI.
        Special key ``divert`` (truthy) sets inland_can_beat_freedays=1 and
        bumps free_days_left by +3 (capped synthetic divert effect).
        """
        df = self._get(table_id)
        label = label_col or self.domain.label_col
        if label not in df.columns:
            raise ValueError(f"label_col {label!r} not in table")
        key = id_col or self.domain.id_col or "container_id"
        if key not in df.columns:
            raise ValueError(f"id_col {key!r} not in table")
        matches = df.index[df[key].astype(str) == str(row_id)].tolist()
        if not matches:
            raise KeyError(f"No row with {key}={row_id!r}")
        idx = matches[0]
        train_df = df.drop(index=idx)
        if len(train_df) < 4:
            raise ValueError("Need at least 4 other rows to fit a what-if model")

        before_row = df.loc[[idx]].copy()
        after_row = before_row.copy()
        ov = dict(overrides or {})
        divert = ov.pop("divert", None)
        if divert is not None and str(divert).lower() not in {"", "0", "false", "no", "off"}:
            if "inland_can_beat_freedays" in after_row.columns:
                after_row.loc[:, "inland_can_beat_freedays"] = 1
            if "free_days_left" in after_row.columns:
                cur = float(after_row.iloc[0]["free_days_left"])
                after_row.loc[:, "free_days_left"] = cur + 3.0
            ov.setdefault("_divert_applied", True)
        for col, val in ov.items():
            if col.startswith("_"):
                continue
            if col not in after_row.columns:
                raise ValueError(f"Unknown override column: {col}")
            after_row.loc[:, col] = val

        X_train = self._feature_frame(train_df, label)
        y_train = train_df[label].to_numpy()
        X_before = self._feature_frame(before_row, label)
        X_after = self._feature_frame(after_row, label)
        y_dummy = before_row[label].to_numpy()

        gcol = self.domain.group_col
        tcol = self.domain.time_col
        result_b = fit_predict_backend(
            mode,
            X_train.reset_index(drop=True),
            y_train,
            X_before.reset_index(drop=True),
            y_dummy,
            group_col=gcol,
            group_time_col=tcol,
            text_cols=self.domain.text_cols,
            high_card_cols=self.domain.high_card_cols,
        )
        result_a = fit_predict_backend(
            mode,
            X_train.reset_index(drop=True),
            y_train,
            X_after.reset_index(drop=True),
            y_dummy,
            group_col=gcol,
            group_time_col=tcol,
            text_cols=self.domain.text_cols,
            high_card_cols=self.domain.high_card_cols,
        )
        proba_before = float(result_b.y_proba[0])
        proba_after = float(result_a.y_proba[0])
        act_b, reason_b = self._action_for_proba(before_row.iloc[0], proba_before)
        act_a, reason_a = self._action_for_proba(after_row.iloc[0], proba_after)

        shown_overrides: dict[str, Any] = {}
        for col in after_row.columns:
            bv, av = before_row.iloc[0][col], after_row.iloc[0][col]
            if pd.isna(bv) and pd.isna(av):
                continue
            try:
                changed = bv != av
            except Exception:
                changed = str(bv) != str(av)
            if changed:
                shown_overrides[col] = {"before": jsonable(bv), "after": jsonable(av)}

        return {
            "simulation": True,
            "label": "what-if simulation (synthetic)",
            "row_id": str(row_id),
            "id_col": key,
            "label_col": label,
            "mode": result_b.mode.value if hasattr(result_b.mode, "value") else str(result_b.mode),
            "backend": result_b.backend,
            "warning": result_b.warning or result_a.warning,
            "proba_before": proba_before,
            "proba_after": proba_after,
            "delta_proba": proba_after - proba_before,
            "action_before": act_b,
            "action_after": act_a,
            "reason_before": reason_b,
            "reason_after": reason_a,
            "overrides_applied": shown_overrides,
            "baseline_features": {
                "free_days_left": jsonable(before_row.iloc[0].get("free_days_left")),
                "projected_demurrage_usd": jsonable(before_row.iloc[0].get("projected_demurrage_usd")),
                "blank_sailing": jsonable(before_row.iloc[0].get("blank_sailing")),
                "inland_can_beat_freedays": jsonable(before_row.iloc[0].get("inland_can_beat_freedays")),
            },
        }
