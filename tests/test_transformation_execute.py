"""Fictional inputs only: closed executor, no public interface or file output."""

import csv
from decimal import Decimal
from datetime import date
import io
import os
import pty
import select
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from importlib import import_module

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.csv_profiler import profile_csv_bytes
from test_data_agent.io.transformation_source import prepare_csv_review_request, _profile_transformation_csv, TransformationSourceError


def request(target="second", complete=True, behavior=None,
            source_bytes=b"flag,code\ntrue,001\nfalse,002\n"):
    source = SnapshotPart("source", "items", source_bytes)
    profile = _profile_transformation_csv(source, null_token=None,
        budget=GenerationBudget(5), max_bytes=8192)
    def table(path):
        return {"kind": "csv", "path": path, "source_columns": ["old"],
                "replacement_columns": ["new"]}
    policy = yaml.safe_dump({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "file_text_mapping": table("all.csv"), "fields": [
            {"entity": "items", "field": "flag", "sensitivity": "non_sensitive",
             "behavior": behavior or {"action": "replace_text"}},
            {"entity": "items", "field": "code", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text", "mapping": table("code.csv")}},
        ]}).encode()
    global_pairs = b"old,new\ntrue,no\n001,1\n002,global\nsecond,cascade\n"
    if complete:
        global_pairs += b"false,yes\n"
    column_pairs = io.StringIO(newline="")
    csv.writer(column_pairs).writerows([("old", "new"), ("002", target)])
    return prepare_csv_review_request(policy, source, (
        SnapshotPart("mapping", "all.csv", global_pairs),
        SnapshotPart("mapping", "code.csv", column_pairs.getvalue().encode()),
    ), max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))


def execute(material, limit=8192):
    module = import_module("test_data_agent.io.transformation_execute")
    return module.replace_csv_snapshot(material, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=limit, budget=GenerationBudget(5)).csv_bytes


def test_closed_bundle_writer_preserves_existing_output_and_cleans_staging(tmp_path):
    from test_data_agent.io.transformation_publish import _publish_test_bundle
    destination = tmp_path / "output"
    destination.mkdir()
    (destination / "owned.txt").write_bytes(b"fictional-existing-artifact")
    with pytest.raises(ValueError):
        _publish_test_bundle(destination, "dataset.csv", b"label\ngamma\n",
                             b'{"origin":"transformed_mixed"}', GenerationBudget(5),
                             max_output_bytes=8192)
    assert list(tmp_path.iterdir()) == [destination]
    assert (destination / "owned.txt").read_bytes() == b"fictional-existing-artifact"
    with pytest.raises(ValueError):
        _publish_test_bundle(tmp_path / "new", "../escape", b"", b"", GenerationBudget(5),
                             max_output_bytes=8192)
    assert list(tmp_path.iterdir()) == [destination]


def test_closed_bundle_writer_byte_boundary_before_any_files(tmp_path):
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.io.transformation_publish import _publish_test_bundle
    destination = tmp_path / "output"
    payload, manifest = b"label\ngamma\n", b'{"origin":"transformed_mixed"}'
    size = len(payload) + len(manifest)
    with pytest.raises(TransformationLimitError) as caught:
        _publish_test_bundle(destination, "dataset.csv", payload, manifest, GenerationBudget(5),
                             max_output_bytes=size - 1)
    assert caught.value.amount == size and caught.value.limit == size - 1
    assert caught.value.origin == "bundle_run"
    assert list(tmp_path.iterdir()) == []
    _publish_test_bundle(destination, "dataset.csv", payload, manifest, GenerationBudget(5),
                         max_output_bytes=size)
    assert (destination / "dataset.csv").read_bytes() == payload
    assert (destination / "manifest.json").read_bytes() == manifest
    assert list(tmp_path.iterdir()) == [destination]


def test_publication_fsync_failure_after_rename_rolls_back_own_bundle(tmp_path, monkeypatch):
    from test_data_agent.io import path_policy
    from test_data_agent.io.transformation_publish import (
        TransformationPublicationError, _publish_reviewed_test_snapshot,
    )
    destination = tmp_path / "output"
    original_fsync = path_policy.os.fsync
    failures = []

    def fail_after_rename(fd):
        if destination.exists():
            failures.append(True)
            raise OSError("fictional-private-fsync-marker")
        return original_fsync(fd)

    monkeypatch.setattr(path_policy.os, "fsync", fail_after_rename)
    with pytest.raises(TransformationPublicationError) as caught:
        _publish_reviewed_test_snapshot(request(), destination, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert failures == [True]
    assert list(tmp_path.iterdir()) == []
    assert caught.value.__context__ is None
    assert "fictional-private-fsync-marker" not in str(caught.value)


def test_successful_publication_does_not_reopen_staging_for_cleanup(tmp_path, monkeypatch):
    from test_data_agent.io import transformation_publish as publisher

    def fail_cleanup(path):
        pytest.fail("cleanup called after successful publication")

    original_remove = publisher.remove_tree_if_identity
    def fail_staging_cleanup(path, identity):
        if path != tmp_path / "output":
            fail_cleanup(path)
        return original_remove(path, identity)
    monkeypatch.setattr(publisher, "remove_tree_if_identity", fail_staging_cleanup)
    destination = tmp_path / "output"
    summary = publisher._publish_reviewed_test_snapshot(request(), destination,
        max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192,
        budget=GenerationBudget(5))
    assert summary["origin"] == "transformed_mixed"
    assert (destination / "dataset.csv").read_bytes() == execute(request())


def test_failed_rollback_has_distinct_value_free_retained_output_error(tmp_path, monkeypatch):
    from test_data_agent.io import path_policy, transformation_publish as publisher
    destination = tmp_path / "output"
    original_fsync = path_policy.os.fsync

    def fail_after_rename(fd):
        if destination.exists():
            raise OSError("fictional-private-fsync-marker")
        return original_fsync(fd)

    def fail_rollback(path, identity):
        raise OSError("fictional-private-rollback-marker")

    monkeypatch.setattr(path_policy.os, "fsync", fail_after_rename)
    monkeypatch.setattr(publisher, "remove_tree_if_identity", fail_rollback)
    with pytest.raises(publisher.TransformationCleanupError) as caught:
        publisher._publish_reviewed_test_snapshot(request(), destination,
            max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192,
            budget=GenerationBudget(5))
    assert "output or staging may remain" in str(caught.value)
    assert "before retrying" in str(caught.value)
    assert "fictional-private" not in str(caught.value)
    assert caught.value.__context__ is None
    assert (destination / "dataset.csv").read_bytes() == execute(request())


@pytest.mark.parametrize("phase", ["initial_identity", "cleanup_lookup"])
def test_staging_lookup_failure_is_not_silently_discarded(tmp_path, monkeypatch, phase):
    from test_data_agent.io import transformation_publish as publisher
    original_remove = publisher.remove_tree_if_identity
    destination = tmp_path / "output"

    def fail_write(path, payload):
        raise OSError("fictional-private-write-marker")

    def fail_staging_lookup(path, identity):
        if path != destination:
            raise ValueError("fictional-private-lookup-marker")
        return original_remove(path, identity)

    monkeypatch.setattr(publisher, "atomic_write_bytes", fail_write)
    monkeypatch.setattr(publisher, "remove_tree_if_identity", fail_staging_lookup)
    if phase == "initial_identity":
        def fail_identity(path):
            raise ValueError("fictional-private-identity-marker")
        monkeypatch.setattr(publisher, "path_identity", fail_identity)
    with pytest.raises(publisher.TransformationCleanupError) as caught:
        publisher._publish_reviewed_test_snapshot(request(), destination,
            max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192,
            budget=GenerationBudget(5))
    assert "cleanup incomplete" in str(caught.value)
    assert "fictional-private" not in str(caught.value)
    assert caught.value.__context__ is None
    assert not destination.exists()
    assert len(list(tmp_path.iterdir())) == 1


@pytest.mark.parametrize("failure", [None, "changed_review", "output_budget"])
def test_fixed_review_to_closed_destination_publication(tmp_path, failure):
    import json
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.io.transformation_publish import (
        TransformationPublicationError, _publish_reviewed_test_snapshot,
    )
    material = request()
    destination = tmp_path / "output"
    if failure == "changed_review":
        material = replace(material, review=b"{}")
    kwargs = dict(max_total_bytes=8192, max_review_bytes=4096,
                  max_output_bytes=1 if failure == "output_budget" else 8192,
                  budget=GenerationBudget(5))
    if failure:
        with pytest.raises(TransformationLimitError if failure == "output_budget"
                           else TransformationPublicationError):
            _publish_reviewed_test_snapshot(material, destination, **kwargs)
        assert list(tmp_path.iterdir()) == []
        return
    _publish_reviewed_test_snapshot(material, destination, **kwargs)
    assert list(csv.reader(io.StringIO((destination / "dataset.csv").read_text()))) == [
        ["flag", "code"], ["no", "1"], ["yes", "second"]]
    manifest = json.loads((destination / "manifest.json").read_bytes())
    assert manifest["origin"] == "transformed_mixed"
    assert manifest["provenance"]["replacement_percent"] == "100.00"
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize("failure", [None, "stale_digest", "session_ceiling"])
def test_saved_policy_to_closed_command_publication(tmp_path, monkeypatch, failure):
    from test_data_agent.io.transformation_publish import (
        TransformationLimitError, TransformationPublicationError, _execute_reviewed_test_from_paths,
    )
    material = request()
    for part in material.parts:
        if part.kind in {"policy", "mapping", "source"}:
            (tmp_path / ("items.csv" if part.kind == "source" else part.name)).write_bytes(part.payload)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    destination = tmp_path / "output"
    if failure == "session_ceiling":
        monkeypatch.setenv("TEST_DATA_AGENT_TRANSFORM_MAX_OUTPUT_BYTES", "4096")
    kwargs = dict(expected_snapshot_sha256="0" * 64 if failure == "stale_digest"
                  else material.snapshot_sha256, max_total_bytes=8192, max_review_bytes=4096,
                  max_output_bytes=8192, budget=GenerationBudget(5))
    if failure:
        with pytest.raises(TransformationLimitError if failure == "session_ceiling"
                           else TransformationPublicationError) as caught:
            _execute_reviewed_test_from_paths(tmp_path / "items.csv", "items",
                tmp_path / "behavior.yaml", destination, **kwargs)
        assert not destination.exists()
        if failure == "session_ceiling":
            assert caught.value.code == "requested_above_limit"
            assert caught.value.origin == "session" and caught.value.limit == 4096
    else:
        summary = _execute_reviewed_test_from_paths(tmp_path / "items.csv", "items",
            tmp_path / "behavior.yaml", destination, **kwargs)
        assert summary["snapshot_sha256"] == material.snapshot_sha256
        assert (destination / "dataset.csv").read_bytes() == execute(material)
        assert summary["provenance"]["replacement_percent"] == "100.00"
    assert {name: (tmp_path / name).read_bytes() for name in before} == before


@pytest.mark.parametrize("invalid_type", [False, True])
def test_private_csv_to_parquet_publication(invalid_type):
    import json
    pq = pytest.importorskip("pyarrow.parquet")
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["output"] = {"format": "parquet", "fields": [
        {"name": "flag", "type": "string"},
        {"name": "code", "type": "integer" if invalid_type else "string"}]}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"),
        tuple(p for p in original.parts if p.kind == "mapping"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert material.snapshot_sha256 != original.snapshot_sha256
    publisher = import_module("test_data_agent.io.transformation_publish")
    kwargs = dict(max_total_bytes=8192, max_review_bytes=4096,
                  max_output_bytes=8192, budget=GenerationBudget(5))
    if invalid_type:
        with pytest.raises(publisher.TransformationPublicationError) as caught:
            with publisher.temporary_csv_publication(material, **kwargs):
                pytest.fail("invalid Parquet output published")
        assert caught.value.__context__ is None
        return
    with publisher.temporary_csv_publication(material, **kwargs) as output:
        assert pq.read_table(output / "dataset.parquet").to_pylist() == [
            {"flag": "no", "code": "1"}, {"flag": "yes", "code": "second"}]
        manifest = json.loads((output / "manifest.json").read_bytes())
        assert manifest["output"] == json.loads(material.review)["output"]
        assert manifest["provenance"]["replacement_percent"] == "100.00"
        assert not (output / "dataset.csv").exists()
    assert not output.parent.exists()


@pytest.mark.parametrize("invalid_type", [False, True])
def test_private_csv_to_sql_publication_uses_bound_output_schema(invalid_type):
    import json
    original = request(target="fictional'quoted")
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["output"] = {"format": "postgresql_sql", "table": "items",
        "fields": [{"name": name, "type": "string"} for name in ("flag", "code")]}
    if invalid_type:
        policy["output"]["fields"][1]["type"] = "integer"
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"),
        tuple(p for p in original.parts if p.kind == "mapping"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert material.snapshot_sha256 != original.snapshot_sha256
    publisher = import_module("test_data_agent.io.transformation_publish")
    if invalid_type:
        with pytest.raises(publisher.TransformationPublicationError) as caught:
            with publisher.temporary_csv_publication(material, max_total_bytes=8192,
                    max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)):
                pytest.fail("invalid SQL output was published")
        assert caught.value.__context__ is None
        assert "fictional" not in str(caught.value)
        return
    output_review = json.loads(material.review)["output"]
    assert output_review == {"format": "postgresql_sql", "fields": [
        {"position": index, "type": "string", "nullable": False} for index in (1, 2)]}
    assert "fictional'quoted" not in material.review.decode()
    publisher = import_module("test_data_agent.io.transformation_publish")
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        sql = (output / "dataset.sql").read_text()
        assert "VALUES ('yes', 'fictional''quoted');" in sql
        assert sql.endswith("COMMIT;\n")
        assert not (output / "dataset.csv").exists()
        assert json.loads((output / "manifest.json").read_bytes())["output"] == output_review
        provenance = json.loads((output / "manifest.json").read_bytes())["provenance"]
        assert provenance["replacement_percent"] == "100.00"
        assert provenance["output_cells"] == 4
    assert not output.parent.exists()


@pytest.mark.parametrize("invalid_date", [False, True])
def test_csv_to_sql_date_publication(invalid_date):
    import json
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["output"] = {"format": "postgresql_sql", "table": "items", "fields": [
        {"name": "flag", "type": "string"},
        {"name": "code", "type": "date", "temporal_type": {
            "type": "date", "format": "%d/%m/%Y", "output_format": "%Y-%m-%d"}}]}
    parts = tuple(replace(p, payload=b"old,new\n001,31/08/2026\n002," +
        (b"31/02/2026\n" if invalid_date else b"01/09/2026\n")) if p.name == "code.csv" else p
        for p in original.parts if p.kind == "mapping")
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"), parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert json.loads(material.review)["output"]["fields"][1]["temporal"] == {
        "explicit_format": True, "source_timezone_configured": False, "target_timezone_configured": False}
    assert b"%d/%m/%Y" not in material.review
    publisher = import_module("test_data_agent.io.transformation_publish")
    kwargs = dict(max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    if invalid_date:
        with pytest.raises(publisher.TransformationPublicationError):
            with publisher.temporary_csv_publication(material, **kwargs):
                pytest.fail("invalid date was published")
    else:
        with publisher.temporary_csv_publication(material, **kwargs) as output:
            sql = (output / "dataset.sql").read_text()
            assert "DATE '2026-08-31'" in sql and "DATE '2026-09-01'" in sql
        assert not output.parent.exists()


def test_closed_csv_exact_text_override_no_cascade():
    assert list(csv.reader(io.StringIO(execute(request()).decode()))) == [
        ["flag", "code"], ["no", "1"], ["yes", "second"]]


@pytest.mark.parametrize("output_format", ["csv", "postgresql_sql", "parquet"])
@pytest.mark.parametrize("native_null", [False, True])
def test_private_parquet_string_input_all_outputs(output_format, native_null):
    import json
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_source import _profile_transformation_source
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    original = request()
    buffer = io.BytesIO()
    pq.write_table(pa.table({"flag": ["true", "false"],
        "code": [None, ""] if native_null else ["001", "002"]}), buffer)
    source = SnapshotPart("source", "items", buffer.getvalue())
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["input_format"] = "parquet"
    if native_null:
        policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": {
            "kind": "inline", "entries": [
                {"original": [None], "replacement": [""]},
                {"original": [""], "replacement": [None]}]}}
        if output_format == "csv":
            policy["csv_nulls"] = {"output_token": "\\N"}
    if output_format != "csv":
        policy["output"] = {"format": output_format, "fields": [
            {"name": name, "type": "string", "nullable": native_null and name == "code"}
            for name in ("flag", "code")]}
        if output_format == "postgresql_sql":
            policy["output"]["table"] = "items"
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(), max_bytes=8192, budget=GenerationBudget(5))
    profile = _profile_transformation_source(source, parsed, budget=GenerationBudget(5), max_bytes=8192)
    assert all(field.data_type.value == "string" for field in profile.entities[0].fields)
    policy["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        tuple(p for p in original.parts if p.kind == "mapping" and (not native_null or p.name == "all.csv")),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert json.loads(material.review)["input_format"] == "parquet"
    assert next(p.payload for p in material.parts if p.kind == "source") == buffer.getvalue()
    publisher = import_module("test_data_agent.io.transformation_publish")
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        if output_format == "csv":
            assert (output / "dataset.csv").read_bytes() == (
                b"flag,code\nno,\nyes,\\N\n" if native_null else b"flag,code\nno,1\nyes,second\n")
        elif output_format == "parquet":
            assert pq.read_table(output / "dataset.parquet").to_pylist() == [
                {"flag": "no", "code": "" if native_null else "1"},
                {"flag": "yes", "code": None if native_null else "second"}]
        else:
            assert ("VALUES ('yes', NULL);" if native_null else "VALUES ('yes', 'second');") in (
                output / "dataset.sql").read_text()
    assert not output.parent.exists()
    tampered = replace(material, parts=tuple(replace(p, payload=p.payload + b"drift")
        if p.kind == "source" else p for p in material.parts))
    with pytest.raises(publisher.TransformationPublicationError):
        with publisher.temporary_csv_publication(tampered, max_total_bytes=8192,
                max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)):
            pytest.fail("changed source published")


@pytest.mark.parametrize("values", [[1, 2], [True, False], [["nested"], ["value"]]])
def test_parquet_input_unsupported_native_values_fail_closed(values):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["input_format"] = "parquet"
    buffer = io.BytesIO()
    pq.write_table(pa.table({"flag": ["true", "false"], "code": values}), buffer)
    with pytest.raises(TransformationSourceError, match="invalid transformation source review"):
        prepare_csv_review_request(yaml.safe_dump(policy).encode(),
            SnapshotPart("source", "items", buffer.getvalue()),
            tuple(p for p in original.parts if p.kind == "mapping"),
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))


@pytest.mark.parametrize("kind,values,replacements", [
    ("integer", [1, 2], [7, 8]), ("float", [1.25, 2.5], [7.5, 8.25]),
    ("boolean", [True, False], [False, True]),
    ("date", [date(2026, 1, 2), date(2026, 2, 3)], [date(2027, 3, 4), date(2027, 4, 5)]),
    pytest.param("date", [None, date(2026, 2, 3)], [date(2027, 3, 4), None], id="nullable-date"),
    ("decimal", [Decimal("1.25"), Decimal("2.50")], [Decimal("7.50"), Decimal("8.25")])])
@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
@pytest.mark.parametrize("input_format", ["parquet", "postgres_query", "trino_query"])
def test_parquet_native_numeric_substitution(kind, values, replacements, output_format, input_format):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_source import _profile_transformation_source
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["input_format"] = input_format
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": {
        "kind": "inline", "entries": [{"original": [str(a) if a is not None and kind in {"decimal", "date"} else a],
                                        "replacement": [str(b) if b is not None and kind in {"decimal", "date"} else b]}
                                      for a, b in zip(values, replacements)]}}
    if None in replacements and output_format == "csv":
        policy["csv_nulls"] = {"output_token": "\\N"}
    if kind == "decimal":
        policy["fields"][1]["decimal_type"] = {"precision": 5, "scale": 2}
    if output_format != "csv":
        policy["output"] = {"format": output_format, "fields": [
            {"name": "flag", "type": "string"}, {"name": "code", "type": kind, "nullable": None in replacements}]}
        if output_format == "postgresql_sql":
            policy["output"]["table"] = "items"
        if kind == "decimal":
            policy["output"]["fields"][1]["decimal_type"] = {"precision": 5, "scale": 2}
        if kind == "date":
            policy["output"]["fields"][1]["temporal_type"] = {
                "type": "date", "format": "%Y-%m-%d", "output_format": "%Y-%m-%d"}
    buffer = io.BytesIO()
    pq.write_table(pa.table({"flag": ["true", "false"], "code":
        pa.array(values, type=pa.decimal128(5, 2)) if kind == "decimal" else values}), buffer)
    source = SnapshotPart("source", "items", buffer.getvalue())
    if input_format != "parquet":
        from test_data_agent.io.transformation_query_snapshot import _capture_query_result
        source = _capture_query_result(buffer.getvalue(), adapter=input_format,
            query_sha256="a" * 64, entity="items")
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(), max_bytes=8192, budget=GenerationBudget(5))
    profile = _profile_transformation_source(source, parsed, budget=GenerationBudget(5), max_bytes=8192)
    assert profile.entities[0].fields[1].data_type.value == kind
    assert profile.source_type == input_format
    policy["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        tuple(p for p in original.parts if p.kind == "mapping" and p.name == "all.csv"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    publisher = import_module("test_data_agent.io.transformation_publish")
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        if output_format == "parquet":
            assert pq.read_table(output / "dataset.parquet").column("code").to_pylist() == replacements
        elif output_format == "csv":
            assert [row["code"] for row in csv.DictReader(io.StringIO(
                (output / "dataset.csv").read_text()))] == ["\\N" if value is None else str(value) for value in replacements]
        else:
            literal = str(replacements[1]).upper() if kind == "boolean" else str(replacements[1])
            if kind == "date":
                literal = f"DATE '{literal}'"
            if replacements[1] is None:
                literal = "NULL"
            assert f"VALUES ('yes', {literal});" in (output / "dataset.sql").read_text()
    assert not output.parent.exists()
    if input_format != "parquet" and kind == "integer" and output_format == "csv":
        changed_source = _capture_query_result(buffer.getvalue(), adapter=input_format,
            query_sha256="b" * 64, entity="items")
        changed = prepare_csv_review_request(yaml.safe_dump(policy).encode(), changed_source,
            tuple(p for p in original.parts if p.kind == "mapping" and p.name == "all.csv"),
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
        assert changed.snapshot_sha256 != material.snapshot_sha256
        tampered = replace(material, parts=tuple(changed_source if p.kind == "source" else p
            for p in material.parts))
        with pytest.raises(publisher.TransformationPublicationError):
            with publisher.temporary_csv_publication(tampered, max_total_bytes=8192,
                    max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)):
                pytest.fail("changed query identity published")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_native_parquet_nonfinite_rejects_before_profiling(value):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_input import source_reader
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["input_format"] = "parquet"
    policy["fields"][1]["behavior"] = {"action": "drop"}
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(),
        max_bytes=8192, budget=GenerationBudget(5))
    buffer = io.BytesIO()
    pq.write_table(pa.table({"flag": ["fictional"], "code": [value]}), buffer)
    with pytest.raises(ValueError, match="unsupported Parquet source cell"):
        source_reader(SnapshotPart("source", "items", buffer.getvalue()), parsed,
            budget=GenerationBudget(5))


@pytest.mark.parametrize("value", [1, 1.25, date(2026, 2, 3)])
def test_native_numeric_identity_rejects_before_execution(value):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_source import _profile_transformation_source
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    buffer = io.BytesIO()
    pq.write_table(pa.table({"amount": [value]}), buffer)
    source = SnapshotPart("source", "items", buffer.getvalue())
    policy = {"schema_version": "0.1", "schema_fingerprint": "0" * 64,
        "input_format": "parquet", "seed": 7, "fields": [
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "behavior": {"action": "substitute", "mapping": {"kind": "inline",
                 "entries": [{"original": [value.isoformat() if type(value) is date else value],
                              "replacement": [value.isoformat() if type(value) is date else value]}]}}}]}
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(), max_bytes=8192, budget=GenerationBudget(5))
    profile = _profile_transformation_source(source, parsed, budget=GenerationBudget(5), max_bytes=8192)
    policy["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    with pytest.raises(TransformationSourceError):
        prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, (),
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))


def test_native_empty_to_null_is_not_whole_row_preservation():
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_source import _profile_transformation_source
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    buffer = io.BytesIO()
    pq.write_table(pa.table({"code": ["", None]}), buffer)
    source = SnapshotPart("source", "items", buffer.getvalue())
    policy = {"schema_version": "0.1", "schema_fingerprint": "0" * 64,
        "input_format": "parquet", "seed": 7, "fields": [
            {"entity": "items", "field": "code", "sensitivity": "non_sensitive",
             "behavior": {"action": "substitute", "mapping": {"kind": "inline",
                 "entries": [{"original": [""], "replacement": [None]},
                             {"original": [None], "replacement": ["filled"]}]}}}],
        "output": {"format": "parquet", "fields": [
            {"name": "code", "type": "string", "nullable": True}]}}
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(), max_bytes=8192, budget=GenerationBudget(5))
    profile = _profile_transformation_source(source, parsed, budget=GenerationBudget(5), max_bytes=8192)
    policy["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, (),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    publisher = import_module("test_data_agent.io.transformation_publish")
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        assert pq.read_table(output / "dataset.parquet").column("code").to_pylist() == [None, "filled"]


@pytest.mark.parametrize("replacement,expected", [
    ("2026-02-03", True), ("20260203", True), ("2027-02-03", False),
    ("not-a-date", False), (None, False)])
def test_native_date_reuse_guard(replacement, expected):
    from test_data_agent.io.transformation_input import same_native_value
    assert same_native_value(date(2026, 2, 3), replacement) is expected


@pytest.mark.parametrize("target", ["done", "1.250"])
@pytest.mark.parametrize("sensitivity", ["non_sensitive", "sensitive"])
def test_explicit_native_text_format_and_row_reuse(target, sensitivity):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_source import _profile_transformation_source, trace_csv_review_request
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    buffer = io.BytesIO()
    pq.write_table(pa.table({"amount": [1.25]}), buffer)
    source = SnapshotPart("source", "items", buffer.getvalue())
    policy = {"schema_version": "0.1", "schema_fingerprint": "0" * 64,
        "input_format": "parquet", "seed": 7, "fields": [
            {"entity": "items", "field": "amount", "sensitivity": sensitivity, "match_format": ".2f",
             "behavior": {"action": "replace_text", "mapping": {"kind": "csv", "path": "map.csv",
                 "source_columns": ["old"], "replacement_columns": ["new"]}}}]}
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(), max_bytes=8192, budget=GenerationBudget(5))
    profile = _profile_transformation_source(source, parsed, budget=GenerationBudget(5), max_bytes=8192)
    policy["schema_fingerprint"] = transformation_schema_fingerprint(profile)
    if sensitivity == "sensitive" and target == "1.250":
        with pytest.raises(TransformationSourceError):
            prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
                (SnapshotPart("mapping", "map.csv", b"old,new\n1.25,1.250\n"),),
                max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
        return
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        (SnapshotPart("mapping", "map.csv", f"old,new\n1.25,{target}\n".encode()),),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert b'"explicit_match_format": true' in material.review
    assert trace_csv_review_request(material, max_events=5, max_cells=5,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5)).matched_cells == 1
    if target == "done":
        assert execute(material) == b"amount\ndone\n"
    else:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)


@pytest.mark.parametrize("pattern", ["100d", ".19f", "n", "{value}", "1000000000d", ""])
def test_native_match_format_is_bounded(pattern):
    from test_data_agent.core.transformation_policy import parse_behavior_policy, BehaviorPolicyError
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["fields"][1]["match_format"] = pattern
    with pytest.raises(BehaviorPolicyError):
        parse_behavior_policy(policy)


def test_input_format_change_invalidates_review_before_publication():
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["input_format"] = "parquet"
    tampered = replace(original, parts=tuple(replace(p, payload=yaml.safe_dump(policy).encode())
        if p.kind == "policy" else p for p in original.parts))
    publisher = import_module("test_data_agent.io.transformation_publish")
    with pytest.raises(publisher.TransformationPublicationError) as caught:
        with publisher.temporary_csv_publication(tampered, max_total_bytes=8192,
                max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)):
            pytest.fail("changed input format published")
    assert caught.value.__context__ is None


@pytest.mark.parametrize("precision,scale,declared,valid", [
    (38, 37, (38, 37), True), (6, 2, (5, 2), False),
    (6, 2, (6, 3), False), (6, 2, None, False), (39, 2, (38, 2), False)])
def test_native_decimal_shape_boundary(precision, scale, declared, valid):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    from test_data_agent.io.transformation_input import source_reader
    from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
    original = request()
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["input_format"] = "parquet"
    policy["fields"][1]["behavior"] = {"action": "drop"}
    if declared:
        policy["fields"][1]["decimal_type"] = {"precision": declared[0], "scale": declared[1]}
    parsed = load_behavior_policy_yaml(yaml.safe_dump(policy).encode(),
        max_bytes=8192, budget=GenerationBudget(5))
    value = Decimal("0." + "1234567890123456789012345678901234567") if scale == 37 else Decimal("1.25")
    arrow_type = pa.decimal128(precision, scale) if precision <= 38 else pa.decimal256(precision, scale)
    buffer = io.BytesIO()
    pq.write_table(pa.table({"flag": ["fictional"], "code": pa.array([value], type=arrow_type)}), buffer)
    source = SnapshotPart("source", "items", buffer.getvalue())
    if valid:
        reader = source_reader(source, parsed, budget=GenerationBudget(5))
        assert reader.decimal_shapes["code"] == (38, 37)
        observed = next(iter(reader))["code"]
        assert type(observed) is Decimal and observed.as_tuple() == value.as_tuple()
    else:
        with pytest.raises(ValueError):
            source_reader(source, parsed, budget=GenerationBudget(5))


@pytest.mark.parametrize("action", ["preserve", "replace_text", "substitute"])
def test_declared_decimal_preservation_rejected_before_approval(action):
    from test_data_agent.core.transformation_policy import (
        BehaviorPolicyError, parse_behavior_policy, validate_policy_field_coverage,
    )
    material = request(source_bytes=b"flag,code\ntrue,1.25\nfalse,2.50\n")
    policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
    preserve = {"action": "preserve", "authorization_ref": "fictional", "comment": "Fictional decimal"}
    behavior = preserve if action == "preserve" else {"action": action, "unmatched": preserve}
    if action == "substitute":
        behavior["mapping"] = {"kind": "inline", "entries": [
            {"original": ["1.25"], "replacement": ["3.75"]}]}
    policy["fields"][1].update(decimal_type={"precision": 8, "scale": 2}, behavior=behavior)
    source = next(p for p in material.parts if p.kind == "source")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5)))
    with pytest.raises(BehaviorPolicyError):
        validate_policy_field_coverage(parse_behavior_policy(policy), profile)


def test_source_evidence_error_has_no_private_context():
    from test_data_agent.io.transformation_source import TransformationSourceError, revalidate_csv_evidence
    with pytest.raises(TransformationSourceError) as caught:
        revalidate_csv_evidence(SnapshotPart("source", "items", b"flag\nfictional\n"),
            b'{"entities":"fictional-private-marker"}', budget=GenerationBudget(5))
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None


def test_private_temporary_publication_contains_csv_and_manifest():
    import json
    module = import_module("test_data_agent.io.transformation_publish")
    with module.temporary_csv_publication(request(), max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        assert (output / "dataset.csv").read_bytes() == execute(request())
        manifest_bytes = (output / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        assert manifest["origin"] == "transformed_mixed"
        assert manifest["privacy_notice"] == "Mixed-origin output may retain source information; not anonymized."
        assert manifest["provenance"]["output_cells"] == 4
        assert b"second" not in manifest_bytes
        assert set(path.name for path in output.iterdir()) == {"dataset.csv", "manifest.json"}
        assert output.stat().st_mode & 0o077 == 0
        assert all(path.stat().st_mode & 0o077 == 0 for path in output.iterdir())
    assert not output.parent.exists()


@pytest.mark.parametrize("failure", ["digest", "digest_shape", "input_budget", "output_budget", "deadline", "receipt"])
def test_private_command_failures_preserve_input_files(tmp_path, failure):
    material = request(behavior={"action": "preserve", "authorization_ref": "fictional-ref",
        "comment": "Fictional local approval required"} if failure == "receipt" else None)
    for part in material.parts:
        if part.kind in {"policy", "mapping", "source"}:
            (tmp_path / ("items.csv" if part.kind == "source" else part.name)).write_bytes(part.payload)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    ticks = iter([0.0, 2.0])
    budget = GenerationBudget(1, clock=lambda: next(ticks)) if failure == "deadline" else GenerationBudget(5)
    publisher = import_module("test_data_agent.io.transformation_publish")
    with pytest.raises(publisher.TransformationLimitError if failure == "output_budget"
                       else publisher.TransformationPublicationError) as caught:
        publisher._run_temporary_transform(tmp_path / "items.csv", "items", tmp_path / "behavior.yaml",
            expected_snapshot_sha256=("0" * 64 if failure == "digest" else "bad" if failure == "digest_shape"
                                      else material.snapshot_sha256),
            max_total_bytes=1 if failure == "input_budget" else 8192,
            max_review_bytes=4096, max_output_bytes=1 if failure == "output_budget" else 8192,
            budget=budget)
    if failure == "output_budget":
        assert caught.value.code == "limit_exceeded" and caught.value.limit == 1
    else:
        assert str(caught.value) == "invalid temporary transformation command"
    assert caught.value.__context__ is None
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("output_limit", [8192, 1])
def test_private_command_subprocess_parser_and_cleanup(tmp_path, output_limit):
    import json
    import subprocess
    import sys
    from pathlib import Path
    material = request()
    for part in material.parts:
        if part.kind in {"policy", "mapping", "source"}:
            (tmp_path / ("items.csv" if part.kind == "source" else part.name)).write_bytes(part.payload)
    temporary = tmp_path / "temporary"
    temporary.mkdir()
    script = '''
import argparse
import json
from pathlib import Path
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.io.transformation_publish import _run_temporary_transform, TransformationPublicationError
from test_data_agent.core.transformation_limits import TransformationLimitError
parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("policy", type=Path)
parser.add_argument("digest")
parser.add_argument("limit", type=int)
args = parser.parse_args()
try:
    result = _run_temporary_transform(args.source, "items", args.policy,
        expected_snapshot_sha256=args.digest, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=args.limit, budget=GenerationBudget(5))
except (TransformationPublicationError, TransformationLimitError) as error:
    assert error.__context__ is None
    print(json.dumps({"status": "rejected"}))
else:
    print(json.dumps(result))
'''
    completed = subprocess.run([sys.executable, "-c", script, str(tmp_path / "items.csv"),
        str(tmp_path / "behavior.yaml"), material.snapshot_sha256, str(output_limit)],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
             "TMPDIR": str(temporary)}, capture_output=True, text=True, timeout=30, check=True)
    if output_limit == 1:
        assert json.loads(completed.stdout) == {"status": "rejected"}
    else:
        assert json.loads(completed.stdout)["provenance"]["replacement_percent"] == "100.00"
    assert "second" not in completed.stdout + completed.stderr
    assert list(temporary.iterdir()) == []


def test_saved_csv_policy_cli_review_to_private_publication(tmp_path):
    """Real CLI review and file adapters share bytes; no public execution enabled."""
    import json
    import subprocess
    import sys
    from pathlib import Path
    from test_data_agent.io.transformation_source import prepare_csv_review_from_paths

    material = request()
    for part in material.parts:
        if part.kind in {"policy", "mapping", "source"}:
            name = "items.csv" if part.kind == "source" else part.name
            (tmp_path / name).write_bytes(part.payload)
    cli = subprocess.run(
        [sys.executable, "-m", "test_data_agent.cli", "transform-review",
         str(tmp_path / "items.csv"), str(tmp_path / "behavior.yaml"), "--trace"],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True, text=True, timeout=30, check=True,
    )
    review = json.loads(cli.stdout)
    assert review["status"] == "review_only"
    assert review["snapshot_sha256"] == material.snapshot_sha256
    assert "second" not in cli.stdout
    assert not (tmp_path / "dataset.csv").exists()
    captured = prepare_csv_review_from_paths(
        tmp_path / "items.csv", "items", tmp_path, "behavior.yaml",
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert captured.snapshot_sha256 == review["snapshot_sha256"]
    publisher = import_module("test_data_agent.io.transformation_publish")
    summary = publisher._run_temporary_transform(
        tmp_path / "items.csv", "items", tmp_path / "behavior.yaml",
        expected_snapshot_sha256=review["snapshot_sha256"], max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert summary["status"] == "temporary_test_completed"
    assert summary["provenance"]["replacement_cells"] == 4
    assert "second" not in json.dumps(summary)
    assert not (tmp_path / "dataset.csv").exists()
    # Execution consumes the reviewed snapshot, not reopened mutable paths.
    (tmp_path / "items.csv").write_bytes(b"flag,code\nchanged,999\n")
    (tmp_path / "code.csv").write_bytes(b"old,new\n002,changed\n")
    with pytest.raises(publisher.TransformationPublicationError) as drift:
        publisher._run_temporary_transform(
            tmp_path / "items.csv", "items", tmp_path / "behavior.yaml",
            expected_snapshot_sha256=review["snapshot_sha256"], max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert str(drift.value) == "invalid temporary transformation command"
    assert drift.value.__context__ is None
    module = import_module("test_data_agent.io.transformation_publish")
    with module.temporary_csv_publication(captured, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        assert (output / "dataset.csv").read_bytes() == b"flag,code\nno,1\nyes,second\n"
        manifest = json.loads((output / "manifest.json").read_bytes())
        assert manifest["origin"] == "transformed_mixed"
        assert manifest["provenance"]["output_cells"] == 4
    assert not output.parent.exists()


@pytest.mark.parametrize("complete,limit", [(False, 8192), (True, 1), (True, 64)])
def test_private_temporary_publication_rejects_before_yield(complete, limit):
    module = import_module("test_data_agent.io.transformation_publish")
    with pytest.raises(module.TransformationLimitError if complete
                       else module.TransformationPublicationError) as error:
        with module.temporary_csv_publication(request(complete=complete), max_total_bytes=8192,
                max_review_bytes=4096, max_output_bytes=limit, budget=GenerationBudget(5)):
            pytest.fail("invalid output published")
    assert error.value.__context__ is None
    if complete and limit == 64:
        assert error.value.origin == "bundle_run"
        assert error.value.amount > error.value.limit == 64
        assert error.value.run_setting == "temporary_csv_publication(max_output_bytes=...)"


@pytest.mark.parametrize("format", ["postgresql_sql", "parquet"])
def test_final_format_budget_diagnostic_and_exact_boundary(format):
    from test_data_agent.core.transformation_policy import SqlOutput, ParquetOutput
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.io.transformation_sql import render_transformation_sql
    from test_data_agent.io.transformation_parquet import render_transformation_parquet
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.replace_csv_snapshot(request(), max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    fields = [{"name": name, "type": "string"} for name in result.columns]
    if format == "parquet":
        pytest.importorskip("pyarrow")
        output = ParquetOutput.model_validate({"format": format, "fields": fields})
        render = render_transformation_parquet
    else:
        output = SqlOutput.model_validate({"format": format, "table": "fictional", "fields": fields})
        render = render_transformation_sql
    expected = render(result, output, max_bytes=8192, budget=GenerationBudget(5))
    assert render(result, output, max_bytes=len(expected), budget=GenerationBudget(5)) == expected
    with pytest.raises(TransformationLimitError) as caught:
        render(result, output, max_bytes=len(expected) - 1, budget=GenerationBudget(5))
    assert caught.value.amount > caught.value.limit == len(expected) - 1
    assert caught.value.unit == "bytes" and caught.value.code == "limit_exceeded"
    assert caught.value.profile_key == "resource_limits.max_output_bytes"
    assert "max_bytes=" in caught.value.run_setting


def test_temporary_publication_cleans_up_after_consumer_failure():
    module = import_module("test_data_agent.io.transformation_publish")
    with pytest.raises(RuntimeError, match="fictional consumer failure"):
        with module.temporary_csv_publication(request(), max_total_bytes=8192,
                max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
            raise RuntimeError("fictional consumer failure")
    assert not output.parent.exists()


@pytest.mark.parametrize("publication_check", [1, 2])
def test_temporary_publication_checks_deadline_before_and_after_staging(publication_check):
    module = import_module("test_data_agent.io.transformation_publish")
    now = [0.0]

    class PublicationBudget(GenerationBudget):
        calls = 0

        def check(self, stage):
            if stage == "temporary transformation publication":
                self.calls += 1
                if self.calls == publication_check:
                    now[0] = 10.0
            super().check(stage)

    budget = PublicationBudget(5, clock=lambda: now[0])
    with pytest.raises(module.TransformationPublicationError) as error:
        with module.temporary_csv_publication(request(), max_total_bytes=8192,
                max_review_bytes=4096, max_output_bytes=8192, budget=budget):
            pytest.fail("expired publication yielded artifacts")
    assert budget.calls == publication_check
    assert error.value.__context__ is None


def test_engine_retention_counts_numeric_formatting_as_unchanged():
    material = request(source_bytes=b"flag,code\ntrue,1.0\nfalse,2.0\n")
    policy = next(part.payload for part in material.parts if part.kind == "policy")
    source = next(part for part in material.parts if part.kind == "source")
    parts = tuple(replace(part, payload=b"old,new\n1.0,1.00\n2.0,2.00\n")
                  if part.name == "code.csv" else part for part in material.parts if part.kind == "mapping")
    material = prepare_csv_review_request(policy, source, parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.replace_csv_snapshot(material, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert result.retention.unchanged_cells == 2
    assert result.retention.unchanged_percent == "50.00"


@pytest.mark.parametrize("target", ["\\N", ""])
def test_output_null_marker_does_not_reinterpret_literal_replacement(target):
    original = request(target=target)
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["csv_nulls"] = {"output_token": "\\N"}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"),
        tuple(p for p in original.parts if p.kind == "mapping"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert material.snapshot_sha256 != original.snapshot_sha256
    if target:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)
    else:
        assert execute(material).endswith(b"yes,\n")


@pytest.mark.parametrize("csv_mapping", [False, True])
@pytest.mark.parametrize("missing_token", [None, "input_token", "output_token"])
def test_nullable_substitution_keeps_empty_distinct_from_null(csv_mapping, missing_token):
    original = request(source_bytes=b"flag,code\ntrue,\\N\nfalse,\n")
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["csv_nulls"] = {"input_token": "\\N", "output_token": "NULL"}
    if missing_token:
        policy["csv_nulls"].pop(missing_token)
    mapping = ({"kind": "csv", "path": "nullable.csv", "source_columns": ["old"],
                "replacement_columns": ["new"], "null_token": "<null>"} if csv_mapping else
               {"kind": "inline", "entries": [
                   {"original": [None], "replacement": ["filled"]},
                   {"original": [""], "replacement": [None]}]})
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    parts = tuple(p for p in original.parts if p.kind == "mapping" and p.name == "all.csv")
    if csv_mapping:
        parts += (SnapshotPart("mapping", "nullable.csv", b"old,new\n<null>,filled\n,<null>\n"),)
    source = next(p for p in original.parts if p.kind == "source")
    policy["schema_fingerprint"] = transformation_schema_fingerprint(_profile_transformation_csv(
        source, null_token=policy["csv_nulls"].get("input_token"), budget=GenerationBudget(5), max_bytes=8192))
    if missing_token == "input_token":
        with pytest.raises(TransformationSourceError):
            prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
                max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
        return
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"), parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if missing_token:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)
    else:
        assert execute(material) == b"flag,code\nno,filled\nyes,NULL\n"
        module = import_module("test_data_agent.io.transformation_execute")
        result = module.replace_csv_snapshot(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
        assert result.columns == ("flag", "code")
        assert result.rows == (("no", "filled"), ("yes", None))
        assert "filled" not in repr(result)


@pytest.mark.parametrize("output_format", ["parquet", "postgresql_sql"])
def test_native_output_null_needs_no_csv_output_marker(output_format):
    original = request(source_bytes=b"flag,code\ntrue,\\N\nfalse,\n")
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["csv_nulls"] = {"input_token": "\\N"}
    policy["output"] = {"format": output_format, "fields": [
        {"name": "flag", "type": "string"},
        {"name": "code", "type": "string", "nullable": True}]}
    if output_format == "postgresql_sql":
        policy["output"]["table"] = "items"
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": {
        "kind": "inline", "entries": [
            {"original": [None], "replacement": [""]},
            {"original": [""], "replacement": [None]}]}}
    source = next(p for p in original.parts if p.kind == "source")
    policy["schema_fingerprint"] = transformation_schema_fingerprint(_profile_transformation_csv(
        source, null_token="\\N", budget=GenerationBudget(5), max_bytes=8192))
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        tuple(p for p in original.parts if p.kind == "mapping" and p.name == "all.csv"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    publisher = import_module("test_data_agent.io.transformation_publish")
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)) as output:
        if output_format == "parquet":
            pq = pytest.importorskip("pyarrow.parquet")
            assert pq.read_table(output / "dataset.parquet").to_pylist() == [
                {"flag": "no", "code": ""}, {"flag": "yes", "code": None}]
        else:
            sql = (output / "dataset.sql").read_text()
            assert "VALUES ('no', '');" in sql
            assert "VALUES ('yes', NULL);" in sql
    assert not output.parent.exists()


@pytest.mark.parametrize("decimal", [False, True])
@pytest.mark.parametrize("action", ["substitute", "synthesize"])
def test_numeric_null_source_can_be_replaced(decimal, action):
    source = SnapshotPart("source", "items", b"flag,amount\ntrue,\\N\nfalse,2\n")
    profile = _profile_transformation_csv(source, null_token="\\N", budget=GenerationBudget(5), max_bytes=8192)
    behavior = ({"action": "synthesize", "generation_policy_ref": "gen.yaml"} if action == "synthesize" else
        {"action": "substitute", "mapping": {"kind": "inline", "entries": [
            {"original": [None], "replacement": ["3.00" if decimal else 3]},
            {"original": ["2.00" if decimal else 2], "replacement": ["4.00" if decimal else 4]}]}})
    amount = {"entity": "items", "field": "amount", "sensitivity": "non_sensitive", "behavior": behavior}
    if decimal:
        amount["decimal_type"] = {"precision": 12, "scale": 2}
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "csv_nulls": {"input_token": "\\N"}, "fields": [
            {"entity": "items", "field": "flag", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text"}}, amount],
        "file_text_mapping": {"kind": "csv", "path": "flags.csv",
            "source_columns": ["old"], "replacement_columns": ["new"]}}
    parts = (SnapshotPart("mapping", "flags.csv", b"old,new\ntrue,no\nfalse,yes\n"),)
    if action == "synthesize":
        spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 2,
            "fields": [{"name": "amount", "data_type": "integer",
                "distribution": {"kind": "numeric", "min_value": 8, "max_value": 8}}]}]}
        if decimal:
            spec["entities"][0]["fields"][0].update(data_type="decimal", distribution={
                "kind": "decimal_range", "precision": 12, "scale": 2, "min": "8.00", "max": "8.00"})
        parts += (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    result = list(csv.DictReader(io.StringIO(execute(material).decode())))
    assert [row["amount"] for row in result] == (["8.00" if decimal else "8"] * 2 if action == "synthesize" else
                                               ["3.00", "4.00"] if decimal else ["3", "4"])


def test_derive_rejects_numeric_null_marker_in_transformed_dependency():
    source = SnapshotPart("source", "items", b"total,amount\n9,2\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source.payload, "items", budget=GenerationBudget()))
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "csv_nulls": {"output_token": "0"}, "fields": [
            {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
             "behavior": {"action": "derive", "expression": "amount + 1", "dependencies": ["amount"]}},
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "behavior": {"action": "synthesize", "generation_policy_ref": "gen.yaml"}}]}
    spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "amount", "data_type": "integer", "nullable": True, "null_ratio": 1.0}]}]}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError):
        execute(material)


def test_literal_date_replacement_ignores_temporal_format_settings():
    original = request(target="2026-08-31")
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["fields"][1]["temporal_type"] = {"type": "datetime", "format": "%d/%m/%Y",
        "output_format": "%Y", "source_timezone": "Europe/Samara", "target_timezone": "UTC"}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"),
        tuple(p for p in original.parts if p.kind == "mapping"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert execute(material) == b"flag,code\nno,1\nyes,2026-08-31\n"
    assert material.snapshot_sha256 != original.snapshot_sha256


@pytest.mark.parametrize("preserve_categories", [False, True])
def test_financial_mapping_derivation_temporary_csv_end_to_end(tmp_path, preserve_categories):
    """Fictional invoices: exact amounts, optional approved category preservation."""
    import json
    source = SnapshotPart("source", "items", b"total,amount,quantity\n2.00,1.000,2\n6.00,2.000,3\n")
    if preserve_categories:
        source = replace(source, payload=(
            b"total,amount,quantity,product,segment,bank,invoice\n"
            b"2.00,1.000,2,widget,retail,fictional-bank-a,invoice-a\n"
            b"6.00,2.000,3,gadget,wholesale,fictional-bank-b,invoice-a\n"))
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source.payload, "items", budget=GenerationBudget()))
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile), "fields": [
            {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 20, "scale": 2},
             "behavior": {"action": "derive", "expression": "amount * quantity", "dependencies": ["amount", "quantity"]}},
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 20, "scale": 3},
             "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                 {"original": ["1.000"], "replacement": ["2.345"]},
                 {"original": ["2.000"], "replacement": ["3.125"]}]}}},
            {"entity": "items", "field": "quantity", "sensitivity": "non_sensitive",
             "behavior": {"action": "replace_text", "mapping": {"kind": "csv", "path": "quantity.csv",
                 "source_columns": ["old"], "replacement_columns": ["new"]}}}]}
    if preserve_categories:
        policy["fields"].extend({"entity": "items", "field": name, "sensitivity": "non_sensitive",
            "behavior": {"action": "preserve", "authorization_ref": "fictional-ref",
                         "comment": "Reviewed fictional category"}}
            for name in ("product", "segment", "bank"))
        policy["fields"].append({"entity": "items", "field": "invoice", "sensitivity": "non_sensitive",
            "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                {"original": ["invoice-a"], "replacement": ["synthetic-invoice-a"]}]}}})
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        (SnapshotPart("mapping", "quantity.csv", b"old,new\n2,3\n3,4\n"),),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    publisher = import_module("test_data_agent.io.transformation_publish")
    receipt_path = None
    if preserve_categories:
        from test_data_agent.io.transformation_receipt import _issue_to_tty_fd
        receipt_path = tmp_path / "approval.json"
        with pytest.raises(publisher.TransformationPublicationError):
            with publisher.temporary_csv_publication(material, max_total_bytes=8192,
                    max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)):
                pytest.fail("preservation without local receipt")
        master, slave = pty.openpty()
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                issued = pool.submit(_issue_to_tty_fd, material, receipt_path, slave, GenerationBudget(5))
                prompt = bytearray()
                while b"Type APPROVE" not in prompt:
                    assert select.select([master], [], [], 5)[0]
                    prompt.extend(os.read(master, 4096))
                os.write(master, b"APPROVE\n")
                issued.result(timeout=5)
        finally:
            os.close(master)
            os.close(slave)
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5),
            receipt_path=receipt_path) as output:
        expected = (b"total,amount,quantity,product,segment,bank,invoice\n"
                    b"7.04,2.345,3,widget,retail,fictional-bank-a,synthetic-invoice-a\n"
                    b"12.50,3.125,4,gadget,wholesale,fictional-bank-b,synthetic-invoice-a\n" if preserve_categories else
                    b"total,amount,quantity\n7.04,2.345,3\n12.50,3.125,4\n")
        assert (output / "dataset.csv").read_bytes() == expected
        manifest_bytes = (output / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        assert manifest["provenance"]["output_cells"] == (14 if preserve_categories else 6)
        assert manifest["provenance"]["replacement_cells"] == (8 if preserve_categories else 6)
        assert manifest["provenance"]["original_cells"] == (6 if preserve_categories else 0)
        assert manifest["provenance"]["replacement_percent"] == ("57.14" if preserve_categories else "100.00")
        assert manifest["origin"] == "transformed_mixed"
        assert all(value not in manifest_bytes for value in (b"fictional-bank-a", b"widget", b"invoice-a", b"2.345"))
    assert not output.parent.exists()
    with publisher.temporary_csv_publication(material, max_total_bytes=8192,
            max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5),
            receipt_path=receipt_path) as replay:
        assert (replay / "dataset.csv").read_bytes() == expected
        assert (replay / "manifest.json").read_bytes() == manifest_bytes
    assert not replay.parent.exists()


def test_decimal_declaration_is_reviewed_and_never_silently_ignored():
    material = request()
    policy = yaml.safe_load(next(part.payload for part in material.parts if part.kind == "policy"))
    policy["fields"][1]["decimal_type"] = {"precision": 20, "scale": 2}
    source = next(part for part in material.parts if part.kind == "source")
    references = tuple(part for part in material.parts if part.kind == "mapping")
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, references,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert b'"precision": 20' in material.review
    assert b'"scale": 2' in material.review
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError):
        execute(material)


@pytest.mark.parametrize("replacement,expected", [("2.345", b"2.35,2.345\n"),
    ("-2.345", b"-2.35,-2.345\n"), ("2.3456", None), ("NaN", None)])
def test_exact_decimal_csv_formula(replacement, expected):
    source = SnapshotPart("source", "items", b"total,amount\n1.00,1.000\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source.payload, "items", budget=GenerationBudget()))
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile), "fields": [
            {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 20, "scale": 2},
             "behavior": {"action": "derive", "expression": "amount + 0", "dependencies": ["amount"]}},
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 20, "scale": 3},
             "behavior": {"action": "replace_text", "mapping": {"kind": "csv", "path": "m.csv",
                 "source_columns": ["old"], "replacement_columns": ["new"]}}}]}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source,
        (SnapshotPart("mapping", "m.csv", f"old,new\n1.000,{replacement}\n".encode()),),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if expected is None:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)
    else:
        assert execute(material) == b"total,amount\n" + expected


@pytest.mark.parametrize("formula", ["amount * 2", "amount / 0", "amount * 1e309", "amount + True",
    "amount + 'fictional' * 999999999999999999999999999999"])
@pytest.mark.parametrize("integer", [False, True])
def test_derive_uses_transformed_dependencies_in_topological_order(formula, integer):
    source = SnapshotPart("source", "items", b"grand,total,amount\n9,4,2\n" if integer else
                          b"grand,total,amount\n9.5,4.5,1.5\n")
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(source.payload, "items", budget=GenerationBudget()))
    policy = {"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile), "fields": [
            {"entity": "items", "field": "grand", "sensitivity": "non_sensitive",
             "behavior": {"action": "derive", "expression": "total + amount", "dependencies": ["total", "amount"]}},
            {"entity": "items", "field": "total", "sensitivity": "non_sensitive",
             "behavior": {"action": "derive", "expression": formula, "dependencies": ["amount"]}},
            {"entity": "items", "field": "amount", "sensitivity": "non_sensitive",
             "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                 {"original": [2 if integer else 1.5], "replacement": [3 if integer else 3.5]}]}}},
        ]}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, (),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if formula == "amount * 2":
        assert execute(material) == (b"grand,total,amount\n9,6,3\n" if integer else
                                     b"grand,total,amount\n10.5,7.0,3.5\n")
    else:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError) as caught:
            execute(material)
        assert caught.value.__context__ is None


@pytest.mark.parametrize("case", ["valid", "final_schema", "final_unique", "negative_mode", "null", "null_encoded", "numeric_identity"])
@pytest.mark.parametrize("action_kind", ["synthesize", "replace_text", "substitute"])
def test_closed_synthesis_uses_bound_spec_seed_and_source_row_count(case, action_kind):
    original = request(source_bytes=(b"flag,code\ntrue,1.00\nfalse,2.00\n"
                       if case == "numeric_identity" else b"flag,code\ntrue,alpha\nfalse,beta\n"))
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    policy["fields"][1]["behavior"] = {"action": "synthesize", "generation_policy_ref": "gen.yaml"}
    if action_kind != "synthesize":
        fallback = policy["fields"][1]["behavior"]
        policy["fields"][1]["behavior"] = {"action": action_kind, "unmatched": fallback}
        if action_kind == "substitute":
            policy["fields"][1]["behavior"]["mapping"] = {"kind": "inline", "entries": [
                {"original": [3.0], "replacement": [4.0]} if case == "numeric_identity" else
                {"original": ["alpha"], "replacement": ["manual"]}]}
    spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 999,
        "fields": [{"name": "code", "data_type": "string"}]}],
        "generation_settings": {"seed": 999}}
    if case == "final_schema":
        spec["entities"][0]["fields"].append({"name": "flag", "data_type": "string",
            "distribution": {"kind": "string_pattern", "min_length": 8, "max_length": 8}})
        spec["validation_settings"] = {"validate_schema": False, "validate_privacy": False,
                                       "validate_relationships": False, "validate_constraints": False}
    elif case == "final_unique":
        spec["entities"][0]["fields"].append({"name": "flag", "data_type": "string", "is_identifier": True})
        spec["entities"][0]["primary_key"] = "flag"
        spec["validation_settings"] = {"validate_schema": False, "validate_privacy": False,
                                       "validate_relationships": False, "validate_constraints": False}
    elif case == "negative_mode":
        spec["generation_settings"]["mode"] = "negative"
    elif case in {"null", "null_encoded"}:
        spec["entities"][0]["fields"][0].update(nullable=True, null_ratio=1.0)
        if case == "null_encoded":
            policy["csv_nulls"] = {"output_token": "\\N"}
    elif case == "numeric_identity":
        spec["entities"][0]["fields"][0].update(data_type="float",
            distribution={"kind": "numeric", "min_value": 1.0, "max_value": 1.0})
    parts = tuple(part for part in original.parts if part.kind == "mapping" and part.name == "all.csv")
    if case == "final_unique":
        parts = (replace(parts[0], payload=b"old,new\ntrue,duplicate\nfalse,duplicate\n"),)
    if action_kind == "replace_text":
        parts = (replace(parts[0], payload=parts[0].payload + b"alpha,manual\n"),)
    parts += (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if case == "final_unique":
        valid_parts = tuple(replace(part, payload=part.payload.replace(
            b"false,duplicate", b"false,distinct")) if part.name == "all.csv" else part for part in parts)
        valid_request = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, valid_parts,
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
        valid_rows = list(csv.DictReader(io.StringIO(execute(valid_request).decode())))
        assert [row["flag"] for row in valid_rows] == ["duplicate", "distinct"]
    if case == "null_encoded":
        rows = list(csv.DictReader(io.StringIO(execute(material).decode())))
        assert rows[-1]["code"] == "\\N"
        assert rows[0]["code"] == ("\\N" if action_kind == "synthesize" else "manual")
        return
    if case != "valid":
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError) as caught:
            execute(material)
        assert caught.value.__context__ is None
        if case in {"final_schema", "final_unique"}:
            publisher = import_module("test_data_agent.io.transformation_publish")
            with pytest.raises(publisher.TransformationPublicationError) as failed_publication:
                with publisher.temporary_csv_publication(material, max_total_bytes=8192,
                        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5)):
                    pytest.fail("invalid final dataset published")
            assert failed_publication.value.__context__ is None
        return
    module = import_module("test_data_agent.io.transformation_execute")
    measured = module.replace_csv_snapshot(material, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert measured.provenance.synthetic_cells == (2 if action_kind == "synthesize" else 1)
    assert measured.provenance.original_cells == 0
    assert measured.provenance.replacement_cells == (2 if action_kind == "synthesize" else 3)
    first = measured.csv_bytes
    assert execute(material) == first
    rows = list(csv.DictReader(io.StringIO(first.decode())))
    assert len(rows) == 2
    assert [row["flag"] for row in rows] == ["no", "yes"]
    assert all(row["code"] not in {"alpha", "beta"} for row in rows)
    if action_kind != "synthesize":
        assert rows[0]["code"] == "manual"


@pytest.mark.parametrize(("kind", "zero"), [("integer", "0"), ("float", "0.0"), ("float", "-0.00")])
@pytest.mark.parametrize("whole_row", [False, True])
def test_numeric_zero_synthesis_origin_and_whole_row_guard(kind, zero, whole_row):
    second = "2.5" if kind == "float" else "2"
    original = request(source_bytes=f"flag,code\ntrue,{zero}\nfalse,{second}\n".encode())
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["fields"][1]["behavior"] = {"action": "synthesize", "generation_policy_ref": "gen.yaml"}
    source = next(p for p in original.parts if p.kind == "source")
    parts = tuple(p for p in original.parts if p.kind == "mapping" and p.name == "all.csv")
    if whole_row:
        source = replace(source, payload=f"code\n{zero}\n{second}\n".encode())
        policy["fields"] = [policy["fields"][1]]
        policy.pop("file_text_mapping")
        parts = ()
        policy["schema_fingerprint"] = transformation_schema_fingerprint(_profile_transformation_csv(
            source, null_token=None, budget=GenerationBudget(5), max_bytes=8192))
    spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 2,
        "fields": [{"name": "code", "data_type": kind,
                    "distribution": {"kind": "numeric", "min_value": 0, "max_value": 0}}]}]}
    parts += (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),)
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    kwargs = dict(max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192,
                  budget=GenerationBudget(5))
    if whole_row:
        with pytest.raises(module.TransformationExecutionError):
            module.replace_csv_snapshot(material, **kwargs)
    else:
        result = module.replace_csv_snapshot(material, **kwargs)
        assert result.provenance.synthetic_cells == 2
        assert result.provenance.replacement_cells == 2
        assert result.provenance.original_cells == 0


@pytest.mark.parametrize("scale", [2, 3])
@pytest.mark.parametrize("precision", [20, 19])
@pytest.mark.parametrize("fallback", [False, True])
@pytest.mark.parametrize("generated", ["3.00", "1.00", "0.00"])
def test_decimal_synthesis_binds_declared_shape(scale, precision, fallback, generated):
    original = request(source_bytes=b"flag,code\ntrue,0.00\nfalse,0.00\n" if generated == "0.00"
                       else b"flag,code\ntrue,1.00\nfalse,2.00\n")
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    policy["fields"][1].update(decimal_type={"precision": 20, "scale": 2},
        behavior={"action": "synthesize", "generation_policy_ref": "gen.yaml"})
    if fallback:
        policy["fields"][1]["behavior"] = {"action": "replace_text",
            "unmatched": policy["fields"][1]["behavior"]}
    spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 999,
        "fields": [{"name": "code", "data_type": "decimal", "distribution": {
            "kind": "decimal_range", "precision": precision, "scale": scale,
            "min": generated, "max": generated}}]}]}
    parts = tuple(part for part in original.parts if part.kind == "mapping" and part.name == "all.csv")
    parts += (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),)
    if scale != 2 or precision != 20:
        from test_data_agent.io.transformation_source import TransformationSourceError
        with pytest.raises(TransformationSourceError):
            prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
                max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    else:
        material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
        if generated == "1.00":
            module = import_module("test_data_agent.io.transformation_execute")
            with pytest.raises(module.TransformationExecutionError):
                execute(material)
        else:
            assert execute(material) == f"flag,code\nno,{generated}\nyes,{generated}\n".encode()


@pytest.mark.parametrize("csv_mapping", [False, True])
def test_declared_decimal_substitution_matches_numeric_text(csv_mapping):
    original = request(source_bytes=b"flag,code\ntrue,1.0\nfalse,2.00\n")
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    mapping = {"kind": "inline", "entries": [
        {"original": ["1.00"], "replacement": ["3"]},
        {"original": ["2"], "replacement": ["4.5"]}]}
    parts = tuple(part for part in original.parts if part.kind == "mapping" and part.name == "all.csv")
    if csv_mapping:
        mapping = {"kind": "csv", "path": "d.csv", "source_columns": ["old"], "replacement_columns": ["new"]}
        parts += (SnapshotPart("mapping", "d.csv", b"old,new\n1.00,3\n2,4.5\n"),)
    policy["fields"][1].update(decimal_type={"precision": 20, "scale": 2},
        behavior={"action": "substitute", "mapping": mapping})
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, parts,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert execute(material) == b"flag,code\nno,3.00\nyes,4.50\n"


def test_closed_csv_trace_reports_unmatched_without_values():
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.trace_csv_replacements(request(complete=False), max_total_bytes=8192,
        max_review_bytes=4096, max_events=2, max_cells=4, max_rule_counts=4,
        budget=GenerationBudget(5))
    assert result.matched_cells == 3
    assert result.unmatched_cells == 1
    assert result.truncated and len(result.events) == 2
    assert result.rule_counts == ((1, "file", 1, 1), (2, "column", 1, 1), (2, "file", 2, 1))
    assert all(value not in repr(result) for value in ("001", "002", "second", "cascade"))


def test_closed_csv_trace_rejects_requested_budget_above_effective_limit():
    module = import_module("test_data_agent.io.transformation_execute")
    from test_data_agent.core.transformation_limits import InputDimension, resolve_input_limit
    import os
    limit = resolve_input_limit(InputDimension.CELLS, None, os.environ)
    with pytest.raises(module.TransformationLimitError) as caught:
        module.trace_csv_replacements(request(), max_total_bytes=8192,
            max_review_bytes=4096, max_events=2, max_cells=limit.value + 1,
            max_rule_counts=4, budget=GenerationBudget(5))
    assert caught.value.code == "requested_above_limit"
    assert (caught.value.amount, caught.value.limit, caught.value.origin) == (
        limit.value + 1, limit.value, limit.origin)


@pytest.mark.parametrize("case", ["events", "cells", "rules", "tampered"])
def test_closed_csv_trace_rejects_limits_and_tampering(case):
    module = import_module("test_data_agent.io.transformation_execute")
    material = request()
    if case == "tampered":
        material = replace(material, parts=tuple(
            replace(part, payload=part.payload + b"true,003\n") if part.kind == "source" else part
            for part in material.parts))
    with pytest.raises(module.TransformationLimitError if case == "cells" else module.TransformationExecutionError) as caught:
        module.trace_csv_replacements(material, max_total_bytes=8192, max_review_bytes=4096,
            max_events=0 if case == "events" else 4, max_cells=3 if case == "cells" else 4,
            max_rule_counts=1 if case == "rules" else 4, budget=GenerationBudget(5))
    if case == "cells":
        assert (caught.value.code, caught.value.amount, caught.value.limit) == ("limit_exceeded", 4, 3)
        assert caught.value.run_setting == "trace_csv_replacements(max_cells=...)"
    else:
        assert str(caught.value) == "invalid CSV replacement trace"
    assert caught.value.__context__ is None


def test_closed_csv_trace_keeps_source_column_ordinals_after_drop():
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.trace_csv_replacements(request(behavior={"action": "drop"}),
        max_total_bytes=8192, max_review_bytes=4096, max_events=4, max_cells=4,
        max_rule_counts=4, budget=GenerationBudget(5))
    assert [(event.row_ordinal, event.column_ordinal, event.scope) for event in result.events] == [
        (1, 2, "file"), (2, 2, "column")]


@pytest.mark.parametrize("case", ["unmatched", "tampered", "budget", "pii"])
def test_closed_csv_fails_without_returning_partial_output(case):
    material = request(target="fictional@example.com" if case == "pii" else "second",
                       complete=case != "unmatched")
    if case == "tampered":
        material = replace(material, parts=tuple(
            replace(part, payload=b"flag,code\ntrue,001\n")
            if part.kind == "source" else part for part in material.parts))
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationLimitError if case == "budget"
                       else module.TransformationExecutionError) as caught:
        execute(material, 1 if case == "budget" else 8192)
    if case == "budget":
        assert caught.value.code == "limit_exceeded" and caught.value.limit == 1
    else:
        assert str(caught.value) == "invalid CSV replacement"
    assert caught.value.__context__ is None


@pytest.mark.parametrize("target", ['quoted,"cell"', "two\nlines", "кириллица", ""])
def test_closed_csv_roundtrips_literal_replacement(target):
    output = execute(request(target=target))
    rows = list(csv.reader(io.StringIO(output.decode(), newline="")))
    assert rows == [["flag", "code"], ["no", "1"], ["yes", target]]
    assert execute(request(target=target), len(output)) == output
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationLimitError) as caught:
        execute(request(target=target), len(output) - 1)
    assert caught.value.amount == len(output) and caught.value.limit == len(output) - 1
    assert caught.value.run_setting == "replace_csv_snapshot(max_output_bytes=...)"


@pytest.mark.parametrize("behavior", [
    {"action": "preserve", "authorization_ref": "not-approval", "comment": "fictional enum"},
    {"action": "replace_text", "unmatched": {
        "action": "preserve", "authorization_ref": "not-approval", "comment": "fictional enum"}},
])
def test_closed_replace_only_rejects_other_actions_and_preservation(behavior):
    material = request(behavior=behavior)
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError, match="^invalid CSV replacement$"):
        execute(material)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_closed_csv_rejects_invalid_output_limits(limit):
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError, match="^invalid CSV replacement$"):
        execute(request(), limit)


def test_output_profile_budget_and_above_old_input_cap_request():
    original = request()
    expected = execute(original)
    assert execute(original, 128 * 1024 * 1024 + 1) == expected
    policy = yaml.safe_load(next(p.payload for p in original.parts if p.kind == "policy"))
    policy["resource_limits"] = {"max_output_bytes": len(expected)}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in original.parts if p.kind == "source"),
        tuple(p for p in original.parts if p.kind == "mapping"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationLimitError) as caught:
        execute(material, len(expected) + 1)
    assert (caught.value.code, caught.value.origin, caught.value.limit) == (
        "requested_above_limit", "profile", len(expected))
    assert caught.value.session_setting == "TEST_DATA_AGENT_TRANSFORM_MAX_OUTPUT_BYTES"
    assert caught.value.profile_key == "resource_limits.max_output_bytes"
    assert execute(material, len(expected)) == expected


def test_closed_csv_enforces_invocation_deadline():
    material = request()
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    tick[0] = 2.0
    module = import_module("test_data_agent.io.transformation_execute")
    with pytest.raises(module.TransformationExecutionError, match="^invalid CSV replacement$"):
        module.replace_csv_snapshot(material, max_total_bytes=8192, max_review_bytes=4096,
                                    max_output_bytes=8192, budget=budget)


def test_closed_csv_drops_selected_column_without_changing_row_order():
    material = request(complete=False, behavior={"action": "drop"})
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["code"], ["1"], ["second"]]


@pytest.mark.parametrize("action", ["preserve", "replace_text", "substitute", "format_temporal", "format_all_preserve", "preserve_null", "typed_output", "zero_direct", "zero_fallback"])
def test_closed_preservation_requires_exact_local_receipt(tmp_path, action):
    from test_data_agent.io.transformation_receipt import _issue_to_tty_fd

    zero_case = action if action.startswith("zero_") else None
    all_preserved = action == "format_all_preserve" or zero_case is not None
    typed_output = action == "typed_output"
    if typed_output:
        action = "preserve"
    preserve_null = action == "preserve_null"
    if preserve_null:
        action = "preserve"
    if all_preserved:
        action = "format_temporal"

    preserve = {"action": "preserve", "authorization_ref": "fictional-ref",
                "comment": "Reviewed fictional flag"}
    behavior = {"action": action, "unmatched": preserve} if action != "preserve" else preserve
    source_bytes = b"flag,code\ntrue,001\nfalse,002\n"
    if preserve_null:
        source_bytes = b"flag,code\n\\N,001\n,002\n"
    if action == "substitute":
        source_bytes = b"flag,code\nready,001\nwaiting,002\n"
        behavior["mapping"] = {"kind": "inline", "entries": [
            {"original": ["ready"], "replacement": ["done"]}]}
    if action == "format_temporal":
        behavior = preserve
        source_bytes = (b"flag,code\n2026-08-31,-0.00\n2026-09-01,2.5\n" if zero_case else
                        b"flag,code\n2026-08-31,001\n2026-09-01,002\n")
    material = request(complete=False, behavior=behavior, source_bytes=source_bytes)
    if preserve_null:
        policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
        policy["csv_nulls"] = {"input_token": "\\N", "output_token": "NULL"}
        policy["schema_fingerprint"] = transformation_schema_fingerprint(_profile_transformation_csv(
            next(p for p in material.parts if p.kind == "source"), null_token="\\N",
            budget=GenerationBudget(5), max_bytes=8192))
        material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
            next(p for p in material.parts if p.kind == "source"),
            tuple(p for p in material.parts if p.kind == "mapping"),
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if action == "format_temporal":
        policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
        policy["fields"][0]["behavior"]["format_temporal"] = True
        policy["fields"][0]["temporal_type"] = {"type": "date", "format": "%Y-%m-%d", "output_format": "%d/%m/%Y"}
        if all_preserved:
            policy.pop("file_text_mapping")
            policy["fields"][1]["behavior"]["unmatched"] = preserve
        extra_parts = ()
        if zero_case:
            synth = {"action": "synthesize", "generation_policy_ref": "gen.yaml"}
            if zero_case == "zero_direct":
                policy["fields"][1]["behavior"] = synth
            else:
                policy["fields"][1]["behavior"]["unmatched"] = synth
            spec = {"schema_version": "1.1", "entities": [{"name": "items", "row_count": 2,
                "fields": [{"name": "code", "data_type": "float", "distribution": {
                    "kind": "numeric", "min_value": 0, "max_value": 0}}]}]}
            extra_parts = (SnapshotPart("generation_policy", "gen.yaml", yaml.safe_dump(spec).encode()),)
        material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
            next(p for p in material.parts if p.kind == "source"),
            ((() if zero_case == "zero_direct" else
              (SnapshotPart("mapping", "code.csv", b"old,new\n999,888\n"),)) if all_preserved else
             tuple(p for p in material.parts if p.kind == "mapping")) + extra_parts,
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if typed_output:
        policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
        policy["output"] = {"format": "postgresql_sql", "table": "items", "fields": [
            {"name": name, "type": "string"} for name in ("flag", "code")]}
        material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
            next(p for p in material.parts if p.kind == "source"),
            tuple(p for p in material.parts if p.kind == "mapping"),
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    path = tmp_path / "approval.json"
    kwargs = dict(max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192)
    with pytest.raises(module.TransformationExecutionError):
        module.replace_csv_snapshot(material, receipt_path=path, budget=GenerationBudget(5), **kwargs)
    master, slave = pty.openpty()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            issued = pool.submit(_issue_to_tty_fd, material, path, slave, GenerationBudget(5))
            prompt = bytearray()
            while b"Type APPROVE" not in prompt:
                assert select.select([master], [], [], 5)[0]
                prompt.extend(os.read(master, 4096))
            os.write(master, b"APPROVE\n")
            issued.result(timeout=5)
        assert b"second" not in prompt
    finally:
        os.close(master)
        os.close(slave)
    if all_preserved:
        publisher = import_module("test_data_agent.io.transformation_publish")
        with pytest.raises(publisher.TransformationPublicationError):
            with publisher.temporary_csv_publication(material, receipt_path=path,
                    budget=GenerationBudget(5), **kwargs):
                pytest.fail("whole row information retained through fallback")
        return
    output = module.replace_csv_snapshot(material, receipt_path=path,
                                         budget=GenerationBudget(5), **kwargs)
    expected_flags = {"preserve": ("true", "false"), "replace_text": ("no", "false"),
                      "substitute": ("done", "waiting"), "format_temporal": ("31/08/2026", "01/09/2026")}[action]
    if preserve_null:
        expected_flags = ("NULL", "")
    assert list(csv.reader(io.StringIO(output.csv_bytes.decode()))) == [
        ["flag", "code"], [expected_flags[0], "1"], [expected_flags[1], "second"]]
    # Profile identifies code as INTEGER: 001 -> 1 also retains its numeric value.
    if action != "format_temporal" and not typed_output:
        assert output.retention.unchanged_percent == ("75.00" if action == "preserve" else "50.00")
    else:
        assert output.retention.status == "unavailable"
        assert output.retention.unchanged_percent is None
    assert output.retention.compared_cells == 4
    assert output.provenance.synthetic_cells == 0
    assert output.provenance.original_cells == (0 if action == "format_temporal" or typed_output else 2 if action == "preserve" else 1)
    assert output.provenance.replacement_cells == 4 - output.provenance.original_cells
    for part in material.parts:
        if part.kind in {"policy", "mapping", "source"}:
            (tmp_path / ("items.csv" if part.kind == "source" else part.name)).write_bytes(part.payload)
    command_summary = import_module("test_data_agent.io.transformation_publish")._run_temporary_transform(
        tmp_path / "items.csv", "items", tmp_path / "behavior.yaml",
        expected_snapshot_sha256=material.snapshot_sha256, receipt_path=path,
        budget=GenerationBudget(5), **kwargs)
    assert command_summary["provenance"]["original_cells"] == output.provenance.original_cells
    if preserve_null:
        # Changing either marker invalidates the exact local approval.
        for settings in ({"input_token": "OTHER", "output_token": "NULL"},
                         {"input_token": "\\N"}):
            changed_policy = dict(policy, csv_nulls=settings)
            changed_policy["schema_fingerprint"] = transformation_schema_fingerprint(_profile_transformation_csv(
                next(p for p in material.parts if p.kind == "source"), null_token=settings["input_token"],
                budget=GenerationBudget(5), max_bytes=8192))
            changed_nulls = prepare_csv_review_request(yaml.safe_dump(changed_policy).encode(),
                next(p for p in material.parts if p.kind == "source"),
                tuple(p for p in material.parts if p.kind == "mapping"),
                max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
            assert changed_nulls.snapshot_sha256 != material.snapshot_sha256
            with pytest.raises(module.TransformationExecutionError):
                module.replace_csv_snapshot(changed_nulls, receipt_path=path,
                    budget=GenerationBudget(5), **kwargs)
    assert "second" not in repr(output)
    # The same fictional TTY receipt gates filesystem publication, not only
    # the in-memory executor. No public execution interface is registered.
    import json
    publisher = import_module("test_data_agent.io.transformation_publish")
    with publisher.temporary_csv_publication(material, receipt_path=path,
            budget=GenerationBudget(5), **kwargs) as published:
        if typed_output:
            assert "VALUES ('true', '1');" in (published / "dataset.sql").read_text()
        else:
            assert (published / "dataset.csv").read_bytes() == output.csv_bytes
        manifest = json.loads((published / "manifest.json").read_bytes())
        assert manifest["origin"] == "transformed_mixed"
        assert manifest["version"] == 2
        assert "retention" not in manifest
        assert manifest["provenance"]["original_cells"] == output.provenance.original_cells
    assert not published.parent.exists()
    changed = request(target="changed", complete=False, behavior=behavior, source_bytes=source_bytes)
    for invalid_request, receipt in ((changed, path), (material, None)):
        with pytest.raises(publisher.TransformationPublicationError) as publication_error:
            with publisher.temporary_csv_publication(invalid_request, receipt_path=receipt,
                    budget=GenerationBudget(5), **kwargs):
                pytest.fail("unapproved preservation was published")
        assert publication_error.value.__context__ is None
    with pytest.raises(module.TransformationExecutionError):
        module.replace_csv_snapshot(changed, receipt_path=path, budget=GenerationBudget(5), **kwargs)
    for kind in ("source", "policy", "evidence", "review"):
        tampered = replace(material, parts=tuple(
            replace(part, payload=part.payload + b" ") if part.kind == kind else part
            for part in material.parts))
        with pytest.raises(module.TransformationExecutionError) as caught:
            module.replace_csv_snapshot(tampered, receipt_path=path,
                                         budget=GenerationBudget(5), **kwargs)
        assert str(caught.value) == "invalid CSV replacement"
        assert caught.value.__context__ is None
    original_receipt = path.read_bytes()
    for mode, payload in ((0o644, original_receipt), (0o600, b"not-json"),
                          (0o600, b'{"version":1,"snapshot_sha256":"wrong"}')):
        path.write_bytes(payload)
        path.chmod(mode)
        with pytest.raises(module.TransformationExecutionError) as caught:
            module.replace_csv_snapshot(material, receipt_path=path,
                                         budget=GenerationBudget(5), **kwargs)
        assert str(caught.value) == "invalid CSV replacement"
        assert caught.value.__context__ is None
    path.write_bytes(original_receipt)
    path.chmod(0o600)
    link = tmp_path / "approval-link.json"
    link.symlink_to(path)
    with pytest.raises(module.TransformationExecutionError):
        module.replace_csv_snapshot(material, receipt_path=link,
                                     budget=GenerationBudget(5), **kwargs)


def test_engine_retention_excludes_dropped_cells():
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.replace_csv_snapshot(request(behavior={"action": "drop"}),
        max_total_bytes=8192, max_review_bytes=4096, max_output_bytes=8192,
        budget=GenerationBudget(5))
    assert result.retention.compared_cells == 2
    assert result.retention.excluded_dropped_cells == 2
    assert result.retention.unchanged_percent == "50.00"
    assert result.provenance.replacement_cells == 2
    assert result.provenance.original_cells == 0
    assert result.provenance.replacement_percent == "100.00"
    assert result.provenance.excluded_dropped_cells == 2


def test_all_dropped_columns_have_no_retention_measurement():
    original = request()
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    policy.pop("file_text_mapping")
    for decision in policy["fields"]:
        decision["behavior"] = {"action": "drop"}
    source = next(part for part in original.parts if part.kind == "source")
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, (),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    module = import_module("test_data_agent.io.transformation_execute")
    result = module.replace_csv_snapshot(material, max_total_bytes=8192,
        max_review_bytes=4096, max_output_bytes=8192, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(result.csv_bytes.decode()))) == [[], [], []]
    assert result.retention.status == "unavailable"
    assert result.retention.unchanged_percent is None
    assert result.retention.compared_cells == 0
    assert result.retention.excluded_dropped_cells == 4
    assert result.provenance.output_cells == 0
    assert result.provenance.excluded_dropped_cells == 4
    assert result.provenance.original_percent is None
    assert result.provenance.synthetic_percent is None
    assert result.provenance.replacement_percent is None


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
@pytest.mark.parametrize("bom", [b"", b"\xef\xbb\xbf"])
def test_execution_uses_profile_dialect_and_source_column_order(delimiter, bom):
    source = bom + (f"code{delimiter}flag\r\n001{delimiter}true\r\n"
                    f"002{delimiter}false\r\n").encode()
    output = execute(request(source_bytes=source))
    assert list(csv.reader(io.StringIO(output.decode()))) == [
        ["code", "flag"], ["1", "no"], ["second", "yes"]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
@pytest.mark.parametrize("case", ["valid", "unmatched", "pii"])
def test_string_substitute_inline_and_csv_have_same_result(kind, case):
    original = request(source_bytes=b"flag,code\ntrue,alpha\nfalse,beta\n")
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    target = "fictional@example.com" if case == "pii" else "second"
    pairs = [("alpha", "first")]
    if case != "unmatched":
        pairs.append(("beta", target))
    mapping = {"kind": "inline", "entries": [
        {"original": [before], "replacement": [after]} for before, after in pairs]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    # A global replace rule must not cover a missing substitute key.
    parts[0] = replace(parts[0], payload=parts[0].payload + b"beta,global-fallback\n")
    if kind == "csv":
        mapping = {"kind": "csv", "path": "pairs.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        payload = io.StringIO(newline="")
        csv.writer(payload).writerows([("old", "new"), *pairs])
        parts.append(SnapshotPart("mapping", "pairs.csv", payload.getvalue().encode()))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    if case != "valid":
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError) as caught:
            execute(material)
        assert str(caught.value) == "invalid CSV replacement"
        assert caught.value.__context__ is None
        return
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", "first"], ["yes", "second"]]


@pytest.mark.parametrize("missing", [False, True])
@pytest.mark.parametrize("kind", ["inline", "csv"])
@pytest.mark.parametrize("scalar", ["string", "integer", "float", "date"])
def test_composite_domain_matches_whole_original_tuple(missing, kind, scalar):
    before, after = {
        "string": (("north", "south"), ("west", "east")),
        "integer": ((1, 2), (11, 22)),
        "float": ((1.25, 2.75), (3.125, 4.5)),
        "date": (("2025-01-01", "2025-01-02"), ("2026-01-01", "2026-01-02")),
    }[scalar]
    source = SnapshotPart("source", "items",
                          f"region,code\n{before[0]},A001\n{before[1]},A001\n".encode())
    profile = csv_profile_to_dataset_profile(profile_csv_bytes(
        source.payload, source.name, budget=GenerationBudget(5)))
    entries = [{"original": [before[0], "A001"], "replacement": [after[0], "first"]}]
    if not missing:
        entries.append({"original": [before[1], "A001"], "replacement": [after[1], "second"]})
    mapping = {"kind": "inline", "entries": entries}
    parts = ()
    if kind == "csv":
        mapping = {"kind": "csv", "path": "pairs.csv", "source_columns": ["old_region", "old_code"],
                   "replacement_columns": ["new_region", "new_code"]}
        payload = io.StringIO(newline="")
        csv.writer(payload).writerows([
            ("old_region", "old_code", "new_region", "new_code"),
            *(tuple(entry["original"] + entry["replacement"]) for entry in entries)])
        parts = (SnapshotPart("mapping", "pairs.csv", payload.getvalue().encode()),)
    policy = yaml.safe_dump({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": transformation_schema_fingerprint(profile),
        "domains": [{"name": "pair", "mapping": mapping}],
        "fields": [{"entity": "items", "field": name, "sensitivity": "non_sensitive",
                    "behavior": {"action": "substitute", "mapping": {
                        "kind": "domain", "name": "pair", "component": component}}}
                   for component, name in reversed(list(enumerate(("region", "code"))))],
    }).encode()
    material = prepare_csv_review_request(policy, source, parts, max_total_bytes=8192,
        max_review_bytes=4096, budget=GenerationBudget(5))
    if missing:
        module = import_module("test_data_agent.io.transformation_execute")
        with pytest.raises(module.TransformationExecutionError):
            execute(material)
    else:
        assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
            ["region", "code"], [str(after[0]), "first"], [str(after[1]), "second"]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
@pytest.mark.parametrize("floating", [False, True])
def test_numeric_substitute_preserves_declared_numeric_contract(kind, floating):
    before = (1.25, 2.75) if floating else (1, 2)
    after = (2.5, 3.125) if floating else (9007199254740993, 9007199254740995)
    original = request(source_bytes=f"flag,code\ntrue,{before[0]}\nfalse,{before[1]}\n".encode())
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    mapping = {"kind": "inline", "entries": [
        {"original": [old], "replacement": [new]} for old, new in zip(before, after)]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    if kind == "csv":
        mapping = {"kind": "csv", "path": "ints.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        text = (f"old,new\n1.25e0,{after[0]}\n2.75,{after[1]}\n" if floating else
                f"old,new\n001,{after[0]}\n002,{after[1]}\n")
        parts.append(SnapshotPart("mapping", "ints.csv", text.encode()))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", str(after[0])], ["yes", str(after[1])]]


@pytest.mark.parametrize("kind", ["inline", "csv"])
def test_date_substitute_keeps_canonical_iso_text(kind):
    before = ["2025-01-02", "2025-01-03"]
    after = ["2026-02-04", "2026-02-05"]
    original = request(source_bytes=f"flag,code\ntrue,{before[0]}\nfalse,{before[1]}\n".encode())
    source = next(part for part in original.parts if part.kind == "source")
    policy = yaml.safe_load(next(part.payload for part in original.parts if part.kind == "policy"))
    mapping = {"kind": "inline", "entries": [
        {"original": [old], "replacement": [new]} for old, new in zip(before, after)]}
    parts = [part for part in original.parts if part.kind == "mapping" and part.name == "all.csv"]
    if kind == "csv":
        mapping = {"kind": "csv", "path": "dates.csv", "source_columns": ["old"],
                   "replacement_columns": ["new"]}
        parts.append(SnapshotPart("mapping", "dates.csv",
            ("old,new\n" + "".join(f"{old},{new}\n" for old, new in zip(before, after))).encode()))
    policy["fields"][1]["behavior"] = {"action": "substitute", "mapping": mapping}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(), source, tuple(parts),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert list(csv.reader(io.StringIO(execute(material).decode()))) == [
        ["flag", "code"], ["no", after[0]], ["yes", after[1]]]
