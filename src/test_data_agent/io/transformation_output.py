"""Private shared typed-output checks; no publication or database access."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from collections.abc import Iterator

from test_data_agent.core.field import FieldType
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.privacy import looks_sensitive_value
from test_data_agent.core.transformation_policy import TypedOutput
from test_data_agent.core.transformation_csv import normalize_csv_scalar
from test_data_agent.io.transformation_execute import CsvTransformationResult
from test_data_agent.postgres_sql_export import postgres_literal


def normalized_output_rows(result: CsvTransformationResult, output: TypedOutput, *,
                           budget: GenerationBudget,
                           source_rows: Iterator[tuple[str | int | float | Decimal | date | None, ...]] | None = None,
                           ) -> Iterator[tuple[list[str], list[Any]]]:
    """Share existing strict SQL-compatible scalars and final row safety gates."""
    if (tuple(item.name for item in output.fields) != result.columns
            or len(set(result.columns)) != len(result.columns)
            or any(looks_sensitive_value(name) for name in result.columns)):
        raise ValueError("invalid typed output schema")
    if result.mapped_cells and (len(result.mapped_cells) != len(result.rows)
            or any(type(mask) is not bytes or len(mask) != len(result.columns)
                   or any(flag not in (0, 1) for flag in mask) for mask in result.mapped_cells)):
        raise ValueError("invalid mapped-cell execution evidence")
    def literals(row: tuple[str | int | float | Decimal | date | None, ...], indices: tuple[int, ...] | None = None,
                 *, mapped: bytes = b"", check_sensitive: bool = True) -> tuple[list[str], list[Any]]:
        values = []
        logical = []
        fields = output.fields if indices is None else tuple(output.fields[index] for index in indices)
        for column, (value, item) in enumerate(zip(row, fields, strict=True)):
            budget.check("transformation SQL cell")
            if value is None and not item.nullable:
                raise ValueError("null in required SQL output field")
            shape = item.decimal_type
            if isinstance(value, str) and item.type == "float":
                normalize_csv_scalar(value, FieldType.FLOAT)
            encoded_value: Any = value
            if value is not None and item.temporal_type is not None and not (item.type == "date" and type(value) is date):
                if not isinstance(value, str):
                    raise ValueError("unsupported native temporal output")
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
            if (check_sensitive and not (mapped and mapped[column])
                    and encoded_value is not None and looks_sensitive_value(str(encoded_value))):
                raise ValueError("sensitive normalized SQL output")
            logical.append(encoded_value)
        return values, logical

    for row_index, row in enumerate(result.rows):
        values, logical = literals(row, mapped=result.mapped_cells[row_index] if result.mapped_cells else b"")
        if source_rows is not None:
            original = next(source_rows, None)
            if original is None:
                raise ValueError("typed output row count mismatch")
            changed = False
            for index, (source_value, final_value) in enumerate(zip(original, logical, strict=True)):
                try:
                    # Comparing fixed source values is not publication authority.
                    _, original_values = literals((source_value,), (index,), check_sensitive=False)
                except (ValueError, ArithmeticError):
                    continue  # Unknown comparison is not evidence that this row changed.
                changed |= original_values[0] != final_value
            if not changed:
                raise ValueError("SQL output retains complete source row or comparison is unresolved")
        yield values, logical
    if source_rows is not None and next(source_rows, None) is not None:
        raise ValueError("typed output row count mismatch")
