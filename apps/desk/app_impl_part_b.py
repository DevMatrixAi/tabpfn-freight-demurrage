"""Desk impl part B: HTTP routes + create_app (judge repro).

Executed into app_impl globals after part A.
"""
@app.on_event("startup")
def _startup() -> None:
    import os as _os
    if _os.environ.get("DESK_NO_DOTENV", "").strip().lower() not in {"1", "true", "yes"}:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    sess = _session(DEFAULT_PACK)
    _STATE["pack"] = DEFAULT_PACK
    _STATE["pack_label"] = PACKS[DEFAULT_PACK]["label"]
    _STATE["pack_gloss"] = PACKS[DEFAULT_PACK].get("gloss")
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["blank_label"] = getattr(sess.domain, "secondary_label_col", None) or "blank_sailing"
    if PACKS[DEFAULT_PACK]["csv"].is_file():
        _load_default_csv(sess)
    else:
        app.state.session = sess


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login", response_model=None)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if check_password(username, password):
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie(SESSION_COOKIE, "1", httponly=True, samesite="lax")
        return resp
    return templates.TemplateResponse(
        request, "login.html", {"error": "Invalid demo credentials."}, status_code=401
    )


@app.post("/logout")
async def logout() -> RedirectResponse:
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.post("/select-client")
async def select_client(client_id: str = Form(...)) -> RedirectResponse:
    _STATE["client_id"] = client_id if client_id in {c["id"] for c in list_clients()} else DEFAULT_CLIENT
    _STATE["client_label"] = client_meta(_STATE["client_id"])["label"]
    if getattr(app.state, "session", None) is not None:
        _load_default_csv(app.state.session)
        return RedirectResponse(url="/desk", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def saas_home(request: Request) -> HTMLResponse:
    """Multi-desk home + client switcher."""
    cid = _STATE.get("client_id") or DEFAULT_CLIENT
    cmeta = client_meta(cid)
    desks = [
        {"id": k, "label": v["label"], "spine": v["spine"], "gloss": v.get("gloss")}
        for k, v in PACKS.items()
    ]
    try:
        from apps.desk.dev_sample import live_budget_chip
    except ImportError:
        from dev_sample import live_budget_chip  # type: ignore
    return templates.TemplateResponse(request, "home_saas.html", {
        "clients": list_clients(),
        "active_client": cid,
        "active_client_gloss": cmeta.get("gloss", ""),
        "desks": desks,
        "live_budget": live_budget_chip(),
        "has_token": _has_token(),
        "replay_on": __import__("tabpfn_hack_core.core.replay", fromlist=["replay_enabled"]).replay_enabled(),
    })


def _auto_triage_from_replay() -> None:
    """First visit with recorded TabPFN scores available: fill the board (free, no API call)."""
    if _STATE.get("risk_cards") or not meta_is_spine():
        return
    from tabpfn_hack_core.core import replay as _replay

    sess = getattr(app.state, "session", None)
    tid = _STATE.get("table_id")
    if sess is None or not tid or tid not in sess.tables:
        return
    if not _replay.covers(sess.tables[tid], sess.domain.id_col):
        return
    try:
        from apps.desk.desk_triage_apply import apply_triage
    except ImportError:
        from desk_triage_apply import apply_triage  # type: ignore
    apply_triage(
        app, _STATE, mode="plus",
        pack_meta=_pack_meta, resolve_mode=_resolve_mode, metric_slice=_metric_slice,
        money_total=_money_total, build_risk_cards=_build_risk_cards,
        load_default_csv=_load_default_csv, sample_ids=sample_ids,
    )


def meta_is_spine() -> bool:
    return bool(_pack_meta().get("spine"))


@app.get("/desk", response_class=HTMLResponse)
async def desk_board(request: Request, pack: str | None = None) -> HTMLResponse:
    """Ops board for one desk/pack."""
    if pack and pack in PACKS and pack != _pack_id():
        _STATE["pack"] = pack
        _STATE["pack_label"] = PACKS[pack]["label"]
        _STATE["pack_gloss"] = PACKS[pack].get("gloss")
        sess = _session(pack)
        _load_default_csv(sess)
    meta = _pack_meta()
    disclaimer = load_domain(meta["domain"]).disclaimer
    _auto_triage_from_replay()
    if not _STATE.get("coach_active_beat"):
        _STATE["coach_active_beat"] = "drawer" if _STATE.get("risk_cards") else "triage"
    try:
        from apps.desk.dev_sample import live_budget_chip, resolve_sample_n
    except ImportError:
        from dev_sample import live_budget_chip, resolve_sample_n  # type: ignore
    pref_n = _STATE.get("settings_sample_n")
    if pref_n is None:
        pref_n = resolve_sample_n(None)
    return templates.TemplateResponse(request, "index.html", {
        "adapters": list_adapters(), "state": _STATE,
        "packs": [{"id": k, "label": v["label"], "spine": v["spine"], "gloss": v.get("gloss")} for k, v in PACKS.items()],
        "disclaimer": disclaimer,
        "has_token": _has_token(), "primary_modes": PRIMARY_MODES, "metric_keys": METRIC_KEYS,
        "is_spine": bool(meta.get("spine")),
        "clients": list_clients(),
        "saas_home": "/",
        "live_budget": live_budget_chip(sample_n=pref_n),
        "default_sample_n": pref_n,
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
    _STATE["demurrage_total"] = _money_total(loaded)
    _STATE["preview_rows"] = loaded.head(8).fillna("").to_dict(orient="records")
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["sample_row_ids"] = sample_ids(loaded, id_col=sess.domain.id_col or "container_id")
    try:
        from apps.desk.missingness import missingness_summary as _miss
    except ImportError:
        from missingness import missingness_summary as _miss  # type: ignore
    _STATE["missingness"] = _miss(loaded)
    try:
        from apps.desk.column_chips import apply_column_chips as _chips
    except ImportError:
        from column_chips import apply_column_chips as _chips  # type: ignore
    _chips(_STATE, sess.domain, loaded)
    _reset_triage_state()
    return RedirectResponse(url="/desk", status_code=303)


@app.post("/load-domain-csv")
async def load_domain_csv() -> RedirectResponse:
    _load_default_csv(app.state.session)
    return RedirectResponse(url="/desk", status_code=303)



@app.post("/load-stress-missing")
async def load_stress_missing() -> RedirectResponse:
    """Load fixtures/stress/missing_wide_demurrage.csv for missingness showcase."""
    sess = app.state.session
    path = ROOT / "fixtures" / "stress" / "missing_wide_demurrage.csv"
    if not path.exists():
        import runpy
        runpy.run_path(str(ROOT / "fixtures" / "stress" / "_unpack_missing_wide.py"))
    result = sess.load_table(path=str(path), table_id="desk")
    loaded = sess.tables[result.table_id]
    _STATE["source"] = "stress:missing_wide"
    _STATE["adapter"] = None
    _STATE["table_id"] = result.table_id
    _STATE["n_rows"] = result.n_rows
    _STATE["demurrage_total"] = _money_total(loaded)
    _STATE["preview_rows"] = loaded.head(8).fillna("").to_dict(orient="records")
    _STATE["group_col"] = sess.domain.group_col
    _STATE["group_time_col"] = sess.domain.time_col
    _STATE["sample_row_ids"] = sample_ids(loaded, id_col=sess.domain.id_col or "container_id")
    try:
        from apps.desk.missingness import missingness_summary as _miss
    except ImportError:
        from missingness import missingness_summary as _miss  # type: ignore
    _STATE["missingness"] = _miss(loaded)
    try:
        from apps.desk.column_chips import apply_column_chips as _chips
    except ImportError:
        from column_chips import apply_column_chips as _chips  # type: ignore
    _chips(_STATE, sess.domain, loaded)
    _reset_triage_state()
    return RedirectResponse(url="/desk", status_code=303)

@app.post("/switch-pack")
async def switch_pack(pack: str = Form(...)) -> RedirectResponse:
    """Swap spine / coda domain packs (fixtures only)."""
    pid = pack if pack in PACKS else DEFAULT_PACK
    _STATE["pack"] = pid
    _STATE["pack_label"] = PACKS[pid]["label"]
    _STATE["pack_gloss"] = PACKS[pid].get("gloss")
    sess = _session(pid)
    _load_default_csv(sess)
    return RedirectResponse(url="/desk", status_code=303)

try:
    from apps.desk.desk_triage import register_triage_routes
except ImportError:
    from desk_triage import register_triage_routes  # type: ignore

register_triage_routes(
    app,
    state=_STATE,
    pack_meta=_pack_meta,
    resolve_mode=_resolve_mode,
    metric_slice=_metric_slice,
    money_total=_money_total,
    build_risk_cards=_build_risk_cards,
    load_default_csv=_load_default_csv,
    sample_ids=sample_ids,
)

try:
    from apps.desk.judge_path import register_judge_path_routes
except ImportError:
    from judge_path import register_judge_path_routes  # type: ignore

register_judge_path_routes(
    app,
    state=_STATE,
    pack_meta=_pack_meta,
    resolve_mode=_resolve_mode,
    metric_slice=_metric_slice,
    money_total=_money_total,
    build_risk_cards=_build_risk_cards,
    load_default_csv=_load_default_csv,
    sample_ids=sample_ids,
)

try:
    from apps.desk.api_robot import register_robot_api
except ImportError:
    from api_robot import register_robot_api  # type: ignore

register_robot_api(app)

try:
    from apps.desk.stream_rescore import register_stream_routes
except ImportError:
    from stream_rescore import register_stream_routes  # type: ignore

register_stream_routes(
    app,
    state=_STATE,
    templates=templates,
    pack_meta=_pack_meta,
    resolve_mode=_resolve_mode,
    metric_slice=_metric_slice,
    money_total=_money_total,
    build_risk_cards=_build_risk_cards,
    load_default_csv=_load_default_csv,
    sample_ids=sample_ids,
    primary_modes=PRIMARY_MODES,
    metric_keys=METRIC_KEYS,
)



try:
    from apps.desk.eval_dashboard import register_eval_routes
except ImportError:
    from eval_dashboard import register_eval_routes  # type: ignore

register_eval_routes(
    app,
    state=_STATE,
    templates=templates,
    packs=PACKS,
    default_pack=DEFAULT_PACK,
    session_factory=_session,
    load_pack_csv=_load_default_csv,
    resolve_mode=_resolve_mode,
    metric_slice=_metric_slice,
    has_token=_has_token,
)




def create_app() -> FastAPI:
    return app
