"""Desk app helpers — readable extract for judge repro / MCP-sized pushes."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from tabpfn_hack_core.adapters.registry import get_adapter, list_adapters
from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import load_domain
from tabpfn_hack_core.tools_api import BackendMode

try:
    from apps.desk.wow import sample_ids
except ImportError:
    from wow import sample_ids  # type: ignore

try:
    from apps.desk.packs import DEFAULT_PACK, build_packs
except ImportError:
    from packs import DEFAULT_PACK, build_packs  # type: ignore

try:
    from apps.desk.clients import DEFAULT_CLIENT, client_meta, list_clients
except ImportError:
    from clients import DEFAULT_CLIENT, client_meta, list_clients  # type: ignore

# Packs resolved at import by caller binding; helpers expect module-level PACKS/ROOT/_STATE injected
# via register_helpers() to avoid circular imports.

PACKS: dict[str, Any] = {}
ROOT: Path | None = None
METRIC_KEYS: tuple[str, ...] = ("accuracy", "f1", "roc_auc", "avg_precision")
_STATE: dict[str, Any] = {}
app = None  # set by bind()


def bind(*, packs: dict[str, Any], root: Path, state: dict[str, Any], fastapi_app: Any, metric_keys: tuple[str, ...] | None = None) -> None:
    global PACKS, ROOT, _STATE, app, METRIC_KEYS
    PACKS = packs
    ROOT = root
    _STATE = state
    app = fastapi_app
    if metric_keys:
        METRIC_KEYS = metric_keys


def _has_token() -> bool:
    return bool(os.environ.get("TABPFN_TOKEN", "").strip())


def _resolve_mode(requested: str) -> tuple[BackendMode, str | None]:
    req = (requested or "mock").lower().strip()
    try:
        mode = BackendMode(req)
    except ValueError:
        return BackendMode.mock, f"Unknown mode {requested!r}; using mock"
    warn = None
    from tabpfn_hack_core.core import replay as _replay

    if mode in {BackendMode.plus, BackendMode.thinking} and _replay.replay_enabled():
        return mode, None  # recorded TabPFN-3.5 scores stand in; labeled on the page
    if mode in {BackendMode.plus, BackendMode.thinking, BackendMode.fast} and not _has_token():
        warn = (
            f"TABPFN_TOKEN not set; requested mode={mode.value} will fall back to mock "
            "(set TABPFN_TOKEN in env for Plus/Thinking/Fast)."
        )
    return mode, warn


def _pack_id() -> str:
    pid = _STATE.get("pack") or DEFAULT_PACK
    return pid if pid in PACKS else DEFAULT_PACK


def _pack_meta() -> dict[str, Any]:
    return PACKS[_pack_id()]


def _session(pack: str | None = None) -> PipelineSession:
    pid = pack if pack in PACKS else _pack_id()
    return PipelineSession(domain=load_domain(PACKS[pid]["domain"]), root=ROOT)


def _reset_triage_state() -> None:
    for k in (
        "metrics", "baseline_metrics", "delta", "baseline_narrative", "actions",
        "action_counts", "backend", "mode", "requested_mode", "warning", "fast_ab",
        "elapsed_s", "blank_metrics", "blank_backend", "blank_warning", "what_if",
        "chart_stats", "explain", "morning_digest", "judge_path",
    ):
        _STATE[k] = None
    _STATE["risk_cards"] = []
    _STATE["thinking_timeline"] = []
    _STATE["coach_active_beat"] = "triage"


def _metric_slice(metrics: dict[str, float] | None) -> dict[str, float]:
    if not metrics:
        return {}
    return {
        k: float(metrics[k])
        for k in METRIC_KEYS
        if k in metrics and isinstance(metrics[k], (int, float))
    }


def _money_total(df) -> float:
    col = _pack_meta().get("money_col")
    if col and col in df.columns:
        return float(df[col].fillna(0).sum())
    return 0.0


try:
    from apps.desk.risk_board import build_risk_cards as _build_risk_cards_impl
except ImportError:
    from risk_board import build_risk_cards as _build_risk_cards_impl  # type: ignore

try:
    from apps.desk.missingness import missingness_summary
except ImportError:
    from missingness import missingness_summary  # type: ignore

try:
    from apps.desk.column_chips import apply_column_chips
except ImportError:
    from column_chips import apply_column_chips  # type: ignore


def _build_risk_cards(sess: PipelineSession, tid: str, actions: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    return _build_risk_cards_impl(sess, tid, actions, _pack_meta(), limit=limit)



def _load_default_csv(session: PipelineSession | None = None) -> None:
    meta = _pack_meta()
    sess = session or _session()
    csv_path = meta["csv"]
    result = sess.load_table(path=str(csv_path), table_id="desk")
    _STATE["pack"] = _pack_id()
    _STATE["pack_label"] = meta["label"]
    _STATE["source"] = "domain_csv"
    _STATE["adapter"] = None
    _STATE["table_id"] = result.table_id
    _STATE["n_rows"] = result.n_rows
    df = sess.tables[result.table_id]
    cid = _STATE.get("client_id") or DEFAULT_CLIENT
    if cid != "ALL" and "client_id" in df.columns:
        df = df[df["client_id"].astype(str) == cid].copy()
        # write filtered view back for triage on this table id
        sess.tables[result.table_id] = df
        result.n_rows = len(df)
    _STATE["n_rows"] = int(len(df))
    _STATE["demurrage_total"] = _money_total(df)
    _STATE["preview_rows"] = df.head(8).fillna("").to_dict(orient="records")
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["sample_row_ids"] = sample_ids(df, id_col=sess.domain.id_col or "container_id")
    _STATE["missingness"] = missingness_summary(df)
    apply_column_chips(_STATE, sess.domain, df)
    _STATE["blank_label"] = getattr(sess.domain, "secondary_label_col", None) or "blank_sailing"
    _STATE["money_label"] = meta.get("money_label") or "Exposure"
    _STATE["pack_gloss"] = meta.get("gloss")
    _STATE["risk_cards"] = []
    _reset_triage_state()
    app.state.session = sess
