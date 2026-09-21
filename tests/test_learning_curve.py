"""Small-n learning curve showcase."""
from __future__ import annotations

import numpy as np
import pandas as pd

from tabpfn_hack_core.core.learning_curve import small_n_learning_curve


def test_small_n_learning_curve_mock():
    rng = np.random.default_rng(0)
    n = 80
    X = pd.DataFrame({
        "dwell_days": rng.normal(5, 2, n),
        "free_days": rng.integers(3, 10, n),
        "notes": rng.choice(["gate delay", "vessel late", "ok", "weather"], n),
        "vessel_id": rng.choice([f"V{i}" for i in range(12)], n),
    })
    y = (X["dwell_days"] > 5).astype(int).to_numpy()
    out = small_n_learning_curve(
        X, y, text_cols=["notes"], high_card_cols=["vessel_id"], ns=(16, 32, 64)
    )
    assert out["rows"]
    assert out["rows"][0]["n_train"] == 16
    assert "accuracy" in out["rows"][0]["metrics"]
    assert "few-shot" in out["headline"].lower() or "Small-n" in out["headline"]
