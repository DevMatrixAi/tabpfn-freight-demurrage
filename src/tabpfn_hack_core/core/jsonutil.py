"""Shared helpers for pipeline mixins."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def jsonable(v: Any) -> Any:
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if pd.isna(v):
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v
