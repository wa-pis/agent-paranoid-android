"""Call-local reuse preserves mandatory checks and normalized report semantics."""

from copy import deepcopy
from unittest.mock import Mock

import pytest

import test_data_agent.validation.reconciliation as validation
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode


def related_spec() -> DatasetSpec:
    return DatasetSpec.model_validate({
        "entities": [
            {"name": "parents", "row_count": 1, "primary_key": "id", "fields": [
                {"name": "id", "data_type": "integer", "is_identifier": True}]},
            {"name": "children", "row_count": 1, "primary_key": "id", "fields": [
                {"name": "id", "data_type": "integer", "is_identifier": True},
                {"name": "parent_id", "data_type": "integer"},
                {"name": "quantity", "data_type": "integer"},
                {"name": "doubled", "data_type": "integer"}]},
        ],
        "relationships": [{"parent_entity": "parents", "parent_field": "id",
                           "child_entity": "children", "child_field": "parent_id",
                           "confidence": 1}],
        "constraints": [{"type": "formula", "entity": "children", "fields": ["doubled"],
                         "expression": "quantity * 2", "confidence": 1}],
    })


def related_rows():
    return {"parents": [{"id": 1}], "children": [
        {"id": 11, "parent_id": 1, "quantity": 3, "doubled": 6},
    ]}


def test_canonical_rows_run_each_check_and_normalization_once(monkeypatch):
    spec, rows = related_spec(), related_rows()
    expected = validation.validate_dataset(rows, spec)
    original_rows, original_spec = deepcopy(rows), spec.model_dump(mode="json")
    tracked = {}
    for name in ("assert_spec_safe", "validate_generated_row_privacy", "validate_schema",
                 "validate_relationships", "validate_constraints", "normalize_dataset_values"):
        tracked[name] = Mock(wraps=getattr(validation, name))
        monkeypatch.setattr(validation, name, tracked[name])

    report, normalized = validation._validate_generated_dataset(rows, spec)

    assert report == expected
    assert normalized is rows
    assert all(check.call_count == 1 for check in tracked.values())
    assert tracked["validate_generated_row_privacy"].call_args.kwargs == {}
    assert rows == original_rows and spec.model_dump(mode="json") == original_spec
    report.settings.fail_fast = True
    assert not spec.validation_settings.fail_fast


def test_numeric_key_conversion_keeps_normalized_uniqueness_check(monkeypatch):
    spec = related_spec()
    spec.entities[0].row_count = 2
    rows = related_rows()
    rows["parents"].append({"id": "1"})
    original = deepcopy(rows)
    expected = validation.validate_dataset(rows, spec)
    schema = Mock(wraps=validation.validate_schema)
    monkeypatch.setattr(validation, "validate_schema", schema)

    report, normalized = validation._validate_generated_dataset(rows, spec)

    assert report == expected and not report.valid
    assert "is not unique" in report.sections[0].errors[0]
    assert schema.call_count == 2
    assert normalized["parents"] == [{"id": 1}, {"id": 1}]
    assert rows == original


def test_conversion_keeps_normalized_relationship_check():
    spec, rows = related_spec(), related_rows()
    spec.entities[1].field("parent_id").data_type = "string"
    rows["parents"][0]["id"] = "1"
    rows["children"][0]["parent_id"] = "1"

    report, _ = validation._validate_generated_dataset(rows, spec)

    assert report == validation.validate_dataset(rows, spec)
    assert report.sections[1].errors == ["children[0].parent_id has no parent"]


def test_conversion_keeps_released_mandatory_conditional_check():
    spec = DatasetSpec.model_validate({
        "entities": [{"name": "items", "row_count": 1, "fields": [
            {"name": "active", "data_type": "boolean"},
            {"name": "note", "data_type": "string", "nullable": True}]}],
        "constraints": [{"type": "conditional_required", "entity": "items",
                         "fields": ["note"], "condition": {"field": "active", "equals": True},
                         "confidence": 1}],
    })
    rows = {"items": [{"active": "true", "note": None}]}

    report = validation.validate_dataset(rows, spec)
    assert report.sections[2].errors == ["items[0] missing conditional fields ['note']"]
    with pytest.raises(validation.GenerationValidationError,
                       match="^generated dataset failed post-solve constraint validation$"):
        validation._validate_generated_dataset(rows, spec)
    assert rows["items"][0]["active"] == "true"


@pytest.mark.parametrize("mode", list(GenerationMode))
def test_raw_numeric_strings_remain_subject_to_strict_privacy(mode):
    spec = DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 1,
        "fields": [{"name": "quantity", "data_type": "integer"}]}]})
    spec.generation_settings.mode = mode
    rows = {"items": [{"quantity": "12025550123"}]}
    assert validation.validate_dataset(rows, spec).valid
    for flag in ("validate_schema", "validate_relationships", "validate_constraints", "validate_privacy"):
        setattr(spec.validation_settings, flag, False)

    for check in (validation._validate_generated_dataset, validation.assert_generated_dataset_valid):
        with pytest.raises(validation.GenerationValidationError,
                           match="^generated dataset failed post-solve privacy validation$"):
            check(rows, spec)


@pytest.mark.parametrize("mode", [GenerationMode.MIXED, GenerationMode.NEGATIVE])
@pytest.mark.parametrize("fail_fast", [False, True])
@pytest.mark.parametrize("disabled", [False, True])
def test_negative_reports_preserve_flags_and_fail_fast(mode, fail_fast, disabled):
    spec, rows = related_spec(), related_rows()
    spec.generation_settings.mode = mode
    spec.validation_settings.fail_fast = fail_fast
    rows["children"][0]["quantity"] = "synthetic_wrong_type"
    if disabled:
        for flag in ("validate_schema", "validate_relationships", "validate_constraints", "validate_privacy"):
            setattr(spec.validation_settings, flag, False)

    report, normalized = validation._validate_generated_dataset(rows, spec)

    assert report == validation.validate_dataset(rows, spec)
    assert normalized is rows
    assert report.valid is disabled
    assert len(report.sections) == (0 if disabled else 1 if fail_fast else 4)


@pytest.mark.parametrize("fail_fast", [False, True])
def test_input_errors_override_every_enabled_report_section(fail_fast):
    spec, rows = related_spec(), related_rows()
    spec.generation_settings.mode = GenerationMode.NEGATIVE
    spec.validation_settings.fail_fast = fail_fast
    rows["extra"] = [{"nested": []}]

    report, _ = validation._validate_generated_dataset(rows, spec)

    assert report == validation.validate_dataset(rows, spec)
    assert len(report.sections) == (1 if fail_fast else 4)
    assert all(section.errors == ["extra[0].nested must be a scalar"] for section in report.sections)


@pytest.mark.parametrize("mutate_spec", [False, True])
def test_success_never_caches_mutable_rows_or_specs(mutate_spec):
    spec, rows = related_spec(), related_rows()
    assert validation._validate_generated_dataset(rows, spec)[0].valid
    if mutate_spec:
        spec.constraints[0].expression = "quantity * 3"
    else:
        rows["children"][0]["doubled"] = 9

    with pytest.raises(validation.GenerationValidationError,
                       match="^generated dataset failed post-solve constraint validation$"):
        validation._validate_generated_dataset(rows, spec)


@pytest.mark.parametrize("mode", [GenerationMode.VALID, GenerationMode.EDGE, GenerationMode.LOAD_TEST])
@pytest.mark.parametrize("violation,field,value,expected_calls", [
    ("privacy", "quantity", "fictional-person@example.invalid", [1, 0, 0, 0]),
    ("type", "quantity", "synthetic_wrong_type", [1, 1, 0, 0]),
    ("constraint", "parent_id", 99, [1, 1, 1, 0]),
    ("constraint", "doubled", 9, [1, 1, 1, 1]),
])
def test_mandatory_order_and_errors_ignore_report_flags(
    monkeypatch, mode, violation, field, value, expected_calls,
):
    spec, rows = related_spec(), related_rows()
    spec.generation_settings.mode = mode
    for flag in ("validate_schema", "validate_relationships", "validate_constraints", "validate_privacy"):
        setattr(spec.validation_settings, flag, False)
    rows["children"][0][field] = value
    tracked = []
    for name in ("validate_generated_row_privacy", "validate_schema",
                 "validate_relationships", "validate_constraints"):
        check = Mock(wraps=getattr(validation, name))
        monkeypatch.setattr(validation, name, check)
        tracked.append(check)

    for check in (validation.assert_generated_dataset_valid, validation._validate_generated_dataset):
        with pytest.raises(validation.GenerationValidationError,
                           match=f"^generated dataset failed post-solve {violation} validation$"):
            check(rows, spec)
        assert [spy.call_count for spy in tracked] == expected_calls
        for spy in tracked:
            spy.reset_mock()
