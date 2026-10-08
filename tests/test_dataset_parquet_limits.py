from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest

from test_data_agent.core.limits import InputLimitError
from test_data_agent.io.readers import load_dataset_rows

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")


def write(path, values, *, dictionary=False):
    array = pa.array(values)
    if dictionary:
        array = array.dictionary_encode()
    pq.write_table(pa.table({"value": array}), path, use_dictionary=True)


@pytest.mark.parametrize("dictionary", [False, True])
def test_dictionary_expansion_is_not_authorized_by_encoded_metadata(tmp_path, monkeypatch, dictionary):
    path = tmp_path / "data.parquet"
    write(path, ["x" * 8192] * 256, dictionary=dictionary)
    metadata = pq.ParquetFile(path).metadata
    assert metadata.row_group(0).column(0).total_uncompressed_size < 65536
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES", "65536")
    with pytest.raises(InputLimitError, match="decoded size"):
        load_dataset_rows(tmp_path)


@pytest.mark.parametrize("first", ["csv", "json", "parquet"])
def test_mixed_dataset_cells_are_cumulative(tmp_path, monkeypatch, first):
    write(tmp_path / "z.parquet", [1, 2])
    if first == "csv":
        (tmp_path / "a.csv").write_text("value\n1\n2\n")
    elif first == "json":
        (tmp_path / "a.json").write_text(json.dumps([{"value": 1}, {"value": 2}]))
    else:
        write(tmp_path / "a.parquet", [1, 2])
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "3")
    with pytest.raises(InputLimitError, match="dataset.*cells"):
        load_dataset_rows(tmp_path)


def test_decoded_bytes_across_files_and_exact_limit(tmp_path, monkeypatch):
    write(tmp_path / "a.parquet", [1, 2])
    size = next(pq.ParquetFile(tmp_path / "a.parquet").iter_batches()).nbytes
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES", str(max(size, 1000)))
    assert load_dataset_rows(tmp_path)["a"] == [{"value": 1}, {"value": 2}]
    write(tmp_path / "b.parquet", [1, 2])
    # Bypass encoded metadata only to isolate the actual decoded accounting gate.
    monkeypatch.setattr("test_data_agent.io.readers.enforce_parquet_metadata_limits", lambda *args, **kwargs: None)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES", str(size))
    with pytest.raises(InputLimitError, match="decoded size"):
        load_dataset_rows(tmp_path)


@pytest.mark.parametrize("values", [["é" * 5], [b"12345"], [["12345"]], [{"nested": "12345"}]])
def test_parquet_cell_size_checked_before_python_rows(tmp_path, monkeypatch, values):
    write(tmp_path / "data.parquet", values)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")
    with pytest.raises(InputLimitError, match="cell exceeds"):
        load_dataset_rows(tmp_path)


def test_nested_cells_and_valid_typed_values(tmp_path, monkeypatch):
    write(tmp_path / "data.parquet", [[1, 2, 3]])
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "2")
    with pytest.raises(InputLimitError, match="cells"):
        load_dataset_rows(tmp_path)
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELLS", "10")
    assert load_dataset_rows(tmp_path)["data"] == [{"value": [1, 2, 3]}]
    (tmp_path / "data.parquet").unlink()
    pq.write_table(pa.table({"date": [date(2020, 1, 1)], "decimal": [Decimal("1.25")],
                            "text": ["é" * 4], "null": [None]}), tmp_path / "safe.parquet")
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")
    assert load_dataset_rows(tmp_path)["safe"][0]["decimal"] == Decimal("1.25")


@pytest.mark.parametrize("mode", ["bytes", "cells", "cell_size"])
def test_rejected_batch_never_converts_or_reads_whole_table(tmp_path, monkeypatch, mode):
    from types import SimpleNamespace
    write(tmp_path / "data.parquet", ["12345", "12345"])
    original = pq.ParquetFile
    file = original(tmp_path / "data.parquet")
    batch = next(file.iter_batches(batch_size=256))
    converted = []
    def forbidden():
        converted.append(True)
        pytest.fail("rejected batch reached Python conversion")
    wrapped_batch = SimpleNamespace(num_rows=batch.num_rows, nbytes=batch.nbytes,
                                    columns=batch.columns, to_pylist=forbidden)
    wrapped_file = SimpleNamespace(metadata=file.metadata,
                                  iter_batches=lambda **kwargs: iter([wrapped_batch]), read=forbidden)
    monkeypatch.setattr(pq, "ParquetFile", lambda *args: wrapped_file)
    monkeypatch.setattr("test_data_agent.io.readers.enforce_parquet_metadata_limits", lambda *args, **kwargs: None)
    limits = {"bytes": ("TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES", "1"),
              "cells": ("TEST_DATA_AGENT_MAX_INPUT_CELLS", "1"),
              "cell_size": ("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")}
    monkeypatch.setenv(*limits[mode])
    with pytest.raises(InputLimitError):
        load_dataset_rows(tmp_path)
    assert converted == []
