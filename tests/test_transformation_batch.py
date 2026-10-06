"""Fictional closed multi-input execution; no product monkeypatch or I/O."""
from dataclasses import replace
import json
import errno
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import time

import pytest
import yaml

from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
from test_data_agent.io.transformation_batch import (
    prepare_batch, execute_batch, review_batch, TransformationBatchError, temporary_batch_publication,
)
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.io.transformation_batch_receipt import verify_batch_receipt
from test_data_agent.io.transformation_receipt import LocalReceiptError
from test_data_agent.io.transformation_batch_profile import load_batch_profile


def fixture_batch(case):
    requests = []
    for entity, values in (("parents", [1, 2]), ("children", [1, 2, 1])):
        if case == "orphan" and entity == "parents":
            values = [1, 3]
        decimal = case == "decimal_mismatch"
        if decimal:
            values = [f"{value}.25" for value in values]
        source = SnapshotPart("source", entity, ("key\n" + "".join(f"{value}\n" for value in values)).encode())
        policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
            "schema_fingerprint": "0" * 64, "domains": [{"name": "shared", "mapping": {
                "kind": "inline", "entries": [
                    {"original": ["1.25" if decimal else 1], "replacement": ["11.25" if decimal else 11]},
                    {"original": ["3.25" if decimal else 3], "replacement": ["13.25" if decimal else 13]},
                    {"original": ["2.25" if decimal else 2], "replacement": ["12.25" if decimal else
                        13 if case == "conflict" and entity == "children" else 12]}]}}],
            "fields": [{"entity": entity, "field": "key", "sensitivity": "non_sensitive",
                **({"decimal_type": {"precision": 8 if entity == "parents" else 9, "scale": 2}}
                   if decimal else {}),
                "behavior": ({"action": "preserve", "authorization_ref": "fictional-local",
                              "comment": "Fictional review"} if case == "preserve" else
                    {"action": "substitute", "mapping": {"kind": "domain", "name": "shared"}})}]})
        profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
        requests.append(prepare_csv_review_request(yaml.safe_dump(policy.model_dump(mode="json")).encode(),
            source, (), max_total_bytes=16384, max_review_bytes=8192, budget=GenerationBudget(5)))
    spec = {"schema_version": "1.1", "entities": [
        {"name": entity, "row_count": count, "fields": [{"name": "key", "data_type": "integer",
            "is_identifier": True}],
         **({"primary_key": "key"} if entity == "parents" else {})}
        for entity, count in (("parents", 2), ("children", 3))],
        "relationships": [{"parent_entity": "parents", "parent_field": "key",
                           "child_entity": "children", "child_field": "key", "confidence": 1}],
        "validation_settings": {"validate_schema": False, "validate_relationships": False,
                                "validate_constraints": False, "validate_privacy": False}}
    return prepare_batch(tuple(requests), yaml.safe_dump(spec).encode(),
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))


@pytest.mark.parametrize("case", ["valid", "orphan", "conflict", "stale", "budget", "preserve", "decimal_mismatch"])
def test_closed_parent_child_batch(case):
    if case == "preserve":
        # Existing numeric preservation preflight is stricter than batch execution.
        with pytest.raises(ValueError):
            fixture_batch(case)
        return
    batch = fixture_batch(case)
    arguments = dict(expected_snapshot_sha256=batch.snapshot_sha256, max_total_bytes=32768,
                     max_review_bytes=8192, max_output_bytes=8192, budget=GenerationBudget(5))
    if case == "stale":
        batch = replace(batch, validation_yaml=batch.validation_yaml + b"\n")
    if case == "budget":
        arguments["max_output_bytes"] = 1
    if case != "valid":
        with pytest.raises(TransformationLimitError if case == "budget" else TransformationBatchError) as caught:
            execute_batch(batch, **arguments)
        if case != "budget":
            assert str(caught.value) == "invalid transformation batch"
            assert caught.value.__context__ is None
    else:
        results = execute_batch(batch, **arguments)
        assert [result.csv_bytes for result in results] == [b"key\n11\n12\n", b"key\n11\n12\n11\n"]
        assert [result.csv_bytes for result in execute_batch(batch, **arguments)] == [
            result.csv_bytes for result in results]


def test_closed_batch_atomic_temporary_bundle():
    batch = fixture_batch("valid")
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5)) as bundle:
        assert {item.name for item in bundle.iterdir()} == {"input-0.csv", "input-1.csv", "manifest.json"}
        assert (bundle / "input-0.csv").read_bytes() == b"key\n11\n12\n"
        assert (bundle / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"
    assert not bundle.parent.exists()


@pytest.mark.parametrize("output_format", ["parquet", "postgresql_sql"])
@pytest.mark.parametrize("case", ["valid", "orphan", "budget"])
@pytest.mark.parametrize("retained", [False, True])
def test_saved_batch_typed_output_bundle(tmp_path, output_format, case, retained):
    save_fictional_batch_profile(tmp_path)
    for index in range(2):
        path = tmp_path / f"policy-{index}.yaml"
        policy = yaml.safe_load(path.read_bytes())
        policy["output"] = {"format": output_format,
            "fields": [{"name": "key", "type": "integer"}]}
        if output_format == "postgresql_sql":
            policy["output"]["table"] = f"fictional_{index}"
        path.write_text(yaml.safe_dump(policy))
    if case == "orphan":
        path = tmp_path / "source-0.csv"
        path.write_bytes(b"key\n1\n3\n")
        policy_path = tmp_path / "policy-0.yaml"
        policy = BehaviorPolicy.model_validate(yaml.safe_load(policy_path.read_bytes()))
        evidence = _profile_transformation_source(SnapshotPart("source", "parents", path.read_bytes()),
            policy, max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(expected_snapshot_sha256=batch.snapshot_sha256, max_total_bytes=32768,
                     max_review_bytes=8192, max_output_bytes=50 if case == "budget" else 8192)
    def publication():
        if not retained:
            return temporary_batch_publication(batch, **arguments, budget=GenerationBudget(5))
        from contextlib import nullcontext
        from test_data_agent.io.transformation_batch_workflow import BatchWorkflowRequest, run_batch_workflow
        result = run_batch_workflow(BatchWorkflowRequest(operation="execute", root=tmp_path,
            profile="batch.yaml", destination="output", snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192,
            max_output_bytes=arguments["max_output_bytes"]), budget=GenerationBudget(5))
        assert result.status == "closed_publication_completed"
        assert result.summary_json == (tmp_path / "output" / "manifest.json").read_bytes()
        return nullcontext(tmp_path / "output")
    if case != "valid":
        with pytest.raises(TransformationLimitError if case == "budget" else TransformationBatchError):
            with publication():
                pytest.fail("invalid typed batch published")
        assert not (tmp_path / "output").exists()
        assert not list(tmp_path.glob(".output.*"))
        return
    suffix = "parquet" if output_format == "parquet" else "sql"
    with publication() as bundle:
        manifest = json.loads((bundle / "manifest.json").read_bytes())
        assert manifest["artifacts"] == [f"input-0.{suffix}", f"input-1.{suffix}"]
        for index, keys in enumerate(([11, 12], [11, 12, 11])):
            path = bundle / f"input-{index}.{suffix}"
            if suffix == "parquet":
                import pyarrow.parquet as pq
                assert pq.read_table(path).to_pydict() == {"key": keys}
            else:
                statements = path.read_text().splitlines()
                inserts = [line for line in statements if line.startswith("INSERT INTO")]
                assert inserts == [f'INSERT INTO "fictional_{index}" ("key") VALUES ({key});' for key in keys]
    assert bundle.exists() if retained else not bundle.parent.exists()


@pytest.mark.parametrize("output_format", ["parquet", "postgresql_sql"])
@pytest.mark.parametrize("retained", [False, True])
def test_saved_batch_native_null_and_exact_decimal(tmp_path, output_format, retained):
    from decimal import Decimal
    save_fictional_batch_profile(tmp_path)
    spec = yaml.safe_load((tmp_path / "validation.yaml").read_bytes())
    null_token = "\\N"
    for index in range(2):
        source_path, policy_path = tmp_path / f"source-{index}.csv", tmp_path / f"policy-{index}.yaml"
        keys = source_path.read_text().splitlines()[1:]
        source_path.write_text("key,label,amount\n" + "".join(
            f"{key},{'fictional-label-a' if row % 2 else null_token},1.25\n" for row, key in enumerate(keys)))
        raw = yaml.safe_load(policy_path.read_bytes())
        raw["csv_nulls"] = {"input_token": null_token}
        raw["fields"].extend([
            {"entity": spec["entities"][index]["name"], "field": "label", "sensitivity": "non_sensitive",
             "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                 {"original": [None], "replacement": [None]},
                 {"original": ["fictional-label-a"], "replacement": [""]}]}}},
            {"entity": spec["entities"][index]["name"], "field": "amount", "sensitivity": "non_sensitive",
             "decimal_type": {"precision": 8, "scale": 2},
             "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                 {"original": ["1.25"], "replacement": ["999.99"]}]}}}])
        raw["output"] = {"format": output_format, "fields": [
            {"name": "key", "type": "integer"}, {"name": "label", "type": "string", "nullable": True},
            {"name": "amount", "type": "decimal", "decimal_type": {"precision": 8, "scale": 2}}]}
        if output_format == "postgresql_sql":
            raw["output"]["table"] = f"fictional_{index}"
        policy = BehaviorPolicy.model_validate(raw)
        evidence = _profile_transformation_source(
            SnapshotPart("source", spec["entities"][index]["name"], source_path.read_bytes()),
            policy, max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
        spec["entities"][index]["fields"].extend([
            {"name": "label", "data_type": "string", "nullable": True},
            {"name": "amount", "data_type": "decimal", "distribution": {
                "kind": "decimal_range", "precision": 8, "scale": 2, "min": "0.00", "max": "9999.99"}}])
    (tmp_path / "validation.yaml").write_text(yaml.safe_dump(spec))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    publication = temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=16384,
            budget=GenerationBudget(5))
    if retained:
        from contextlib import nullcontext
        from test_data_agent.io.transformation_batch_workflow import BatchWorkflowRequest, run_batch_workflow
        result = run_batch_workflow(BatchWorkflowRequest(operation="execute", root=tmp_path,
            profile="batch.yaml", destination="output", snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=16384),
            budget=GenerationBudget(5))
        assert result.status == "closed_publication_completed"
        publication = nullcontext(tmp_path / "output")
    with publication as bundle:
        for index, keys in enumerate(([11, 12], [11, 12, 11])):
            if output_format == "parquet":
                import pyarrow as pa
                import pyarrow.parquet as pq
                table = pq.read_table(bundle / f"input-{index}.parquet")
                assert table.schema.field("amount").type == pa.decimal128(8, 2)
                assert table.to_pylist() == [{"key": key, "label": None if row % 2 == 0 else "",
                    "amount": Decimal("999.99")} for row, key in enumerate(keys)]
            else:
                text = (bundle / f"input-{index}.sql").read_text()
                assert '"amount" NUMERIC(8,2) NOT NULL' in text
                inserts = [line for line in text.splitlines() if line.startswith("INSERT")]
                expected = [f"VALUES ({key}, {'NULL' if row % 2 == 0 else chr(39) * 2}, 999.99);"
                            for row, key in enumerate(keys)]
                assert all(line.endswith(value) for line, value in zip(inserts, expected, strict=True))
        assert "999.99" not in (bundle / "manifest.json").read_text()
    assert bundle.exists() if retained else not bundle.parent.exists()


@pytest.mark.parametrize("native_inputs", [(0,), (0, 1)])
@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
def test_saved_batch_native_parquet_sources(tmp_path, native_inputs, output_format):
    import pyarrow as pa
    import pyarrow.parquet as pq
    save_fictional_batch_profile(tmp_path)
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    for index, item in enumerate(profile["inputs"]):
        policy_path = tmp_path / item["policy"]
        raw = yaml.safe_load(policy_path.read_bytes())
        if index in native_inputs:
            keys = [int(value) for value in (tmp_path / item["source"]).read_text().splitlines()[1:]]
            item["source"] = f"source-{index}.parquet"
            pq.write_table(pa.table({"key": pa.array(keys, type=pa.int64())}), tmp_path / item["source"])
            raw["input_format"] = "parquet"
        if output_format != "csv":
            raw["output"] = {"format": output_format, "fields": [{"name": "key", "type": "integer"}]}
            if output_format == "postgresql_sql":
                raw["output"]["table"] = f"fictional_{index}"
        policy = BehaviorPolicy.model_validate(raw)
        source = SnapshotPart("source", item["entity"], (tmp_path / item["source"]).read_bytes())
        evidence = _profile_transformation_source(source, policy,
            max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    suffix = "sql" if output_format == "postgresql_sql" else output_format
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=16384,
            budget=GenerationBudget(5)) as bundle:
        for index, keys in enumerate(([11, 12], [11, 12, 11])):
            path = bundle / f"input-{index}.{suffix}"
            if output_format == "parquet":
                assert pq.read_table(path).to_pydict() == {"key": keys}
            elif output_format == "csv":
                assert path.read_text() == "key\n" + "".join(f"{key}\n" for key in keys)
            else:
                inserts = [line for line in path.read_text().splitlines() if line.startswith("INSERT")]
                assert inserts == [f'INSERT INTO "fictional_{index}" ("key") VALUES ({key});' for key in keys]
    assert not bundle.parent.exists()
    native_path = tmp_path / profile["inputs"][0]["source"]
    pq.write_table(pa.table({"key": pa.array([1, 3], type=pa.int64())}), native_path)
    changed = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                                max_review_bytes=8192, budget=GenerationBudget(5))
    assert changed.snapshot_sha256 != batch.snapshot_sha256
    with pytest.raises(TransformationBatchError):
        execute_batch(changed, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=16384,
            budget=GenerationBudget(5))
    with pytest.raises(TransformationBatchError):
        execute_batch(changed, expected_snapshot_sha256=changed.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=16384,
            budget=GenerationBudget(5))


@pytest.mark.parametrize("adapters", [("postgres", "postgres"), ("postgres", "trino"), ("trino", "trino")])
@pytest.mark.parametrize("output_format", ["csv", "parquet", "postgresql_sql"])
def test_saved_batch_authorized_fictional_query_captures(tmp_path, adapters, output_format):
    from contextlib import contextmanager
    import pyarrow as pa
    import pyarrow.parquet as pq
    from test_data_agent.io.transformation_query_capture import _capture_authorized_result
    from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryAdapter, SqlQueryProfileRequest
    save_fictional_batch_profile(tmp_path)
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    spec = yaml.safe_load((tmp_path / "validation.yaml").read_bytes())
    for entity in spec["entities"]:
        entity["name"] = "fictional." + entity["name"]
    for relationship in spec["relationships"]:
        for side in ("parent_entity", "child_entity"):
            relationship[side] = "fictional." + relationship[side]
    (tmp_path / "validation.yaml").write_text(yaml.safe_dump(spec))
    opened = []
    for index, item in enumerate(profile["inputs"]):
        raw = yaml.safe_load((tmp_path / item["policy"]).read_bytes())
        item["entity"] = "fictional." + item["entity"]
        for decision in raw["fields"]:
            decision["entity"] = item["entity"]
        raw["input_format"] = adapters[index] + "_query"
        if output_format != "csv":
            raw["output"] = {"format": output_format, "fields": [{"name": "key", "type": "integer"}]}
            if output_format == "postgresql_sql":
                raw["output"]["table"] = f"fictional_{index}"
        policy = BehaviorPolicy.model_validate(raw)
        keys = [int(value) for value in (tmp_path / item["source"]).read_text().splitlines()[1:]]
        table = pa.table({"key": pa.array(keys, type=pa.int64())})
        physical = "public.items" if adapters[index] == "postgres" else "lake.safe.items"
        query_path = tmp_path / f"query-{index}.sql"
        query_path.write_text(f'SELECT "key" FROM {physical}')

        @contextmanager
        def stream(query):
            assert query.sql.endswith("LIMIT 5") and "SELECT *" not in query.sql
            opened.append(index)
            yield iter(table.to_batches())

        request = SqlQueryProfileRequest(SqlQueryAdapter(adapters[index]), "fictional",
            item["entity"].removeprefix("fictional."), query_path)
        arguments = dict(source_columns=(QuerySourceColumn("key", "bigint", False),),
            schema=table.schema, policy=policy, stream=stream, max_rows=4, max_bytes=32768)
        with pytest.raises(ValueError, match="invalid bounded query capture"):
            _capture_authorized_result(request, allowed_tables=frozenset({"outside.items"}),
                **arguments, budget=GenerationBudget(5))
        assert len(opened) == index  # Authorization fails before injected stream access.
        source = _capture_authorized_result(request, allowed_tables=frozenset({physical}),
            **arguments, budget=GenerationBudget(5))
        item["source"] = f"capture-{index}.bin"
        (tmp_path / item["source"]).write_bytes(source.payload)
        evidence = _profile_transformation_source(source, policy, max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        (tmp_path / item["policy"]).write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    assert opened == [0, 1]
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=16384,
            budget=GenerationBudget(5)) as bundle:
        for index, keys in enumerate(([11, 12], [11, 12, 11])):
            if output_format == "csv":
                assert (bundle / f"input-{index}.csv").read_text() == "key\n" + "".join(f"{key}\n" for key in keys)
            elif output_format == "parquet":
                assert pq.read_table(bundle / f"input-{index}.parquet").to_pydict() == {"key": keys}
            else:
                inserts = [line for line in (bundle / f"input-{index}.sql").read_text().splitlines()
                           if line.startswith("INSERT")]
                assert inserts == [f'INSERT INTO "fictional_{index}" ("key") VALUES ({key});' for key in keys]
    assert not bundle.parent.exists()


def test_batch_identity_binds_artifact_order():
    batch = fixture_batch("valid")
    reversed_batch = prepare_batch(tuple(reversed(batch.requests)), batch.validation_yaml,
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    assert reversed_batch.snapshot_sha256 != batch.snapshot_sha256
    with pytest.raises(TransformationBatchError):
        execute_batch(reversed_batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5))
    with temporary_batch_publication(reversed_batch,
            expected_snapshot_sha256=reversed_batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5)) as bundle:
        assert (bundle / "input-0.csv").read_bytes() == b"key\n11\n12\n11\n"
        assert (bundle / "input-1.csv").read_bytes() == b"key\n11\n12\n"
        assert json.loads((bundle / "manifest.json").read_bytes())["snapshot_sha256"] == (
            reversed_batch.snapshot_sha256)
    assert not bundle.parent.exists()


def test_closed_batch_cleans_up_after_consumer_failure():
    batch = fixture_batch("valid")
    with pytest.raises(RuntimeError, match="fictional consumer failure"):
        with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
                max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
                budget=GenerationBudget(5)) as bundle:
            raise RuntimeError("fictional consumer failure")
    assert not bundle.parent.exists()


@pytest.mark.parametrize("case", ["valid", "existing", "file", "symlink", "stale", "budget"])
def test_closed_retained_batch_publication(tmp_path, case):
    from test_data_agent.io.transformation_batch import _publish_retained_test_batch
    batch = fixture_batch("valid")
    destination = tmp_path / "output"
    original = {}
    if case == "existing":
        destination.mkdir()
        (destination / "keep.txt").write_bytes(b"fictional unrelated file")
        original = {path.name: path.read_bytes() for path in destination.iterdir()}
    elif case == "file":
        destination.write_bytes(b"fictional unrelated file")
    elif case == "symlink":
        (tmp_path / "untouched").mkdir()
        destination.symlink_to(tmp_path / "untouched")
    arguments = dict(expected_snapshot_sha256="0" * 64 if case == "stale" else batch.snapshot_sha256,
        max_total_bytes=32768, max_review_bytes=8192,
        max_output_bytes=1 if case == "budget" else 8192, budget=GenerationBudget(5))
    if case != "valid":
        with pytest.raises(ValueError):
            _publish_retained_test_batch(batch, destination, **arguments)
        if case == "existing":
            assert {path.name: path.read_bytes() for path in destination.iterdir()} == original
        elif case == "file":
            assert destination.read_bytes() == b"fictional unrelated file"
        elif case == "symlink":
            assert destination.is_symlink() and not list((tmp_path / "untouched").iterdir())
        else:
            assert not destination.exists()
    else:
        manifest = _publish_retained_test_batch(batch, destination, **arguments)
        assert (destination / "manifest.json").read_bytes() == manifest
        assert json.loads(manifest)["snapshot_sha256"] == batch.snapshot_sha256
        assert (destination / "input-0.csv").read_bytes() == b"key\n11\n12\n"
        assert (destination / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"
    assert not list(tmp_path.glob(".output.*"))


def test_closed_batch_manifest_charged_to_output_budget():
    batch = fixture_batch("valid")
    with pytest.raises(TransformationLimitError):
        with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
                max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=30,
                budget=GenerationBudget(5)):
            pytest.fail("over-budget bundle returned")


@pytest.mark.parametrize("limit", [1, 17, 18])
def test_batch_output_diagnostic_uses_shared_counter(limit):
    batch = fixture_batch("valid")
    with pytest.raises(TransformationLimitError) as caught:
        execute_batch(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=limit,
            budget=GenerationBudget(5))
    error = caught.value
    assert error.origin == "batch_output_run"
    assert error.limit == limit and error.amount > limit and error.unit == "bytes"
    assert error.code == "limit_exceeded"
    assert error.run_setting == "execute_batch(max_output_bytes=...)"


def test_closed_batch_input_limit_includes_validation():
    batch = fixture_batch("valid")
    payload_bytes = sum(len(part.payload) for request in batch.requests for part in request.parts)
    with pytest.raises(TransformationLimitError):
        prepare_batch(batch.requests, batch.validation_yaml,
            max_total_bytes=payload_bytes, max_review_bytes=8192, budget=GenerationBudget(5))


def test_closed_batch_expired_explicit_clock_budget():
    batch = fixture_batch("valid")
    ticks = iter((0.0, 2.0))
    budget = GenerationBudget(1, clock=lambda: next(ticks))
    with pytest.raises(GenerationLimitError):
        execute_batch(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192, budget=budget)


@pytest.mark.parametrize("fallback", [False, True])
def test_batch_rejects_string_preservation_at_execution(fallback):
    requests = []
    for entity in ("parents", "children"):
        source = SnapshotPart("source", entity, b"key,label\nfictional-code-a,fictional-label-a\n")
        preserve = {"action": "preserve", "authorization_ref": "fictional-local",
                    "comment": "Fictional operator evidence"}
        action = ({"action": "substitute", "mapping": {"kind": "domain", "name": "shared"},
                   "unmatched": preserve} if fallback else preserve)
        policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
            "schema_fingerprint": "0" * 64, "domains": ([{"name": "shared", "mapping": {
                "kind": "inline", "entries": [{"original": ["fictional-code-a"],
                                                 "replacement": ["fictional-code-b"]}]}}] if fallback else []),
            "fields": [{"entity": entity, "field": "key", "sensitivity": "non_sensitive",
                        "behavior": action},
                       {"entity": entity, "field": "label", "sensitivity": "non_sensitive",
                        "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                            {"original": ["fictional-label-a"], "replacement": ["fictional-label-b"]}]}}}]})
        profile = _profile_transformation_source(source, policy, max_bytes=8192, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
        requests.append(prepare_csv_review_request(yaml.safe_dump(policy.model_dump(mode="json")).encode(),
            source, (), max_total_bytes=16384, max_review_bytes=8192, budget=GenerationBudget(5)))
    spec = {"schema_version": "1.1", "entities": [
        {"name": entity, "row_count": 1, "fields": [
            {"name": name, "data_type": "string"} for name in ("key", "label")]}
        for entity in ("parents", "children")]}
    batch = prepare_batch(tuple(requests), yaml.safe_dump(spec).encode(),
        max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5))
    with pytest.raises(TransformationBatchError) as caught:
        execute_batch(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192, budget=GenerationBudget(5))
    assert caught.value.__context__ is None
    assert str(caught.value) == "invalid transformation batch"


@pytest.mark.parametrize("case", ["valid", "stale", "small", "combined"])
def test_common_batch_review_is_bound_bounded_and_not_authority(case):
    batch = fixture_batch("valid")
    if case == "stale":
        batch = replace(batch, validation_yaml=batch.validation_yaml + b"\n")
    arguments = dict(max_total_bytes=32768, max_review_bytes=8 if case == "small" else 8192,
                     budget=GenerationBudget(5))
    if case == "combined":
        arguments["max_review_bytes"] = max(len(request.review) for request in batch.requests)
    if case != "valid":
        with pytest.raises(TransformationBatchError):
            review_batch(batch, **arguments)
        return
    review = review_batch(batch, **arguments)
    payload = json.loads(review)
    assert payload["snapshot_sha256"] == batch.snapshot_sha256
    assert payload["input_count"] == 2 and payload["relationship_count"] == 1
    assert payload["status"] == "review_only"
    assert not payload["approved"] and payload["preservation_supported"]
    assert not payload["public_execution_supported"]
    assert b"shared" not in review and b'"original":' not in review and b'"replacement":' not in review
    assert [item["local_plan"] for item in payload["inputs"]] == [
        json.loads(request.review) for request in batch.requests]
    assert payload["relationships"] == [{"parent_input": 0, "parent_field": "key",
                                          "child_input": 1, "child_field": "key"}]


@pytest.mark.parametrize("payload", [
    b'{"approved":true}',
    b'{"version":1,"snapshot_sha256":"incorrect"}',
    b'{"version":1,"kind":"transformation_batch","snapshot_sha256":"incorrect"}',
    b'{"version":true,"kind":"transformation_batch","snapshot_sha256":"incorrect"}',
    b"x" * 256,
])
def test_batch_confirmation_rejects_wrong_scope_or_digest(tmp_path, payload):
    batch = fixture_batch("valid")
    receipt = tmp_path / "receipt.json"
    receipt.write_bytes(payload)
    receipt.chmod(0o600)
    with pytest.raises(LocalReceiptError) as caught:
        verify_batch_receipt(batch, receipt, max_total_bytes=32768,
            max_review_bytes=8192, budget=GenerationBudget(5))
    assert caught.value.__context__ is None
    assert str(caught.value) == "local batch confirmation failed"


@pytest.mark.parametrize("controlling_tty", [False, True])
@pytest.mark.parametrize("preservation", [None, "direct", "fallback"])
def test_batch_confirmation_requires_real_controlling_tty(tmp_path, controlling_tty, preservation):
    receipt = tmp_path / "receipt.json"
    save_fictional_batch_profile(tmp_path, preservation)
    program = (
        "import os,sys; "
        + ("import fcntl,termios; fcntl.ioctl(0,termios.TIOCSCTTY,0); "
           "os.tcsetpgrp(0,os.getpgrp()); " if controlling_tty else "")
        + "from pathlib import Path; "
        "from test_data_agent.io.transformation_batch_receipt import issue_batch_receipt; "
        "from test_data_agent.core.limits import GenerationBudget; "
        "from test_data_agent.io.transformation_batch_profile import load_batch_profile; "
        "batch=load_batch_profile(Path(sys.argv[2]).parent,'batch.yaml',"
        "max_total_bytes=32768,max_review_bytes=8192,budget=GenerationBudget(20)); "
        "issue_batch_receipt(batch,Path(sys.argv[2]),max_total_bytes=32768,"
        "max_review_bytes=8192,budget=GenerationBudget(20))"
    )
    command = [sys.executable, "-c", program, str(Path(__file__).resolve()), str(receipt)]
    if not controlling_tty:
        result = subprocess.run(command, input="APPROVE\n", text=True,
            capture_output=True, start_new_session=True, timeout=25)
        assert result.returncode != 0
        assert "local batch confirmation failed" in result.stderr
        assert not receipt.exists()
        return
    transcript = run_controlling_confirmation(command)
    assert receipt.stat().st_mode & 0o077 == 0
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                               max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(max_total_bytes=32768, max_review_bytes=8192)
    verify_batch_receipt(batch, receipt, **arguments, budget=GenerationBudget(5))
    original_receipt = receipt.read_bytes()
    payload = json.loads(original_receipt)
    assert payload["version"] == 2 and len(original_receipt) < 256
    payload["review_sha256"] = "0" * 64
    receipt.write_text(json.dumps(payload, separators=(",", ":")))
    with pytest.raises(LocalReceiptError):
        verify_batch_receipt(batch, receipt, **arguments, budget=GenerationBudget(5))
    receipt.write_bytes(original_receipt)
    assert b'"local_plan"' in transcript and b'"relationships"' in transcript
    assert b"shared" not in transcript and b'"original":' not in transcript
    assert b"fictional-label-a" not in transcript
    reordered = prepare_batch(tuple(reversed(batch.requests)), batch.validation_yaml,
                              **arguments, budget=GenerationBudget(5), profile_yaml=batch.profile_yaml)
    with pytest.raises(LocalReceiptError):
        verify_batch_receipt(reordered, receipt, **arguments, budget=GenerationBudget(5))
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            **arguments, max_output_bytes=8192, budget=GenerationBudget(5),
            receipt_path=receipt if preservation else None) as bundle:
        manifest = json.loads((bundle / "manifest.json").read_bytes())
        assert manifest["snapshot_sha256"] == batch.snapshot_sha256
        assert manifest["origin"] == "transformed_mixed"
        assert "not anonymized" in manifest["privacy_notice"]
        assert "fictional-label-a" not in json.dumps(manifest)
        assert [item["original_cells"] for item in manifest["provenance"]] == (
            [2, 3] if preservation else [0, 0])
        assert [item["replacement_cells"] for item in manifest["provenance"]] == [2, 3]
        if preservation:
            assert (bundle / "input-0.csv").read_bytes() == (
                b"key,label\n11,fictional-label-a\n12,fictional-label-a\n")
            assert (bundle / "input-1.csv").read_bytes() == (
                b"key,label\n11,fictional-label-a\n12,fictional-label-a\n11,fictional-label-a\n")
        else:
            assert (bundle / "input-0.csv").read_bytes() == b"key\n11\n12\n"
            assert (bundle / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"
    assert not bundle.parent.exists()
    if preservation:
        with pytest.raises(TransformationBatchError):
            execute_batch(batch, expected_snapshot_sha256=batch.snapshot_sha256,
                **arguments, max_output_bytes=8192, budget=GenerationBudget(5))
        from test_data_agent.io.transformation_execute import replace_csv_snapshot, TransformationExecutionError
        with pytest.raises(TransformationExecutionError):
            replace_csv_snapshot(batch.requests[0], **arguments,
                max_output_bytes=8192, budget=GenerationBudget(5), receipt_path=receipt)
    with pytest.raises(LocalReceiptError):
        verify_batch_receipt(replace(batch, validation_yaml=batch.validation_yaml + b"\n"),
                             receipt, **arguments, budget=GenerationBudget(5))
    receipt.chmod(0o644)
    with pytest.raises(LocalReceiptError):
        verify_batch_receipt(batch, receipt, **arguments, budget=GenerationBudget(5))


def run_controlling_confirmation(command):
    master, slave = pty.openpty()
    process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave,
                               start_new_session=True)
    os.close(slave)
    transcript = bytearray()
    approved = False
    deadline = time.monotonic() + 25
    try:
        while process.poll() is None:
            assert time.monotonic() < deadline
            if select.select([master], [], [], 0.1)[0]:
                try:
                    transcript.extend(os.read(master, 16384))
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    break
                if not approved and b"Type APPROVE" in transcript:
                    os.write(master, b"APPROVE\n")
                    approved = True
        process.wait(timeout=5)
        assert approved and process.returncode == 0, bytes(transcript)
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    return bytes(transcript)


@pytest.mark.parametrize("case", ["keep", "edit_actions", "blank", "cli_blank", "preserve", "cancel", "noninteractive"])
def test_closed_common_decision_wizard(tmp_path, case):
    save_fictional_batch_profile(tmp_path, "direct" if case == "preserve" else None)
    if case in {"blank", "cli_blank"}:
        for index in range(2):
            (tmp_path / f"policy-{index}.yaml").unlink()
        validation = yaml.safe_load((tmp_path / "validation.yaml").read_bytes())
        validation["relationships"] = []
        (tmp_path / "validation.yaml").write_text(yaml.safe_dump(validation))
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    program = '''
import sys, json
from pathlib import Path
import yaml
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.io.transformation_batch_profile import BatchProfile, temporary_batch_decisions, save_batch_profile, load_batch_profile
from test_data_agent.io.transformation_batch import temporary_batch_publication, TransformationBatchError
root = Path(sys.argv[1])
profile = BatchProfile.model_validate(yaml.safe_load((root / "batch.yaml").read_bytes()))
try:
    with temporary_batch_decisions(root, profile, input_stream=sys.stdin, output_stream=sys.stdout,
            max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(20),
            edit_actions=sys.argv[2] in {"edit_actions", "blank"},
            create_csv_policies=sys.argv[2] == "blank", seed=7) as (created, batch):
        assert not (created / "receipt.json").exists()
        if sys.argv[2] == "blank":
            retained = save_batch_profile(root, "saved", batch, max_total_bytes=32768,
                max_review_bytes=8192, budget=GenerationBudget(5))
            assert retained.snapshot_sha256 != batch.snapshot_sha256
        try:
            with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
                    max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
                    budget=GenerationBudget(5)) as bundle:
                assert sys.argv[2] != "preserve"
                assert (bundle / "input-0.csv").read_bytes() == b"key\\n11\\n12\\n"
                assert (bundle / "input-1.csv").read_bytes() == b"key\\n11\\n12\\n11\\n"
            assert not bundle.parent.exists()
        except TransformationBatchError:
            assert sys.argv[2] == "preserve"
            print("FICTIONAL_PRESERVE_REQUIRES_APPROVAL")
    assert not created.exists()
    if sys.argv[2] == "blank":
        reopened = load_batch_profile(root, "saved/batch.yaml", max_total_bytes=32768,
            max_review_bytes=8192, budget=GenerationBudget(5))
        assert reopened == retained
        with temporary_batch_publication(reopened, expected_snapshot_sha256=reopened.snapshot_sha256,
                max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
                budget=GenerationBudget(5)) as bundle:
            assert (bundle / "input-1.csv").read_bytes() == b"key\\n11\\n12\\n11\\n"
    print("FICTIONAL_WIZARD_COMPLETED")
except TransformationBatchError as error:
    assert error.__context__ is None
    assert str(error) == "common profile decisions not saved"
    print("FICTIONAL_WIZARD_REJECTED")
'''
    if case == "cli_blank":
        program = '''
import sys
from pathlib import Path
from test_data_agent.cli_transformation_candidate import _candidate_common_main
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.io.transformation_batch_profile import load_batch_profile
root = Path(sys.argv[1])
limits = ["--max-total-input-bytes", "32768", "--max-review-bytes", "8192"]
assert _candidate_common_main(["create", str(root), "batch.yaml", "saved", *limits,
    "--create-csv-policies", "--seed", "7", "--decide", "--edit-actions"]) == 0
assert not (root / "receipt.json").exists()
batch = load_batch_profile(root, "saved/batch.yaml", max_total_bytes=32768,
    max_review_bytes=8192, budget=GenerationBudget(5))
for operation in ("review", "validate", "execute"):
    arguments = [operation, str(root), "saved/batch.yaml", *limits, "--max-output-bytes", "8192"]
    if operation != "review":
        arguments += ["--snapshot-sha256", batch.snapshot_sha256]
    if operation == "execute":
        arguments += ["--destination", "output"]
    assert _candidate_common_main(arguments) == 0
assert (root / "output" / "input-1.csv").read_bytes() == b"key\\n11\\n12\\n11\\n"
print("FICTIONAL_WIZARD_COMPLETED")
'''
    command = [sys.executable, "-c", program, str(tmp_path), case]
    if case == "noninteractive":
        result = subprocess.run(command, input="SAVE\n", text=True, capture_output=True, timeout=25)
        assert result.returncode == 0 and "FICTIONAL_WIZARD_REJECTED" in result.stdout
    else:
        responses = []
        for _ in range(2):
            for _ in range(2 if case == "preserve" else 1):
                responses.append((b"Decision [", b"non_sensitive\n"))
                if case in {"edit_actions", "blank", "cli_blank"}:
                    mapping = ({"kind": "domain", "name": "shared"} if case == "edit_actions" else
                        {"kind": "inline", "entries": [
                            {"original": [1], "replacement": [11]},
                            {"original": [2], "replacement": [12]}]})
                    responses.extend(((b"Action [", b"substitute\n"),
                        (b"Mapping JSON (hidden):", json.dumps(mapping).encode() + b"\n"),
                        (b"Unmatched [", b"reject\n")))
            responses.append((b"Type SAVE to replace", b"SAVE\n"))
        responses.append((b"Type SAVE for the common profile", b"CANCEL\n" if case == "cancel" else b"SAVE\n"))
        master, slave = pty.openpty()
        process = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
        os.close(slave)
        transcript, pending = bytearray(), bytearray()
        deadline = time.monotonic() + 25
        try:
            while process.poll() is None:
                assert time.monotonic() < deadline
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(master, 16384)
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        break
                    transcript.extend(chunk)
                    pending.extend(chunk)
                    if responses and responses[0][0] in pending:
                        prompt, answer = responses.pop(0)
                        del pending[:pending.index(prompt) + len(prompt)]
                        os.write(master, answer)
            process.wait(timeout=5)
            assert process.returncode == 0, bytes(transcript)
            expected = b"FICTIONAL_WIZARD_REJECTED" if case == "cancel" else b"FICTIONAL_WIZARD_COMPLETED"
            assert expected in transcript and not responses, bytes(transcript)
            assert b"Type APPROVE" not in transcript and b'"original":' not in transcript
            assert b"fictional-label-a" not in transcript
            if case == "preserve":
                assert b"FICTIONAL_PRESERVE_REQUIRES_APPROVAL" in transcript
        finally:
            os.close(master)
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()} == before
    if case in {"blank", "cli_blank"}:
        assert {path.name for path in (tmp_path / "saved").iterdir()} == {
            "batch.yaml", "validation.yaml", "policy-0.yaml", "policy-1.yaml"}


@pytest.mark.parametrize("case", ["valid", "missing_seed", "policy_collision", "policy_traversal", "no_action_decisions"])
def test_blank_common_policy_drafts(tmp_path, case):
    from test_data_agent.io.transformation_batch_profile import (
        BatchProfile, temporary_batch_profile, temporary_batch_decisions,
    )
    import io

    save_fictional_batch_profile(tmp_path)
    for index in range(2):
        (tmp_path / f"policy-{index}.yaml").unlink()
    raw = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    if case == "policy_collision":
        raw["inputs"][0]["policy"] = "source-0.csv"
    elif case == "policy_traversal":
        raw["inputs"][0]["policy"] = "../outside.yaml"
    profile = BatchProfile.model_validate(raw)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    arguments = dict(max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5),
                     create_csv_policies=True, seed=None if case == "missing_seed" else 7)
    if case == "no_action_decisions":
        with pytest.raises(TransformationBatchError, match="requires explicit action decisions"):
            with temporary_batch_decisions(tmp_path, profile, input_stream=io.StringIO(),
                    output_stream=io.StringIO(), **arguments):
                pytest.fail("missing decisions accepted")
    elif case != "valid":
        with pytest.raises(TransformationBatchError) as caught:
            with temporary_batch_profile(tmp_path, profile, **arguments):
                pytest.fail("invalid draft accepted")
        assert caught.value.__context__ is None
    else:
        with temporary_batch_profile(tmp_path, profile, **arguments) as (root, batch):
            for item in profile.inputs:
                draft = yaml.safe_load((root / item.policy).read_bytes())
                assert draft["seed"] == 7
                assert all(field["sensitivity"] == "unknown" and field["behavior"] == {"action": "drop"}
                           for field in draft["fields"])
                assert not draft.get("domains")
            assert not json.loads(review_batch(batch, max_total_bytes=32768,
                max_review_bytes=8192, budget=GenerationBudget(5)))["approved"]
        assert not root.exists()
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("case", ["valid", "existing", "stale_source", "traversal", "budget"])
def test_closed_configuration_only_profile_publication(tmp_path, case):
    from test_data_agent.io.transformation_batch_profile import save_batch_profile

    save_fictional_batch_profile(tmp_path)
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    destination = "saved"
    if case == "existing":
        (tmp_path / "saved").mkdir()
        (tmp_path / "saved" / "owned.txt").write_bytes(b"fictional user-owned file")
    elif case == "stale_source":
        (tmp_path / "source-0.csv").write_bytes(b"key\n1\n3\n")
    elif case == "traversal":
        destination = "../outside"
    original = {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()}
    arguments = dict(max_total_bytes=1 if case == "budget" else 32768, max_review_bytes=8192,
                     budget=GenerationBudget(5))
    if case != "valid":
        with pytest.raises(TransformationLimitError if case == "budget" else TransformationBatchError) as caught:
            save_batch_profile(tmp_path, destination, batch, **arguments)
        if case != "budget":
            assert caught.value.__context__ is None
        if case == "existing":
            assert (tmp_path / "saved" / "owned.txt").read_bytes() == b"fictional user-owned file"
        else:
            assert not (tmp_path / "saved").exists()
    else:
        saved = save_batch_profile(tmp_path, destination, batch, **arguments)
        assert saved.snapshot_sha256 != batch.snapshot_sha256
        assert saved.requests == batch.requests
        assert {path.name for path in (tmp_path / "saved").iterdir()} == {
            "batch.yaml", "validation.yaml", "policy-0.yaml", "policy-1.yaml"}
        loaded = load_batch_profile(tmp_path, "saved/batch.yaml", max_total_bytes=32768,
                                   max_review_bytes=8192, budget=GenerationBudget(5))
        assert loaded == saved
        assert not json.loads(review_batch(saved, max_total_bytes=32768,
            max_review_bytes=8192, budget=GenerationBudget(5)))["approved"]
        with temporary_batch_publication(loaded, expected_snapshot_sha256=loaded.snapshot_sha256,
                max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
                budget=GenerationBudget(5)) as bundle:
            assert (bundle / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"
        assert not bundle.parent.exists()
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()} == original
    assert not list(tmp_path.glob(".saved.*"))


@pytest.mark.parametrize("growth", [1, 2000])
def test_profile_save_rejects_source_growth_before_payload_read(tmp_path, monkeypatch, growth):
    from contextlib import contextmanager
    from test_data_agent.io import mapping_snapshot
    from test_data_agent.io.transformation_batch_profile import save_batch_profile

    save_fictional_batch_profile(tmp_path)
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    source = tmp_path / "source-0.csv"
    source.write_bytes(source.read_bytes() + b"1" * growth)
    original_open = mapping_snapshot.open_regular_file
    reads = []

    class ObservedFile:
        def __init__(self, handle):
            self.handle = handle

        def fileno(self):
            return self.handle.fileno()

        def read(self, size):
            reads.append(size)
            return self.handle.read(size)

    @contextmanager
    def observed_open(path):
        with original_open(path) as handle:
            yield ObservedFile(handle) if path == source else handle

    monkeypatch.setattr(mapping_snapshot, "open_regular_file", observed_open)
    with pytest.raises(TransformationBatchError):
        save_batch_profile(tmp_path, "saved", batch, max_total_bytes=32768,
                           max_review_bytes=8192, budget=GenerationBudget(5))
    assert reads == []
    assert not (tmp_path / "saved").exists()
    assert not list(tmp_path.glob(".saved.*"))


@pytest.mark.parametrize("case", ["validate", "execute", "stale", "missing_digest", "receipt_escape", "review_receipt", "mutated"])
def test_shared_closed_workflow_review_consumer(tmp_path, case):
    from test_data_agent.io.transformation_batch_workflow import BatchWorkflowRequest, run_batch_workflow

    save_fictional_batch_profile(tmp_path)
    arguments = dict(root=tmp_path, profile="batch.yaml", max_total_bytes=32768,
                     max_review_bytes=8192, max_output_bytes=8192)
    review = run_batch_workflow(BatchWorkflowRequest(operation="review", **arguments), budget=GenerationBudget(5))
    assert review.status == "review_only" and review.summary_json is None
    assert review.review_json is not None and not json.loads(review.review_json)["approved"]
    snapshot = None if case == "missing_digest" else "0" * 64 if case == "stale" else review.snapshot_sha256
    operation = "review" if case == "review_receipt" else "validate" if case == "validate" else "execute"
    request = BatchWorkflowRequest(operation=operation, snapshot_sha256=snapshot,
        receipt="../outside.json" if case == "receipt_escape" else "receipt.json" if case == "review_receipt" else None,
        **arguments)
    if case == "mutated":
        request = request.model_copy(update={"operation": "fictional-private-token"})
    if case not in {"validate", "execute"}:
        with pytest.raises(TransformationBatchError) as caught:
            run_batch_workflow(request, budget=GenerationBudget(5))
        assert caught.value.__context__ is None
    else:
        result = run_batch_workflow(request, budget=GenerationBudget(5))
        assert result.status == f"closed_{'validation' if case == 'validate' else 'execution'}_completed"
        assert result.review_json is None and result.summary_json is not None
        summary = json.loads(result.summary_json)
        assert summary["snapshot_sha256"] == snapshot
        assert summary["origin"] == "transformed_mixed"
        assert "rows" not in summary and "not anonymized" in summary["privacy_notice"]


@pytest.mark.parametrize("case", ["validate", "execute", "stale", "missing_digest", "budget", "private_argument"])
def test_closed_common_cli_consumer(tmp_path, case):
    save_fictional_batch_profile(tmp_path)
    program = "import sys; from test_data_agent.cli_transformation_candidate import _candidate_batch_main; raise SystemExit(_candidate_batch_main(sys.argv[1:]))"
    base = [str(tmp_path), "batch.yaml", "--max-total-input-bytes", "32768",
            "--max-review-bytes", "8192", "--max-output-bytes", "8192"]
    command = [sys.executable, "-c", program]
    review = subprocess.run(command + ["review", *base], capture_output=True, text=True, timeout=25)
    assert review.returncode == 0, review.stderr
    payload = json.loads(review.stdout)
    assert payload["status"] == "review_only" and not payload["review"]["approved"]
    operation = "validate" if case == "validate" else "execute"
    arguments = base.copy()
    if case != "missing_digest":
        arguments.extend(("--snapshot-sha256", "0" * 64 if case == "stale" else payload["snapshot_sha256"]))
    if case == "budget":
        arguments[arguments.index("--max-output-bytes") + 1] = "1"
    elif case == "private_argument":
        arguments.extend(("--fictional-private-token", "fictional-private-value"))
    result = subprocess.run(command + [operation, *arguments], capture_output=True, text=True, timeout=25)
    assert "fictional-private" not in result.stdout + result.stderr
    if case in {"validate", "execute"}:
        assert result.returncode == 0, result.stderr
        completed = json.loads(result.stdout)
        assert completed["snapshot_sha256"] == payload["snapshot_sha256"]
        assert completed["summary"]["origin"] == "transformed_mixed"
    else:
        assert result.returncode != 0
        assert "no completion confirmed" in result.stdout + result.stderr or case in {"budget", "private_argument"}


@pytest.mark.parametrize("operation,destination", [("review", "output"), ("validate", "output"),
    ("execute", "../escape"), ("execute", "/absolute"), ("execute", "batch.yaml"),
    ("execute", "nested/output"), ("execute", "")])
def test_common_retained_destination_rejection(tmp_path, operation, destination):
    from test_data_agent.io.transformation_batch_workflow import BatchWorkflowRequest, run_batch_workflow
    save_fictional_batch_profile(tmp_path)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    request = BatchWorkflowRequest(operation=operation, root=tmp_path, profile="batch.yaml",
        snapshot_sha256=batch.snapshot_sha256, destination=destination,
        max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192)
    with pytest.raises(TransformationBatchError):
        run_batch_workflow(request, budget=GenerationBudget(5))
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("case", ["detached", "stale", "traversal", "existing", "unknown"])
def test_closed_common_cli_approval_rejects_untrusted_requests(tmp_path, case):
    save_fictional_batch_profile(tmp_path, "direct")
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    if case == "existing":
        (tmp_path / "receipt.json").write_bytes(b"fictional existing receipt")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    program = ("import sys; from test_data_agent.cli_transformation_candidate import _candidate_batch_approve_main; "
               "raise SystemExit(_candidate_batch_approve_main(sys.argv[1:]))")
    command = [sys.executable, "-c", program, str(tmp_path), "batch.yaml",
        "../fictional-private-marker" if case == "traversal" else "receipt.json",
        "--snapshot-sha256", "0" * 64 if case == "stale" else batch.snapshot_sha256,
        "--max-total-input-bytes", "32768", "--max-review-bytes", "8192"]
    if case == "unknown":
        command.extend(("--approved", "fictional-private-marker"))
    result = subprocess.run(command, input="APPROVE\n", text=True, capture_output=True,
                            start_new_session=True, timeout=25)
    assert result.returncode != 0
    assert "fictional-private-marker" not in result.stdout + result.stderr
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("case", ["valid", "blank", "missing_seed", "traversal", "piped_wizard", "unknown"])
@pytest.mark.parametrize("versioned", [False, True])
def test_closed_unified_common_cli_creation(tmp_path, case, versioned):
    save_fictional_batch_profile(tmp_path)
    if case in {"blank", "missing_seed"}:
        for index in range(2):
            (tmp_path / f"policy-{index}.yaml").unlink()
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    program = ("import sys; from test_data_agent.cli_transformation_candidate import _candidate_common_main; "
               f"raise SystemExit(_candidate_common_main(sys.argv[1:], versioned_output={versioned!r}))")
    command = [sys.executable, "-c", program]
    if versioned and os.environ.get("APA_TEST_ACTUAL_COMMON_CLI") == "1":
        command = [sys.executable, "-m", "test_data_agent.cli", "transform-batch"]
    limits = ["--max-total-input-bytes", "32768", "--max-review-bytes", "8192"]
    options = ["--create-csv-policies"] if case in {"blank", "missing_seed"} else []
    if versioned:
        options.extend(("--json", "--debug"))
    if case == "blank":
        options.extend(("--seed", "7"))
    if case == "piped_wizard":
        options.append("--decide")
    if case == "unknown":
        options.extend(("--approved", "fictional-private-marker"))
    result = subprocess.run(command + ["create", str(tmp_path), "batch.yaml",
        "../fictional-private-marker" if case == "traversal" else "saved", *limits, *options],
        input="SAVE\n", capture_output=True, text=True, timeout=25)
    assert "fictional-private-marker" not in result.stdout + result.stderr
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir() if path.is_file()} == before
    if case not in {"valid", "blank"}:
        assert result.returncode != 0 and not (tmp_path / "saved").exists()
        if versioned:
            error = json.loads(result.stdout)
            assert error["schema_version"] == "1.0" and error["ok"] is False
            assert error["error"]["command"] == "test-data-agent transform-batch"
        return
    assert result.returncode == 0, result.stderr
    created = json.loads(result.stdout)
    if versioned:
        assert created["schema_version"] == "1.0" and created["ok"] is True
        assert created["exit_code"] == 0 and created["status"] == "succeeded"
        created = created["result"]
    assert created["status"] == "common_configuration_saved" and created["approved"] is False
    assert not (tmp_path / "receipt.json").exists()
    for operation in (["review", "validate", "execute"] if case == "valid" else ["review"]):
        arguments = [operation, str(tmp_path), "saved/batch.yaml", *limits, "--max-output-bytes", "8192"]
        if versioned:
            arguments.append("--json")
        if operation != "review":
            arguments.extend(("--snapshot-sha256", created["snapshot_sha256"]))
        if operation == "execute":
            arguments.extend(("--destination", "output"))
        consumed = subprocess.run(command + arguments, capture_output=True, text=True, timeout=25)
        assert consumed.returncode == 0, consumed.stderr
        payload = json.loads(consumed.stdout)
        if versioned:
            assert payload["schema_version"] == "1.0" and payload["ok"] is True
            payload = payload["result"]
        assert payload["snapshot_sha256"] == created["snapshot_sha256"]
    if case == "valid":
        assert (tmp_path / "output" / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"


@pytest.mark.parametrize("position", ["root", "command", "operation"])
def test_isolated_common_cli_runtime_flags(position):
    if os.environ.get("APA_TEST_ACTUAL_COMMON_CLI") != "1":
        pytest.skip("requires isolated actual CLI composition")
    arguments = ["transform-batch", "create", "/private/tmp", "nonexistent.yaml", "saved",
                 "--max-total-input-bytes", "32768", "--max-review-bytes", "8192"]
    index = {"root": 0, "command": 1, "operation": len(arguments)}[position]
    arguments[index:index] = ["--json", "--debug"]
    result = subprocess.run([sys.executable, "-m", "test_data_agent.cli", *arguments],
        capture_output=True, text=True, timeout=25)
    assert result.returncode == 2 and not result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0" and payload["ok"] is False
    assert payload["error"]["command"] == "test-data-agent transform-batch"


def test_isolated_common_contract_inventory():
    if (os.environ.get("APA_TEST_ACTUAL_COMMON_CLI") != "1"
            or os.environ.get("APA_TEST_ACTUAL_COMMON_MCP") != "1"):
        pytest.skip("requires isolated actual CLI/MCP composition")
    from scripts.contract_fixtures import _cli_parser_surface, _mcp_tool_contract
    from test_data_agent.mcp_generator_server import mcp

    fixtures = Path("tests/fixtures/contracts")
    expected = json.loads((fixtures / "cli-parser-surface.json").read_bytes())
    actual = _cli_parser_surface()
    assert set(actual["commands"]) == set(expected["commands"]) | {"transform-batch"}
    assert {key: value for key, value in actual.items() if key != "commands"} == {
        key: value for key, value in expected.items() if key != "commands"}
    tools = _mcp_tool_contract(mcp)
    assert tools == json.loads(
        (fixtures / "mcp-generator-tools.json").read_bytes())
    common = [tool for tool in tools if tool["name"] == "common_transformation"]
    assert len(common) == 1
    schema = common[0]["input_schema"]
    assert set(schema["properties"]) == {
        "operation", "profile", "max_total_bytes", "max_review_bytes", "max_output_bytes",
        "snapshot_sha256", "receipt", "destination"}
    assert set(schema["required"]) == {
        "operation", "profile", "max_total_bytes", "max_review_bytes", "max_output_bytes"}
    assert schema["properties"]["operation"]["enum"] == ["review", "validate", "execute"]


@pytest.mark.parametrize("preservation", [None, "direct", "fallback"])
@pytest.mark.parametrize("retained", [False, True])
def test_closed_common_mcp_stdio_consumer(tmp_path, preservation, retained):
    import asyncio
    from datetime import timedelta
    from importlib.metadata import version
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    save_fictional_batch_profile(tmp_path, preservation)
    profile = "batch.yaml"
    if preservation:
        from test_data_agent.io.transformation_batch_profile import save_batch_profile
        original = load_batch_profile(tmp_path, profile, max_total_bytes=32768,
                                      max_review_bytes=8192, budget=GenerationBudget(5))
        save_batch_profile(tmp_path, "saved", original, max_total_bytes=32768,
                           max_review_bytes=8192, budget=GenerationBudget(5))
        profile = "saved/batch.yaml"
        issuer = (
            "import os,sys,fcntl,termios; from pathlib import Path; "
            "fcntl.ioctl(0,termios.TIOCSCTTY,0); os.tcsetpgrp(0,os.getpgrp()); "
            "from test_data_agent.cli_transformation_candidate import _candidate_batch_approve_main; "
            "raise SystemExit(_candidate_batch_approve_main(sys.argv[1:]))"
        )
        actual_cli = os.environ.get("APA_TEST_ACTUAL_COMMON_CLI") == "1"
        if actual_cli:
            issuer = (
                "import os,sys,fcntl,termios,runpy; "
                "fcntl.ioctl(0,termios.TIOCSCTTY,0); os.tcsetpgrp(0,os.getpgrp()); "
                "sys.argv[1:1]=['transform-batch','approve']; "
                "runpy.run_module('test_data_agent.cli',run_name='__main__')"
            )
        saved = load_batch_profile(tmp_path, profile, max_total_bytes=32768,
                                   max_review_bytes=8192, budget=GenerationBudget(5))
        transcript = run_controlling_confirmation([sys.executable, "-c", issuer, str(tmp_path),
            profile, "receipt.json", "--snapshot-sha256", saved.snapshot_sha256,
            "--max-total-input-bytes", "32768", "--max-review-bytes", "8192"])
        assert b"fictional-label-a" not in transcript
        if actual_cli:
            assert b'"schema_version": "1.0"' in transcript
            assert b'"local_batch_receipt_created"' in transcript
    before = {str(path.relative_to(tmp_path)): path.read_bytes()
              for path in tmp_path.rglob("*") if path.is_file()}
    batch = load_batch_profile(tmp_path, profile, max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    if preservation:
        cli_program = (
            "import sys; from test_data_agent.cli_transformation_candidate import _candidate_batch_main; "
            "raise SystemExit(_candidate_batch_main(sys.argv[1:]))"
        )
        cli_arguments = [str(tmp_path), profile, "--max-total-input-bytes", "32768",
            "--max-review-bytes", "8192", "--max-output-bytes", "8192",
            "--snapshot-sha256", batch.snapshot_sha256]
        cli_command = ([sys.executable, "-m", "test_data_agent.cli", "transform-batch"]
            if actual_cli else [sys.executable, "-c", cli_program])
        for supplied_receipt in (False, True):
            result = subprocess.run([*cli_command, "execute", *cli_arguments,
                *(["--destination", "output-cli"] if retained else []),
                *(["--receipt", "receipt.json"] if supplied_receipt else [])],
                capture_output=True, text=True, timeout=25)
            assert "fictional-label-a" not in result.stdout + result.stderr
            assert (result.returncode == 0) is supplied_receipt
            if supplied_receipt:
                payload = json.loads(result.stdout)
                if actual_cli:
                    assert payload["schema_version"] == "1.0" and payload["ok"] is True
                    payload = payload["result"]
                summary = payload["summary"]
                assert summary["snapshot_sha256"] == batch.snapshot_sha256
                assert [item["original_cells"] for item in summary["provenance"]] == [2, 3]
                if retained:
                    assert payload["status"] == "closed_publication_completed"
    program = (
        "import sys; from pathlib import Path; "
        "from test_data_agent.mcp_transformation_candidate import _create_test_batch_mcp; "
        "from test_data_agent.mcp_generator_transport import run_bounded_generator_mcp; "
        "from test_data_agent.mcp_generator_server import _new_transport_work_budget; "
        "run_bounded_generator_mcp(_create_test_batch_mcp(Path(sys.argv[1])),"
        "max_payload_bytes=65536,request_context_factory=_new_transport_work_budget)"
    )

    async def invoke():
        actual_mcp = os.environ.get("APA_TEST_ACTUAL_COMMON_MCP") == "1"
        environment = dict(os.environ)
        environment["TEST_DATA_AGENT_WORKSPACE_ROOT"] = str(tmp_path)
        server_args = (["-m", "test_data_agent.mcp_generator_server"] if actual_mcp
                       else ["-c", program, str(tmp_path)])
        parameters = StdioServerParameters(command=sys.executable, args=server_args, env=environment)
        async with stdio_client(parameters) as (reader, writer):
            timeout = 15 if version("mcp").split(".")[0] == "2" else timedelta(seconds=15)
            async with ClientSession(reader, writer, read_timeout_seconds=timeout) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = [tool.name for tool in tools.tools]
                if actual_mcp:
                    assert len(names) == 13 and {"profile_csv", "generate_dataset", "execute_transformation"} <= set(names)
                    rejected = await session.call_tool("profile_csv", {"fictional-private-marker": True})
                    assert rejected.model_dump(by_alias=True)["isError"]
                    assert "fictional-private-marker" not in rejected.model_dump_json()
                    profiled = await session.call_tool("profile_csv", {
                        "input_path": "source-0.csv", "output_path": "output-profile.json"})
                    assert not profiled.model_dump(by_alias=True)["isError"]
                    assert "fictional-label-a" not in profiled.model_dump_json()
                    assert (tmp_path / "output-profile.json").is_file()
                else:
                    assert names == ["common_transformation"]
                schema = next(tool for tool in tools.tools if tool.name == "common_transformation").model_dump(by_alias=True)["inputSchema"]
                assert "root" not in schema["properties"] and "approved" not in schema["properties"]
                arguments = dict(profile=profile, max_total_bytes=32768,
                                 max_review_bytes=8192, max_output_bytes=8192)
                for operation in ("review", "validate", "execute"):
                    result = await session.call_tool("common_transformation", dict(
                        **arguments, operation=operation,
                        **({"snapshot_sha256": batch.snapshot_sha256,
                            **({"destination": "output-mcp"} if retained and operation == "execute" else {}),
                            **({"receipt": "receipt.json"} if preservation else {})}
                           if operation != "review" else {})))
                    assert not result.model_dump(by_alias=True)["isError"]
                    assert batch.snapshot_sha256 in result.model_dump_json()
                    assert "fictional-label-a" not in result.model_dump_json()
                if preservation:
                    result = await session.call_tool("common_transformation", {
                        **arguments, "operation": "execute", "snapshot_sha256": batch.snapshot_sha256})
                    assert result.model_dump(by_alias=True)["isError"]
                for extra in ({"snapshot_sha256": "0" * 64}, {"receipt": "../fictional-private-marker"},
                              {"profile": "../fictional-private-marker"}, {"approved": True},
                              {"destination": "../fictional-private-marker"},
                              {"profile": {"fictional-private-marker": "invalid"}}):
                    result = await session.call_tool("common_transformation", {
                        **arguments, "operation": "execute", "snapshot_sha256": batch.snapshot_sha256, **extra})
                    assert result.model_dump(by_alias=True)["isError"]
                    assert "fictional-private-marker" not in result.model_dump_json()

    asyncio.run(invoke())
    if retained:
        for directory in (["output-cli", "output-mcp"] if preservation else ["output-mcp"]):
            bundle = tmp_path / directory
            manifest = json.loads((bundle / "manifest.json").read_bytes())
            assert manifest["snapshot_sha256"] == batch.snapshot_sha256
            for index, keys in enumerate(([11, 12], [11, 12, 11])):
                expected = ("key,label\n" + "".join(f"{key},fictional-label-a\n" for key in keys)
                            if preservation else "key\n" + "".join(f"{key}\n" for key in keys))
                assert (bundle / f"input-{index}.csv").read_text() == expected
    assert {str(path.relative_to(tmp_path)): path.read_bytes()
            for path in tmp_path.rglob("*") if path.is_file()
            and not path.relative_to(tmp_path).parts[0].startswith("output-")} == before


def save_fictional_batch_profile(root, preservation=None):
    batch = fixture_batch("valid")
    entries = []
    validation = yaml.safe_load(batch.validation_yaml)
    for index, request in enumerate(batch.requests):
        source = next(part for part in request.parts if part.kind == "source")
        policy = next(part for part in request.parts if part.kind == "policy")
        policy_payload = policy.payload
        if preservation:
            keys = source.payload.decode().splitlines()[1:]
            source = SnapshotPart("source", source.name, ("key,label\n" + "".join(
                f"{key},fictional-label-a\n" for key in keys)).encode())
            raw = yaml.safe_load(policy.payload)
            behavior = {"action": "preserve", "authorization_ref": "fictional-local",
                        "comment": "Fictional repeated business label reviewed locally"}
            if preservation == "fallback":
                behavior = {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                    {"original": ["fictional-unseen"], "replacement": ["fictional-label-b"]}]},
                    "unmatched": behavior}
            raw["fields"].append({"entity": source.name, "field": "label",
                                  "sensitivity": "non_sensitive", "behavior": behavior})
            updated = BehaviorPolicy.model_validate(raw)
            evidence = _profile_transformation_source(source, updated,
                max_bytes=32768, budget=GenerationBudget(5))
            updated = updated.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
            policy_payload = yaml.safe_dump(updated.model_dump(mode="json")).encode()
            validation["entities"][index]["fields"].append({"name": "label", "data_type": "string"})
        source_path, policy_path = f"source-{index}.csv", f"policy-{index}.yaml"
        (root / source_path).write_bytes(source.payload)
        (root / policy_path).write_bytes(policy_payload)
        entries.append({"entity": source.name, "source": source_path, "policy": policy_path})
    (root / "validation.yaml").write_text(yaml.safe_dump(validation))
    (root / "batch.yaml").write_text(yaml.safe_dump({"schema_version": "0.1",
        "validation": "validation.yaml", "inputs": entries}))


@pytest.mark.parametrize("case", ["valid", "whitespace", "traversal", "symlink", "unknown", "budget",
                                 "duplicate", "malformed"])
def test_saved_batch_profile_capture(tmp_path, case):
    save_fictional_batch_profile(tmp_path)
    arguments = dict(max_total_bytes=32768, max_review_bytes=8192)
    original = load_batch_profile(tmp_path, "batch.yaml", **arguments, budget=GenerationBudget(5))
    if case == "traversal":
        profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
        profile["inputs"][0]["source"] = "../outside.csv"
        (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    elif case == "symlink":
        (tmp_path / "source-0.csv").rename(tmp_path / "actual.csv")
        (tmp_path / "source-0.csv").symlink_to(tmp_path / "actual.csv")
    elif case == "unknown":
        with (tmp_path / "batch.yaml").open("a") as handle:
            handle.write("approved: true\n")
    elif case == "budget":
        arguments["max_total_bytes"] = 8
    elif case == "whitespace":
        with (tmp_path / "batch.yaml").open("a") as handle:
            handle.write("\n")
    elif case == "duplicate":
        with (tmp_path / "batch.yaml").open("a") as handle:
            handle.write("schema_version: '0.1'\n")
    elif case == "malformed":
        (tmp_path / "batch.yaml").write_text("fictional-private-label: [\n")
    if case not in {"valid", "whitespace"}:
        with pytest.raises(TransformationLimitError if case == "budget" else TransformationBatchError) as caught:
            load_batch_profile(tmp_path, "batch.yaml", **arguments, budget=GenerationBudget(5))
        if case != "budget":
            assert str(caught.value) == "invalid transformation batch profile"
            assert caught.value.__context__ is None
        return
    loaded = load_batch_profile(tmp_path, "batch.yaml", **arguments, budget=GenerationBudget(5))
    assert (loaded.snapshot_sha256 == original.snapshot_sha256) == (case == "valid")
    with temporary_batch_publication(loaded, expected_snapshot_sha256=loaded.snapshot_sha256,
            **arguments, max_output_bytes=8192, budget=GenerationBudget(5)) as bundle:
        assert (bundle / "input-0.csv").read_bytes() == b"key\n11\n12\n"
        assert (bundle / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"
    assert not bundle.parent.exists()


@pytest.mark.parametrize("case", ["valid", "limits", "traversal", "collision", "reserved_subtree",
                                 "mutated_model", "consumer_failure"])
def test_closed_profile_creation_review_execution(tmp_path, case, recwarn):
    from test_data_agent.io.transformation_batch_profile import BatchProfile, temporary_batch_profile

    save_fictional_batch_profile(tmp_path)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    raw = yaml.safe_load(before["batch.yaml"])
    if case == "limits":
        raw["resource_limits"] = {"max_total_input_bytes": 32768, "max_output_bytes": 8192}
    elif case == "traversal":
        raw["inputs"][0]["source"] = "../outside.csv"
    elif case == "collision":
        raw["inputs"][0]["source"] = "batch.yaml"
    elif case == "reserved_subtree":
        raw["inputs"][0]["source"] = "batch.yaml/fictional-private-source.csv"
    profile = BatchProfile.model_validate(raw)
    if case == "mutated_model":
        profile = profile.model_copy(update={"validation": {"fictional-private-label": "not a path"}})
    arguments = dict(max_total_bytes=32768, max_review_bytes=8192)
    if case in {"traversal", "collision", "reserved_subtree", "mutated_model"}:
        with pytest.raises(TransformationBatchError, match="invalid transformation batch profile") as caught:
            with temporary_batch_profile(tmp_path, profile, **arguments, budget=GenerationBudget(5)):
                pytest.fail("invalid profile created")
        assert caught.value.__context__ is None
    else:
        try:
            with temporary_batch_profile(tmp_path, profile, **arguments, budget=GenerationBudget(5)) as (root, batch):
                assert root != tmp_path
                saved = yaml.safe_load((root / "batch.yaml").read_bytes())
                if case == "limits":
                    assert saved["resource_limits"] == raw["resource_limits"]
                assert not json.loads(review_batch(batch, **arguments, budget=GenerationBudget(5)))["approved"]
                with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
                        **arguments, max_output_bytes=8192, budget=GenerationBudget(5)) as bundle:
                    assert (bundle / "input-0.csv").read_bytes() == b"key\n11\n12\n"
                    assert (bundle / "input-1.csv").read_bytes() == b"key\n11\n12\n11\n"
                assert not bundle.parent.exists()
                if case == "consumer_failure":
                    raise RuntimeError("fictional consumer failure")
        except RuntimeError:
            assert case == "consumer_failure"
        assert not root.exists()
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    assert not recwarn


@pytest.mark.parametrize("route", ["load", "create"])
def test_batch_source_file_ceiling(tmp_path, route):
    from test_data_agent.io.transformation_batch_profile import BatchProfile, temporary_batch_profile

    save_fictional_batch_profile(tmp_path)
    policy_path = tmp_path / "policy-0.yaml"
    policy = yaml.safe_load(policy_path.read_bytes())
    policy["resource_limits"] = {"max_input_file_bytes": 1}
    policy_path.write_text(yaml.safe_dump(policy))
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    with pytest.raises(TransformationLimitError) as caught:
        if route == "load":
            load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                max_review_bytes=8192, budget=GenerationBudget(5))
        else:
            profile = BatchProfile.model_validate(yaml.safe_load((tmp_path / "batch.yaml").read_bytes()))
            with temporary_batch_profile(tmp_path, profile, max_total_bytes=32768,
                    max_review_bytes=8192, budget=GenerationBudget(5)):
                pytest.fail("oversized source accepted")
    assert caught.value.dimension.value == "max_input_file_bytes"
    assert caught.value.origin == "profile" and caught.value.limit == 1
    assert caught.value.amount == len(before["source-0.csv"])
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_blank_batch_source_uses_session_file_ceiling(tmp_path):
    save_fictional_batch_profile(tmp_path)
    for index in range(2):
        (tmp_path / f"policy-{index}.yaml").unlink()
    program = '''
import sys, yaml
from pathlib import Path
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.io.transformation_batch_profile import BatchProfile, temporary_batch_profile
root = Path(sys.argv[1])
profile = BatchProfile.model_validate(yaml.safe_load((root / "batch.yaml").read_bytes()))
try:
    with temporary_batch_profile(root, profile, max_total_bytes=32768,
            max_review_bytes=8192, budget=GenerationBudget(5), create_csv_policies=True, seed=7):
        raise AssertionError("oversized source accepted")
except TransformationLimitError as error:
    assert error.origin == "session" and error.limit == 1
    assert error.dimension.value == "max_input_file_bytes"
'''
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    result = subprocess.run([sys.executable, "-c", program, str(tmp_path)],
        env={**os.environ, "TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_FILE_BYTES": "1"},
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize("route", ["load", "create"])
def test_batch_session_ceiling_precedes_missing_profile(tmp_path, route):
    program = '''
import sys
from pathlib import Path
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.io.transformation_batch_profile import load_batch_profile
from test_data_agent.cli_transformation_candidate import _candidate_batch_create_main
if sys.argv[2] == "load":
    try:
        load_batch_profile(Path(sys.argv[1]), "missing.yaml", max_total_bytes=32768,
            max_review_bytes=8192, budget=GenerationBudget(5))
    except TransformationLimitError as error:
        assert error.code == "requested_above_limit" and error.origin == "session"
        assert error.limit == 1 and error.amount == 32768
    else:
        raise AssertionError("session ceiling not enforced")
else:
    assert _candidate_batch_create_main([sys.argv[1], "missing.yaml", "saved",
        "--max-total-input-bytes", "32768", "--max-review-bytes", "8192"]) == 2
'''
    result = subprocess.run([sys.executable, "-c", program, str(tmp_path), route],
        env={**os.environ, "TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES": "1"},
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    if route == "create":
        assert "32768" in result.stdout and "session" in result.stdout
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("dimension", ["max_total_input_bytes", "max_output_bytes"])
@pytest.mark.parametrize("session_limit", [1, 65536])
def test_saved_batch_session_overrides_profile(tmp_path, dimension, session_limit):
    save_fictional_batch_profile(tmp_path)
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    profile["resource_limits"] = {dimension: 1}
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    program = '''
import sys
from pathlib import Path
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.io.transformation_batch_profile import load_batch_profile
from test_data_agent.io.transformation_batch import temporary_batch_publication
try:
    batch = load_batch_profile(Path(sys.argv[1]), "batch.yaml", max_total_bytes=32768,
        max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
        max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
        budget=GenerationBudget(5)) as bundle:
        assert (bundle / "input-0.csv").read_bytes() == b"key\\n11\\n12\\n"
    assert not bundle.parent.exists()
    assert sys.argv[2] == "65536"
except TransformationLimitError as error:
    assert sys.argv[2] == "1"
    assert error.origin == "session" and error.code == "requested_above_limit"
    assert error.limit == 1 and error.amount > 1
print("isolated shared session limits")
'''
    result = subprocess.run([sys.executable, "-c", program, str(tmp_path), str(session_limit)],
        env={**os.environ, "TEST_DATA_AGENT_TRANSFORM_" + dimension.upper(): str(session_limit)},
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "isolated shared session limits"


@pytest.mark.parametrize("dimension", ["max_input_rows", "max_input_columns", "max_input_cells",
    "max_input_file_bytes", "max_input_cell_chars", "max_parquet_expanded_bytes"])
def test_saved_batch_rejects_ignored_shared_limits(tmp_path, dimension):
    save_fictional_batch_profile(tmp_path)
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    profile["resource_limits"] = {dimension: 1}
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    with pytest.raises(TransformationBatchError, match="^invalid transformation batch profile$"):
        load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                           max_review_bytes=8192, budget=GenerationBudget(5))


@pytest.mark.parametrize("dimension", ["max_total_input_bytes", "max_output_bytes"])
def test_saved_batch_shared_profile_ceiling(tmp_path, dimension):
    save_fictional_batch_profile(tmp_path)
    original = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                                 max_review_bytes=8192, budget=GenerationBudget(5))
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    profile["resource_limits"] = {dimension: 65536}
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    assert batch.snapshot_sha256 != original.snapshot_sha256
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5)) as bundle:
        assert (bundle / "input-0.csv").read_bytes() == b"key\n11\n12\n"
    assert not bundle.parent.exists()
    profile["resource_limits"][dimension] = 8191 if dimension == "max_output_bytes" else 32767
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    with pytest.raises(TransformationLimitError) as caught:
        limited = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                                     max_review_bytes=8192, budget=GenerationBudget(5))
        execute_batch(limited, expected_snapshot_sha256=limited.snapshot_sha256,
            max_total_bytes=32768, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5))
    assert caught.value.origin == "profile"
    assert caught.value.code == "requested_above_limit"
    assert caught.value.amount == (8192 if dimension == "max_output_bytes" else 32768)
    assert caught.value.profile_key == "resource_limits." + dimension


@pytest.mark.parametrize("csv_mapping", [False, True])
@pytest.mark.parametrize("nullable", [False, True])
def test_saved_linked_batch_distinguishes_empty_and_null(tmp_path, csv_mapping, nullable):
    save_fictional_batch_profile(tmp_path)
    spec = yaml.safe_load((tmp_path / "validation.yaml").read_bytes())
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    null_token = "\\N"
    for index, item in enumerate(profile["inputs"]):
        source_path, policy_path = tmp_path / item["source"], tmp_path / item["policy"]
        keys = source_path.read_text().splitlines()[1:]
        source_path.write_text("key,label\n" + "".join(
            f"{key},{null_token if row % 2 == 0 else ''}\n" for row, key in enumerate(keys)))
        raw = yaml.safe_load(policy_path.read_bytes())
        raw["csv_nulls"] = {"input_token": "\\N", "output_token": "NULL"}
        mapping_path = f"nullable-{index}.csv"
        mapping = ({"kind": "csv", "path": mapping_path, "source_columns": ["old"],
                    "replacement_columns": ["new"], "null_token": "<null>"}
                   if csv_mapping else {"kind": "inline", "entries": [
                       {"original": [None], "replacement": ["fictional-filled"]},
                       {"original": [""], "replacement": [None]}]})
        if csv_mapping:
            (tmp_path / mapping_path).write_text("old,new\n<null>,fictional-filled\n,<null>\n")
            item["mappings"] = [mapping_path]
        raw["fields"].append({"entity": item["entity"], "field": "label",
            "sensitivity": "non_sensitive", "behavior": {"action": "substitute", "mapping": mapping}})
        policy = BehaviorPolicy.model_validate(raw)
        source = SnapshotPart("source", item["entity"], source_path.read_bytes())
        evidence = _profile_transformation_source(source, policy,
            max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
        spec["entities"][index]["fields"].append(
            {"name": "label", "data_type": "string", "nullable": nullable})
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    (tmp_path / "validation.yaml").write_text(yaml.safe_dump(spec))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                               max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(expected_snapshot_sha256=batch.snapshot_sha256,
                     max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192)
    if not nullable:
        # Optional reporting flags in the fixture cannot disable final schema validation.
        with pytest.raises(TransformationBatchError, match="^invalid transformation batch$"):
            with temporary_batch_publication(batch, **arguments, budget=GenerationBudget(5)):
                pytest.fail("invalid null result published")
        return
    results = execute_batch(batch, **arguments, budget=GenerationBudget(5))
    assert results[0].rows == (("11", "fictional-filled"), ("12", None))
    assert results[1].rows == (("11", "fictional-filled"), ("12", None), ("11", "fictional-filled"))
    with temporary_batch_publication(batch, **arguments, budget=GenerationBudget(5)) as bundle:
        assert (bundle / "input-0.csv").read_bytes() == b"key,label\n11,fictional-filled\n12,NULL\n"
        assert (bundle / "input-1.csv").read_bytes() == (
            b"key,label\n11,fictional-filled\n12,NULL\n11,fictional-filled\n")
        assert "fictional-filled" not in (bundle / "manifest.json").read_text()
    assert not bundle.parent.exists()


@pytest.mark.parametrize("action_kind", ["inline", "csv", "replace_text", "synthesize", "synthesize_fallback"])
def test_saved_linked_batch_with_unlinked_replacements(tmp_path, action_kind):
    save_fictional_batch_profile(tmp_path)
    spec = yaml.safe_load((tmp_path / "validation.yaml").read_bytes())
    profile = yaml.safe_load((tmp_path / "batch.yaml").read_bytes())
    replacement = "2026-08-31" if action_kind == "replace_text" else "fictional-label-b"
    for index, item in enumerate(profile["inputs"]):
        source_path, policy_path = tmp_path / item["source"], tmp_path / item["policy"]
        keys = source_path.read_text().splitlines()[1:]
        source_path.write_text("key,label\n" + "".join(f"{key},fictional-label-a\n" for key in keys))
        raw = yaml.safe_load(policy_path.read_bytes())
        if action_kind in {"synthesize", "synthesize_fallback"}:
            generation_path = f"generation-{index}.yaml"
            item["generation_policies"] = [generation_path]
            generation = {"schema_version": "1.1", "entities": [{"name": item["entity"],
                "row_count": 999, "fields": [{"name": "label", "data_type": "string",
                    "distribution": {"kind": "string_pattern", "min_length": 8, "max_length": 8}}]}],
                "generation_settings": {"seed": 999}}
            (tmp_path / generation_path).write_text(yaml.safe_dump(generation))
            action = {"action": "synthesize", "generation_policy_ref": generation_path}
            if action_kind == "synthesize_fallback":
                action = {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                    {"original": ["fictional-unseen"], "replacement": ["fictional-label-b"]}]},
                    "unmatched": action}
        elif action_kind == "inline":
            action = {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                {"original": ["fictional-label-a"], "replacement": [replacement]}]}}
        else:
            mapping_path = f"mapping-{index}.csv"
            (tmp_path / mapping_path).write_text(f"old,new\nfictional-label-a,{replacement}\n")
            item["mappings"] = [mapping_path]
            action = {"action": "replace_text" if action_kind == "replace_text" else "substitute",
                      "mapping": {"kind": "csv", "path": mapping_path,
                                  "source_columns": ["old"], "replacement_columns": ["new"]}}
        raw["fields"].append({"entity": item["entity"], "field": "label",
                              "sensitivity": "non_sensitive", "behavior": action})
        policy = BehaviorPolicy.model_validate(raw)
        source = SnapshotPart("source", item["entity"], source_path.read_bytes())
        evidence = _profile_transformation_source(source, policy,
            max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
        spec["entities"][index]["fields"].append({"name": "label", "data_type": "string"})
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump(profile))
    (tmp_path / "validation.yaml").write_text(yaml.safe_dump(spec))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                               max_review_bytes=8192, budget=GenerationBudget(5))
    with temporary_batch_publication(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5)) as bundle:
        for index, expected_keys in enumerate(([11, 12], [11, 12, 11])):
            if action_kind in {"synthesize", "synthesize_fallback"}:
                rows = (bundle / f"input-{index}.csv").read_text().splitlines()[1:]
                assert [int(row.split(",")[0]) for row in rows] == expected_keys
                assert all(len(row.split(",")[1]) == 8 for row in rows)
            else:
                expected = "key,label\n" + "".join(f"{key},{replacement}\n" for key in expected_keys)
                assert (bundle / f"input-{index}.csv").read_text() == expected
    assert not bundle.parent.exists()
    if action_kind in {"synthesize", "synthesize_fallback"}:
        results = execute_batch(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5))
        repeated = execute_batch(batch, expected_snapshot_sha256=batch.snapshot_sha256,
            max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192,
            budget=GenerationBudget(5))
        assert [result.csv_bytes for result in results] == [result.csv_bytes for result in repeated]
        changed = tmp_path / profile["inputs"][0]["generation_policies"][0]
        with changed.open("a") as handle:
            handle.write("\n")
        rebound = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                                    max_review_bytes=8192, budget=GenerationBudget(5))
        assert rebound.snapshot_sha256 != batch.snapshot_sha256
        with pytest.raises(TransformationBatchError):
            execute_batch(rebound, expected_snapshot_sha256=batch.snapshot_sha256,
                max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192,
                budget=GenerationBudget(5))
        generation = yaml.safe_load(changed.read_bytes())
        generation["generation_settings"]["mode"] = "negative"
        changed.write_text(yaml.safe_dump(generation))
        with pytest.raises(ValueError):
            negative = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                                          max_review_bytes=8192, budget=GenerationBudget(5))
            execute_batch(negative, expected_snapshot_sha256=negative.snapshot_sha256,
                max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192,
                budget=GenerationBudget(5))
        changed.unlink()
        with pytest.raises(TransformationBatchError):
            load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                               max_review_bytes=8192, budget=GenerationBudget(5))


@pytest.mark.parametrize("conflict", [False, True])
def test_shared_csv_domain_compares_its_exact_bytes(conflict):
    batch = fixture_batch("valid")
    requests = []
    for index, request in enumerate(batch.requests):
        raw = yaml.safe_load(next(part.payload for part in request.parts if part.kind == "policy"))
        raw["domains"][0]["mapping"] = {"kind": "csv", "path": "shared.csv",
            "source_columns": ["old"], "replacement_columns": ["new"]}
        mapping = SnapshotPart("mapping", "shared.csv",
            b"old,new\n1,11\n2,13\n3,14\n" if conflict and index else b"old,new\n1,11\n2,12\n3,14\n")
        requests.append(prepare_csv_review_request(yaml.safe_dump(raw).encode(),
            next(part for part in request.parts if part.kind == "source"), (mapping,),
            max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5)))
    combined = prepare_batch(tuple(requests), batch.validation_yaml,
        max_total_bytes=65536, max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(expected_snapshot_sha256=combined.snapshot_sha256,
        max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192, budget=GenerationBudget(5))
    if conflict:
        with pytest.raises(TransformationBatchError):
            execute_batch(combined, **arguments)
    else:
        results = execute_batch(combined, **arguments)
        assert [result.csv_bytes for result in results] == [b"key\n11\n12\n", b"key\n11\n12\n11\n"]


@pytest.mark.parametrize("orphan", [False, True])
def test_linked_synthesis_fallback_validates_final_keys(orphan):
    batch = fixture_batch("valid")
    requests = []
    for index, request in enumerate(batch.requests):
        raw = yaml.safe_load(next(part.payload for part in request.parts if part.kind == "policy"))
        raw["domains"][0]["mapping"]["entries"] = [
            entry for entry in raw["domains"][0]["mapping"]["entries"] if entry["original"] != [2]]
        raw["fields"][0]["behavior"]["unmatched"] = {
            "action": "synthesize", "generation_policy_ref": "generation.yaml"}
        source = next(part for part in request.parts if part.kind == "source")
        value = 16 if orphan and index else 15
        generation = {"schema_version": "1.1", "entities": [{"name": source.name,
            "row_count": 999, "fields": [{"name": "key", "data_type": "integer",
                "distribution": {"kind": "numeric", "min_value": value, "max_value": value}}]}]}
        parts = (SnapshotPart("generation_policy", "generation.yaml", yaml.safe_dump(generation).encode()),)
        requests.append(prepare_csv_review_request(yaml.safe_dump(raw).encode(), source, parts,
            max_total_bytes=32768, max_review_bytes=8192, budget=GenerationBudget(5)))
    combined = prepare_batch(tuple(requests), batch.validation_yaml,
        max_total_bytes=65536, max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(expected_snapshot_sha256=combined.snapshot_sha256,
        max_total_bytes=65536, max_review_bytes=8192, max_output_bytes=8192, budget=GenerationBudget(5))
    if orphan:
        with pytest.raises(TransformationBatchError):
            execute_batch(combined, **arguments)
    else:
        results = execute_batch(combined, **arguments)
        assert [result.csv_bytes for result in results] == [b"key\n11\n15\n", b"key\n11\n15\n11\n"]


@pytest.mark.parametrize("version", [1, 2])
def test_batch_receipt_cannot_confirm_unbound_review(tmp_path, version):
    batch = fixture_batch("valid")
    payload = {"version": version, "kind": "transformation_batch",
               "snapshot_sha256": batch.snapshot_sha256}
    if version == 2:
        payload["review_sha256"] = "0" * 64
    receipt = tmp_path / "unbound-review.json"
    receipt.write_text(json.dumps(payload, separators=(",", ":")))
    receipt.chmod(0o600)
    with pytest.raises(LocalReceiptError) as caught:
        verify_batch_receipt(batch, receipt, max_total_bytes=32768,
                             max_review_bytes=8192, budget=GenerationBudget(5))
    assert str(caught.value) == "local batch confirmation failed"
    assert caught.value.__context__ is None


@pytest.mark.parametrize("case", ["valid", "orphan", "incomplete", "duplicate_parent",
                                 "one_to_one_valid", "one_to_one_duplicate"])
def test_saved_composite_relationship_uses_whole_tuple(tmp_path, case):
    profile_entries, entities = [], []
    for index, entity in enumerate(("parents", "children")):
        records = [(1, 2), (2, 1)]
        if entity == "children" and case != "one_to_one_valid":
            records.append((1, 1) if case == "orphan" else (1, 2))
        if entity == "parents" and case == "duplicate_parent":
            records.append((1, 2))
        source = SnapshotPart("source", entity, ("key_a,key_b\n" + "".join(
            f"{a},{b}\n" for a, b in records)).encode())
        policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
            "schema_fingerprint": "0" * 64,
            "domains": [{"name": "shared", "mapping": {"kind": "inline", "entries": [
                {"original": [1, 2], "replacement": [11, 12]},
                {"original": [2, 1], "replacement": [12, 11]},
                {"original": [1, 1], "replacement": [11, 11]}]}}],
            "fields": [{"entity": entity, "field": name, "sensitivity": "non_sensitive",
                "behavior": {"action": "substitute", "mapping": {"kind": "domain",
                    "name": "shared", "component": component}}}
                for component, name in enumerate(("key_a", "key_b"))]})
        evidence = _profile_transformation_source(source, policy,
            max_bytes=32768, budget=GenerationBudget(5))
        policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(evidence)})
        (tmp_path / f"source-{index}.csv").write_bytes(source.payload)
        (tmp_path / f"policy-{index}.yaml").write_text(yaml.safe_dump(policy.model_dump(mode="json")))
        profile_entries.append({"entity": entity, "source": f"source-{index}.csv",
                                "policy": f"policy-{index}.yaml"})
        entities.append({"name": entity, "row_count": len(records), "fields": [
            {"name": name, "data_type": "integer", "is_identifier": True}
            for name in ("key_a", "key_b")]})
    relationships = [{"parent_entity": "parents", "parent_field": name,
        "child_entity": "children", "child_field": name, "confidence": 1.0,
        "relationship_type": "one_to_one" if case.startswith("one_to_one") else "many_to_one"}
        for name in (("key_a",) if case == "incomplete" else ("key_a", "key_b"))]
    (tmp_path / "validation.yaml").write_text(yaml.safe_dump({"schema_version": "1.1",
        "entities": entities, "relationships": relationships,
        "validation_settings": {"validate_schema": False, "validate_relationships": False,
                                "validate_constraints": False, "validate_privacy": False}}))
    (tmp_path / "batch.yaml").write_text(yaml.safe_dump({"schema_version": "0.1",
        "validation": "validation.yaml", "inputs": profile_entries}))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=65536,
                               max_review_bytes=8192, budget=GenerationBudget(5))
    arguments = dict(expected_snapshot_sha256=batch.snapshot_sha256, max_total_bytes=65536,
                     max_review_bytes=8192, max_output_bytes=8192, budget=GenerationBudget(5))
    if case not in {"valid", "one_to_one_valid"}:
        with pytest.raises(TransformationBatchError):
            with temporary_batch_publication(batch, **arguments):
                pytest.fail("invalid composite bundle returned")
        return
    with temporary_batch_publication(batch, **arguments) as bundle:
        assert (bundle / "input-0.csv").read_bytes() == b"key_a,key_b\n11,12\n12,11\n"
        expected = b"key_a,key_b\n11,12\n12,11\n" + (b"11,12\n" if case == "valid" else b"")
        assert (bundle / "input-1.csv").read_bytes() == expected
    assert not bundle.parent.exists()


def test_saved_batch_raised_source_budget_preserves_bootstrap_file_cap(tmp_path, monkeypatch):
    from test_data_agent.core import transformation_limits as limits
    save_fictional_batch_profile(tmp_path)
    profile_path = tmp_path / "batch.yaml"
    profile = yaml.safe_load(profile_path.read_bytes())
    profile["resource_limits"] = {"max_total_input_bytes": 32768}
    profile_path.write_text(yaml.safe_dump(profile))
    bootstrap_cap = len(profile_path.read_bytes()) + 1
    assert sum(path.stat().st_size for path in tmp_path.iterdir() if path.is_file()) > bootstrap_cap
    monkeypatch.setattr(limits, "resolve_input_limit", lambda *args:
        limits.EffectiveInputLimit(limits.InputDimension.TOTAL_BYTES, bootstrap_cap, "default"))
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
        max_review_bytes=8192, budget=GenerationBudget(5))
    assert len(batch.snapshot_sha256) == 64

@pytest.mark.parametrize("versioned", [False, True])
def test_common_cli_real_failed_rollback_warning(tmp_path, monkeypatch, capsys, versioned):
    from test_data_agent.cli_transformation_candidate import _candidate_batch_main
    from test_data_agent.io import path_policy, transformation_publish as publisher

    save_fictional_batch_profile(tmp_path)
    batch = load_batch_profile(tmp_path, "batch.yaml", max_total_bytes=32768,
                              max_review_bytes=8192, budget=GenerationBudget(5))
    destination = tmp_path / "output"
    original_fsync = path_policy.os.fsync

    def fail_after_rename(fd):
        if destination.exists():
            raise OSError("fictional-private-fsync-marker")
        return original_fsync(fd)

    def fail_rollback(path, identity, *, strict=False):
        raise OSError("fictional-private-rollback-marker")

    monkeypatch.setattr(path_policy.os, "fsync", fail_after_rename)
    monkeypatch.setattr(publisher, "remove_tree_if_identity", fail_rollback)
    assert _candidate_batch_main(["execute", str(tmp_path), "batch.yaml",
        "--snapshot-sha256", batch.snapshot_sha256, "--destination", "output",
        "--max-total-input-bytes", "32768", "--max-review-bytes", "8192",
        "--max-output-bytes", "8192"], versioned_output=versioned) == 2
    captured = capsys.readouterr()
    message = json.loads(captured.out)["error"]["message"]
    assert "cleanup incomplete" in message and "output or staging may remain" in message
    assert "before retrying" in message and "fictional-private" not in captured.out
    assert str(tmp_path) not in captured.out and not captured.err
    assert (destination / "input-0.csv").read_bytes() == b"key\n11\n12\n"
