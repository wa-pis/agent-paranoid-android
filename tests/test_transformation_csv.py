import pytest

from test_data_agent.core.transformation_csv import normalize_csv_mapping, parse_csv_mapping_bytes
from test_data_agent.core.field import FieldType
from test_data_agent.core.transformation_mapping import parse_mapping_declaration
from test_data_agent.core.transformation_mapping import CsvMapping, MappingDeclarationError
from test_data_agent.core.limits import GenerationBudget


def parse(payload, **limits):
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    return parse_csv_mapping_bytes(payload, declaration, encoding="utf-8",
                                   delimiter=",", null_token="NULL",
                                   budget=limits.pop("budget", GenerationBudget()), **limits)


def test_private_csv_pairs_preserve_empty_and_explicit_null():
    result = parse(b'new,old\n2026-09-23,2025-04-30\nNULL,""\n')
    assert result.entries[0].original == ("2025-04-30",)
    assert result.entries[0].replacement == ("2026-09-23",)
    assert result.entries[1].original == ("",)
    assert result.entries[1].replacement == (None,)


@pytest.mark.parametrize("payload,limits", [
    (b"old,new\na,b\n", {"max_bytes": 3}),
    (b"old,new\na,b\nc,d\n", {"max_rows": 1}),
    (b"old,new\na,b\n", {"max_cells": 1}),
    (b"old,new\na,b\n", {"max_columns": 1}),
    (b"old,new\nlong,b\n", {"max_cell_chars": 3}),
    (b"old,new\na,b\na,c\n", {}),
    (b"old,new\na\n", {}),
    (b"old,new\na,b,c\n", {}),
    (b"old,old\na,b\n", {}),
    (b"old,new,extra\na,b,c\n", {}),
    (b'old,new\n"unterminated,b\n', {}),
    (b"old,new\n\xff,b\n", {}),
])
def test_invalid_csv_is_bounded_and_detached(payload, limits):
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(MappingDeclarationError) as caught:
            parse(payload, **limits)
    assert str(caught.value) == "invalid CSV mapping"
    assert caught.value.__context__ is None


def test_csv_reuses_invocation_deadline():
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    tick[0] = 2.0
    with pytest.raises(MappingDeclarationError, match="^invalid CSV mapping$"):
        parse(b"old,new\na,b\n", budget=budget)


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_explicit_dialect_bom_and_no_null_conversion(delimiter):
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    payload = ("\ufeffold" + delimiter + "new\r\nNULL" + delimiter + '"two\nlines"\r\n').encode()
    result = parse_csv_mapping_bytes(payload, declaration, encoding="utf-8-sig",
                                    delimiter=delimiter, null_token=None, budget=GenerationBudget())
    assert result.entries[0].original == ("NULL",)
    assert result.entries[0].replacement == ("two\nlines",)


@pytest.mark.parametrize("overrides", [
    {"encoding": "latin-1"}, {"delimiter": "::"}, {"null_token": ""},
    {"null_token": 3}, {"max_rows": True}, {"max_columns": 0},
])
def test_invalid_configuration_is_value_free(overrides):
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    options = {"encoding": "utf-8", "delimiter": ",", "null_token": None,
               "budget": GenerationBudget(), **overrides}
    with pytest.raises(MappingDeclarationError, match="^invalid CSV mapping$"):
        parse_csv_mapping_bytes(b"old,new\na,b\n", declaration, **options)


def test_integer_normalization_preserves_composite_strings_and_null():
    mapping = parse_mapping_declaration({"kind": "inline", "entries": [
        {"original": ["01", "001"], "replacement": [None, "002"]}]})
    result = normalize_csv_mapping(mapping, data_types=(FieldType.INTEGER, FieldType.STRING),
                                   nullable=(True, False), budget=GenerationBudget())
    assert result.entries[0].original == (1, "001")
    assert result.entries[0].replacement == (None, "002")


@pytest.mark.parametrize("case", ["nullability", "expired", "already_typed", "invalid_type"])
def test_normalization_failures_are_detached(case):
    mapping = parse_mapping_declaration({"kind": "inline", "entries": [
        {"original": [1 if case == "already_typed" else "1"], "replacement": [None]}]})
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    if case == "expired":
        tick[0] = 2.0
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(MappingDeclarationError) as caught:
            normalize_csv_mapping(mapping, data_types=("integer" if case == "invalid_type" else FieldType.INTEGER,),
                                  nullable=(case != "nullability",), budget=budget)
    assert str(caught.value) == "invalid typed CSV mapping"
    assert caught.value.__context__ is None
