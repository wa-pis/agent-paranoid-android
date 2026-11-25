"""Preserve CSV bytes, formula neutralization and writer failure behavior."""

from __future__ import annotations

import csv
import random
from collections import OrderedDict, UserDict
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
from io import StringIO
from types import MappingProxyType
from typing import Any

import pytest

from test_data_agent.adapters.parallel_generation import ParallelGenerationPolicy
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.io import streaming_csv
from test_data_agent.io.csv_encoding import encode_csv_cell
from test_data_agent.io.writers import neutralize_csv_cell, rows_to_csv, write_bounded_text


def _original_neutralize(value: Any) -> Any:
    if not isinstance(value, str) or not value:
        return value
    stripped = value.lstrip(" \t\r\n")
    if value[0] in "\t\r\n" or (stripped and stripped[0] in "=+-@"):
        return "'" + value
    return value


def _original_rows_to_csv(rows: list[dict[str, Any]], *, typed: bool = False) -> str:
    # Freeze the complete original walk, including schema checks and C csv formatting.
    if not rows:
        return ""
    handle = StringIO()
    fieldnames = list(rows[0])
    fieldname_set = set(fieldnames)
    writer = csv.writer(handle)
    writer.writerow([encode_csv_cell(name) if typed else _original_neutralize(name) for name in fieldnames])
    for row in rows:
        if set(row) - fieldname_set:
            raise ValueError("CSV rows must share one schema")
        writer.writerow([encode_csv_cell(row.get(name)) if typed else _original_neutralize(row.get(name)) for name in fieldnames])
    return handle.getvalue()


class _StringSubclass(str):
    pass


class _HiddenLstripString(str):
    def lstrip(self, chars=None):
        return "synthetic_hidden"


class _RaisingLstripString(str):
    def lstrip(self, chars=None):
        raise ValueError("synthetic lstrip failure")


class _RaisingIndexString(str):
    def __getitem__(self, key):
        raise ValueError("synthetic index failure")


class _EmptyStringSubclass(str):
    def __bool__(self):
        return False


class _RaisingAddString(str):
    def __radd__(self, other):
        raise ValueError("synthetic concatenation failure")


class _IntegerSubclass(int):
    def __str__(self):
        return "synthetic_integer"


class _FloatSubclass(float):
    def __str__(self):
        return "synthetic_float"


class _RaisingScalar:
    def __str__(self):
        raise ValueError("synthetic scalar conversion failure")


class _ReverseIterationDict(dict):
    def __iter__(self):
        return reversed(list(dict.__iter__(self)))


class _DuplicateIterationDict(dict):
    def __iter__(self):
        return iter(["payload", "payload"])


class _RaisingGetDict(dict):
    def get(self, key, default=None):
        raise ValueError("synthetic lookup failure")


class _AlternativeGetDict(dict):
    def get(self, key, default=None):
        return "=synthetic_lookup"


class _HiddenKeysDict(dict):
    def keys(self):
        return {"payload": None}.keys()


class _HiddenIterationDict(dict):
    def __iter__(self):
        return iter(["payload"])


def _strings() -> list[str]:
    markers = ["=", "+", "-", "@"]
    prefixes = ["", " ", "  ", "\t", "\r", "\n", " \t\r\n"]
    return [
        "", "synthetic_plain", "synthetic_кириллица", "synthetic_😀", "synthetic,comma",
        'synthetic_"quote"', "synthetic_line\r\nnext", "synthetic_\x00nul", " ", "\t", "\r", "\n",
        " synthetic_spaced", "\tsynthetic_control", "\rsynthetic_control", "\nsynthetic_control",
        "\u00a0=synthetic_nbsp", "\v=synthetic_vertical", "\f=synthetic_formfeed",
        "'=synthetic_already_quoted", "synthetic_interior=sign", " \t synthetic_plain",
        *[prefix + marker + "synthetic_formula" for prefix in prefixes for marker in markers],
    ]


def _values() -> list[Any]:
    return [
        None, False, True, 0, 7, -7, 2**70, 0.0, -0.0, 1.5, float("nan"), float("inf"),
        float("-inf"), Decimal("7.25"), date(2024, 2, 29), datetime(2024, 2, 29, 1, 2, 3),
        datetime(2024, 2, 29, tzinfo=timezone.utc), _IntegerSubclass(7), _FloatSubclass(1.5),
        b"synthetic_bytes", [], {}, ("synthetic_tuple",), *_strings(),
        _StringSubclass(" =synthetic_subclass"), _HiddenLstripString(" =synthetic_hidden"),
        _RaisingLstripString("synthetic_plain"), _RaisingIndexString("synthetic_plain"),
        _EmptyStringSubclass("=synthetic_empty"), _RaisingAddString("=synthetic_add"),
        _RaisingScalar(),
    ]


def _outcome(function, *args):
    try:
        result = function(*args)
    except Exception as error:
        return "exception", type(error), error.args
    return "result", result


@pytest.mark.parametrize("value", _strings())
def test_string_neutralization_matches_frozen_policy(value: str) -> None:
    assert neutralize_csv_cell(value) == _original_neutralize(value)
    assert neutralize_csv_cell(value) is value or neutralize_csv_cell(value) == "'" + value


def test_native_and_subclass_neutralization_preserves_results_and_identity() -> None:
    for index, value in enumerate(_values()):
        expected = _outcome(_original_neutralize, value)
        actual = _outcome(neutralize_csv_cell, value)
        if expected[0] == "exception":
            assert actual == expected, index
        else:
            assert actual[0] == "result", index
            if expected[1] is value:
                assert actual[1] is value, index
            else:
                assert type(actual[1]) is type(expected[1]) and actual[1] == expected[1], index


def test_csv_preserves_all_scalar_formatting_and_formula_bytes() -> None:
    for index, value in enumerate(_values()):
        rows = [{"payload": value, "=synthetic_header": "synthetic_other"}]
        assert _outcome(rows_to_csv, rows) == _outcome(_original_rows_to_csv, rows), index

    assert rows_to_csv([{"label": 'synthetic_,"quoted"\nline', "number": -7, "missing": None}]) == (
        'label,number,missing\r\n"synthetic_,""quoted""\nline",-7,\r\n'
    )


@pytest.mark.parametrize("rows", [
    [], [{}], [{}, {}], [{}, {"extra": 7}],
    [{"b": 1, "a": 2}, {"a": 3}, {}],
    [{"b": 1, "a": 2}, {"a": 3, "b": 4}],
    [{"payload": "synthetic_value"}, {"extra": "synthetic_extra"}],
    [{"payload": "synthetic_value"}, None],
    [OrderedDict([("b", 1), ("a", 2)])],
    [UserDict(payload="synthetic_value")],
    [MappingProxyType({"payload": "synthetic_value"})],
    [_ReverseIterationDict(b=1, a=2)],
    [_DuplicateIterationDict(payload="synthetic_duplicate")],
    [_AlternativeGetDict(payload="synthetic_value")],
    [_RaisingGetDict(payload="synthetic_value")],
    [{"payload": "synthetic_value"}, _RaisingGetDict(extra="synthetic_extra")],
    [{"payload": "synthetic_value"}, _HiddenKeysDict(payload="synthetic_value", extra=7)],
    [{"payload": "synthetic_value"}, _HiddenIterationDict(payload="synthetic_value", extra=7)],
    [{7: "synthetic_numeric_header", None: "synthetic_null_header"}],
])
def test_csv_preserves_column_order_missing_keys_and_schema_failures(rows) -> None:
    assert _outcome(rows_to_csv, rows) == _outcome(_original_rows_to_csv, rows)


def test_csv_schema_failure_precedes_value_conversion() -> None:
    rows = [{"payload": "synthetic_value"}, {"extra": _RaisingScalar()}]
    assert _outcome(rows_to_csv, rows) == (
        "exception", ValueError, ("CSV rows must share one schema",),
    )


def test_csv_encoding_preserves_seeded_mixed_datasets() -> None:
    rng = random.Random(1123)
    keys = ["payload", "=synthetic_header", 'synthetic_"quote', "synthetic,comma", "Юникод"]
    values = _values()
    for _ in range(100):
        fieldnames = rng.sample(keys, rng.randrange(1, len(keys) + 1))
        rows = [dict(zip(fieldnames, (rng.choice(values) for _ in fieldnames), strict=True))]
        for _ in range(rng.randrange(4)):
            selected = rng.sample(keys, rng.randrange(len(keys) + 1))
            rows.append({name: rng.choice(values) for name in selected})
        assert _outcome(rows_to_csv, rows) == _outcome(_original_rows_to_csv, rows)


def test_csv_encoding_observes_changes_and_never_mutates_rows() -> None:
    rows = [{"first": "=synthetic_formula", "second": "synthetic_plain"}]
    original = deepcopy(rows)
    assert rows_to_csv(rows) == _original_rows_to_csv(rows)
    assert rows == original
    rows[0]["first"] = "\tsynthetic_control"
    assert rows_to_csv(rows) == _original_rows_to_csv(rows)
    rows[0]["third"] = date(2024, 2, 29)
    assert rows_to_csv(rows) == _original_rows_to_csv(rows)
    rows.reverse()
    assert rows_to_csv(rows) == _original_rows_to_csv(rows)


@pytest.mark.parametrize("source_type", [
    "csv", "csv_folder", "parquet", "json_profile", "legacy_profile", "postgres",
    "postgres_query", "trino", "trino_query", "custom_source",
])
def test_source_derived_specs_share_exact_csv_encoding(source_type: str) -> None:
    profile = DatasetProfile.model_validate({
        "source_type": source_type,
        "has_unmodeled_expressions": False,
        "entities": [{"name": "fictional", "row_count": 3, "fields": [
            {"name": "synthetic_id", "data_type": "integer", "is_identifier": True},
            {"name": "amount", "data_type": "float"},
            {"name": "active", "data_type": "boolean"},
            {"name": "label", "data_type": "string"},
        ]}],
    })
    spec = infer_dataset_spec(profile, count=3)
    first = generate_dataset(spec, seed=42)
    second = generate_dataset(spec, seed=42)
    assert rows_to_csv(first["fictional"]) == _original_rows_to_csv(first["fictional"])
    assert rows_to_csv(second["fictional"]) == rows_to_csv(first["fictional"])


@pytest.mark.parametrize("step", [1, 2, 4])
def test_streaming_tiles_match_frozen_csv_bytes(tmp_path, monkeypatch, step: int) -> None:
    rows = [
        {"id": index + 1, "=synthetic_header": value, "note": 'synthetic_кириллица,"quoted"\nline'}
        for index, value in enumerate(["=synthetic_formula", " +synthetic_formula", "\tsynthetic_control", None])
    ]
    spec = DatasetSpec.model_validate({"entities": [{
        "name": "fictional", "row_count": len(rows), "primary_key": "id", "fields": [
            {"name": "id", "data_type": "integer", "is_identifier": True},
            {"name": "=synthetic_header", "data_type": "string", "nullable": True},
            {"name": "note", "data_type": "string"},
        ],
    }]})

    def visit(spec, seed, *, policy, budget, consume):
        for start in range(0, len(rows), step):
            consume(0, start, rows[start:start + step])

    monkeypatch.setattr(streaming_csv, "_visit_generated_tiles", visit)
    original = deepcopy(rows)
    report = streaming_csv.write_streaming_csv(
        spec, output_folder=tmp_path, seed=42, policy=ParallelGenerationPolicy(workers=1),
        budget=GenerationBudget(60),
    )
    path = tmp_path / "fictional.csv"
    assert report.valid and all(section.failed == 0 for section in report.sections)
    assert path.read_bytes() == _original_rows_to_csv(rows, typed=True).encode("utf-8")
    assert path.stat().st_mode & 0o777 == 0o600
    assert rows == original
    assert not list(tmp_path.glob("*.tmp"))


def test_utf8_encoding_failure_preserves_existing_output(tmp_path) -> None:
    output = tmp_path / "fictional.csv"
    output.write_bytes(b"synthetic_previous\r\n")
    text = rows_to_csv([{"payload": "synthetic_\ud800"}])
    with pytest.raises(UnicodeEncodeError):
        write_bounded_text(text, output)
    assert output.read_bytes() == b"synthetic_previous\r\n"
    assert not list(tmp_path.glob("*.tmp"))
