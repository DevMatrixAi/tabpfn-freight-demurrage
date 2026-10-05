"""Readable desk FastAPI implementation (judge repro).

Imported by ``apps.desk.app`` so the entrypoint stays small for MCP pushes.
"""
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
PRIMARY_MODES = ("plus", "thinking", "mock")
METRIC_KEYS = ("accuracy", "f1", "roc_auc", "avg_precision")

try:
    from apps.desk.packs import DEFAULT_PACK, build_packs
except ImportError:
    from packs import DEFAULT_PACK, build_packs  # type: ignore

PACKS = build_packs(ROOT)

try:
    from apps.desk import app_helpers as _ah
except ImportError:
    import app_helpers as _ah  # type: ignore

# Re-export helpers under original private names
_has_token = _ah._has_token
_resolve_mode = _ah._resolve_mode
_pack_id = _ah._pack_id
_pack_meta = _ah._pack_meta
_session = _ah._session
_reset_triage_state = _ah._reset_triage_state
_metric_slice = _ah._metric_slice
_money_total = _ah._money_total
_build_risk_cards = _ah._build_risk_cards
_load_default_csv = _ah._load_default_csv


app = FastAPI(
    title="Freight Ops Board",
    version="0.9.0",
    description=(
        "SaaS shell + UI polish + streaming fixture re-score + eval dashboard + ops board. "
        "Robot/TMS API under /api/v1 (decisions only). Demo auth, not production IAM."
    ),
)


from fastapi.responses import JSONResponse as _JSONResponse
from tabpfn_hack_core.core.backend import TabPFNLiveError as _TabPFNLiveError


@app.exception_handler(_TabPFNLiveError)
async def _tabpfn_live_error(request: Request, exc: _TabPFNLiveError) -> _JSONResponse:
    """A refused live TabPFN call returns a clear error instead of offline numbers."""
    return _JSONResponse(
        status_code=getattr(exc, "status", 502),
        content={"error": "tabpfn_live_failed", "detail": str(exc)},
    )
try:
    from apps.desk.ensure_deep_templates import ensure_deep_templates as _ensure_deep_tpl
    _ensure_deep_tpl()
except Exception:
    try:
        from ensure_deep_templates import ensure_deep_templates as _ensure_deep_tpl  # type: ignore
        _ensure_deep_tpl()
    except Exception:
        pass

templates = Jinja2Templates(directory=str(DESK_DIR / "templates"))
try:
    from apps.desk.risk_board import human_action as _human_action
except ImportError:
    from risk_board import human_action as _human_action  # type: ignore
templates.env.filters["human_action"] = _human_action
app.state.templates = templates
static_dir = DESK_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

try:
    from apps.desk.auth import (
        DemoAuthMiddleware,
        SESSION_COOKIE,
        check_password,
        demo_credentials,
        is_authenticated,
    )
    from apps.desk.clients import DEFAULT_CLIENT, client_meta, list_clients
except ImportError:
    from auth import (  # type: ignore
        DemoAuthMiddleware,
        SESSION_COOKIE,
        check_password,
        demo_credentials,
        is_authenticated,
    )
    from clients import DEFAULT_CLIENT, client_meta, list_clients  # type: ignore

_STATE: dict[str, Any] = {
    "client_id": "ALL", "client_label": "All clients",
    "pack": DEFAULT_PACK, "pack_label": PACKS[DEFAULT_PACK]["label"],
    "source": "domain_csv", "adapter": None, "table_id": None, "n_rows": 0,
    "metrics": None, "baseline_metrics": None, "delta": None, "baseline_narrative": None,
    "backend": None, "mode": None, "requested_mode": None, "warning": None,
    "demurrage_total": 0.0, "actions": None, "action_counts": None, "preview_rows": [],
    "group_col": None, "group_time_col": None, "fast_ab": None, "elapsed_s": None,
    "blank_metrics": None, "blank_backend": None, "blank_warning": None,
    "blank_label": "blank_sailing", "what_if": None, "sample_row_ids": [],
    "risk_cards": [], "chart_stats": None, "thinking_timeline": [], "explain": None,
    "money_label": "Possible late fees", "pack_gloss": PACKS[DEFAULT_PACK].get("gloss"),
    "stream_cursor": 0, "stream_log": [], "stream_last": [],
}

app.add_middleware(DemoAuthMiddleware)

_ah.bind(packs=PACKS, root=ROOT, state=_STATE, fastapi_app=app, metric_keys=METRIC_KEYS)
