"""Learning-curve wire for desk eval (judge-repro split)."""
from __future__ import annotations

from typing import Any

from tabpfn_hack_core.core.learning_curve import small_n_learning_curve


def maybe_learning_curve(sess: Any, table_id: str, warnings: list[str]) -> dict[str, Any] | None:
    """Run small-n curve; append warn on failure; never raise."""
    try:
        df_lc = sess.tables[table_id]
        label_lc = sess.domain.label_col
        X_lc = sess._feature_frame(df_lc, label_lc)
        y_lc = df_lc[label_lc].to_numpy()
        return small_n_learning_curve(
            X_lc,
            y_lc,
            text_cols=list(getattr(sess.domain, "text_cols", []) or []),
            high_card_cols=list(getattr(sess.domain, "high_card_cols", []) or []),
        )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"learning_curve skipped: {exc}")
        return None
