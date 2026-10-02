"""Fictional dictionary expansion; isolated environment, no product monkeypatch."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import (
    InputDimension, TransformationInputLimits, TransformationLimitError, resolve_input_limit,
)
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader


def _policy(limits):
    return BehaviorPolicy.model_validate({"schema_version": "0.1", "schema_fingerprint": "0" * 64,
        "seed": 7, "resource_limits": limits, "fields": [
            {"entity": "items", "field": name, "sensitivity": "non_sensitive",
             "behavior": {"action": "drop"}} for name in ("a", "b")]})


def test_scoped_csv_readers_restore_global_limit_across_threads():
    import csv
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from test_data_agent.core.csv_reader import ScopedDictReader

    previous = csv.field_size_limit()
    barrier = Barrier(2)

    def read(limit):
        for _ in range(20):
            reader = ScopedDictReader(iter(["a\n", "abcdefgh\n"]), max_chars=limit)
            assert reader.fieldnames == ["a"]
            barrier.wait(timeout=5)
            if limit == 3:
                with pytest.raises(csv.Error):
                    next(reader)
            else:
                assert next(reader) == {"a": "abcdefgh"}
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(read, limit) for limit in (3, 64)]
        assert all(future.result(timeout=10) for future in futures)
    assert csv.field_size_limit() == previous


def test_private_scalar_profile_override_retains_sensitivity_and_source_free_limit():
    script = '''
import csv
from tests.test_transformation_input_limits import _policy
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source
from test_data_agent.csv_profiler import profile_csv_bytes
previous = csv.field_size_limit()
payload = b"a,b\\nfictional@example.test,plain\\n"
profile = _profile_transformation_source(SnapshotPart("source", "items", payload),
    _policy({"max_input_cell_chars": 64}), budget=GenerationBudget(5), max_bytes=1024)
assert profile.entities[0].fields[0].sensitive
assert "fictional@example.test" not in profile.model_dump_json()
try:
    profile_csv_bytes(payload, "items", budget=GenerationBudget(5))
except csv.Error:
    pass
else:
    raise AssertionError("source-free character limit raised")
assert csv.field_size_limit() == previous
print("isolated")
'''
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-c", script], cwd=root,
        env={**os.environ, "TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS": "4",
             "PYTHONPATH": os.pathsep.join([str(root / "src"), str(root)])},
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "isolated"


@pytest.mark.parametrize("key,limit", [("max_input_rows", 1), ("max_input_columns", 1),
    ("max_input_cells", 3), ("max_input_file_bytes", 5), ("max_input_cell_chars", 1)])
def test_csv_profile_limits_have_actionable_value_free_errors(key, limit):
    source = SnapshotPart("source", "items", b"a,b\naa,x\ny,z\n")
    with pytest.raises(TransformationLimitError) as caught:
        list(source_reader(source, _policy({key: limit}), budget=GenerationBudget(5)))
    error = caught.value
    assert error.code == "limit_exceeded" and error.origin == "profile"
    assert error.amount > error.limit == limit
    assert f"resource_limits.{key}" in str(error)
    assert f"TEST_DATA_AGENT_TRANSFORM_{key.upper()}" in str(error)
    assert "aa" not in str(error) and error.__context__ is None


def test_exact_boundary_and_iterator_do_not_reset_counter():
    source = SnapshotPart("source", "items", b"a,b\nx,y\nz,w\n")
    policy = _policy({"max_input_rows": 2, "max_input_cells": 4})
    assert len(list(source_reader(source, policy, budget=GenerationBudget(5)))) == 2
    reader = source_reader(source, _policy({"max_input_rows": 1}), budget=GenerationBudget(5))
    assert next(iter(reader)) == {"a": "x", "b": "y"}
    with pytest.raises(TransformationLimitError):
        next(iter(reader))


def test_limit_precedence_and_request_category():
    dimension = InputDimension.ROWS
    profile = TransformationInputLimits(max_input_rows=7)
    session = {"TEST_DATA_AGENT_MAX_INPUT_ROWS": "3",
               "TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS": "9"}
    selected = resolve_input_limit(dimension, profile, session)
    assert (selected.value, selected.origin) == (9, "session")
    with pytest.raises(TransformationLimitError) as caught:
        selected.check(10, requested=True)
    assert caught.value.code == "requested_above_limit"
    session.pop("TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS")
    assert resolve_input_limit(dimension, profile, session).value == 7
    assert resolve_input_limit(dimension, None, session).value == 3
    assert resolve_input_limit(dimension, None, {}).value == 1_000_000
    assert resolve_input_limit(InputDimension.CELLS, None, {}).value == 100_000_000


@pytest.mark.parametrize("value", ["fictional-private", "-1", "0", "NaN", "9" * 100])
def test_invalid_session_value_is_not_reflected(value):
    with pytest.raises(ValueError) as caught:
        resolve_input_limit(InputDimension.ROWS, None,
            {"TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS": value})
    assert str(caught.value) == (
        "invalid resource setting: TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS; "
        "use a positive integer <= 9223372036854775807; profile key resource_limits.max_input_rows")
    assert caught.value.__context__ is None


def test_limit_survives_real_review_preflight():
    import yaml
    from tests.test_transformation_execute import request
    from test_data_agent.io.transformation_source import prepare_csv_review_request

    material = request()
    policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
    policy["resource_limits"] = {"max_input_rows": 1}
    with pytest.raises(TransformationLimitError) as caught:
        prepare_csv_review_request(yaml.safe_dump(policy).encode(),
            next(p for p in material.parts if p.kind == "source"),
            tuple(p for p in material.parts if p.kind == "mapping"),
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert caught.value.dimension is InputDimension.ROWS
    assert caught.value.amount == 2 and caught.value.origin == "profile"


def test_real_session_setting_and_recovery_in_isolated_process():
    script = '''
import os
from tests.test_transformation_input_limits import _policy
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader
source = SnapshotPart("source", "items", b"a,b\\nx,y\\nz,w\\n")
policy = _policy({"max_input_rows": 2})
try:
    list(source_reader(source, policy, budget=GenerationBudget(5)))
except TransformationLimitError as error:
    assert error.origin == "session" and error.amount == 2 and error.limit == 1
    os.environ[error.session_setting] = "2"
else:
    raise AssertionError("session limit not enforced")
assert len(list(source_reader(source, policy, budget=GenerationBudget(5)))) == 2
print("recovered")
'''
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-c", script], cwd=root,
        env={**os.environ, "TEST_DATA_AGENT_TRANSFORM_MAX_INPUT_ROWS": "1",
             "PYTHONPATH": os.pathsep.join([str(root / "src"), str(root)])},
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "recovered"


def test_file_review_reports_profile_byte_limit_and_recovers(tmp_path):
    import yaml
    from tests.test_transformation_execute import request
    from test_data_agent.io.transformation_source import prepare_csv_review_from_paths

    material = request()
    source = next(p for p in material.parts if p.kind == "source")
    source_path = tmp_path / "input.csv"
    source_path.write_bytes(source.payload)
    for part in material.parts:
        if part.kind == "mapping":
            (tmp_path / part.name).write_bytes(part.payload)
    policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
    policy["resource_limits"] = {"max_input_file_bytes": len(source.payload) - 1}
    policy_path = tmp_path / "behavior.yaml"
    policy_path.write_text(yaml.safe_dump(policy))

    def prepare():
        return prepare_csv_review_from_paths(source_path, "items", tmp_path, "behavior.yaml",
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))

    with pytest.raises(TransformationLimitError) as caught:
        prepare()
    assert caught.value.amount == len(source.payload)
    assert caught.value.limit == len(source.payload) - 1
    assert caught.value.origin == "profile" and caught.value.unit == "bytes"
    assert caught.value.profile_key == "resource_limits.max_input_file_bytes"
    policy["resource_limits"]["max_input_file_bytes"] = len(source.payload)
    policy_path.write_text(yaml.safe_dump(policy))
    assert next(p for p in prepare().parts if p.kind == "source").payload == source.payload


def test_trace_rejects_requested_budget_above_profile_without_clamping():
    import yaml
    from tests.test_transformation_execute import request
    from test_data_agent.io.transformation_source import prepare_csv_review_request, trace_csv_review_request

    material = request()
    policy = yaml.safe_load(next(p.payload for p in material.parts if p.kind == "policy"))
    policy["resource_limits"] = {"max_input_cells": 4}
    material = prepare_csv_review_request(yaml.safe_dump(policy).encode(),
        next(p for p in material.parts if p.kind == "source"),
        tuple(p for p in material.parts if p.kind == "mapping"),
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    with pytest.raises(TransformationLimitError) as caught:
        trace_csv_review_request(material, max_events=1, max_cells=5,
            max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert (caught.value.code, caught.value.amount, caught.value.limit, caught.value.origin) == (
        "requested_above_limit", 5, 4, "profile")
    summary = trace_csv_review_request(material, max_events=1, max_cells=4,
        max_total_bytes=8192, max_review_bytes=4096, budget=GenerationBudget(5))
    assert summary.matched_cells + summary.unmatched_cells == 4


@pytest.mark.parametrize("legacy_key", ["MAX_INPUT_ROWS", "MAX_INPUT_COLUMNS", "MAX_INPUT_CELLS"])
def test_private_profile_shape_override_does_not_raise_source_free_limits(legacy_key):
    script = '''
from tests.test_transformation_input_limits import _policy
from test_data_agent.core.limits import GenerationBudget, InputLimitError
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source
from test_data_agent.csv_profiler import _profile_csv_rows, _csv_reader_from_snapshot
payload = b"a,b\\nx,y\\nz,w\\n"
policy = _policy({"max_input_rows": 2, "max_input_columns": 2, "max_input_cells": 4})
profile = _profile_transformation_source(SnapshotPart("source", "items", payload),
    policy, budget=GenerationBudget(5), max_bytes=1024)
assert profile.entities[0].row_count == 2
try:
    _profile_csv_rows(_csv_reader_from_snapshot(payload), "items", (), None, GenerationBudget(5))
except InputLimitError:
    pass
else:
    raise AssertionError("source-free limits changed")
print("isolated")
'''
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-c", script], cwd=root,
        env={**os.environ, "TEST_DATA_AGENT_" + legacy_key: "1",
             "PYTHONPATH": os.pathsep.join([str(root / "src"), str(root)])},
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "isolated"


@pytest.mark.parametrize("width,accepted", [(128, True), (768, False), (4096, False)])
def test_decoded_parquet_limit_across_batches(width, accepted):
    pytest.importorskip("pyarrow")
    script = '''
import io
import sys
import pyarrow as pa
import pyarrow.parquet as pq
from test_data_agent.core.limits import GenerationBudget, InputLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader

width = int(sys.argv[1])
buffer = io.BytesIO()
pq.write_table(pa.table({"code": ["x" * width] * 2048}), buffer,
               use_dictionary=True)
metadata = pq.ParquetFile(io.BytesIO(buffer.getvalue())).metadata
assert metadata.row_group(0).column(0).total_uncompressed_size < 1024 * 1024
policy = BehaviorPolicy.model_validate({"schema_version": "0.1",
    "schema_fingerprint": "0" * 64, "seed": 7, "input_format": "parquet",
    "fields": [{"entity": "items", "field": "code",
        "sensitivity": "non_sensitive", "behavior": {"action": "drop"}}]})
try:
    rows = source_reader(SnapshotPart("source", "items", buffer.getvalue()),
                         policy, budget=GenerationBudget(5))
except InputLimitError as error:
    assert error.dimension == "max_parquet_expanded_bytes"
    assert error.amount > error.limit == 1048576
    assert error.origin == "legacy_session"
    print("rejected")
else:
    assert len(rows.rows) == 2048
    print("accepted")
'''
    result = subprocess.run([sys.executable, "-c", script, str(width)],
        env={**os.environ, "TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES": "1048576",
             "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ("accepted" if accepted else "rejected")
