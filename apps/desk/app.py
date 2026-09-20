"""Lean FastAPI + Jinja demurrage desk wrapping PipelineSession + fixture adapters."""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_SRC))

from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters  # noqa: E402
from tabpfn_hack_core.core.pipeline import PipelineSession  # noqa: E402
from tabpfn_hack_core.domain import find_project_root, load_domain  # noqa: E402
from tabpfn_hack_core.tools_api import BackendMode  # noqa: E402

try:
    from apps.desk.wow import run_blank_head, run_what_if, sample_ids  # noqa: E402
except ImportError:  # uvicorn app-dir=.
    from wow import run_blank_head, run_what_if, sample_ids  # type: ignore  # noqa: E402

DESK_DIR = Path(__file__).resolve().parent
ROOT = find_project_root(_ROOT)
DOMAIN_PATH = ROOT / "domains" / "freight-demurrage" / "domain.yaml"
DEFAULT_CSV = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"
PRIMARY_MODES = ("plus", "thinking", "mock")
METRIC_KEYS = ("accuracy", "f1", "roc_auc", "avg_precision")

app = FastAPI(title="Freight Demurrage Desk", version="0.3.0")
templates = Jinja2Templates(directory=str(DESK_DIR / "templates"))
static_dir = DESK_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

_STATE: dict[str, Any] = {
    "source": "domain_csv", "adapter": None, "table_id": None, "n_rows": 0,
    "metrics": None, "baseline_metrics": None, "delta": None, "baseline_narrative": None,
    "backend": None, "mode": None, "requested_mode": None, "warning": None,
    "demurrage_total": 0.0, "actions": None, "action_counts": None, "preview_rows": [],
    "group_col": None, "group_time_col": None, "fast_ab": None, "elapsed_s": None,
    "blank_metrics": None, "blank_backend": None, "blank_warning": None,
    "blank_label": "blank_sailing", "what_if": None, "sample_row_ids": [],
}


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


def _session() -> PipelineSession:
    return PipelineSession(domain=load_domain(DOMAIN_PATH), root=ROOT)


def _reset_triage_state() -> None:
    for k in (
        "metrics", "baseline_metrics", "delta", "baseline_narrative", "actions",
        "action_counts", "backend", "mode", "requested_mode", "warning", "fast_ab",
        "elapsed_s", "blank_metrics", "blank_backend", "blank_warning", "what_if",
    ):
        _STATE[k] = None


def _metric_slice(metrics: dict[str, float] | None) -> dict[str, float]:
    if not metrics:
        return {}
    return {
        k: float(metrics[k])
        for k in METRIC_KEYS
        if k in metrics and isinstance(metrics[k], (int, float))
    }


def _load_default_csv(session: PipelineSession) -> None:
    result = session.load_table(path=str(DEFAULT_CSV), table_id="desk")
    _STATE["source"] = "domain_csv"
    _STATE["adapter"] = None
    _STATE["table_id"] = result.table_id
    _STATE["n_rows"] = result.n_rows
    df = session.tables[result.table_id]
    _STATE["demurrage_total"] = float(df["projected_demurrage_usd"].fillna(0).sum())
    _STATE["preview_rows"] = df.head(8).fillna("").to_dict(orient="records")
    _STATE["group_col"] = session.domain.group_col
    _STATE["group_time_col"] = session.domain.time_col
    _STATE["sample_row_ids"] = sample_ids(df)
    _STATE["blank_label"] = getattr(session.domain, "secondary_label_col", None) or "blank_sailing"
    _reset_triage_state()


@app.on_event("startup")
def _startup() -> None:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    sess = _session()
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["blank_label"] = getattr(sess.domain, "secondary_label_col", None) or "blank_sailing"
    if DEFAULT_CSV.is_file():
        _load_default_csv(sess)
    app.state.session = sess


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {
        "adapters": list_adapters(), "state": _STATE,
        "disclaimer": "Synthetic / public-derived ocean freight demo only. Not a carrier system of record.",
        "has_token": _has_token(), "primary_modes": PRIMARY_MODES, "metric_keys": METRIC_KEYS,
    })


@app.post("/load-adapter")
async def load_adapter(adapter_name: str = Form(...)) -> RedirectResponse:
    adapter = get_adapter(adapter_name)
    df = adapter.to_dataframe()
    sess: PipelineSession = app.state.session
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        df.to_csv(tmp.name, index=False)
        path = tmp.name
    result = sess.load_table(path=path, table_id="desk")
    Path(path).unlink(missing_ok=True)
    _STATE["source"] = f"adapter:{adapter.name}"
    _STATE["adapter"] = adapter.name
    _STATE["table_id"] = result.table_id
    _STATE["n_rows"] = result.n_rows
    loaded = sess.tables[result.table_id]
    _STATE["demurrage_total"] = float(loaded["projected_demurrage_usd"].fillna(0).sum())
    _STATE["preview_rows"] = loaded.head(8).fillna("").to_dict(orient="records")
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["sample_row_ids"] = sample_ids(loaded)
    _reset_triage_state()
    return RedirectResponse(url="/", status_code=303)


@app.post("/load-domain-csv")
async def load_domain_csv() -> RedirectResponse:
    _load_default_csv(app.state.session)
    return RedirectResponse(url="/", status_code=303)


@app.post("/run-triage")
async def run_triage(mode: str = Form("mock"), fast_ab: str | None = Form(None)) -> RedirectResponse:
    """Run triage with judge-priority modes; always attach HistGBM baseline delta."""
    sess: PipelineSession = app.state.session
    tid = _STATE.get("table_id")
    if not tid or tid not in sess.tables:
        _load_default_csv(sess)
        tid = _STATE["table_id"]
    backend_mode, resolve_warn = _resolve_mode(mode)
    n = len(sess.tables[tid])
    test_size = 0.3 if n >= 10 else 0.25
    if n < 4:
        import pandas as pd
        combined = pd.concat([pd.read_csv(DEFAULT_CSV), sess.tables[tid]], ignore_index=True)
        sess.tables[tid] = combined
        _STATE["n_rows"] = len(combined)
        _STATE["demurrage_total"] = float(combined["projected_demurrage_usd"].fillna(0).sum())
        _STATE["sample_row_ids"] = sample_ids(combined)
        test_size = 0.2
    t0 = time.perf_counter()
    cmp_ = sess.compare_baseline(tid, mode=backend_mode, baseline="sklearn_hist_gbm", test_size=test_size)
    elapsed = time.perf_counter() - t0
    actions = sess.suggest_actions(tid, max_rows=50)
    warnings: list[str] = []
    if resolve_warn:
        warnings.append(resolve_warn)
    if sess.last_warning:
        warnings.append(str(sess.last_warning))
    _STATE["metrics"] = _metric_slice(cmp_.tabpfn_metrics)
    _STATE["baseline_metrics"] = _metric_slice(cmp_.baseline_metrics)
    _STATE["delta"] = _metric_slice(cmp_.delta)
    _STATE["baseline_narrative"] = cmp_.narrative
    _STATE["backend"] = sess.last_backend
    effective = sess.last_mode
    _STATE["mode"] = effective.value if hasattr(effective, "value") else str(effective)
    _STATE["requested_mode"] = backend_mode.value if hasattr(backend_mode, "value") else str(backend_mode)
    _STATE["warning"] = " · ".join(warnings) if warnings else None
    _STATE["elapsed_s"] = round(elapsed, 3)
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["actions"] = [
        {"row_id": a.row_id, "proba": round(float(a.proba), 4), "action": a.action, "reason": a.reason}
        for a in actions.items
    ]
    _STATE["action_counts"] = dict(actions.counts)
    _STATE["what_if"] = None
    run_blank_head(sess, tid, backend_mode, test_size, _STATE)
    if fast_ab in {"1", "on", "true", "yes"}:
        snap_pred = None if sess.last_predictions is None else sess.last_predictions.copy()
        snap = (sess.last_metrics, sess.last_backend, sess.last_mode, sess.last_warning, sess.last_baseline)
        t1 = time.perf_counter()
        fast_mode, fast_warn = _resolve_mode("fast")
        fast_fit = sess.fit_predict(tid, mode=fast_mode, test_size=test_size)
        _STATE["fast_ab"] = {
            "mode": "fast", "backend": fast_fit.backend, "metrics": _metric_slice(fast_fit.metrics),
            "elapsed_s": round(time.perf_counter() - t1, 3), "warning": fast_warn or fast_fit.warning,
            "note": "Fast A/B stub — queue latency vs Thinking/Plus score (optional).",
        }
        if snap_pred is not None:
            sess.last_predictions = snap_pred
            sess.last_metrics, sess.last_backend, sess.last_mode, sess.last_warning, sess.last_baseline = snap
    else:
        _STATE["fast_ab"] = None
    return RedirectResponse(url="/", status_code=303)


@app.post("/what-if")
async def what_if(
    row_id: str = Form(...),
    free_days_left: str | None = Form(None),
    projected_demurrage_usd: str | None = Form(None),
    divert: str | None = Form(None),
    mode: str | None = Form(None),
) -> RedirectResponse:
    """Synthetic what-if simulation on a selected container row."""
    sess: PipelineSession = app.state.session
    tid = _STATE.get("table_id")
    if not tid or tid not in sess.tables:
        _load_default_csv(sess)
        tid = _STATE["table_id"]
    overrides: dict[str, Any] = {}
    if free_days_left is not None and str(free_days_left).strip() != "":
        overrides["free_days_left"] = float(free_days_left)
    if projected_demurrage_usd is not None and str(projected_demurrage_usd).strip() != "":
        overrides["projected_demurrage_usd"] = float(projected_demurrage_usd)
    if divert in {"1", "on", "true", "yes"}:
        overrides["divert"] = 1
    backend_mode, resolve_warn = _resolve_mode(mode or _STATE.get("requested_mode") or "mock")
    try:
        result = run_what_if(sess, tid, row_id, overrides, backend_mode)
        if resolve_warn:
            result["warning"] = " · ".join(x for x in [resolve_warn, result.get("warning")] if x)
        _STATE["what_if"] = result
    except Exception as exc:  # noqa: BLE001
        _STATE["what_if"] = {
            "simulation": True,
            "label": "what-if simulation (synthetic)",
            "error": str(exc),
            "row_id": row_id,
        }
    return RedirectResponse(url="/#what-if", status_code=303)


def create_app() -> FastAPI:
    return app
