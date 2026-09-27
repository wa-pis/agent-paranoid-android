"""Fictional Parquet round trips through private typed-output safety gates."""

import io
from datetime import date
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import ParquetOutput
from test_data_agent.core.transformation_report import retention_summary_from_counts
from test_data_agent.io.transformation_execute import CsvTransformationResult
from test_data_agent.io.transformation_parquet import render_transformation_parquet

pq = pytest.importorskip("pyarrow.parquet")


def render(value, kind="string", *, source=None, limit=8192, **settings):
    output = ParquetOutput.model_validate({"format": "parquet", "fields": [
        {"name": "value", "type": kind, **settings}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0),
                                     ("value",), ((value,),))
    return render_transformation_parquet(result, output, max_bytes=limit,
        budget=GenerationBudget(5), source_rows=iter([(source,)]) if source is not None else None)


@pytest.mark.parametrize("value,kind,settings,expected", [
    ("", "string", {}, ""), (None, "string", {"nullable": True}, None),
    ("7", "integer", {}, 7), ("1.25", "float", {}, 1.25),
    ("true", "boolean", {}, True),
    ("12.34", "decimal", {"decimal_type": {"precision": 5, "scale": 2}}, Decimal("12.34")),
    ("31/08/2026", "date", {"temporal_type": {"type": "date", "format": "%d/%m/%Y",
        "output_format": "%Y-%m-%d"}}, date(2026, 8, 31)),
])
def test_typed_round_trip(value, kind, settings, expected):
    assert pq.read_table(io.BytesIO(render(value, kind, **settings))).to_pylist() == [{"value": expected}]


@pytest.mark.parametrize("value,kind", [(None, "string"), ("1e-999", "float"),
    ("1.234567e6", "float"), (str(2**63), "integer")])
def test_invalid_or_sensitive_normalized_value(value, kind):
    with pytest.raises(ValueError):
        render(value, kind)


def test_budget_and_normalized_source_reuse():
    payload = render("7", "integer")
    assert render("7", "integer", limit=len(payload)) == payload
    with pytest.raises(ValueError):
        render("7", "integer", limit=len(payload) - 1)
    with pytest.raises(ValueError, match="complete source row"):
        render(" 1 ", "integer", source="1")


def test_explicit_timezone_round_trip_and_all_null_rejection():
    temporal = {"type": "datetime", "format": "%Y-%m-%d %H:%M:%S",
        "output_format": "%Y-%m-%dT%H:%M:%S.%f%z",
        "source_timezone": "Europe/Samara", "target_timezone": "UTC"}
    payload = render("2026-08-31 03:15:00", "datetime", temporal_type=temporal)
    assert pq.read_table(io.BytesIO(payload)).to_pylist() == [
        {"value": datetime(2026, 8, 30, 23, 15, tzinfo=timezone.utc)}]
    payload = render(None, "datetime", nullable=True, temporal_type=temporal)
    table = pq.read_table(io.BytesIO(payload))
    assert table.schema.field("value").type.tz == "UTC"
    assert table.to_pylist() == [{"value": None}]
    with pytest.raises(ValueError, match="explicit timezone"):
        render(None, "datetime", nullable=True, temporal_type={
            "type": "datetime", "format": "%Y-%m-%dT%H:%M:%S%z",
            "output_format": "%Y-%m-%dT%H:%M:%S.%f%z"})


@pytest.mark.parametrize("columns,rows,source", [
    (("other",), (("second",),), None),
    (("value",), (("second", "extra"),), None),
    (("value",), (("second",),), []),
    (("value",), (("second",),), [("first",), ("third",)]),
])
def test_schema_and_source_cardinality_reject(columns, rows, source):
    output = ParquetOutput.model_validate({"format": "parquet", "fields": [
        {"name": "value", "type": "string"}]})
    result = CsvTransformationResult(b"", retention_summary_from_counts(0, 1, 0), columns, rows)
    with pytest.raises(ValueError):
        render_transformation_parquet(result, output, max_bytes=8192,
            budget=GenerationBudget(5), source_rows=None if source is None else iter(source))
