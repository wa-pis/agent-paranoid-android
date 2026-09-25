"""Fixed fictional CSV snapshots; no source-preserving execution."""

import os

import pytest
import yaml

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_approval import ApprovalRequest, prepare_approval_request
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.csv_profiler import profile_csv, profile_csv_bytes
from test_data_agent.io.transformation_receipt import _canonical_request
from test_data_agent.io.transformation_source import (
    TransformationSourceError, load_csv_source_snapshot, prepare_csv_review_from_paths,
    prepare_csv_review_request,
    revalidate_csv_evidence, trace_csv_review_request,
)


def test_csv_review_derives_evidence_from_bound_source_bytes():
    source = SnapshotPart("source", "items", b"status\nready\nwaiting\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5),
    ))
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "fields": [{"entity": "items", "field": "status",
        "sensitivity": "non_sensitive", "behavior": {"action": "preserve",
        "authorization_ref": "fictional-ref", "comment": "Reviewed fictional status"}}],
    }).encode()
    request = prepare_csv_review_request(
        policy, source, (), max_total_bytes=8192, max_review_bytes=4096,
        budget=GenerationBudget(5),
    )
    assert next(part.payload for part in request.parts if part.kind == "evidence") == (
        profile.model_dump_json().encode()
    )
    assert _canonical_request(request, max_total_bytes=8192, max_review_bytes=4096,
                              budget=GenerationBudget(5)) == request
    with pytest.raises(TransformationSourceError, match="^invalid transformation source review$"):
        prepare_csv_review_request(policy, source, (source,), max_total_bytes=8192,
                                   max_review_bytes=4096, budget=GenerationBudget(5))


def test_csv_review_rejects_policy_for_other_source_without_values():
    source = SnapshotPart("source", "items", b"status\nready\n")
    wrong_profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        b"different\nfictional-marker\n", "items", budget=GenerationBudget(5),
    ))
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(wrong_profile),
        "seed": 7, "fields": [{"entity": "items", "field": "different",
        "sensitivity": "non_sensitive", "behavior": {"action": "preserve",
        "authorization_ref": "fictional-ref", "comment": "Reviewed fictional field"}}],
    }).encode()
    with pytest.raises(TransformationSourceError, match="^invalid transformation source review$") as error:
        prepare_csv_review_request(policy, source, (), max_total_bytes=8192,
                                   max_review_bytes=4096, budget=GenerationBudget(5))
    assert "fictional-marker" not in str(error.value)


def test_csv_review_binds_referenced_mapping_bytes():
    source = SnapshotPart("source", "items", b"status\nready\nwaiting\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5),
    ))
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "fields": [{"entity": "items", "field": "status",
        "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
        "kind": "csv", "path": "status-map.csv", "source_columns": ["old"],
        "replacement_columns": ["new"]}}}],
    }).encode()
    mapping = SnapshotPart("mapping", "status-map.csv", b"old,new\nready,done\nwaiting,pending\n")
    request = prepare_csv_review_request(policy, source, (mapping,), max_total_bytes=8192,
                                         max_review_bytes=4096, budget=GenerationBudget(5))
    assert mapping in request.parts
    assert _canonical_request(request, max_total_bytes=8192, max_review_bytes=4096,
                              budget=GenerationBudget(5)) == request
    changed = SnapshotPart("mapping", mapping.name, b"old,new\nready,other\nwaiting,pending\n")
    changed_request = prepare_csv_review_request(policy, source, (changed,), max_total_bytes=8192,
                                                 max_review_bytes=4096, budget=GenerationBudget(5))
    assert changed_request.snapshot_sha256 != request.snapshot_sha256


def test_csv_review_trace_combines_file_and_column_rules_without_values():
    source = SnapshotPart("source", "items", b"a,b,c\none,two,private-marker\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5),
    ))
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "file_text_mapping": {"kind": "csv", "path": "all.csv",
        "source_columns": ["old"], "replacement_columns": ["new"]},
        "fields": [
            {"entity": "items", "field": "a", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text"}},
            {"entity": "items", "field": "b", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text", "mapping": {"kind": "csv",
             "path": "b.csv", "source_columns": ["old"], "replacement_columns": ["new"]}}},
            {"entity": "items", "field": "c", "sensitivity": "unknown",
             "behavior": {"action": "drop"}},
        ],
    }).encode()
    request = prepare_csv_review_request(policy, source, (
        SnapshotPart("mapping", "all.csv", b"old,new\none,global\n"),
        SnapshotPart("mapping", "b.csv", b"old,new\ntwo,local\n"),
    ), max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    summary = trace_csv_review_request(
        request, max_events=1, max_cells=2, max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5),
    )
    assert (summary.matched_cells, summary.unmatched_cells, summary.truncated) == (2, 0, True)
    assert summary.rule_counts == ((1, "file", 1, 1), (2, "column", 1, 1))
    assert "private-marker" not in repr(summary)
    assert "global" not in repr(summary)
    for kind, name, payload in (
        ("source", "items", b"a,b,c\none,two,other-marker\n"),
        ("mapping", "all.csv", b"old,new\none,other-replacement\n"),
    ):
        forged_parts = tuple(
            SnapshotPart(part.kind, part.name, payload)
            if (part.kind, part.name) == (kind, name) else part
            for part in request.parts
        )
        forged = ApprovalRequest(request.review, forged_parts, request.snapshot_sha256)
        with pytest.raises(TransformationSourceError, match="^invalid transformation trace$"):
            trace_csv_review_request(forged, max_events=1, max_cells=2,
                                     max_total_bytes=8192, max_review_bytes=4096,
                                     budget=GenerationBudget(5))
    with pytest.raises(TransformationSourceError, match="^invalid transformation trace$") as error:
        trace_csv_review_request(request, max_events=1, max_cells=1,
                                 max_total_bytes=8192, max_review_bytes=4096,
                                 budget=GenerationBudget(5))
    assert "private-marker" not in str(error.value)


@pytest.mark.parametrize("source_bytes,sensitivity,field,blocked", [
    (b"status\nA\nB\n", "sensitive", "status", True),
    (b"status\nA\nB\n", "unknown", "status", True),
    (b"status\nA\nB\n", "non_sensitive", "status", False),
    (b"status\nA\n", "sensitive", "status", False),
    (b" status \nA\n", "sensitive", "status", False),
    (b"status;other\nA;x\nB;y\n", "sensitive", "status", True),
    (b"email\nA\nB\n", "non_sensitive", "email", True),
])
def test_sensitive_text_review_rejects_only_reachable_source_value_reuse(
    source_bytes, sensitivity, field, blocked,
):
    source = SnapshotPart("source", "items", source_bytes)
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5),
    ))
    names = tuple(column.name for column in profile.entities[0].fields)
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "file_text_mapping": {"kind": "csv", "path": "all.csv",
        "source_columns": ["old"], "replacement_columns": ["new"]},
        "fields": [{"entity": "items", "field": name,
                    "sensitivity": sensitivity if name == field else "non_sensitive",
                    "behavior": {"action": "replace_text"} if name == field else {"action": "drop"}}
                   for name in names],
    }).encode()
    mapping = SnapshotPart("mapping", "all.csv", b"old,new\nA,B\nB,A\n")
    evidence = profile.model_dump_json().encode()
    request = prepare_approval_request(policy, evidence, (source, mapping),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if blocked:
        with pytest.raises(TransformationSourceError, match="^invalid transformation source review$") as error:
            prepare_csv_review_request(policy, source, (mapping,), max_total_bytes=8192,
                                       max_review_bytes=4096, budget=GenerationBudget(5))
        assert "A" not in str(error.value)
        with pytest.raises(TransformationSourceError, match="^invalid sensitive text replacement$"):
            _canonical_request(request, max_total_bytes=8192, max_review_bytes=4096,
                               budget=GenerationBudget(5))
    else:
        assert prepare_csv_review_request(policy, source, (mapping,), max_total_bytes=8192,
                                          max_review_bytes=4096, budget=GenerationBudget(5)) == request


@pytest.mark.parametrize("other_sensitivity,blocked", [("sensitive", True), ("non_sensitive", False)])
def test_sensitive_text_review_checks_other_sensitive_source_columns(other_sensitivity, blocked):
    source = SnapshotPart("source", "items", b"status,other\nA,X\nB,Y\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5),
    ))
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "file_text_mapping": {"kind": "csv", "path": "all.csv",
        "source_columns": ["old"], "replacement_columns": ["new"]},
        "fields": [{"entity": "items", "field": "status", "sensitivity": "sensitive",
                    "behavior": {"action": "replace_text"}},
                   {"entity": "items", "field": "other", "sensitivity": other_sensitivity,
                    "behavior": {"action": "drop"}}],
    }).encode()
    mapping = SnapshotPart("mapping", "all.csv", b"old,new\nA,X\nB,Z\n")
    if blocked:
        with pytest.raises(TransformationSourceError, match="^invalid transformation source review$"):
            prepare_csv_review_request(policy, source, (mapping,), max_total_bytes=8192,
                                       max_review_bytes=4096, budget=GenerationBudget(5))
    else:
        assert prepare_csv_review_request(policy, source, (mapping,), max_total_bytes=8192,
                                          max_review_bytes=4096, budget=GenerationBudget(5)).snapshot_sha256


def test_csv_review_reads_policy_source_and_mapping_from_fixed_local_paths(tmp_path):
    source = tmp_path / "items.csv"
    source.write_bytes(b"status\nready\nwaiting\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.read_bytes(), "items", budget=GenerationBudget(5),
    ))
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "fields": [{"entity": "items", "field": "status",
        "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": {
        "kind": "csv", "path": "status-map.csv", "source_columns": ["old"],
        "replacement_columns": ["new"]}}}],
    }).encode()
    (tmp_path / "policy.yaml").write_bytes(policy)
    (tmp_path / "status-map.csv").write_bytes(b"old,new\nready,done\nwaiting,pending\n")
    request = prepare_csv_review_from_paths(
        source, "items", tmp_path, "policy.yaml", max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5),
    )
    assert {part.kind for part in request.parts} == {"review", "policy", "evidence", "source", "mapping"}
    assert b"ready" not in request.review
    assert b"done" not in request.review
    (tmp_path / "status-map.csv").write_bytes(b"old,new\nready,other\nwaiting,pending\n")
    changed = prepare_csv_review_from_paths(
        source, "items", tmp_path, "policy.yaml", max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5),
    )
    assert changed.snapshot_sha256 != request.snapshot_sha256
    total_input_bytes = (source.stat().st_size + (tmp_path / "policy.yaml").stat().st_size
                         + (tmp_path / "status-map.csv").stat().st_size)
    with pytest.raises(TransformationSourceError, match="^invalid transformation source review$") as error:
        prepare_csv_review_from_paths(
            source, "items", tmp_path, "policy.yaml", max_total_bytes=total_input_bytes - 1,
            max_review_bytes=4096, budget=GenerationBudget(5),
        )
    assert "ready" not in str(error.value)


def test_csv_review_reads_global_and_column_text_tables_once(tmp_path):
    source = tmp_path / "items.csv"
    source.write_bytes(b"status\ntrue\nlocal\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.read_bytes(), "items", budget=GenerationBudget(5),
    ))
    def table(path):
        return {"kind": "csv", "path": path, "source_columns": ["old"],
                "replacement_columns": ["new"]}
    policy = yaml.safe_dump({
        "schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
        "seed": 7, "file_text_mapping": table("all.csv"), "fields": [{
            "entity": "items", "field": "status", "sensitivity": "non_sensitive",
            "behavior": {"action": "replace_text", "mapping": table("status.csv")},
        }],
    }).encode()
    (tmp_path / "policy.yaml").write_bytes(policy)
    (tmp_path / "all.csv").write_bytes(b"old,new\ntrue,false\n")
    (tmp_path / "status.csv").write_bytes(b"old,new\nlocal,column-result\n")
    request = prepare_csv_review_from_paths(
        source, "items", tmp_path, "policy.yaml", max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5),
    )
    assert sorted(part.name for part in request.parts if part.kind == "mapping") == ["all.csv", "status.csv"]
    assert b"column-result" not in request.review
    assert _canonical_request(request, max_total_bytes=8192, max_review_bytes=4096,
                              budget=GenerationBudget(5)) == request
    (tmp_path / "all.csv").write_bytes(b"old,new\ntrue,other\n")
    changed = prepare_csv_review_from_paths(
        source, "items", tmp_path, "policy.yaml", max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5),
    )
    assert changed.snapshot_sha256 != request.snapshot_sha256


def test_fixed_bytes_reprofile_without_reopening_path(tmp_path):
    path = tmp_path / "items.csv"
    path.write_bytes(b"status,amount\nfictional-a,7\nfictional-b,8\n")
    budget = GenerationBudget(5)
    source = load_csv_source_snapshot(path, "items", budget=budget, max_bytes=1024)
    profile = csv_profile_to_dataset_profile(profile_csv(path, table_name="items"))
    evidence = profile.model_dump_json().encode()
    assert revalidate_csv_evidence(source, evidence, budget=budget, max_bytes=1024) == profile
    path.write_bytes(b"status,amount\nprivate@example.test,7\n")
    assert revalidate_csv_evidence(source, evidence, budget=budget, max_bytes=1024) == profile
    changed = load_csv_source_snapshot(path, "items", budget=budget, max_bytes=1024)
    with pytest.raises(TransformationSourceError, match="^invalid transformation source evidence$"):
        revalidate_csv_evidence(changed, evidence, budget=budget, max_bytes=1024)


def test_snapshot_matches_existing_profiler_and_rejects_changed_evidence(tmp_path):
    path = tmp_path / "items.csv"
    path.write_bytes(b"status,amount\nfictional-a,0\n,1\n")
    budget = GenerationBudget(5)
    source = load_csv_source_snapshot(path, "items", budget=budget, max_bytes=1024)
    assert profile_csv_bytes(source.payload, "items", budget=budget, max_bytes=1024) == profile_csv(
        path, table_name="items"
    )
    evidence = csv_profile_to_dataset_profile(profile_csv(path, table_name="items"))
    evidence.entities[0].fields[0].sensitive = True
    with pytest.raises(TransformationSourceError):
        revalidate_csv_evidence(source, evidence.model_dump_json().encode(), budget=budget, max_bytes=1024)


def test_source_loader_rejects_oversize_and_symlink_without_values(tmp_path):
    path = tmp_path / "items.csv"
    path.write_bytes(b"status\nfictional-a\n")
    link = tmp_path / "link.csv"
    link.symlink_to(path)
    for candidate, max_bytes in ((path, 4), (link, 1024)):
        with pytest.raises(TransformationSourceError, match="^invalid transformation source$") as error:
            load_csv_source_snapshot(candidate, "items", budget=GenerationBudget(5), max_bytes=max_bytes)
        assert "fictional-a" not in str(error.value)


def test_source_loader_rejects_fifo_without_blocking(tmp_path):
    path = tmp_path / "source.pipe"
    os.mkfifo(path)
    with pytest.raises(TransformationSourceError):
        load_csv_source_snapshot(path, "items", budget=GenerationBudget(5), max_bytes=1024)
