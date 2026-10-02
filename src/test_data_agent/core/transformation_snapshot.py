"""Private byte identity for a reviewed transformation; not authorization."""

import hashlib
import hmac
import json
from collections.abc import Sequence
from dataclasses import dataclass, field

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS


class SnapshotIdentityError(ValueError):
    """Invalid private snapshot set; never echo input values."""


@dataclass(frozen=True, repr=False)
class SnapshotPart:
    kind: str
    name: str
    payload: bytes = field(repr=False)


def snapshot_identity(parts: Sequence[SnapshotPart], *, max_total_bytes: int) -> str:
    """Hash exact bounded bytes with domain-separated, order-independent labels."""
    valid_kinds = {"review", "policy", "evidence", "source", "mapping", "generation_policy"}
    seen: set[tuple[str, str]] = set()
    records: list[tuple[str, str, int, str]] = []
    total = 0
    valid = type(max_total_bytes) is int and max_total_bytes > 0
    for part in parts:
        if len(records) >= 3 * DEFAULT_MAX_INPUT_COLUMNS + 3:
            valid = False
            break
        if not isinstance(part, SnapshotPart) or type(part.kind) is not str or type(part.name) is not str:
            valid = False
            break
        if part.kind not in valid_kinds or not part.name or len(part.name) > 256 or type(part.payload) is not bytes:
            valid = False
            break
        if part.kind in {"review", "policy", "evidence"} and not part.payload:
            valid = False
            break
        key = (part.kind, part.name)
        if key in seen:
            valid = False
            break
        seen.add(key)
        total += len(part.payload)
        if total > max_total_bytes:
            valid = False
            break
        records.append((part.kind, part.name, len(part.payload), hashlib.sha256(part.payload).hexdigest()))
    required = {"review", "policy", "evidence", "source"}
    if not valid or not required.issubset({kind for kind, _ in seen}) or any(
        sum(kind == required_kind for kind, _ in seen) != 1
        for required_kind in ("review", "policy", "evidence")
    ):
        raise SnapshotIdentityError("invalid transformation snapshots") from None
    canonical = json.dumps(
        {"version": 1, "parts": sorted(records)},
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(b"transformation-snapshot-v1\0" + canonical).hexdigest()


def matches_snapshot_identity(expected: str, parts: Sequence[SnapshotPart], *, max_total_bytes: int) -> bool:
    """Reject any changed review, evidence, policy, source or transitive input."""
    if type(expected) is not str or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        return False
    return hmac.compare_digest(expected, snapshot_identity(parts, max_total_bytes=max_total_bytes))
