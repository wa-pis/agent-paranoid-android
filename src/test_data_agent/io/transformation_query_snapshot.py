"""Private captured-result envelope, not SQL execution or access authority.

Fictional development only. Parquet is an internal typed encoding, not the
declared input source. Exact envelope bytes bind adapter, query and result.
"""

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_FILE_BYTES
from test_data_agent.core.transformation_limits import EffectiveInputLimit, InputDimension
from test_data_agent.core.transformation_snapshot import SnapshotPart


def _capture_query_result(
    payload: bytes, *, adapter: str, query_sha256: str, entity: str,
    byte_limit: EffectiveInputLimit | None = None,
) -> SnapshotPart:
    """Wrap already captured typed bytes; never open a DB or issue approval."""
    if (type(payload) is not bytes or not payload
            or type(adapter) is not str or adapter not in {"postgres_query", "trino_query"}
            or type(query_sha256) is not str or len(query_sha256) != 64
            or any(c not in "0123456789abcdef" for c in query_sha256)
            or type(entity) is not str or not entity or len(entity) > 256):
        raise ValueError("invalid captured query result")
    envelope = b"APA-QUERY-1\n" + adapter.encode("ascii") + b"\n" + query_sha256.encode("ascii") + b"\n"
    limit = byte_limit or EffectiveInputLimit(InputDimension.BYTES, DEFAULT_MAX_INPUT_FILE_BYTES, "default")
    if limit.dimension is not InputDimension.BYTES:
        raise ValueError("invalid captured query byte limit")
    limit.check(len(payload) + len(envelope))
    return SnapshotPart("source", entity, envelope + payload)


def _query_result_payload(payload: bytes, adapter: str) -> bytes:
    """Reject missing/foreign envelopes; the caller bounds the full snapshot."""
    parts = payload.split(b"\n", 3)
    if (len(parts) != 4 or parts[0] != b"APA-QUERY-1"
            or parts[1] != adapter.encode("ascii") or len(parts[2]) != 64
            or any(c not in b"0123456789abcdef" for c in parts[2]) or not parts[3]):
        raise ValueError("invalid captured query result")
    return parts[3]
