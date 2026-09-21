"""Freight ops desk app — readable entry (judge repro).

Implementation lives in ``app_impl`` so MCP pushes stay under size limits.
Run with: ``uvicorn apps.desk.app:app`` or ``uvicorn app:app`` from apps/desk.
"""
from __future__ import annotations

try:
    from apps.desk import app_impl as _impl
except ImportError:  # uvicorn app-dir=apps/desk
    import app_impl as _impl  # type: ignore

app = _impl.app
create_app = _impl.create_app

# Re-exports expected by tests / tooling
DEFAULT_PACK = getattr(_impl, "DEFAULT_PACK", None)
if DEFAULT_PACK is None:
    try:
        from apps.desk.packs import DEFAULT_PACK
    except ImportError:
        from packs import DEFAULT_PACK  # type: ignore

PACKS = _impl.PACKS
ROOT = _impl.ROOT
DESK_DIR = _impl.DESK_DIR
METRIC_KEYS = _impl.METRIC_KEYS
PRIMARY_MODES = _impl.PRIMARY_MODES
templates = _impl.templates

_STATE = _impl._STATE
_metric_slice = _impl._metric_slice
_resolve_mode = _impl._resolve_mode
_session = _impl._session
_money_total = _impl._money_total
_has_token = _impl._has_token
_pack_id = _impl._pack_id
_pack_meta = _impl._pack_meta

__all__ = [
    "app",
    "create_app",
    "DEFAULT_PACK",
    "PACKS",
    "ROOT",
    "DESK_DIR",
    "METRIC_KEYS",
    "PRIMARY_MODES",
    "templates",
    "_STATE",
    "_metric_slice",
    "_resolve_mode",
    "_session",
    "_money_total",
]
