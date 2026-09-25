from dataclasses import asdict

import pytest

from test_data_agent.core.transformation_csv import (
    compile_text_replacement_table, match_scoped_text, normalize_csv_mapping,
    parse_csv_mapping_bytes, replace_text_row,
    summarize_text_trace, text_trace_event, TextTraceEvent,
)
from test_data_agent.core.field import FieldType
from test_data_agent.core.transformation_mapping import parse_mapping_declaration
from test_data_agent.core.transformation_mapping import CsvMapping, MappingDeclarationError
from test_data_agent.core.limits import GenerationBudget


def parse(payload, **limits):
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",), null_token="NULL")
    return parse_csv_mapping_bytes(payload, declaration,
                                   budget=limits.pop("budget", GenerationBudget()), **limits)


def test_text_replacement_table_is_exact_and_one_pass():
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    table = compile_text_replacement_table(
        b"old,new\ntrue,false\n001,1\nfalse,true\n", declaration, budget=GenerationBudget(),
    )
    assert table.lookup("true") == ("false", 1)
    assert table.lookup("001") == ("1", 2)
    assert table.lookup("false") == ("true", 3)
    assert table.lookup("1") is None
    assert "true" not in repr(table)


@pytest.mark.parametrize("payload", [
    b"old,new\na,b\na,c\n",
    b"old,new\na,NULL\n",
    b"old,new\na,a\n",
])
def test_text_replacement_table_rejects_ambiguous_or_null_pairs(payload):
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",), null_token="NULL")
    with pytest.raises(MappingDeclarationError):
        compile_text_replacement_table(payload, declaration, budget=GenerationBudget())


def test_file_and_column_text_rules_match_without_cascade():
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    file_table = compile_text_replacement_table(
        b"old,new\nfalse,global-next\n", declaration, budget=GenerationBudget(),
    )
    column_table = compile_text_replacement_table(
        b"old,new\ntrue,false\n", declaration, budget=GenerationBudget(),
    )
    matched = match_scoped_text("true", "flag", file_table, {"flag": column_table})
    assert matched is not None
    assert (matched.replacement, matched.scope, matched.rule_ordinal) == ("false", "column", 1)
    assert "false" not in repr(matched)
    assert match_scoped_text("false", "status", file_table, {"flag": column_table}).scope == "file"
    assert match_scoped_text("unmapped", "flag", file_table, {"flag": column_table}) is None
    assert asdict(text_trace_event(2, 1, matched)) == {
        "row_ordinal": 2, "column_ordinal": 1, "matched": True,
        "scope": "column", "rule_ordinal": 1,
    }
    assert asdict(text_trace_event(3, 1, None)) == {
        "row_ordinal": 3, "column_ordinal": 1, "matched": False,
        "scope": None, "rule_ordinal": None,
    }


def test_overlapping_file_and_column_rules_reject_without_values():
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    file_table = compile_text_replacement_table(
        b"old,new\ntrue,global-false\n", declaration, budget=GenerationBudget(),
    )
    column_table = compile_text_replacement_table(
        b"old,new\ntrue,local-false\n", declaration, budget=GenerationBudget(),
    )
    with pytest.raises(MappingDeclarationError) as error:
        match_scoped_text("true", "flag", file_table, {"flag": column_table})
    assert str(error.value) == "conflicting text replacement scopes"
    assert "true" not in repr(error.value)


def test_file_wide_and_column_rules_replace_entire_row_once():
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    file_table = compile_text_replacement_table(
        b"old,new\ntrue,false\nfalse,next\n001,1\n", declaration, budget=GenerationBudget(),
    )
    column_table = compile_text_replacement_table(
        b"old,new\nlocal,column-result\n", declaration, budget=GenerationBudget(),
    )
    assert replace_text_row(
        ("true", "local", "001"), ("a", "b", "c"), file_table, {"b": column_table},
    ) == ("false", "column-result", "1")
    assert replace_text_row(("false",), ("a",), file_table, {}) == ("next",)


def test_text_row_rejects_unmapped_and_overlapping_cells_without_values():
    declaration = CsvMapping(kind="csv", path="not-opened.csv",
                             source_columns=("old",), replacement_columns=("new",))
    file_table = compile_text_replacement_table(
        b"old,new\ntrue,false\n", declaration, budget=GenerationBudget(),
    )
    column_table = compile_text_replacement_table(
        b"old,new\ntrue,column-result\n", declaration, budget=GenerationBudget(),
    )
    for values, columns, column_tables, message in (
        (("true", "private-marker"), ("a", "b"), {}, "unmapped text replacement"),
        (("true",), ("a",), {"a": column_table}, "conflicting text replacement scopes"),
    ):
        with pytest.raises(MappingDeclarationError) as error:
            replace_text_row(values, columns, file_table, column_tables)
        assert str(error.value) == message
        assert "private-marker" not in str(error.value)


def test_text_row_rejects_duplicate_columns():
    with pytest.raises(MappingDeclarationError, match="^invalid text replacement row$"):
        replace_text_row(("true", "false"), ("flag", "flag"), None, {})


def test_text_trace_counts_all_cells_but_limits_local_events():
    events = [
        text_trace_event(1, 1, match_scoped_text("true", "flag", None, {
            "flag": compile_text_replacement_table(
                b"old,new\ntrue,false\n", CsvMapping(kind="csv", path="not-opened.csv",
                source_columns=("old",), replacement_columns=("new",)), budget=GenerationBudget(),
            ),
        })),
        text_trace_event(1, 2, None),
        text_trace_event(2, 1, None),
    ]
    summary = summarize_text_trace(events, max_events=1, max_cells=3,
                                   max_rule_counts=1, budget=GenerationBudget())
    assert summary.events == (events[0],)
    assert (summary.matched_cells, summary.unmatched_cells, summary.truncated) == (1, 2, True)
    assert summary.rule_counts == ((1, "column", 1, 1),)
    assert "true" not in repr(summary)
    assert "false" not in repr(summary)


def test_text_trace_rejects_forged_values_and_rule_bucket_overflow():
    forged = TextTraceEvent("fictional-private-marker", 1, False, None, None)
    with pytest.raises(MappingDeclarationError, match="^invalid text trace event$") as error:
        summarize_text_trace([forged], max_events=1, max_cells=2,
                             max_rule_counts=1, budget=GenerationBudget())
    assert "fictional-private-marker" not in str(error.value)
    events = [TextTraceEvent(1, 1, True, "file", 1),
              TextTraceEvent(1, 2, True, "file", 1)]
    with pytest.raises(MappingDeclarationError, match="^text trace rule limit exceeded$"):
        summarize_text_trace(events, max_events=1, max_cells=2,
                             max_rule_counts=1, budget=GenerationBudget())


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
                             source_columns=("old",), replacement_columns=("new",),
                             encoding="utf-8-sig", delimiter=delimiter)
    payload = ("\ufeffold" + delimiter + "new\r\nNULL" + delimiter + '"two\nlines"\r\n').encode()
    result = parse_csv_mapping_bytes(payload, declaration, budget=GenerationBudget())
    assert result.entries[0].original == ("NULL",)
    assert result.entries[0].replacement == ("two\nlines",)


@pytest.mark.parametrize("overrides", [
    {"encoding": "latin-1"}, {"delimiter": "::"}, {"null_token": ""},
    {"null_token": 3},
])
def test_invalid_configuration_is_value_free(overrides):
    payload = {"kind": "csv", "path": "not-opened.csv", "source_columns": ["old"],
               "replacement_columns": ["new"], **overrides}
    with pytest.raises(MappingDeclarationError, match="^invalid mapping declaration$"):
        parse_mapping_declaration(payload)


@pytest.mark.parametrize("limits", [{"max_rows": True}, {"max_columns": 0}])
def test_invalid_limits_are_value_free(limits):
    with pytest.raises(MappingDeclarationError, match="^invalid CSV mapping$"):
        parse(b"old,new\na,b\n", **limits)


def test_integer_normalization_preserves_composite_strings_and_null():
    mapping = parse_mapping_declaration({"kind": "inline", "entries": [
        {"original": ["01", "001"], "replacement": [None, "002"]}]})
    result = normalize_csv_mapping(mapping, data_types=(FieldType.INTEGER, FieldType.STRING),
                                   nullable=(True, False), budget=GenerationBudget())
    assert result.entries[0].original == (1, "001")
    assert result.entries[0].replacement == (None, "002")


def test_datetime_csv_uses_same_canonical_validation_without_timezone_conversion():
    mapping = parse(b"old,new\n2025-04-30T12:34:56+03:00,2026-09-23T09:34:56Z\n")
    result = normalize_csv_mapping(mapping, data_types=(FieldType.DATETIME,),
                                   nullable=(False,), budget=GenerationBudget())
    assert result.entries[0].original == ("2025-04-30T12:34:56+03:00",)
    assert result.entries[0].replacement == ("2026-09-23T09:34:56Z",)

    invalid = parse(b"old,new\n2025-04-30 12:34:56+03:00,2026-09-23T09:34:56Z\n")
    with pytest.raises(MappingDeclarationError, match="^invalid typed CSV mapping$"):
        normalize_csv_mapping(invalid, data_types=(FieldType.DATETIME,),
                              nullable=(False,), budget=GenerationBudget())


def test_float_normalization_is_approximate_and_catches_converted_duplicates():
    mapping = parse_mapping_declaration({"kind": "inline", "entries": [
        {"original": ["+1.25e2"], "replacement": ["-0.5"]}]})
    result = normalize_csv_mapping(mapping, data_types=(FieldType.FLOAT,),
                                   nullable=(False,), budget=GenerationBudget())
    assert result.entries[0].original == (125.0,)
    assert result.entries[0].replacement == (-0.5,)

    duplicates = parse_mapping_declaration({"kind": "inline", "entries": [
        {"original": ["1.0"], "replacement": ["2.0"]},
        {"original": ["1e0"], "replacement": ["3.0"]}]})
    with pytest.raises(MappingDeclarationError, match="^invalid typed CSV mapping$"):
        normalize_csv_mapping(duplicates, data_types=(FieldType.FLOAT,),
                              nullable=(False,), budget=GenerationBudget())


@pytest.mark.parametrize("value", ["nan", "Infinity", "1e9999", "1e-9999", " 1", "1_000", "0x10"])
def test_float_normalization_rejects_nonfinite_or_ambiguous_text(value):
    mapping = parse_mapping_declaration({"kind": "inline", "entries": [
        {"original": [value], "replacement": ["1.0"]}]})
    with pytest.raises(MappingDeclarationError, match="^invalid typed CSV mapping$"):
        normalize_csv_mapping(mapping, data_types=(FieldType.FLOAT,),
                              nullable=(False,), budget=GenerationBudget())


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
