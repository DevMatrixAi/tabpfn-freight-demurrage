"""Lean FastAPI + Jinja demurrage desk wrapping PipelineSession + fixture adapters."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Ensure src is importable when launched via uvicorn apps.desk.app:app
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_SRC))

from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters  # noqa: E402
from tabpfn_hack_core.core.pipeline import PipelineSession  # noqa: E402
from tabpfn_hack_core.domain import find_project_root, load_domain  # noqa: E402
from tabpfn_hack_core.tools_api import BackendMode  # noqa: E402

DESK_DIR = Path(__file__).resolve().parent
ROOT = find_project_root(_ROOT)
DOMAIN_PATH = ROOT / "domains" / "freight-demurrage" / "domain.yaml"
DEFAULT_CSV = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"

app = FastAPI(title="Freight Demurrage Desk", version="0.1.0")
templates = Jinja2Templates(directory=str(DESK_DIR / "templates"))
static_dir = DESK_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# In-memory desk state for the demo session
_STATE: dict[str, Any] = {
    "source": "domain_csv",
    "adapter": None,
    "table_id": None,
    "n_rows": 0,
    "metrics": None,
    "backend": None,
    "mode": None,
    "warning": None,
    "demurrage_total": 0.0,
    "actions": None,
    "action_counts": None,
    "preview_rows": [],
}


def _resolve_mode(requested: str) -> BackendMode:
    token = os.environ.get("TABPFN_TOKEN", "").strip()
    req = (requested or "mock").lower()
    if req == "plus" and token:
        return BackendMode.plus
    if req in {"plus", "thinking", "fast"} and not token:
        return BackendMode.mock
    try:
        return BackendMode(req)
    except ValueError:
        return BackendMode.mock


def _session() -> PipelineSession:
    domain = load_domain(DOMAIN_PATH)
    return PipelineSession(domain=domain, root=ROOT)


def _load_default_csv(session: PipelineSession) -> None:
    result = session.load_table(path=str(DEFAULT_CSV), table_id="desk")
    _STATE["source"] = "domain_csv"
    _STATE["adapter"] = None
    _STATE["table_id"] = result.table_id
    _STATE["n_rows"] = result.n_rows
    df = session.tables[result.table_id]
    _STATE["demurrage_total"] = float(df["projected_demurrage_usd"].fillna(0).sum())
    _STATE["preview_rows"] = df.head(8).fillna("").to_dict(orient="records")
    _STATE["metrics"] = None
    _STATE["actions"] = None
    _STATE["action_counts"] = None


@app.on_event("startup")
def _startup() -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    sess = _session()
    if DEFAULT_CSV.is_file():
        _load_default_csv(sess)
        app.state.session = sess
    else:
        app.state.session = sess


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "adapters": list_adapters(),
            "state": _STATE,
            "disclaimer": (
                "Synthetic / public-derived ocean freight demo only. "
                "Not a carrier system of record."
            ),
            "has_token": bool(os.environ.get("TABPFN_TOKEN", "").strip()),
        },
    )


@app.post("/load-adapter")
async def load_adapter(adapter_name: str = Form(...)) -> RedirectResponse:
    adapter = get_adapter(adapter_name)
    df = adapter.to_dataframe()
    sess: PipelineSession = app.state.session
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, encoding="utf-8"
    ) as tmp:
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
    _STATE["metrics"] = None
    _STATE["actions"] = None
    _STATE["action_counts"] = None
    _STATE["backend"] = None
    _STATE["warning"] = None
    return RedirectResponse(url="/", status_code=303)


@app.post("/load-domain-csv")
async def load_domain_csv() -> RedirectResponse:
    sess: PipelineSession = app.state.session
    _load_default_csv(sess)
    return RedirectResponse(url="/", status_code=303)


@app.post("/run-triage")
async def run_triage(mode: str = Form("mock")) -> RedirectResponse:
    sess: PipelineSession = app.state.session
    tid = _STATE.get("table_id")
    if not tid or tid not in sess.tables:
        _load_default_csv(sess)
        tid = _STATE["table_id"]
    backend_mode = _resolve_mode(mode)
    n = len(sess.tables[tid])
    test_size = 0.3 if n >= 10 else 0.25
    if n < 4:
        domain_df = __import__("pandas").read_csv(DEFAULT_CSV)
        fixture_df = sess.tables[tid]
        combined = __import__("pandas").concat([domain_df, fixture_df], ignore_index=True)
        sess.tables[tid] = combined
        _STATE["n_rows"] = len(combined)
        _STATE["demurrage_total"] = float(combined["projected_demurrage_usd"].fillna(0).sum())
        test_size = 0.2

    fit = sess.fit_predict(tid, mode=backend_mode, test_size=test_size)
    actions = sess.suggest_actions(tid, max_rows=50)
    _STATE["metrics"] = fit.metrics
    _STATE["backend"] = fit.backend
    _STATE["mode"] = fit.mode.value if hasattr(fit.mode, "value") else str(fit.mode)
    _STATE["warning"] = fit.warning
    _STATE["actions"] = [
        {
            "row_id": a.row_id,
            "proba": round(float(a.proba), 4),
            "action": a.action,
            "reason": a.reason,
        }
        for a in actions.items
    ]
    _STATE["action_counts"] = dict(actions.counts)
    return RedirectResponse(url="/", status_code=303)


def create_app() -> FastAPI:
    return app
