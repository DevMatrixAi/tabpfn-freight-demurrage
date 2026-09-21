"""Unpack deep-showcase desk templates."""
from __future__ import annotations
import base64, zlib
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

def ensure_deep_templates() -> None:
    _DIR.mkdir(parents=True, exist_ok=True)
    for name, blob in _BLOBS.items():
        path = _DIR / name
        data = zlib.decompress(base64.b64decode(blob))
        if (not path.exists()) or path.read_bytes() != data:
            path.write_bytes(data)

ensure_deep_templates()
