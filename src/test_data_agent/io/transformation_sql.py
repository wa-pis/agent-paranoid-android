"""Private SQL encoding of validated transformation results; never executes SQL."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from collections.abc import Iterator

from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.privacy import looks_sensitive_value
from test_data_agent.core.transformation_policy import SqlOutput
from test_data_agent.core.transformation_csv import normalize_csv_scalar
from test_data_agent.io.transformation_execute import CsvTransformationResult
from test_data_agent.postgres_sql_export import postgres_literal, quote_postgres_identifier


def render_transformation_sql(result: CsvTransformationResult, output: SqlOutput, *,
                              max_bytes: int, budget: GenerationBudget,
                              source_rows: Iterator[tuple[str | None, ...]] | None = None) -> bytes:
    """Encode an exact ordered output schema; caller owns approval and publication."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("invalid SQL output budget")
    if (tuple(item.name for item in output.fields) != result.columns
            or len(set(result.columns)) != len(result.columns)
            or any(looks_sensitive_value(name) for name in (output.table, *result.columns))):
        raise ValueError("invalid SQL output schema")
    payload = bytearray()

    def append(statement: str) -> None:
        budget.check("transformation SQL output")
        encoded = statement.encode("utf-8")
        if len(payload) + len(encoded) > max_bytes:
            raise ValueError("SQL output budget exceeded")
        payload.extend(encoded)

    types = {"string": "TEXT", "integer": "BIGINT", "float": "DOUBLE PRECISION", "boolean": "BOOLEAN",
             "date": "DATE", "datetime": "TIMESTAMPTZ"}
    definitions = []
    for item in output.fields:
        shape = item.decimal_type
        sql_type = f"NUMERIC({shape.precision},{shape.scale})" if shape else types[item.type]
        definitions.append(f"{quote_postgres_identifier(item.name)} {sql_type}" + ("" if item.nullable else " NOT NULL"))
    table = quote_postgres_identifier(output.table)
    columns = ", ".join(quote_postgres_identifier(name) for name in result.columns)
    append("BEGIN;\nSET LOCAL standard_conforming_strings = on;\n")
    append(f"CREATE TABLE {table} ({', '.join(definitions)});\n")
    def literals(row: tuple[str | None, ...]) -> tuple[list[str], list[Any]]:
        values = []
        logical = []
        for value, item in zip(row, output.fields, strict=True):
            budget.check("transformation SQL cell")
            if value is None and not item.nullable:
                raise ValueError("null in required SQL output field")
            shape = item.decimal_type
            if value is not None and item.type == "float":
                normalize_csv_scalar(value, FieldType.FLOAT)
            encoded_value: Any = value
            if value is not None and item.temporal_type is not None:
                canonical = item.temporal_type.render(value)
                encoded_value = date.fromisoformat(canonical) if item.type == "date" else datetime.fromisoformat(canonical)
                if item.type == "datetime" and encoded_value.tzinfo is None:
                    raise ValueError("SQL datetime requires explicit offset")
            literal = postgres_literal(encoded_value, FieldType(item.type),
                precision=shape.precision if shape else None, scale=shape.scale if shape else None)
            if value is not None and item.type == "integer" and not -(2**63) <= int(literal) < 2**63:
                raise ValueError("SQL integer exceeds BIGINT range")
            values.append(literal)
            if value is not None and item.type in {"integer", "decimal"}:
                encoded_value = Decimal(literal)
            elif value is not None and item.type == "float":
                encoded_value = float(literal)
            elif value is not None and item.type == "boolean":
                encoded_value = literal == "TRUE"
            logical.append(encoded_value)
        return values, logical

    for row in result.rows:
        values, logical = literals(row)
        if source_rows is not None:
            original = next(source_rows)
            try:
                _, original_values = literals(original)
            except (ValueError, ArithmeticError):
                original_values = None
            if original_values == logical:
                raise ValueError("SQL output retains complete source row")
        append(f"INSERT INTO {table} ({columns}) VALUES ({', '.join(values)});\n")
    append("COMMIT;\n")
    return bytes(payload)
