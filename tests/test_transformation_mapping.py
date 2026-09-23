from decimal import Decimal
import traceback

import pytest

from test_data_agent.core.transformation_mapping import (
    DomainMapping,
    MappingDeclarationError,
    parse_mapping_declaration,
)


@pytest.mark.parametrize("payload", [
    {"kind": "inline", "entries": [{"original": ["2025-04-30"], "replacement": ["2026-09-23"]}]},
    {"kind": "csv", "path": "fictional.csv", "source_columns": ["source"], "replacement_columns": ["target"]},
    {"kind": "domain", "name": "reporting_date"},
])
def test_private_mapping_roundtrip(payload):
    declaration = parse_mapping_declaration(payload)
    assert declaration.model_dump(mode="json") == payload
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
