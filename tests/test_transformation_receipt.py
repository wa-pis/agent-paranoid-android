"""Fictional local approval transport checks; no transformation execution."""

import os
import pty
import select
from dataclasses import replace

import pytest
import yaml

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import prepare_approval_request
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.csv_profiler import profile_csv_bytes
from test_data_agent.io.transformation_receipt import (
    LocalReceiptError, _canonical_request, _confirm_tty_fd, _issue_to_tty_fd, _owner_only,
    verify_local_receipt,
)


def request(*, source: bytes = b"code\nfictional-a\n"):
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source, "items", budget=GenerationBudget(5)))
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "code", "sensitivity": "non_sensitive",
              "behavior": {"action": "preserve", "authorization_ref": "fictional-ref"}}]}
    return prepare_approval_request(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(),
        (SnapshotPart("source", "items", source),), max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5))


def verify(prepared, path):
    return verify_local_receipt(prepared, path, max_total_bytes=8192,
                                max_review_bytes=4096, budget=GenerationBudget(5))


def test_missing_receipt_and_forged_request_fail_value_free(tmp_path):
    prepared = request()
    path = tmp_path / "approval.json"
    assert _canonical_request(prepared, max_total_bytes=8192, max_review_bytes=4096,
                              budget=GenerationBudget(5)) == prepared
    with pytest.raises(LocalReceiptError, match="^local transformation approval failed$") as error:
        verify(prepared, path)
    assert error.value.__context__ is None
    forged = replace(prepared, review=b"hidden plan")
    with pytest.raises(LocalReceiptError):
        verify(forged, path)


def test_receipt_boundary_rejects_source_conflicting_with_reviewed_evidence():
    prepared = request()
    policy = next(part.payload for part in prepared.parts if part.kind == "policy")
    evidence = next(part.payload for part in prepared.parts if part.kind == "evidence")
    forged = prepare_approval_request(
        policy, evidence, (SnapshotPart("source", "items", b"code\nprivate@example.test\n"),),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5),
    )
    with pytest.raises(ValueError) as error:
        _canonical_request(forged, max_total_bytes=8192, max_review_bytes=4096,
                           budget=GenerationBudget(5))
    assert "private@example.test" not in str(error.value)


def test_local_tty_issues_owner_only_receipt_and_stale_bytes_fail(tmp_path):
    prepared = request()
    path = tmp_path / "approval.json"
    master, slave = pty.openpty()
    try:
        os.write(master, b"APPROVE\n")
        _issue_to_tty_fd(prepared, path, slave, GenerationBudget(5))
        ready, _, _ = select.select([master], [], [], 1)
        assert ready
        output = os.read(master, 4096)
        assert b"fictional-a" not in output
        assert b'"preserves_original": true' in output
    finally:
        os.close(master)
        os.close(slave)
    assert path.stat().st_mode & 0o077 == 0
    assert verify(prepared, path) == prepared.parts
    with pytest.raises(LocalReceiptError):
        verify(request(source=b"code\nfictional-b\n"), path)


def test_receipt_rejects_group_or_world_readable_modes():
    assert _owner_only(os.geteuid(), 0o600)
    assert not _owner_only(os.geteuid(), 0o640)
    assert not _owner_only(os.geteuid(), 0o604)
    assert not _owner_only(os.geteuid() + 1, 0o600)


def test_non_tty_cannot_confirm(tmp_path):
    read_fd, write_fd = os.pipe()
    try:
        with pytest.raises(ValueError):
            _confirm_tty_fd(read_fd, b"fictional review", "0" * 64)
        assert not (tmp_path / "approval.json").exists()
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_rejected_answer_does_not_publish_receipt(tmp_path):
    master, slave = pty.openpty()
    path = tmp_path / "approval.json"
    try:
        os.write(master, b"NO\n")
        with pytest.raises(ValueError):
            _issue_to_tty_fd(request(), path, slave, GenerationBudget(5))
        assert not path.exists()
    finally:
        os.close(master)
        os.close(slave)
