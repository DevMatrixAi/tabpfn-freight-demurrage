"""Embedded zlib blobs for deep showcase desk templates."""
from __future__ import annotations
try:
    from deep_template_blobs_eval import EVAL_HTML_BLOB
    from deep_template_blobs_index import INDEX_HTML_BLOB
except ImportError:
    from apps.desk.deep_template_blobs_eval import EVAL_HTML_BLOB
    from apps.desk.deep_template_blobs_index import INDEX_HTML_BLOB
