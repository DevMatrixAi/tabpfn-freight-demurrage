"""Auto-wire stream re-score onto the desk FastAPI app."""
from __future__ import annotations

def install_stream(
    app,
    *,
    state,
    templates,
    pack_meta,
    resolve_mode,
    metric_slice,
    money_total,
    build_risk_cards,
    load_default_csv,
    sample_ids,
    primary_modes,
    metric_keys,
):
    state.setdefault("stream_cursor", 0)
    state.setdefault("stream_log", [])
    state.setdefault("stream_last", [])
    try:
        from apps.desk.stream_rescore import register_stream_routes
    except ImportError:
        from stream_rescore import register_stream_routes  # type: ignore
    register_stream_routes(
        app,
        state=state,
        templates=templates,
        pack_meta=pack_meta,
        resolve_mode=resolve_mode,
        metric_slice=metric_slice,
        money_total=money_total,
        build_risk_cards=build_risk_cards,
        load_default_csv=load_default_csv,
        sample_ids=sample_ids,
        primary_modes=primary_modes,
        metric_keys=metric_keys,
    )
