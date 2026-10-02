"""Only fictional bytes; this identity alone grants no preservation authority."""

from dataclasses import replace

import pytest

from test_data_agent.core.transformation_snapshot import (
    SnapshotIdentityError,
    SnapshotPart,
    matches_snapshot_identity,
    snapshot_identity,
)


def parts() -> tuple[SnapshotPart, ...]:
    return (
        SnapshotPart("review", "display", b"items.code: preserve; items.amount: synthesize"),
        SnapshotPart("policy", "behavior.yaml", b"fictional-policy"),
        SnapshotPart("evidence", "classification", b"code: reviewed non-sensitive"),
        SnapshotPart("source", "items.csv", b"code,amount\nfictional-a,10\n"),
        SnapshotPart("mapping", "code.csv", b"fictional-a,synthetic-1\n"),
        SnapshotPart("generation_policy", "amount.yaml", b"fictional-generator"),
    )


def test_identity_binds_every_byte_and_is_order_independent():
    original = parts()
    digest = snapshot_identity(original, max_total_bytes=1024)
    assert snapshot_identity(tuple(reversed(original)), max_total_bytes=1024) == digest
    for index, part in enumerate(original):
        changed = list(original)
        changed[index] = replace(part, payload=part.payload + b"!")
        assert not matches_snapshot_identity(digest, changed, max_total_bytes=1024)
    renamed = list(original)
    renamed[3] = replace(renamed[3], name="other.csv")
    assert not matches_snapshot_identity(digest, renamed, max_total_bytes=1024)
    assert matches_snapshot_identity(digest, original, max_total_bytes=1024)


@pytest.mark.parametrize("invalid", [
    (SnapshotPart("policy", "x", b"x"),),
    parts() + (SnapshotPart("source", "items.csv", b"different"),),
    parts() + (SnapshotPart("review", "second", b"hidden"),),
    parts() + (SnapshotPart("unexpected", "x", b"x"),),
    tuple(replace(part, payload=b"") if part.kind == "review" else part for part in parts()),
])
def test_missing_duplicate_and_unknown_parts_fail_without_values(invalid):
    with pytest.raises(SnapshotIdentityError, match="^invalid transformation snapshots$") as error:
        snapshot_identity(invalid, max_total_bytes=1024)
    assert "fictional" not in str(error.value)


def test_budget_and_bad_digest_fail_closed():
    with pytest.raises(SnapshotIdentityError):
        snapshot_identity(parts(), max_total_bytes=1)
    assert not matches_snapshot_identity("not-a-digest", parts(), max_total_bytes=1024)
    with pytest.raises(SnapshotIdentityError):
        snapshot_identity(parts() + tuple(
            SnapshotPart("mapping", f"extra-{index}", b"") for index in range(3001)
        ), max_total_bytes=1024)
