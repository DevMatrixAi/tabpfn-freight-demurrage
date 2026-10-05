"""Live TabPFN-3.5 replay (out-of-fold on all rows) + learning curve vs HistGBM.

Every live response is cached to artifacts/freight-demurrage/live_cache/ so a crash
or rerun never pays twice. Token is read from env / .env and never printed.

Usage:
  python scripts/live_replay_and_curve.py smoke
  python scripts/live_replay_and_curve.py replay
  python scripts/live_replay_and_curve.py curve
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "domains/freight-demurrage/data/containers.csv"
OUT = ROOT / "artifacts/freight-demurrage"
CACHE = OUT / "live_cache"
CACHE.mkdir(parents=True, exist_ok=True)
LABEL, GROUP, TIME = "demurrage_risk", "vessel_id", "event_ts"
TEXT = ["terminal_note", "weather_alert"]
HIGH = ["bol_id", "container_id", "pol", "pod"]
ACTION_COSTS = (150.0, 300.0, 600.0)  # assumed $ cost of one intervention (documented)
SEED = 42

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:  # noqa: BLE001
    pass


def load():
    df = pd.read_csv(DATA)
    y = df[LABEL].to_numpy().astype(int)
    X = df.drop(columns=[LABEL])
    return df, X, y


def _key(**kw) -> str:
    return hashlib.sha1(json.dumps(kw, sort_keys=True, default=str).encode()).hexdigest()[:16]


def tabpfn_proba(mode: str, Xtr, ytr, Xte, *, tag: str) -> np.ndarray:
    k = _key(mode=mode, tag=tag, ntr=len(Xtr), nte=len(Xte),
             tr=hashlib.sha1(pd.util.hash_pandas_object(Xtr, index=False).values).hexdigest(),
             te=hashlib.sha1(pd.util.hash_pandas_object(Xte, index=False).values).hexdigest())
    f = CACHE / f"{mode}_{k}.npy"
    if f.exists():
        return np.load(f)
    tok = os.environ.get("TABPFN_TOKEN", "")
    if not tok:
        raise SystemExit("TABPFN_TOKEN not set")
    import tabpfn_client as tc
    from tabpfn_client import TabPFNClassifier

    tc.set_access_token(tok)
    kw = {}
    if mode == "thinking":
        kw = dict(thinking_mode=True, thinking_effort="medium", group_col=GROUP, group_time_col=TIME)
    clf = TabPFNClassifier.create_default_for_version("v3.5", **kw)
    t0 = time.time()
    clf.fit(Xtr, ytr)
    p = clf.predict_proba(Xte)
    classes = list(getattr(clf, "classes_", [0, 1]))
    p = np.asarray(p[:, classes.index(1)] if p.ndim == 2 else p, dtype=float)
    np.save(f, p)
    (CACHE / f"{mode}_{k}.json").write_text(json.dumps(dict(
        mode=mode, tag=tag, n_train=len(Xtr), n_test=len(Xte), elapsed_s=round(time.time() - t0, 2),
        recorded_at=datetime.now(timezone.utc).isoformat(), model_version="v3.5")))
    return p


def hgb_proba(Xtr, ytr, Xte) -> np.ndarray:
    from tabpfn_hack_core.core.backend import fit_mock  # HistGBM baseline, repo featurization

    r = fit_mock(Xtr, ytr, Xte, np.zeros(len(Xte), dtype=int), text_cols=TEXT, high_card_cols=HIGH)
    return np.asarray(r.y_proba, dtype=float)


def cost_metrics(y, p, fee, cost):
    flag = p * fee > cost
    caught = float(fee[(flag) & (y == 1)].sum())
    spent = float(cost * flag.sum())
    tp = int(((flag) & (y == 1)).sum()); fp = int(((flag) & (y == 0)).sum()); fn = int(((~flag) & (y == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    all_net = float(fee[y == 1].sum() - cost * len(y))
    oracle = float(np.clip(fee[y == 1] - cost, 0, None).sum())
    return dict(action_cost=cost, n_flagged=int(flag.sum()), precision=round(prec, 4), recall=round(rec, 4),
                f1=round(f1, 4), fees_avoided=round(caught), action_spend=round(spent),
                net_savings=round(caught - spent), act_on_all_net=round(all_net), oracle_net=round(oracle))


def scores(y, p, fee):
    return dict(roc_auc=round(float(roc_auc_score(y, p)), 4),
                avg_precision=round(float(average_precision_score(y, p)), 4),
                cost=[cost_metrics(y, p, fee, c) for c in ACTION_COSTS])


def folds(X, y):
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    return list(sgkf.split(X, y, groups=X[GROUP]))


def smoke():
    df, X, y = load()
    rng = np.random.RandomState(0)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    tr = np.r_[rng.choice(pos, 5, False), rng.choice(neg, 15, False)]
    te = np.setdiff1d(np.arange(len(y)), tr)[:20]
    p = tabpfn_proba("plus", X.iloc[tr], y[tr], X.iloc[te], tag="smoke20")
    print(json.dumps(dict(smoke="ok", n_train=20, n_test=20, proba_min=float(p.min()), proba_max=float(p.max()))))


def replay():
    df, X, y = load()
    fee = df["projected_demurrage_usd"].fillna(0).to_numpy()
    fs = folds(X, y)
    oof = {m: np.full(len(y), np.nan) for m in ("plus", "thinking", "hist_gbm")}
    fold_id = np.full(len(y), -1)
    for i, (tr, te) in enumerate(fs):
        fold_id[te] = i
        for m in ("plus", "thinking"):
            oof[m][te] = tabpfn_proba(m, X.iloc[tr], y[tr], X.iloc[te], tag=f"oof5_fold{i}")
            print(f"fold {i} {m} done", flush=True)
        oof["hist_gbm"][te] = hgb_proba(X.iloc[tr], y[tr], X.iloc[te])
    now = datetime.now(timezone.utc).isoformat()
    out = pd.DataFrame(dict(container_id=df["container_id"], fold=fold_id, label=y,
                            p_tabpfn_plus=oof["plus"].round(5), p_tabpfn_thinking=oof["thinking"].round(5),
                            p_hist_gbm=oof["hist_gbm"].round(5)))
    out.to_csv(OUT / "replay_tabpfn_oof.csv", index=False)
    rec = dict(kind="tabpfn_oof_replay", rows=len(y), positives=int(y.sum()), folds=5,
               split="StratifiedGroupKFold by vessel_id, seed 42", model="TabPFN-3.5 (tabpfn_client v3.5)",
               thinking=dict(effort="medium", group_col=GROUP, group_time_col=TIME), recorded_at=now,
               action_costs_assumed=list(ACTION_COSTS),
               metrics={m: scores(y, oof[m], fee) for m in oof})
    (OUT / "replay_tabpfn_oof_receipt.json").write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec["metrics"], indent=1))


def curve():
    df, X, y = load()
    fee = df["projected_demurrage_usd"].fillna(0).to_numpy()
    tr_pool, te = folds(X, y)[0]
    sizes = [30, 60, 120, 240, len(tr_pool)]
    rows = []
    for n in sizes:
        reps = 1 if n == len(tr_pool) else 3
        for r in range(reps):
            rng = np.random.RandomState(100 + r)
            if n == len(tr_pool):
                idx = tr_pool
            else:
                pos = tr_pool[y[tr_pool] == 1]; neg = tr_pool[y[tr_pool] == 0]
                npos = max(2, int(round(n * len(pos) / len(tr_pool))))
                idx = np.r_[rng.choice(pos, npos, False), rng.choice(neg, n - npos, False)]
            for m in ("plus", "thinking", "hist_gbm"):
                if m == "hist_gbm":
                    p = hgb_proba(X.iloc[idx], y[idx], X.iloc[te])
                else:
                    p = tabpfn_proba(m, X.iloc[idx], y[idx], X.iloc[te], tag=f"curve_n{n}_r{r}")
                s = scores(y[te], p, fee[te])
                c300 = [c for c in s["cost"] if c["action_cost"] == 300.0][0]
                rows.append(dict(n_train=int(n), repeat=r, model=m, roc_auc=s["roc_auc"], avg_precision=s["avg_precision"],
                                 net_savings_300=c300["net_savings"], f1_cost_300=c300["f1"]))
                print(f"n={n} r={r} {m} auc={s['roc_auc']} ap={s['avg_precision']} net300={c300['net_savings']}", flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "learning_curve_runs.csv", index=False)
    agg = t.groupby(["n_train", "model"]).agg(["mean", "std"]).drop(columns="repeat").round(4)
    agg.to_csv(OUT / "learning_curve_summary.csv")
    meta = dict(kind="learning_curve", test_rows=int(len(te)), test_positives=int(y[te].sum()),
                test_split="fold 0 of StratifiedGroupKFold(5) by vessel_id, seed 42 (held-out vessels)",
                sizes=sizes, repeats="3 (1 at full pool)", recorded_at=datetime.now(timezone.utc).isoformat(),
                action_cost_for_net=300.0)
    (OUT / "learning_curve_meta.json").write_text(json.dumps(meta, indent=1))
    print(agg.to_string())


if __name__ == "__main__":
    {"smoke": smoke, "replay": replay, "curve": curve}[sys.argv[1]]()
