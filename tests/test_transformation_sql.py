"""Fictional private SQL serialization; no database connections."""

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import SqlOutput
from test_data_agent.core.transformation_report import retention_summary_from_counts
from test_data_agent.io.transformation_execute import CsvTransformationResult
from test_data_agent.io.transformation_sql import render_transformation_sql


def render(value, kind="integer", nullable=False, limit=4096):
    output = SqlOutput.model_validate({"format": "postgresql_sql", "table": "items",
        "fields": [{"name": "value", "type": kind, "nullable": nullable}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0),
                                     ("value",), ((value,),))
    return render_transformation_sql(result, output, max_bytes=limit, budget=GenerationBudget(5))


@pytest.mark.parametrize("value", [str(-(2**63)), str(2**63 - 1)])
def test_bigint_boundaries(value):
    assert f"VALUES ({value});".encode() in render(value)


def test_integer_cast_cannot_restore_complete_source_row():
    output = SqlOutput.model_validate({"format": "postgresql_sql", "table": "items",
        "fields": [{"name": "value", "type": "integer"}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0), ("value",), ((" 1 ",),))
    with pytest.raises(ValueError, match="complete source row"):
        render_transformation_sql(result, output, max_bytes=4096,
            budget=GenerationBudget(5), source_rows=iter([("1",)]))
    assert b"VALUES (1);" in render_transformation_sql(result, output, max_bytes=4096,
        budget=GenerationBudget(5), source_rows=iter([("2",)]))


@pytest.mark.parametrize("kind,source,target,settings", [
    ("decimal", "1.0", "1.00", {"decimal_type": {"precision": 5, "scale": 2}}),
    ("float", "0.0", "-0.0", {}),
    ("datetime", "2026-08-31T04:00:00+0400", "2026-08-31T00:00:00+0000",
     {"temporal_type": {"type": "datetime", "format": "%Y-%m-%dT%H:%M:%S%z",
                         "output_format": "%Y-%m-%dT%H:%M:%S.%f%z"}}),
])
def test_sql_equivalent_spelling_does_not_count_as_row_change(kind, source, target, settings):
    output = SqlOutput.model_validate({"format": "postgresql_sql", "table": "items",
        "fields": [{"name": "value", "type": kind, **settings}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0), ("value",), ((target,),))
    with pytest.raises(ValueError, match="complete source row"):
        render_transformation_sql(result, output, max_bytes=4096,
            budget=GenerationBudget(5), source_rows=iter([(source,)]))


@pytest.mark.parametrize("value", [str(-(2**63) - 1), str(2**63), "1.5", "fictional", ""])
def test_invalid_bigint_rejects(value):
    with pytest.raises(ValueError):
        render(value)


def test_null_empty_and_output_budget():
    assert b"VALUES (NULL);" in render(None, kind="string", nullable=True)
    assert b"VALUES ('');" in render("", kind="string", nullable=True)
    with pytest.raises(ValueError):
        render(None)
    payload = render("7")
    assert render("7", limit=len(payload)) == payload
    with pytest.raises(ValueError):
        render("7", limit=len(payload) - 1)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1e999", "1e-999"])
def test_float_rejects_nonfinite_and_underflow(value):
    with pytest.raises(ValueError):
        render(value, kind="float")


@pytest.mark.parametrize("columns,row", [(("other",), ("7",)),
    (("value",), ("7", "8")), (("value",), ())])
def test_schema_mismatch_rejects(columns, row):
    output = SqlOutput.model_validate({"format": "postgresql_sql", "table": "items",
        "fields": [{"name": "value", "type": "integer"}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0), columns, (row,))
    with pytest.raises(ValueError):
        render_transformation_sql(result, output, max_bytes=4096, budget=GenerationBudget(5))


@pytest.mark.parametrize("value,valid", [("12.34", True), ("12.345", False), ("1000.00", False)])
def test_decimal_output_exact_shape(value, valid):
    output = SqlOutput.model_validate({"format": "postgresql_sql", "table": "items",
        "fields": [{"name": "value", "type": "decimal", "decimal_type": {"precision": 5, "scale": 2}}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0), ("value",), ((value,),))
    if valid:
        assert b"VALUES (12.34);" in render_transformation_sql(result, output,
            max_bytes=4096, budget=GenerationBudget(5))
    else:
        with pytest.raises(ValueError):
            render_transformation_sql(result, output, max_bytes=4096, budget=GenerationBudget(5))


@pytest.mark.parametrize("kind,value,pattern,zone,expected", [
    ("date", "31/08/2026", "%d/%m/%Y", None, "DATE '2026-08-31'"),
    ("datetime", "2026-08-31 03:15:00", "%Y-%m-%d %H:%M:%S", "Europe/Samara",
     "TIMESTAMPTZ '2026-08-30 23:15:00+00:00'"),
    ("datetime", "2026-10-25 02:30:00", "%Y-%m-%d %H:%M:%S", "Europe/Berlin", None),
])
def test_explicit_temporal_sql(kind, value, pattern, zone, expected):
    temporal = {"type": kind, "format": pattern,
        "output_format": "%Y-%m-%d" if kind == "date" else "%Y-%m-%dT%H:%M:%S.%f%z"}
    if zone:
        temporal.update(source_timezone=zone, target_timezone="UTC")
    output = SqlOutput.model_validate({"format": "postgresql_sql", "table": "items",
        "fields": [{"name": "value", "type": kind, "temporal_type": temporal}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0), ("value",), ((value,),))
    if expected:
        assert expected.encode() in render_transformation_sql(result, output,
            max_bytes=4096, budget=GenerationBudget(5))
    else:
        with pytest.raises(ValueError):
            render_transformation_sql(result, output, max_bytes=4096, budget=GenerationBudget(5))
