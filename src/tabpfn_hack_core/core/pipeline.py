"""In-memory table session + pipeline steps for MCP / demo."""
from __future__ import annotations

from tabpfn_hack_core.core.pipeline_actions import _BaselineActionsMixin
from tabpfn_hack_core.core.pipeline_explain import _ExplainExportMixin
from tabpfn_hack_core.core.pipeline_fit import _FitMixin
from tabpfn_hack_core.core.pipeline_whatif import _WhatIfMixin


class PipelineSession(_FitMixin, _WhatIfMixin, _ExplainExportMixin, _BaselineActionsMixin):
    """Holds loaded tables, last fit results, and domain config."""

    pass
