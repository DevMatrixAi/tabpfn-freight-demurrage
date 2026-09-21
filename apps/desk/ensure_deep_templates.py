"""Unpack deep-showcase desk templates."""
from __future__ import annotations
import base64, zlib
from pathlib import Path

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
