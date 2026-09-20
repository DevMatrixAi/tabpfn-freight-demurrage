"""One-command demo: load → profile → fit → explain → baseline → actions → report."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode


def generate_synthetic_table(
    n: int = 1000,
    out: Path | str | None = None,
    seed: int = 42,
) -> Path:
    """Create a messy synthetic table matching domain.yaml schema."""
    rng = np.random.default_rng(seed)
    groups = [f"GRP-{c}" for c in "ABCDEFGH"]
    low_cats = ["alpha", "beta", "gamma", "delta"]
    phrases = [
        "routine check looks fine",
        "urgent spike detected in sensor stream",
        "missing context after handoff",
        "customer reported delay and incomplete fields",
        "anomaly cluster near threshold",
        "follow-up needed for high card code mismatch",
        "",
    ]

    rows = []
    base_ts = pd.Timestamp("2026-01-01", tz="UTC")
    for i in range(n):
        group = groups[int(rng.integers(0, len(groups)))]
        x1 = float(rng.normal(0, 1))
        x2 = float(rng.normal(1, 2))
        x3 = float(rng.normal(-0.5, 1.5))
        x4 = float(rng.exponential(1.0))
        x5 = float(rng.uniform(-3, 3))
        if rng.random() < 0.12:
            x1 = np.nan
        if rng.random() < 0.10:
            x3 = np.nan
        if rng.random() < 0.08:
            x5 = np.nan

        note = phrases[int(rng.integers(0, len(phrases)))]
        if rng.random() < 0.15:
            note = ""

        score = (
            0.8 * (0 if np.isnan(x2) else x2)
            + 1.2 * (1 if "urgent" in note or "anomaly" in note else 0)
            + 0.5 * (0 if np.isnan(x4) else np.log1p(x4))
            + float(rng.normal(0, 0.8))
        )
        target = int(score > 1.0)

        rows.append(
            {
                "row_id": f"ROW-{i + 1:06d}",
                "event_ts": (base_ts + pd.to_timedelta(int(i * 7 + int(rng.integers(0, 5))), unit="min")).isoformat(),
                "group_id": group,
                "entity_id": f"ENT-{int(rng.integers(1, 400)):04d}",
                "code_a": f"CA-{int(rng.integers(1, 800)):04d}",
                "code_b": f"CB-{int(rng.integers(1, 600)):04d}",
                "note_text": note,
                "x1": x1,
                "x2": x2,
                "x3": x3,
                "x4": x4,
                "x5": x5,
                "cat_low": low_cats[int(rng.integers(0, len(low_cats)))],
                "target": target,
            }
        )

    df = pd.DataFrame(rows)
    if out is None:
        out_path = Path("data/synthetic_table.csv")
    else:
        out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


def run_demo(
    root: Path | None = None,
    mode: str = "mock",
    data_path: Path | None = None,
    domain_path: Path | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    root = Path(root or Path.cwd())
    out_dir = Path(out_dir or (root / "artifacts"))
    out_dir.mkdir(parents=True, exist_ok=True)

    domain = load_domain(domain_path or (root / "domain.yaml"))
    session = PipelineSession(domain=domain, root=root)

    if data_path is not None:
        csv_path = Path(data_path)
    elif domain.data_path:
        csv_path = root / domain.data_path
    else:
        csv_path = root / "data" / "synthetic_table.csv"
    if not Path(csv_path).is_file():
        if domain.name in {"equipment-size", "inland-mode"} and data_path is None:
            try:
                from tabpfn_hack_core.demo.gen_coda_packs import (
                    gen_equipment_size,
                    gen_inland_mode,
                )
            except ImportError as exc:  # pragma: no cover
                raise FileNotFoundError(
                    f"Domain data_path missing: {csv_path} (pack={domain.name})"
                ) from exc
            Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
            if domain.name == "equipment-size":
                gen_equipment_size(n=250, seed=42).to_csv(csv_path, index=False)
            else:
                gen_inland_mode(n=250, seed=43).to_csv(csv_path, index=False)
        elif domain.data_path and data_path is None:
            raise FileNotFoundError(
                f"Domain data_path missing: {csv_path} "
                f"(pack={domain.name})"
            )
        else:
            generate_synthetic_table(n=1000, out=csv_path, seed=42)

    loaded = session.load_table(path=str(csv_path), table_id="demo")
    session.profile(loaded.table_id)

    effective = mode or "mock"
    if effective in ("auto",):
        effective = "plus"

    pred_path = out_dir / "predictions.json"
    fit = session.fit_predict(
        loaded.table_id,
        mode=BackendMode(effective) if effective != "auto" else BackendMode.mock,
        predictions_path=pred_path,
    )
    session.explain(loaded.table_id, mode=fit.mode)
    try:
        session.compare_baseline(loaded.table_id, mode=fit.mode)
    except Exception:  # noqa: BLE001
        pass
    session.suggest_actions(loaded.table_id)

    title = (
        f"{domain.name} demo report (synthetic)"
        if domain.name != "generic-messy-table"
        else "tabpfn-hack-core demo report (synthetic)"
    )
    report = session.export_report(
        loaded.table_id,
        title=title,
        formats=["markdown", "json"],
        out_dir=str(out_dir),
    )

    return {
        "mode": fit.mode.value,
        "backend": fit.backend,
        "metrics": fit.metrics,
        "warning": fit.warning,
        "report_path": report.paths.get("markdown"),
        "predictions_path": str(pred_path),
        "n_rows": loaded.n_rows,
    }
