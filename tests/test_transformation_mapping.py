from decimal import Decimal
import traceback

import pytest

from test_data_agent.core.transformation_mapping import (
    DomainMapping,
    MappingDeclarationError,
    parse_mapping_declaration,
    validate_inline_mapping_shape,
    validate_inline_scalar_mapping,
)
from test_data_agent.core.field import FieldType


def test_decimal_mapping_canonicalizes_exact_text():
    result = validate_inline_scalar_mapping({"kind": "inline", "entries": [
        {"original": ["1.0"], "replacement": ["2"]}]},
        data_types=(FieldType.DECIMAL,), nullable=(False,), decimal_shapes=((20, 2),))
    assert result.entries[0].original == ("1.00",)
    assert result.entries[0].replacement == ("2.00",)


def test_decimal_mapping_rejects_numeric_duplicate_keys():
    with pytest.raises(MappingDeclarationError):
        validate_inline_scalar_mapping({"kind": "inline", "entries": [
            {"original": ["1.0"], "replacement": ["2"]},
            {"original": ["1.00"], "replacement": ["3"]}]},
            data_types=(FieldType.DECIMAL,), nullable=(False,), decimal_shapes=((20, 2),))


@pytest.mark.parametrize("payload", [
    {"kind": "inline", "entries": [{"original": ["2025-04-30"], "replacement": ["2026-09-23"]}]},
    {"kind": "csv", "path": "fictional.csv", "source_columns": ["source"], "replacement_columns": ["target"]},
    {"kind": "domain", "name": "reporting_date"},
])
def test_private_mapping_roundtrip(payload):
    declaration = parse_mapping_declaration(payload)
    assert declaration.model_dump(mode="json", exclude_defaults=True) == payload
    assert parse_mapping_declaration(declaration.model_dump(mode="json")) == declaration
    assert repr(declaration) == f"{type(declaration).__name__}(kind={payload['kind']!r})"


@pytest.mark.parametrize("payload", [
    {"kind": "external_api", "url": "fictional-secret"},
    {"kind": "inline", "entries": []},
    {"kind": "domain", "name": "fictional-secret", "path": "also.csv"},
    {"kind": "inline", "entries": [{"original": [{}], "replacement": ["fictional-secret"]}]},
    {"kind": "inline", "entries": [{"original": [float("nan")], "replacement": [1]}]},
    {"kind": "csv", "path": 123, "source_columns": [], "replacement_columns": []},
])
def test_mapping_errors_are_detached_and_value_free(payload):
    with pytest.raises(MappingDeclarationError) as caught:
        parse_mapping_declaration(payload)
    assert str(caught.value) == "invalid mapping declaration"
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None


def test_mapping_scalar_kinds_and_null_are_not_conflated():
    values = [True, 1, 1.5, "1", "", None]
    declaration = parse_mapping_declaration({
        "kind": "inline", "entries": [{"original": values, "replacement": values}],
    })
    restored = declaration.model_dump(mode="json")["entries"][0]["original"]
    assert list(map(type, restored)) == list(map(type, values))


def test_preconstructed_models_cannot_skip_structural_validation():
    invalid = DomainMapping.model_construct(kind="domain", name=123)
    with pytest.raises(MappingDeclarationError):
        parse_mapping_declaration(invalid)


def test_decimal_cannot_silently_become_binary_float():
    with pytest.raises(MappingDeclarationError):
        parse_mapping_declaration({"kind": "inline", "entries": [{
            "original": [Decimal("1.234567890123456789")], "replacement": ["1.00"],
        }]})


def test_ambient_exception_is_not_retained_or_printed():
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(MappingDeclarationError) as caught:
            parse_mapping_declaration({"kind": "invalid"})
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert "fictional-private-marker" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("entries,width", [
    ([{"original": [1], "replacement": [2, 3]}], 1),
    ([{"original": [1, 2], "replacement": [3]}], 2),
    ([{"original": [1], "replacement": [2]}] * 2, 1),
    ([{"original": [None], "replacement": [2]}] * 2, 1),
    ([{"original": [1], "replacement": [2]}], True),
])
def test_inline_shape_rejects_width_and_duplicate_errors(entries, width):
    with pytest.raises(MappingDeclarationError, match="^invalid inline mapping shape$"):
        validate_inline_mapping_shape({"kind": "inline", "entries": entries}, key_width=width)


def test_inline_shape_preserves_typed_keys_and_allows_many_to_one():
    values = [True, 1, 1.0, "1", None, ""]
    payload = {"kind": "inline", "entries": [
        {"original": [value], "replacement": ["same"]} for value in values]}
    assert len(validate_inline_mapping_shape(payload, key_width=1).entries) == len(values)
    composite = {"kind": "inline", "entries": [
        {"original": [1, "a"], "replacement": [2, "b"]}]}
    assert validate_inline_mapping_shape(composite, key_width=2).entries[0].replacement == (2, "b")


@pytest.mark.parametrize("value,kind,allows_null,accepted", [
    (1, FieldType.INTEGER, False, True),
    (True, FieldType.INTEGER, False, False),
    ("1", FieldType.INTEGER, False, False),
    (1.0, FieldType.FLOAT, False, True),
    (1, FieldType.FLOAT, False, False),
    ("", FieldType.STRING, False, True),
    (None, FieldType.STRING, True, True),
    (None, FieldType.STRING, False, False),
    ("2025-04-30", FieldType.DATE, False, True),
    ("2025-04-30T12:34:56+03:00", FieldType.DATETIME, False, True),
    ("2025-04-30T09:34:56Z", FieldType.DATETIME, False, True),
    ("2025-04-30T12:34:56", FieldType.DATETIME, False, True),
])
def test_typed_mapping_never_coerces_or_conflates_null(value, kind, allows_null, accepted):
    payload = {"kind": "inline", "entries": [{"original": [value], "replacement": [value]}]}
    if accepted:
        assert validate_inline_scalar_mapping(payload, data_types=(kind,), nullable=(allows_null,))
    else:
        with pytest.raises(MappingDeclarationError, match="^invalid typed inline mapping$"):
            validate_inline_scalar_mapping(payload, data_types=(kind,), nullable=(allows_null,))


@pytest.mark.parametrize("value", ["2025-02-29", "20250430", "2025-W18-3",
    "2025-04-30T00:00:00", "2025-04-30T00:00:00Z", " 2025-04-30", "", 20250430])
@pytest.mark.parametrize("side", ["original", "replacement"])
def test_date_mapping_rejects_noncanonical_dates_on_both_sides(value, side):
    entry = {"original": ["2025-04-30"], "replacement": ["2026-09-23"]}
    entry[side] = [value]
    with pytest.raises(MappingDeclarationError, match="^invalid typed inline mapping$") as caught:
        validate_inline_scalar_mapping({"kind": "inline", "entries": [entry]},
                                      data_types=(FieldType.DATE,), nullable=(False,))
    assert caught.value.__context__ is None


def test_date_mapping_keeps_explicit_substitution_and_leap_date():
    entry = {"original": ["2024-02-29"], "replacement": ["2026-09-23"]}
    result = validate_inline_scalar_mapping({"kind": "inline", "entries": [entry]},
                                          data_types=(FieldType.DATE,), nullable=(False,))
    assert result.model_dump(mode="json")["entries"] == [entry]


@pytest.mark.parametrize("value", [
    "2025-02-29T12:00:00Z", "2025-04-30", "20250430T123456",
    "2025-04-30 12:34:56+03:00", "2025-04-30T12:34:56+0300",
    "2025-04-30T12:34:56z", " 2025-04-30T12:34:56Z", "", 123,
])
@pytest.mark.parametrize("side", ["original", "replacement"])
def test_datetime_mapping_rejects_noncanonical_text_on_both_sides(value, side):
    entry = {"original": ["2025-04-30T12:34:56+03:00"],
             "replacement": ["2026-09-23T09:34:56Z"]}
    entry[side] = [value]
    with pytest.raises(MappingDeclarationError, match="^invalid typed inline mapping$") as caught:
        validate_inline_scalar_mapping({"kind": "inline", "entries": [entry]},
                                      data_types=(FieldType.DATETIME,), nullable=(False,))
    assert caught.value.__context__ is None
