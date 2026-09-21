"""Index.html zlib blob (parts joined; replaces corrupt single-string push)."""
try:
    from deep_template_blobs_index_p0 import P0
    from deep_template_blobs_index_p1 import P1
    from deep_template_blobs_index_p2 import P2
except ImportError:
    from apps.desk.deep_template_blobs_index_p0 import P0
    from apps.desk.deep_template_blobs_index_p1 import P1
    from apps.desk.deep_template_blobs_index_p2 import P2
INDEX_HTML_BLOB = P0 + P1 + P2
