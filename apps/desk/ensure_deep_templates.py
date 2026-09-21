"""Unpack deep-showcase desk templates (fallback only).

Prefer checked-in readable HTML under templates/ for judge repro.
Zlib blobs in deep_template_blobs_*.py are used only when a template is
missing or lacks deep-panel markers (eval-latency / Thinking showcase).
"""
from __future__ import annotations

import base64
import zlib
from pathlib import Path

# One-shot repair if a prior MCP push corrupted the index blob mid-string.
_idx = Path(__file__).resolve().parent / "deep_template_blobs_index.py"
if _idx.exists():
    _t = _idx.read_text()
    if "UeiHerd26vmKN" in _t:
        _idx.write_text(_t.replace("UeiHerd26vmKN", "UeiHer26vmKN"))

try:
    from deep_template_blobs import EVAL_HTML_BLOB, INDEX_HTML_BLOB
except ImportError:
    from apps.desk.deep_template_blobs import EVAL_HTML_BLOB, INDEX_HTML_BLOB

_DIR = Path(__file__).resolve().parent / "templates"
_BLOBS = {"eval.html": EVAL_HTML_BLOB, "index.html": INDEX_HTML_BLOB}
# Markers that prove the deep showcase panels are present (judge path).
_MARKERS = {
    "eval.html": ("id=\"eval-latency\"", "id=\"eval-thinking\"", "id=\"eval-ablations\""),
    "index.html": ("thinking_effort", "judge-strip", "mode-thinking"),
}


def _has_deep_markers(path: Path, name: str) -> bool:
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return all(m in text for m in _MARKERS.get(name, ()))


def ensure_deep_templates(*, force: bool = False) -> dict[str, str]:
    """Write templates from blobs only when missing/stale. Returns status map."""
    _DIR.mkdir(parents=True, exist_ok=True)
    status: dict[str, str] = {}
    for name, blob in _BLOBS.items():
        path = _DIR / name
        if (not force) and _has_deep_markers(path, name):
            status[name] = "kept-readable"
            continue
        data = zlib.decompress(base64.b64decode(blob))
        if (not path.exists()) or path.read_bytes() != data:
            path.write_bytes(data)
            status[name] = "unpacked"
        else:
            status[name] = "blob-match"
    return status


# Import-time: fill gaps only — never clobber polished readable sources.
ensure_deep_templates()
