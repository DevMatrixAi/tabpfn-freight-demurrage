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
