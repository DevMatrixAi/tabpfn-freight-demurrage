"""Write missing_wide_demurrage.csv on import."""
from __future__ import annotations
import base64, zlib
from pathlib import Path
try:
    from _csv_blob_chunks import CSV_BLOB
except ImportError:
    from fixtures.stress._csv_blob_chunks import CSV_BLOB  # type: ignore
_PATH = Path(__file__).resolve().parent / "missing_wide_demurrage.csv"
_data = zlib.decompress(base64.b64decode(CSV_BLOB))
if (not _PATH.exists()) or _PATH.read_bytes() != _data:
    _PATH.write_bytes(_data)
