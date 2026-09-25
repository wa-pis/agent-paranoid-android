import hashlib

import pytest

from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_mapping import CsvMapping, MappingDeclarationError
from test_data_agent.io.mapping_loader import load_csv_mapping


def load(root, kind, **overrides):
    options = dict(data_types=(kind,), nullable=(False,), max_bytes=1000, max_rows=10,
                   max_cells=20, max_columns=2, max_cell_chars=100, budget=GenerationBudget())
    options.update(overrides)
    return load_csv_mapping(root, CsvMapping(kind="csv", path="map.csv",
        source_columns=("old",), replacement_columns=("new",)), **options)


def test_loaded_dates_and_hash_match_same_snapshot(tmp_path):
    payload = b"old,new\n2025-04-30,2026-09-23\n"
    (tmp_path / "map.csv").write_bytes(payload)
    result = load(tmp_path.resolve(), FieldType.DATE)
    assert result.mapping.entries[0].replacement == ("2026-09-23",)
    assert result.source_sha256 == hashlib.sha256(payload).hexdigest()
    assert repr(result) == "LoadedCsvMapping()"


@pytest.mark.parametrize("kind,payload", [
    (FieldType.INTEGER, b"old,new\n1.5,2\n"),
    (FieldType.DATE, b"old,new\n2025-04-30T00:00:00,2026-09-23\n"),
    (FieldType.STRING, b"old,new\na,b\na,c\n"),
])
def test_loader_keeps_typed_and_duplicate_checks(tmp_path, kind, payload):
    (tmp_path / "map.csv").write_bytes(payload)
    with pytest.raises(MappingDeclarationError):
        load(tmp_path.resolve(), kind)


def test_loader_uses_snapshot_after_source_path_changes(tmp_path):
    source = tmp_path / "map.csv"
    original = b"old,new\na,b\n"
    source.write_bytes(original)
    calls = [0]

    def clock():
        calls[0] += 1
        # Construction, entry, read, EOF, then snapshot completion after close.
        if calls[0] == 5:
            source.write_bytes(b"old,new\nx,y\n")
        return 0.0

    result = load(tmp_path.resolve(), FieldType.STRING,
                  budget=GenerationBudget(max_seconds=1, clock=clock))
    assert source.read_bytes() != original
    assert result.mapping.entries[0].original == ("a",)
    assert result.mapping.entries[0].replacement == ("b",)
    assert result.source_sha256 == hashlib.sha256(original).hexdigest()


@pytest.mark.parametrize("limit", [{"max_bytes": 3}, {"max_rows": 1}, {"max_cells": 1},
                                  {"max_columns": 1}, {"max_cell_chars": 2}])
def test_loader_propagates_limits(tmp_path, limit):
    (tmp_path / "map.csv").write_bytes(b"old,new\na,b\nc,d\n")
    with pytest.raises(MappingDeclarationError):
        load(tmp_path.resolve(), FieldType.STRING, **limit)


def test_loader_does_not_reset_deadline_after_snapshot(tmp_path):
    (tmp_path / "map.csv").write_bytes(b"old,new\na,b\n")
    calls = [0]

    def clock():
        calls[0] += 1
        return 2.0 if calls[0] >= 6 else 0.0

    with pytest.raises(MappingDeclarationError) as caught:
        load(tmp_path.resolve(), FieldType.STRING,
             budget=GenerationBudget(max_seconds=1, clock=clock))
    assert caught.value.__context__ is None


def test_integer_csv_normalization_is_exact(tmp_path):
    (tmp_path / "map.csv").write_bytes(b"old,new\n+001,9007199254740993\n")
    result = load(tmp_path.resolve(), FieldType.INTEGER)
    assert result.mapping.entries[0].original == (1,)
    assert result.mapping.entries[0].replacement == (9007199254740993,)


def test_approximate_float_csv_uses_same_snapshot(tmp_path):
    payload = b"old,new\n+1.25e2,-0.5\n"
    (tmp_path / "map.csv").write_bytes(payload)
    result = load(tmp_path.resolve(), FieldType.FLOAT)
    assert result.mapping.entries[0].original == (125.0,)
    assert result.mapping.entries[0].replacement == (-0.5,)
    assert result.source_sha256 == hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize("rows", [b"1,2\n+001,3\n", b"-0,2\n0,3\n", b" 1,2\n",
                                 b"1e2,2\n", b"1_000,2\n", b"true,2\n"])
def test_integer_csv_rejects_ambiguity_and_converted_duplicates(tmp_path, rows):
    (tmp_path / "map.csv").write_bytes(b"old,new\n" + rows)
    with pytest.raises(MappingDeclarationError, match="^invalid typed CSV mapping$"):
        load(tmp_path.resolve(), FieldType.INTEGER)
