"""Fictional approval materials only; no local confirmation or source output."""

from dataclasses import replace

import pytest
import yaml

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import ApprovalMaterialError, prepare_approval_request
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart, snapshot_identity


def material(*, sensitive: bool = False):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "code", "data_type": "string", "sensitive": sensitive}]}]})
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "code", "sensitivity": "non_sensitive",
              "behavior": {"action": "substitute", "mapping": {"kind": "csv", "path": "code-map.csv",
                  "source_columns": ["original"], "replacement_columns": ["replacement"]},
                  "unmatched": {"action": "preserve", "authorization_ref": "fictional-private-ref"}}}]}
    return (
        yaml.safe_dump(policy).encode(),
        profile.model_dump_json().encode(),
        (SnapshotPart("source", "items.csv", b"code\nfictional-a\n"),
         SnapshotPart("mapping", "code-map.csv", b"fictional-a,synthetic-1\n")),
    )


def prepare(policy: bytes, evidence: bytes, parts: tuple[SnapshotPart, ...]):
    return prepare_approval_request(policy, evidence, parts, max_total_bytes=8192,
                                    max_review_bytes=4096, budget=GenerationBudget(5))


def test_request_binds_rendered_review_and_referenced_bytes():
    request = prepare(*material())
    assert b'"unmatched": "preserve"' in request.review
    assert b"fictional-private-ref" not in request.review
    assert b"fictional-a" not in request.review
    assert "fictional" not in repr(request)
    assert snapshot_identity(request.parts, max_total_bytes=8192) == request.snapshot_sha256
    changed = list(request.parts)
    changed[-1] = replace(changed[-1], payload=changed[-1].payload + b"!")
    assert snapshot_identity(changed, max_total_bytes=8192) != request.snapshot_sha256


@pytest.mark.parametrize("change", ["missing_map", "extra_map", "sensitive", "invalid_evidence", "small_budget"])
def test_incomplete_or_unsafe_request_is_value_free(change):
    policy, evidence, parts = material(sensitive=change == "sensitive")
    if change == "missing_map":
        parts = parts[:1]
    elif change == "extra_map":
        parts += (SnapshotPart("mapping", "unreferenced.csv", b"x"),)
    elif change == "invalid_evidence":
        evidence = b'{"private":"fictional-private-marker"}'
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(ApprovalMaterialError) as error:
            prepare_approval_request(policy, evidence, parts,
                max_total_bytes=1 if change == "small_budget" else 8192,
                max_review_bytes=4096, budget=GenerationBudget(5))
    assert str(error.value) == "invalid transformation approval material"
    assert error.value.__context__ is None
