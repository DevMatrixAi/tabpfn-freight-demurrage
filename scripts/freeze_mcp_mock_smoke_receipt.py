#!/usr/bin/env python3
"""Freeze MCP 7-tool mock smoke receipt (refuses real TABPFN_TOKEN).

Always run with empty token:
  TABPFN_TOKEN= python scripts/freeze_mcp_mock_smoke_receipt.py

Writes:
  artifacts/freight-demurrage/mcp_mock_smoke_receipt.json
  artifacts/freight-demurrage/mcp_mock_smoke_receipt.md
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

OUT_DIR = ROOT / "artifacts" / "freight-demurrage"

# Deterministic mock latencies (ms) for VO crib — not wall-clock.
_MOCK_LATENCY_MS = {
    "load_table": 12,
    "profile": 18,
    "fit_predict": 95,
    "explain": 42,
    "export_report": 28,
    "compare_baseline": 55,
    "suggest_actions": 22,
}


def _refuse_token() -> None:
    token = (os.environ.get("TABPFN_TOKEN") or "").strip()
    if token:
        raise SystemExit(
            "Refusing to freeze MCP mock smoke receipt with TABPFN_TOKEN set — "
            "mock-only. Re-run with TABPFN_TOKEN="
        )


def _run_mock_smoke() -> dict:
    """Exercise 7 MCP tools via PipelineSession (mock backend only)."""
    from tabpfn_hack_core.core.pipeline import PipelineSession
    from tabpfn_hack_core.domain import load_domain
    from tabpfn_hack_core.tools_api import BackendMode, TOOL_SPECS

    domain_path = ROOT / "domains" / "freight-demurrage" / "domain.yaml"
    csv_path = ROOT / "domains" / "freight-demurrage" / "data" / "containers.csv"
    domain = load_domain(domain_path)
    sess = PipelineSession(domain=domain, root=ROOT)

    tool_names = [t["name"] for t in TOOL_SPECS]
    steps: list[dict] = []
    t0 = time.perf_counter()

    # 1 load_table
    load = sess.load_table(path=str(csv_path), table_id="freight")
    steps.append(
        {
            "tool": "load_table",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["load_table"],
            "n_rows": load.n_rows,
        }
    )

    # 2 profile
    prof = sess.profile("freight", sample_rows=3)
    steps.append(
        {
            "tool": "profile",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["profile"],
            "n_cols": len(prof.columns),
            "suggested_group_col": prof.suggested_group_col,
            "suggested_time_col": prof.suggested_time_col,
        }
    )

    # 3 fit_predict (force mock)
    fit = sess.fit_predict(
        "freight",
        mode=BackendMode.mock,
        test_size=0.25,
        group_col=domain.group_col,
        group_time_col=domain.time_col,
        thinking_effort="high",
    )
    steps.append(
        {
            "tool": "fit_predict",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["fit_predict"],
            "mode": fit.mode.value,
            "backend": fit.backend,
            "metrics": fit.metrics,
        }
    )

    # 4 explain
    expl = sess.explain("freight", mode=BackendMode.mock, max_features=8)
    steps.append(
        {
            "tool": "explain",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["explain"],
            "method": expl.method,
            "top": [i.get("feature") for i in expl.importances[:5]],
        }
    )

    # 5 export_report
    out = ROOT / "artifacts" / "mcp_cookbook"
    out.mkdir(parents=True, exist_ok=True)
    rep = sess.export_report(
        "freight", title="MCP mock smoke demurrage", out_dir=str(out)
    )
    steps.append(
        {
            "tool": "export_report",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["export_report"],
            "paths": rep.paths,
        }
    )

    # 6 compare_baseline
    cmp_ = sess.compare_baseline("freight", mode=BackendMode.mock)
    steps.append(
        {
            "tool": "compare_baseline",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["compare_baseline"],
            "judge_headline": (cmp_.judge_card or {}).get("headline"),
            "delta": cmp_.delta,
        }
    )

    # 7 suggest_actions
    acts = sess.suggest_actions("freight", max_rows=20)
    steps.append(
        {
            "tool": "suggest_actions",
            "ok": True,
            "latency_ms_mock": _MOCK_LATENCY_MS["suggest_actions"],
            "counts": acts.counts,
            "n_items": len(acts.items),
        }
    )

    wall_s = round(time.perf_counter() - t0, 3)
    assert len(steps) == 7
    assert [s["tool"] for s in steps] == tool_names

    return {
        "frozen": True,
        "mock": True,
        "label": "MCP 7-tool mock smoke receipt",
        "source": "scripts/freeze_mcp_mock_smoke_receipt.py (no live TabPFN)",
        "repro": "TABPFN_TOKEN= python scripts/freeze_mcp_mock_smoke_receipt.py",
        "pack": "freight-demurrage",
        "has_token": False,
        "token_mode": "empty",
        "tools": tool_names,
        "tool_count": len(steps),
        "all_ok": all(s.get("ok") for s in steps),
        "steps": steps,
        "wall_s": wall_s,
        "latency_ms_mock_total": sum(_MOCK_LATENCY_MS[t] for t in tool_names),
        "vo_lines": [
            "MCP 7-tool mock smoke · empty TABPFN_TOKEN · all ok.",
            "Tools: load_table → profile → fit_predict → explain → "
            "export_report → compare_baseline → suggest_actions.",
            f"Mock latency sum ≈ {sum(_MOCK_LATENCY_MS.values())} ms "
            f"(VO crib; wall ~{wall_s}s).",
            "Same PipelineSession / TOOL_SPECS the MCP stdio server exposes.",
        ],
        "frozen_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_receipt(*, out_dir: Path | None = None) -> tuple[Path, Path]:
    _refuse_token()
    dest = out_dir or OUT_DIR
    dest.mkdir(parents=True, exist_ok=True)
    payload = _run_mock_smoke()

    json_path = dest / "mcp_mock_smoke_receipt.json"
    md_path = dest / "mcp_mock_smoke_receipt.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        "# MCP 7-tool mock smoke receipt (VO crib)",
        "",
        f"**Token:** empty (`TABPFN_TOKEN=`) · **Mock only** · "
        f"**All ok:** {payload['all_ok']}",
        "",
        f"**Wall:** {payload['wall_s']}s · "
        f"**Mock latency sum:** {payload['latency_ms_mock_total']} ms",
        "",
        "| # | Tool | ok | latency_ms (mock) |",
        "| --- | --- | --- | ---: |",
    ]
    for i, s in enumerate(payload["steps"], 1):
        ok = "✅" if s.get("ok") else "❌"
        lines.append(
            f"| {i} | `{s['tool']}` | {ok} | {s.get('latency_ms_mock', '—')} |"
        )
    lines += [
        "",
        "## VO lines",
        "",
    ]
    for v in payload["vo_lines"]:
        lines.append(f"- {v}")
    lines += [
        "",
        "> Deterministic mock receipt — not live TabPFN. Freeze via "
        "`TABPFN_TOKEN= python scripts/freeze_mcp_mock_smoke_receipt.py`.",
        "",
        f"_Frozen at {payload['frozen_at']} · repro: `{payload['repro']}`_",
        "",
    ]
    md_path.write_text("\n".join(lines))
    return json_path, md_path


def main() -> int:
    _refuse_token()
    # Force mock path even if .env was loaded elsewhere
    os.environ["TABPFN_TOKEN"] = ""
    jp, mp = write_receipt()
    print(f"wrote {jp.relative_to(ROOT)}")
    print(f"wrote {mp.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
