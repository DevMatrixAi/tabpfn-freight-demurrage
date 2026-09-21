"""Robot / TMS consumer HTTP API — decisions only, not crane control.

Wraps the same PipelineSession triage + suggest_actions path the ops board uses.
Humans (desk UI) or robots (this API) call the same action playbook.
"""
from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Any

import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import find_project_root, load_domain
from tabpfn_hack_core.tools_api import BackendMode

try:
    from apps.desk.packs import DEFAULT_PACK, build_packs
except ImportError:
    from packs import DEFAULT_PACK, build_packs  # type: ignore

_ROOT = find_project_root(Path(__file__).resolve().parents[2])
PACKS = build_packs(_ROOT)
METRIC_KEYS = ("accuracy", "f1", "roc_auc", "avg_precision")
PASSTHROUGH_COLS = ("carrier", "client_id", "trade_lane", "terminal", "vessel_id")

router = APIRouter(
    prefix="/api/v1",
    tags=["robot/TMS consumer API"],
)


class TriageRequest(BaseModel):
    """Triage pack CSV, fixture, or inline rows."""

    pack: str | None = Field(
        default=None,
        description="Domain pack id (freight-demurrage, equipment-size, inland-mode, air-freight, stow-fit).",
    )
    fixture: str | None = Field(
        default=None,
        description="Optional fixture adapter name: terminal49 | project44 | edi_315.",
    )
    rows: list[dict[str, Any]] | None = Field(
        default=None,
        description="Inline CSV-shaped rows (dicts). Multi-client/carrier fields pass through.",
    )
    mode: str = Field(
        default="mock",
        description="Backend mode: mock | plus | thinking | fast. Mock works without TABPFN_TOKEN.",
    )
    max_rows: int = Field(default=50, ge=1, le=500, description="Max action rows to return.")
    client_id: str | None = Field(
        default=None,
        description="Optional client label echoed on the response (multi-client TMS).",
    )
    carrier: str | None = Field(
        default=None,
        description="Optional carrier label echoed on the response (multi-carrier TMS).",
    )


class ActionsRequest(BaseModel):
    """Fit + suggest_actions on rows."""

    pack: str | None = Field(default=None, description="Domain pack id; default freight-demurrage.")
    rows: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Rows to score. Extra columns (carrier, client_id, …) pass through on items.",
    )
    mode: str = Field(default="mock", description="mock | plus | thinking | fast")
    max_rows: int = Field(default=50, ge=1, le=500)
    client_id: str | None = None
    carrier: str | None = None



class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "robot/TMS consumer API"
    has_token: bool
    packs: list[str]
    note: str = (
        "Decisions API only — wraps TabPFN suggest_actions / triage. "
        "Not crane control, not a live TOS."
    )


def _has_token() -> bool:
    return bool(os.environ.get("TABPFN_TOKEN", "").strip())


def _resolve_mode(requested: str) -> tuple[BackendMode, str | None]:
    req = (requested or "mock").lower().strip()
    try:
        mode = BackendMode(req)
    except ValueError:
        return BackendMode.mock, f"Unknown mode {requested!r}; using mock"
    warn = None
    if mode in {BackendMode.plus, BackendMode.thinking, BackendMode.fast} and not _has_token():
        warn = (
            f"TABPFN_TOKEN not set; requested mode={mode.value} will fall back to mock "
            "(set TABPFN_TOKEN in env for Plus/Thinking/Fast)."
        )
    return mode, warn


def _metric_slice(metrics: dict[str, float] | None) -> dict[str, float]:
    if not metrics:
        return {}
    return {
        k: float(metrics[k])
        for k in METRIC_KEYS
        if k in metrics and isinstance(metrics[k], (int, float))
    }


def _pack_id(pack: str | None) -> str:
    pid = (pack or DEFAULT_PACK).strip()
    if pid not in PACKS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown pack {pack!r}. Choose one of: {sorted(PACKS)}",
        )
    return pid


def _session(pack: str) -> PipelineSession:
    return PipelineSession(domain=load_domain(PACKS[pack]["domain"]), root=_ROOT)


def _load_fixture(name: str) -> pd.DataFrame:
    from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters

    try:
        adapter = get_adapter(name)
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown fixture {name!r}. Available: {list_adapters()}",
        ) from exc
    return adapter.to_dataframe()


def _load_table(
    sess: PipelineSession,
    pack: str,
    *,
    rows: list[dict[str, Any]] | None,
    fixture: str | None,
    table_id: str = "robot",
) -> tuple[str, int]:
    if rows:
        df = pd.DataFrame(rows)
        sess.tables[table_id] = df
        return table_id, len(df)
    if fixture:
        df = _load_fixture(fixture)
        sess.tables[table_id] = df
        return table_id, len(df)
    csv_path = PACKS[pack]["csv"]
    if not csv_path.is_file():
        raise HTTPException(status_code=404, detail=f"Pack CSV missing: {csv_path}")
    result = sess.load_table(path=str(csv_path), table_id=table_id)
    return result.table_id, result.n_rows


def _actions_payload(
    sess: PipelineSession,
    tid: str,
    max_rows: int,
    *,
    request_client_id: str | None = None,
    request_carrier: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    actions = sess.suggest_actions(tid, max_rows=max_rows)
    df = sess.tables[tid]
    id_col = sess.domain.id_col or "row_id"
    items: list[dict[str, Any]] = []
    for a in actions.items:
        item: dict[str, Any] = {
            "row_id": a.row_id,
            "proba": round(float(a.proba), 4),
            "action": a.action,
            "reason": a.reason,
            "carrier": request_carrier,
            "client_id": request_client_id,
            "extras": {},
        }
        if id_col in df.columns:
            hit = df.loc[df[id_col].astype(str) == str(a.row_id)]
            if len(hit):
                row = hit.iloc[0]
                for col in PASSTHROUGH_COLS:
                    if col in df.columns and str(row.get(col, "") or ""):
                        val = row[col]
                        if col == "carrier" and item["carrier"] is None:
                            item["carrier"] = str(val)
                        elif col == "client_id" and item["client_id"] is None:
                            item["client_id"] = str(val)
                        else:
                            item["extras"][col] = val if not hasattr(val, "item") else val.item()
        items.append(item)
    return items, dict(actions.counts)


def _disclaimer(sess: PipelineSession) -> str:
    return str(sess.domain.disclaimer or "")


@router.get("/health", response_model=HealthResponse, summary="Health (robot/TMS)")
def health() -> HealthResponse:
    return HealthResponse(has_token=_has_token(), packs=sorted(PACKS))


@router.post("/triage", summary="Triage → metrics + playbook actions")
def triage(body: TriageRequest) -> dict[str, Any]:
    """compare_baseline + suggest_actions (decisions API, not crane control)."""
    pack = _pack_id(body.pack)
    backend_mode, resolve_warn = _resolve_mode(body.mode)
    sess = _session(pack)
    tid, n_rows = _load_table(sess, pack, rows=body.rows, fixture=body.fixture)
    if n_rows < 4:
        # Match desk: pad tiny fixture adapters with pack CSV so fit_predict can run.
        csv_path = PACKS[pack]["csv"]
        if csv_path.is_file():
            combined = pd.concat(
                [pd.read_csv(csv_path), sess.tables[tid]], ignore_index=True
            )
            sess.tables[tid] = combined
            n_rows = len(combined)
        if n_rows < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Need at least 4 rows to triage (got {n_rows}).",
            )
    test_size = 0.3 if n_rows >= 10 else 0.25
    t0 = time.perf_counter()
    cmp_ = sess.compare_baseline(
        tid, mode=backend_mode, baseline="sklearn_hist_gbm", test_size=test_size
    )
    elapsed = time.perf_counter() - t0
    items, counts = _actions_payload(
        sess,
        tid,
        body.max_rows,
        request_client_id=body.client_id,
        request_carrier=body.carrier,
    )
    warnings: list[str] = []
    if resolve_warn:
        warnings.append(resolve_warn)
    if sess.last_warning:
        warnings.append(str(sess.last_warning))
    effective = sess.last_mode
    return {
        "ok": True,
        "api": "robot/TMS consumer API",
        "scope": "decisions only — not crane control",
        "pack": pack,
        "pack_label": PACKS[pack]["label"],
        "n_rows": n_rows,
        "mode_requested": backend_mode.value,
        "mode": effective.value if hasattr(effective, "value") else str(effective),
        "backend": sess.last_backend,
        "has_token": _has_token(),
        "elapsed_s": round(elapsed, 3),
        "warning": " · ".join(warnings) if warnings else None,
        "client_id": body.client_id,
        "carrier": body.carrier,
        "metrics": _metric_slice(cmp_.tabpfn_metrics),
        "baseline_metrics": _metric_slice(cmp_.baseline_metrics),
        "delta": _metric_slice(cmp_.delta),
        "baseline_narrative": cmp_.narrative,
        "action_counts": counts,
        "actions": items,
        "disclaimer": _disclaimer(sess),
    }


@router.post("/actions", summary="Score rows → suggested actions")
def actions(body: ActionsRequest) -> dict[str, Any]:
    """Fit + suggest_actions (same playbook as triage/desk)."""
    pack = _pack_id(body.pack)
    backend_mode, resolve_warn = _resolve_mode(body.mode)
    sess = _session(pack)
    tid, n_rows = _load_table(sess, pack, rows=body.rows, fixture=None)
    if n_rows < 4:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 4 rows to score (got {n_rows}).",
        )
    test_size = 0.3 if n_rows >= 10 else 0.25
    t0 = time.perf_counter()
    fit = sess.fit_predict(tid, mode=backend_mode, test_size=test_size)
    elapsed = time.perf_counter() - t0
    items, counts = _actions_payload(
        sess,
        tid,
        body.max_rows,
        request_client_id=body.client_id,
        request_carrier=body.carrier,
    )
    warnings: list[str] = []
    if resolve_warn:
        warnings.append(resolve_warn)
    if fit.warning:
        warnings.append(str(fit.warning))
    if sess.last_warning and str(sess.last_warning) not in warnings:
        warnings.append(str(sess.last_warning))
    return {
        "ok": True,
        "api": "robot/TMS consumer API",
        "scope": "decisions only — not crane control",
        "pack": pack,
        "n_rows": n_rows,
        "mode_requested": backend_mode.value,
        "mode": fit.mode.value if hasattr(fit.mode, "value") else str(fit.mode),
        "backend": fit.backend,
        "has_token": _has_token(),
        "elapsed_s": round(elapsed, 3),
        "warning": " · ".join(warnings) if warnings else None,
        "client_id": body.client_id,
        "carrier": body.carrier,
        "metrics": _metric_slice(fit.metrics),
        "action_counts": counts,
        "actions": items,
        "disclaimer": _disclaimer(sess),
    }


def register_robot_api(app: FastAPI) -> None:
    """Mount robot/TMS routes (OpenAPI /docs)."""
    app.include_router(router)
    # Enrich OpenAPI description without renaming the human ops board.
    desc = (app.description or "").strip()
    blurb = (
        "Also exposes a **robot/TMS consumer API** under `/api/v1/*` "
        "(decisions only — same suggest_actions / triage path as the desk; not crane control). "
        "Humans or robots call the same action API."
    )
    if "robot/TMS" not in desc:
        app.description = f"{desc}\n\n{blurb}".strip() if desc else blurb
