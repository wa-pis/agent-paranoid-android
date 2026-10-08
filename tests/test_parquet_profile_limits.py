"""Parquet profile inspection shares pre-conversion logical bounds."""

from types import SimpleNamespace

import pytest

from test_data_agent.adapters.parquet_dataset import _parquet_sensitive_columns, parquet_file_to_dataset_profile
from test_data_agent.core.limits import InputLimitError

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")




def test_nested_cells_reject_before_python_conversion(monkeypatch) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "5")
    scalar = pa.scalar([True] * 6, type=pa.list_(pa.bool_()))
    class Scalar:
        type = scalar.type
        is_valid = True
        values = scalar.values
        def as_py(self):
            pytest.fail("nested Python conversion occurred before rejection")
    batch = SimpleNamespace(nbytes=6, columns=[[Scalar()]])
    source = SimpleNamespace(schema_arrow=pa.schema([("payload", scalar.type)]), iter_batches=lambda **_: [batch])
    with pytest.raises(InputLimitError, match="cells"):
        _parquet_sensitive_columns(source)


@pytest.mark.parametrize("values,limit_env,limit", [
    ([[True] * 6], "TEST_DATA_AGENT_MAX_INPUT_CELLS", "5"),
    ([["synthetic" * 4]], "TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "10"),
    ([[[True]]], "TEST_DATA_AGENT_MAX_JSON_DEPTH", "2"),
])
def test_public_adapter_rejects_nested_limits(tmp_path, monkeypatch, values, limit_env, limit) -> None:
    path = tmp_path / "probe.parquet"
    pq.write_table(pa.table({"payload": values}), path)
    monkeypatch.setenv(limit_env, limit)
    with pytest.raises(InputLimitError):
        parquet_file_to_dataset_profile(path)


def test_leaf_cells_cumulative_across_batches(tmp_path, monkeypatch) -> None:
    path = tmp_path / "probe.parquet"
    pq.write_table(pa.table({"payload": [[True, False]] * 257}), path)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "513")
    with pytest.raises(InputLimitError, match="cells"):
        parquet_file_to_dataset_profile(path)


def test_bounded_composite_profile_remains_sensitive(tmp_path) -> None:
    path = tmp_path / "probe.parquet"
    pq.write_table(pa.table({"payload": [[True, False]]}), path)
    profile = parquet_file_to_dataset_profile(path)
    assert profile.entities[0].fields[0].sensitive


def test_profile_charges_retained_dictionary_logical_expansion(monkeypatch):
    array = pa.array(["synthetic" * 1024] * 16).dictionary_encode()
    batch = pa.record_batch([array], names=["payload"])
    assert batch.nbytes < 32768
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES", "32768")
    source = SimpleNamespace(schema_arrow=batch.schema, iter_batches=lambda **_: [batch])
    with pytest.raises(InputLimitError, match="decoded size"):
        _parquet_sensitive_columns(source)
