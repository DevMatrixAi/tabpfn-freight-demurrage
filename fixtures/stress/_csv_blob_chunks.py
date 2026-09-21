"""Chunked zlib of missing_wide_demurrage.csv."""
try:
    from _csv_blob_a import PART_A
    from _csv_blob_b import PART_B
except ImportError:
    from fixtures.stress._csv_blob_a import PART_A  # type: ignore
    from fixtures.stress._csv_blob_b import PART_B  # type: ignore
CSV_BLOB = PART_A + PART_B
