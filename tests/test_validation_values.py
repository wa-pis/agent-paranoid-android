"""Validation sees declared types across synthetic artifact formats."""

import copy
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.io.readers import load_dataset_rows
from test_data_agent.io.writers import rows_to_csv
from test_data_agent.validation import validate_dataset


def conditional_spec(data_type: str, predicate: Any) -> DatasetSpec:
    return DatasetSpec.model_validate({
        "entities": [{"name": "items", "row_count": 1, "fields": [
            {"name": "flag", "data_type": data_type},
            {"name": "note", "data_type": "string", "nullable": True},
        ]}],
        "constraints": [{"type": "conditional_required", "entity": "items", "fields": ["note"],
                         "condition": {"field": "flag", "equals": predicate}, "confidence": 1}],
    })


@pytest.mark.parametrize("data_type,predicate,value,valid", [
    ("boolean", True, True, False),
    ("boolean", True, False, True),
    ("integer", 7, 7, False),
    ("integer", 7, 8, True),
    ("string", "001", "001", False),
    ("string", "001", "1", True),
])
def test_conditions_survive_csv_and_json(
    tmp_path: Path, data_type: str, predicate: Any, value: Any, valid: bool,
) -> None:
    spec = conditional_spec(data_type, predicate)
    rows = {"items": [{"flag": value, "note": None}]}
    original = copy.deepcopy(rows)
    assert validate_dataset(rows, spec).valid is valid
    assert rows == original
    for suffix in ("csv", "json"):
        folder = tmp_path / suffix
        folder.mkdir()
        text = rows_to_csv(rows["items"]) if suffix == "csv" else json.dumps(rows["items"])
        (folder / f"items.{suffix}").write_text(text)
        loaded = load_dataset_rows(folder)
        before = copy.deepcopy(loaded)
        assert validate_dataset(loaded, spec).valid is valid
        assert loaded == before


@pytest.mark.parametrize("value", [[], {}, [1]])
@pytest.mark.parametrize("entity,field", [("parents", "id"), ("children", "parent_id")])
@pytest.mark.parametrize("schema_enabled", [False, True])
def test_composite_keys_report_errors(
    value: Any, entity: str, field: str, schema_enabled: bool,
) -> None:
    spec = DatasetSpec.model_validate({
        "entities": [
            {"name": "parents", "row_count": 1, "primary_key": "id", "fields": [
                {"name": "id", "data_type": "integer", "is_identifier": True}]},
            {"name": "children", "row_count": 1, "fields": [
                {"name": "parent_id", "data_type": "integer"}]},
        ],
        "relationships": [{"parent_entity": "parents", "parent_field": "id",
                           "child_entity": "children", "child_field": "parent_id", "confidence": 1}],
        "validation_settings": {"validate_schema": schema_enabled},
    })
    rows = {"parents": [{"id": 1}], "children": [{"parent_id": 1}]}
    rows[entity][0][field] = value
    report = validate_dataset(rows, spec)
    assert not report.valid
    assert all(section.errors == [f"{entity}[0].{field} must be a scalar"] for section in report.sections)


@pytest.mark.parametrize("fail_fast", [False, True])
def test_malformed_rows_respect_fail_fast(fail_fast: bool) -> None:
    spec = conditional_spec("boolean", True)
    spec.validation_settings.fail_fast = fail_fast
    report = validate_dataset({"items": [None]}, spec)  # type: ignore[list-item]
    assert not report.valid
    assert len(report.sections) == (1 if fail_fast else 4)
    assert report.sections[0].errors == ["items[0] row must be an object"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "nan", "inf"])
def test_nonfinite_floats_are_not_valid_schema_values(value: Any) -> None:
    spec = conditional_spec("float", 1)
    assert not validate_dataset({"items": [{"flag": value, "note": None}]}, spec).valid


@pytest.mark.parametrize("storage", ["python", "csv", "json", "parquet"])
def test_decimal_scalar_in_float_schema_is_format_independent(tmp_path: Path, storage: str) -> None:
    spec = conditional_spec("float", 1)
    rows = {"items": [{"flag": Decimal("1.25"), "note": None}]}
    original = copy.deepcopy(rows)
    if storage == "csv":
        (tmp_path / "items.csv").write_text(rows_to_csv(rows["items"]))
    elif storage == "json":
        (tmp_path / "items.json").write_text(json.dumps(rows["items"], default=str))
    elif storage == "parquet":
        pa = pytest.importorskip("pyarrow")
        pq = pytest.importorskip("pyarrow.parquet")
        pq.write_table(pa.Table.from_pylist(rows["items"]), tmp_path / "items.parquet")
    loaded = rows if storage == "python" else load_dataset_rows(tmp_path)
    assert validate_dataset(loaded, spec).valid
    assert rows == original
