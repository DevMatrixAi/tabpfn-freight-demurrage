"""MCP stdio server exposing 7 generic tools.

Uses the official `mcp` SDK when available; otherwise a minimal JSON-RPC
stdio loop that answers tools/list + tools/call.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from tabpfn_hack_core.core.pipeline import PipelineSession
from tabpfn_hack_core.domain import find_project_root, load_domain
from tabpfn_hack_core.tools_api import (
    CompareBaselineArgs,
    ExplainArgs,
    ExportReportArgs,
    FitPredictArgs,
    LoadTableArgs,
    ProfileArgs,
    SuggestActionsArgs,
    TOOL_SPECS,
)

_SESSION: PipelineSession | None = None


def _session() -> PipelineSession:
    global _SESSION
    if _SESSION is None:
        root = find_project_root()
        _SESSION = PipelineSession(domain=load_domain(root / "domain.yaml"), root=root)
    return _SESSION


def _tool_schemas() -> list[dict[str, Any]]:
    tools = []
    for spec in TOOL_SPECS:
        model = spec["args"]
        schema = model.model_json_schema()
        tools.append(
            {
                "name": spec["name"],
                "description": (model.__doc__ or spec["name"]).strip(),
                "inputSchema": schema,
            }
        )
    return tools


def _dispatch(name: str, arguments: dict[str, Any]) -> Any:
    s = _session()
    if name == "load_table":
        args = LoadTableArgs.model_validate(arguments)
        return s.load_table(
            path=args.path, csv_text=args.csv_text, table_id=args.table_id
        ).model_dump()
    if name == "profile":
        args = ProfileArgs.model_validate(arguments)
        return s.profile(args.table_id, sample_rows=args.sample_rows).model_dump()
    if name == "fit_predict":
        args = FitPredictArgs.model_validate(arguments)
        return s.fit_predict(
            args.table_id,
            label_col=args.label_col,
            feature_cols=args.feature_cols,
            mode=args.mode,
            test_size=args.test_size,
            group_col=args.group_col,
            group_time_col=args.group_time_col,
            random_state=args.random_state,
        ).model_dump(mode="json")
    if name == "explain":
        args = ExplainArgs.model_validate(arguments)
        return s.explain(
            args.table_id,
            label_col=args.label_col,
            mode=args.mode,
            max_features=args.max_features,
        ).model_dump()
    if name == "export_report":
        args = ExportReportArgs.model_validate(arguments)
        return s.export_report(
            args.table_id,
            title=args.title,
            formats=list(args.formats),
            out_dir=args.out_dir,
        ).model_dump()
    if name == "compare_baseline":
        args = CompareBaselineArgs.model_validate(arguments)
        return s.compare_baseline(
            args.table_id,
            label_col=args.label_col,
            mode=args.mode,
            baseline=args.baseline,
        ).model_dump(mode="json")
    if name == "suggest_actions":
        args = SuggestActionsArgs.model_validate(arguments)
        return s.suggest_actions(
            args.table_id,
            proba_col=args.proba_col,
            threshold_high=args.threshold_high,
            threshold_mid=args.threshold_mid,
            max_rows=args.max_rows,
        ).model_dump()
    raise ValueError(f"Unknown tool: {name}")


def _run_fastmcp() -> bool:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return False

    mcp = FastMCP("tabpfn-hack-core")

    @mcp.tool()
    def load_table(
        path: str | None = None,
        csv_text: str | None = None,
        table_id: str | None = None,
    ) -> dict:
        """Load a CSV into the session."""
        return _dispatch(
            "load_table",
            {"path": path, "csv_text": csv_text, "table_id": table_id},
        )

    @mcp.tool()
    def profile(table_id: str, sample_rows: int = 5) -> dict:
        """Profile column types, missingness, cardinality."""
        return _dispatch(
            "profile", {"table_id": table_id, "sample_rows": sample_rows}
        )

    @mcp.tool()
    def fit_predict(
        table_id: str,
        label_col: str | None = None,
        mode: str = "mock",
        test_size: float = 0.2,
        group_col: str | None = None,
        group_time_col: str | None = None,
        random_state: int = 42,
    ) -> dict:
        """Fit TabPFN (or mock) and predict with probabilities."""
        return _dispatch(
            "fit_predict",
            {
                "table_id": table_id,
                "label_col": label_col,
                "mode": mode,
                "test_size": test_size,
                "group_col": group_col,
                "group_time_col": group_time_col,
                "random_state": random_state,
            },
        )

    @mcp.tool()
    def explain(
        table_id: str,
        label_col: str | None = None,
        mode: str = "mock",
        max_features: int = 10,
    ) -> dict:
        """Feature attributions / importances."""
        return _dispatch(
            "explain",
            {
                "table_id": table_id,
                "label_col": label_col,
                "mode": mode,
                "max_features": max_features,
            },
        )

    @mcp.tool()
    def export_report(
        table_id: str,
        title: str = "tabpfn-hack-core demo report (synthetic)",
        out_dir: str = "artifacts",
    ) -> dict:
        """Export markdown/json report artifacts."""
        return _dispatch(
            "export_report",
            {"table_id": table_id, "title": title, "out_dir": out_dir},
        )

    @mcp.tool()
    def compare_baseline(
        table_id: str,
        label_col: str | None = None,
        mode: str = "mock",
        baseline: str = "sklearn_hist_gbm",
    ) -> dict:
        """Compare primary backend vs sklearn baseline."""
        return _dispatch(
            "compare_baseline",
            {
                "table_id": table_id,
                "label_col": label_col,
                "mode": mode,
                "baseline": baseline,
            },
        )

    @mcp.tool()
    def suggest_actions(
        table_id: str,
        proba_col: str = "proba_1",
        threshold_high: float | None = None,
        threshold_mid: float | None = None,
        max_rows: int = 50,
    ) -> dict:
        """Suggest domain-defined actions from score thresholds."""
        return _dispatch(
            "suggest_actions",
            {
                "table_id": table_id,
                "proba_col": proba_col,
                "threshold_high": threshold_high,
                "threshold_mid": threshold_mid,
                "max_rows": max_rows,
            },
        )

    mcp.run(transport="stdio")
    return True


def _run_minimal_stdio() -> None:
    """Minimal JSON-RPC MCP-ish stdio server (tools/list + tools/call)."""
    tools = _tool_schemas()

    def reply(msg_id: Any, result: Any) -> None:
        sys.stdout.write(
            json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n"
        )
        sys.stdout.flush()

    def reply_err(msg_id: Any, code: int, message: str) -> None:
        sys.stdout.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": code, "message": message},
                }
            )
            + "\n"
        )
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        if method == "initialize":
            reply(
                msg_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "tabpfn-hack-core", "version": "0.1.0"},
                },
            )
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            reply(msg_id, {"tools": tools})
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            try:
                result = _dispatch(name, arguments)
                reply(
                    msg_id,
                    {
                        "content": [
                            {"type": "text", "text": json.dumps(result, default=str)}
                        ]
                    },
                )
            except Exception as exc:  # noqa: BLE001
                reply_err(msg_id, -32000, str(exc))
        elif method == "ping":
            reply(msg_id, {})
        else:
            if msg_id is not None:
                reply_err(msg_id, -32601, f"Method not found: {method}")


def main() -> None:
    if not _run_fastmcp():
        _run_minimal_stdio()


if __name__ == "__main__":
    main()
