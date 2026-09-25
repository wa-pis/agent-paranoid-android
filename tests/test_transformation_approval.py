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
                  "unmatched": {"action": "preserve", "authorization_ref": "fictional-private-ref",
                                "comment": "Reviewed fictional business code"}}}]}
    return (
        yaml.safe_dump(policy).encode(),
        profile.model_dump_json().encode(),
        (SnapshotPart("source", "items.csv", b"code\nfictional-a\n"),
         SnapshotPart("mapping", "code-map.csv", b"original,replacement\nfictional-a,synthetic-1\n")),
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


@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("case", ["valid", "entity", "field", "type", "version", "malformed"])
def test_generation_reference_is_validated_against_target(fallback, case):
    policy_bytes, evidence, parts = material()
    policy = yaml.safe_load(policy_bytes)
    action = {"action": "synthesize", "generation_policy_ref": "generation.yaml"}
    if fallback:
        policy["fields"][0]["behavior"]["unmatched"] = action
    else:
        policy["fields"][0]["behavior"] = action
        parts = parts[:1]
    spec = {"schema_version": "1.0" if case == "version" else "1.1", "entities": [{
        "name": "other" if case == "entity" else "items", "row_count": 1, "fields": [{
            "name": "other" if case == "field" else "code",
            "data_type": "integer" if case == "type" else "string"}]}]}
    payload = b"fictional: [" if case == "malformed" else yaml.safe_dump(spec).encode()
    parts += (SnapshotPart("generation_policy", "generation.yaml", payload),)
    if case == "valid":
        assert prepare(yaml.safe_dump(policy).encode(), evidence, parts).snapshot_sha256
    else:
        with pytest.raises(ApprovalMaterialError) as caught:
            prepare(yaml.safe_dump(policy).encode(), evidence, parts)
        assert caught.value.__context__ is None


def test_review_comment_and_profile_evidence_are_snapshot_bound():
    policy, evidence, parts = material()
    original = prepare(policy, evidence, parts)
    profile = DatasetProfile.model_validate_json(evidence)
    profile.entities[0].fields[0].is_identifier = True
    changed = prepare(policy, profile.model_dump_json().encode(), parts)
    assert changed.review != original.review
    assert changed.snapshot_sha256 != original.snapshot_sha256


def test_exact_text_review_binds_global_and_column_tables_without_literals():
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 2,
        "fields": [{"name": "status", "data_type": "string"}]}]})
    def table(path):
        return {"kind": "csv", "path": path, "source_columns": ["old"],
                "replacement_columns": ["new"]}
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "file_text_mapping": table("all.csv"), "fields": [{
                  "entity": "items", "field": "status", "sensitivity": "non_sensitive",
                  "behavior": {"action": "replace_text", "mapping": table("status.csv")},
              }]}
    parts = (SnapshotPart("source", "items", b"status\ntrue\nlocal\n"),
             SnapshotPart("mapping", "all.csv", b"old,new\ntrue,false\n"),
             SnapshotPart("mapping", "status.csv", b"old,new\nlocal,column-result\n"))
    policy_yaml = yaml.safe_dump(policy).encode()
    evidence = profile.model_dump_json().encode()
    request = prepare(policy_yaml, evidence, parts)
    assert b'"file_text_rules": true' in request.review
    assert b'"column_text_rules": true' in request.review
    assert b"column-result" not in request.review
    assert b"local" not in request.review
    changed = list(parts)
    changed[1] = replace(changed[1], payload=b"old,new\ntrue,other\n")
    assert prepare(policy_yaml, evidence, tuple(changed)).snapshot_sha256 != request.snapshot_sha256
    overlapping = list(parts)
    overlapping[2] = replace(overlapping[2], payload=b"old,new\ntrue,column-result\n")
    overridden = prepare(policy_yaml, evidence, tuple(overlapping))
    assert overridden.snapshot_sha256 != request.snapshot_sha256
    assert b"column-result" not in overridden.review
    identity = list(parts)
    identity[1] = replace(identity[1], payload=b"old,new\ntrue,true\n")
    with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$"):
        prepare(policy_yaml, evidence, tuple(identity))


@pytest.mark.parametrize("mapping_kind", ["inline", "csv", "domain"])
@pytest.mark.parametrize("replacement", ["fictional-a", "synthetic-b"])
@pytest.mark.parametrize("sensitive", [False, True])
def test_identity_substitution_fails_before_receipt(mapping_kind, replacement, sensitive):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string", "sensitive": sensitive}]}]})
    inline = {"kind": "inline", "entries": [{"original": ["fictional-a"],
              "replacement": [replacement]}]}
    csv_mapping = {"kind": "csv", "path": "mapping.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
    mapping = (inline if mapping_kind == "inline" else csv_mapping if mapping_kind == "csv"
               else {"kind": "domain", "name": "shared"})
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "value",
              "sensitivity": "sensitive" if sensitive else "non_sensitive",
              "behavior": {"action": "substitute", "mapping": mapping}}]}
    if mapping_kind == "domain":
        policy["domains"] = [{"name": "shared", "mapping": inline}]
    parts = [SnapshotPart("source", "items", b"value\nfictional-a\n")]
    if mapping_kind == "csv":
        parts.append(SnapshotPart("mapping", "mapping.csv",
                                  f"old,new\nfictional-a,{replacement}\n".encode()))
    payload = yaml.safe_dump(policy).encode()
    evidence = profile.model_dump_json().encode()
    if replacement == "fictional-a":
        with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$") as error:
            prepare(payload, evidence, tuple(parts))
        assert error.value.__context__ is None
        assert "fictional-a" not in str(error.value)
    else:
        assert prepare(payload, evidence, tuple(parts)).snapshot_sha256


@pytest.mark.parametrize("mapping_kind", ["inline", "csv", "domain"])
def test_same_datetime_instant_rejected_before_approval(mapping_kind):
    original = "2025-04-30T12:34:56+03:00"
    replacement = "2025-04-30T09:34:56Z"
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "event_at", "data_type": "datetime"}]}]})
    inline = {"kind": "inline", "entries": [{"original": [original],
              "replacement": [replacement]}]}
    csv_mapping = {"kind": "csv", "path": "mapping.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
    mapping = (inline if mapping_kind == "inline" else csv_mapping if mapping_kind == "csv"
               else {"kind": "domain", "name": "shared"})
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "event_at",
              "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": mapping}}]}
    if mapping_kind == "domain":
        policy["domains"] = [{"name": "shared", "mapping": inline}]
    parts = [SnapshotPart("source", "items", b"event_at\n2025-04-30T12:34:56+03:00\n")]
    if mapping_kind == "csv":
        parts.append(SnapshotPart("mapping", "mapping.csv",
                                  f"old,new\n{original},{replacement}\n".encode()))
    with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$") as error:
        prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(), tuple(parts))
    assert error.value.__context__ is None
    assert replacement not in str(error.value)


def test_composite_mapping_has_no_field_binding_and_cannot_be_approved():
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "string", "sensitive": True}]}]})
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "value", "sensitivity": "sensitive",
              "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                  {"original": ["fictional-a", "fictional-b"],
                   "replacement": ["synthetic-a", "fictional-b"]}]}}}]}
    with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$"):
        prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(),
                (SnapshotPart("source", "items", b"value\nfictional-a\n"),))


@pytest.mark.parametrize("mapping_kind", ["inline", "csv"])
@pytest.mark.parametrize("partial_identity", [False, True])
@pytest.mark.parametrize("child_account_type", ["string", "integer"])
def test_composite_domain_binds_ordered_fields_in_both_entities(mapping_kind, partial_identity, child_account_type):
    profile = DatasetProfile.model_validate({"entities": [
        {"name": entity, "row_count": 1, "fields": [
            {"name": "region", "data_type": "string"},
            {"name": "account", "data_type": child_account_type if entity == "child" else "string",
             "sensitive": True},
        ]} for entity in ("parent", "child")
    ]})
    replacement = "fictional-b" if partial_identity else "synthetic-b"
    mapping = ({"kind": "inline", "entries": [{
        "original": ["fictional-a", "fictional-b"],
        "replacement": ["synthetic-a", replacement],
    }]} if mapping_kind == "inline" else {
        "kind": "csv", "path": "pair.csv",
        "source_columns": ["old_region", "old_account"],
        "replacement_columns": ["new_region", "new_account"],
    })
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "domains": [{"name": "pair", "mapping": mapping}], "fields": [
                  {"entity": entity, "field": field, "sensitivity": sensitivity,
                   "behavior": {"action": "substitute", "mapping": {
                       "kind": "domain", "name": "pair", "component": component,
                   }}}
                  for entity in ("parent", "child")
                  for component, field, sensitivity in ((0, "region", "non_sensitive"),
                                                       (1, "account", "sensitive"))
              ]}
    parts = [SnapshotPart("source", "parent.csv", b"region,account\nfictional-a,fictional-b\n"),
             SnapshotPart("source", "child.csv", b"region,account\nfictional-a,fictional-b\n")]
    if mapping_kind == "csv":
        parts.append(SnapshotPart("mapping", "pair.csv", (
            f"old_region,old_account,new_region,new_account\nfictional-a,fictional-b,synthetic-a,{replacement}\n"
        ).encode()))
    if partial_identity or child_account_type != "string":
        with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$") as error:
            prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(), tuple(parts))
        assert error.value.__context__ is None
        assert "fictional-b" not in str(error.value)
    else:
        request = prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(), tuple(parts))
        assert request.snapshot_sha256
        assert request.review.count(b'"mapping_domain": 1') == 4
        assert request.review.count(b'"mapping_component": 0') == 2
        assert request.review.count(b'"mapping_component": 1') == 2
        assert b"fictional-a" not in request.review
        assert b'"pair"' not in request.review


@pytest.mark.parametrize("components", [[None, 1], [0, 0], [0, 2]])
def test_composite_domain_rejects_missing_or_ambiguous_field_positions(components):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "left", "data_type": "string"}, {"name": "right", "data_type": "string"}]}]})
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "domains": [{"name": "pair", "mapping": {"kind": "inline", "entries": [{
                  "original": ["fictional-a", "fictional-b"],
                  "replacement": ["synthetic-a", "synthetic-b"],
              }]}}], "fields": [{"entity": "items", "field": field,
                  "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
                      "kind": "domain", "name": "pair", **({} if component is None else {"component": component}),
                  }}} for field, component in zip(("left", "right"), components, strict=True)]}
    with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$"):
        prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(),
                (SnapshotPart("source", "items.csv", b"left,right\nfictional-a,fictional-b\n"),))


@pytest.mark.parametrize("original,replacement,rejected", [
    ("+001", "1", True), ("+001", "2", False), ("NULL", "NULL", False),
])
def test_sensitive_csv_identity_uses_normalized_types_and_allows_null(original, replacement, rejected):
    profile = DatasetProfile.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "value", "data_type": "integer", "nullable": True, "sensitive": True}]}]})
    policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
              "seed": 7, "fields": [{"entity": "items", "field": "value", "sensitivity": "sensitive",
              "behavior": {"action": "substitute", "mapping": {"kind": "csv", "path": "mapping.csv",
                  "source_columns": ["old"], "replacement_columns": ["new"],
                  "null_token": "NULL"}}}]}
    parts = (SnapshotPart("source", "items", b"value\n1\n"),
             SnapshotPart("mapping", "mapping.csv", f"old,new\n{original},{replacement}\n".encode()))
    if rejected:
        with pytest.raises(ApprovalMaterialError, match="^invalid transformation approval material$"):
            prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(), parts)
    else:
        assert prepare(yaml.safe_dump(policy).encode(), profile.model_dump_json().encode(), parts).snapshot_sha256


@pytest.mark.parametrize("change", ["missing_map", "extra_map", "duplicate_map", "sensitive", "invalid_evidence", "small_budget"])
def test_incomplete_or_unsafe_request_is_value_free(change):
    policy, evidence, parts = material(sensitive=change == "sensitive")
    if change == "missing_map":
        parts = parts[:1]
    elif change == "extra_map":
        parts += (SnapshotPart("mapping", "unreferenced.csv", b"x"),)
    elif change == "duplicate_map":
        parts += (SnapshotPart("mapping", "code-map.csv", b"original,replacement\nfictional-a,synthetic-2\n"),)
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
