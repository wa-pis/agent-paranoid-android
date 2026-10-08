"""Private fixed-byte source decoding; no file reopening or implicit stringify."""

import io
import math
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from dataclasses import dataclass, field
from collections.abc import Iterator

from test_data_agent.core.limits import (
    GenerationBudget,
)
from test_data_agent.core.transformation_limits import InputDimension, resolve_input_limit
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.field import FieldType
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.csv_profiler import _csv_reader_from_snapshot, validate_csv_headers, parse_bool
from test_data_agent.io.transformation_query_snapshot import _query_result_payload


@dataclass(repr=False)
class NativeSourceRows:
    fieldnames: list[str]
    rows: tuple[dict[str, str | int | float | Decimal | date | datetime | None], ...] = field(repr=False)
    types: dict[str, FieldType] = field(repr=False)
    decimal_shapes: dict[str, tuple[int, int]] = field(default_factory=dict, repr=False)

    def __iter__(self) -> Iterator[dict[str, str | int | float | Decimal | date | datetime | None]]:
        return iter(self.rows)


def source_reader(source: SnapshotPart, policy: BehaviorPolicy, *, budget: GenerationBudget) -> Any:
    """Decode supported nullable native scalars; never stringify for matching."""
    budget.check("transformation source decode")
    limits = {item: resolve_input_limit(item, policy.resource_limits, os.environ) for item in InputDimension}
    limits[InputDimension.BYTES].check(len(source.payload))
    if policy.input_format == "csv":
        if any(item.match_format is not None for item in policy.fields):
            raise ValueError("native match format cannot reformat CSV text")
        cell_limit = limits[InputDimension.CELL_CHARS]
        reader = _csv_reader_from_snapshot(source.payload, max_chars=cell_limit.value,
                                           check_size=cell_limit.check)
        names = validate_csv_headers(reader.fieldnames)
        limits[InputDimension.COLUMNS].check(len(names))

        class BoundedCsvRows:
            def __init__(self) -> None:
                self.count = 0
                reader.fieldnames = names

            @property
            def fieldnames(self) -> Any:
                return reader.fieldnames

            @fieldnames.setter
            def fieldnames(self, value: Any) -> None:
                reader.fieldnames = value

            def __iter__(self) -> "BoundedCsvRows":
                return self

            def __next__(self) -> Any:
                row = next(reader)
                self.count += 1
                budget.check("transformation CSV input row")
                limits[InputDimension.ROWS].check(self.count)
                limits[InputDimension.CELLS].check(self.count * len(names))
                for value in row.values():
                    if type(value) is str:
                        limits[InputDimension.CELL_CHARS].check(len(value))
                return row

        return BoundedCsvRows()
    if policy.csv_nulls.input_token is not None:
        raise ValueError("native input cannot use a CSV null marker")
    payload = source.payload
    if policy.input_format in {"postgres_query", "trino_query"}:
        payload = _query_result_payload(payload, policy.input_format)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ValueError("Parquet input requires the parquet extra") from None
    try:
        parquet = pq.ParquetFile(io.BytesIO(payload))
        metadata = parquet.metadata
        limits[InputDimension.ROWS].check(metadata.num_rows)
        limits[InputDimension.COLUMNS].check(metadata.num_columns)
        limits[InputDimension.CELLS].check(metadata.num_rows * metadata.num_columns)
        limits[InputDimension.EXPANDED_BYTES].check(sum(
            metadata.row_group(group).column(column).total_uncompressed_size
            for group in range(metadata.num_row_groups) for column in range(metadata.num_columns)))
        schema = parquet.schema_arrow
        names = validate_csv_headers(schema.names)
        if list(names) != schema.names:
            raise ValueError("invalid native Parquet schema")
        types = {}
        decimal_shapes = {}
        decisions = {item.field: item.behavior for item in policy.fields}
        for item in schema:
            if pa.types.is_string(item.type):
                types[item.name] = FieldType.STRING
            elif pa.types.is_signed_integer(item.type):
                types[item.name] = FieldType.INTEGER
            elif pa.types.is_float64(item.type):
                types[item.name] = FieldType.FLOAT
            elif pa.types.is_boolean(item.type):
                types[item.name] = FieldType.BOOLEAN
            elif pa.types.is_date32(item.type):
                types[item.name] = FieldType.DATE
            elif pa.types.is_timestamp(item.type) and item.type.unit == "us" and item.type.tz == "UTC":
                types[item.name] = FieldType.DATETIME
            elif pa.types.is_decimal128(item.type) and 0 <= item.type.scale <= item.type.precision <= 38:
                types[item.name] = FieldType.DECIMAL
                decimal_shapes[item.name] = (item.type.precision, item.type.scale)
                declared = next((entry.decimal_type for entry in policy.fields if entry.field == item.name), None)
                if declared is None or (declared.precision, declared.scale) != decimal_shapes[item.name]:
                    raise ValueError("Parquet decimal shape differs from field declaration")
            else:
                raise ValueError("native Parquet type is not implemented")
            if types[item.name] != FieldType.STRING:
                action = decisions.get(item.name)
                matching = next((entry.match_format for entry in policy.fields if entry.field == item.name), None)
                if (action is None or action.action == "preserve"
                        or action.action == "replace_text" and matching is None
                        or types[item.name] == FieldType.DECIMAL and action.action == "replace_text"
                        or getattr(getattr(action, "unmatched", None), "action", None) == "preserve"):
                    raise ValueError("native numeric text/preservation requires explicit formatting")
        rows = []
        decoded_bytes = 0
        for batch in parquet.iter_batches(batch_size=1024):
            budget.check("transformation Parquet input batch")
            # Arrow string buffers include dictionary expansion, unlike page metadata.
            # This bounds decoded payload, not Python object overhead or Arrow peak RSS.
            decoded_bytes += batch.nbytes
            limits[InputDimension.EXPANDED_BYTES].check(decoded_bytes)
            for row in batch.to_pylist():
                budget.check("transformation Parquet input row")
                if any(value is not None and (
                        type(value) not in {str, int, float, bool, Decimal, date, datetime}
                        or isinstance(value, float) and not math.isfinite(value))
                       for value in row.values()):
                    raise ValueError("unsupported Parquet source cell")
                for value in row.values():
                    if type(value) is str:
                        limits[InputDimension.CELL_CHARS].check(len(value))
                rows.append(row)
        budget.check("transformation Parquet decoded")
        return NativeSourceRows(list(names), tuple(rows), types, decimal_shapes)
    except (pa.ArrowException, OSError, TypeError, OverflowError):
        raise ValueError("invalid transformation Parquet source") from None


def matching_text(policy: BehaviorPolicy, name: str, value: Any) -> str:
    if value is None:
        raise ValueError("null has no matching text")
    pattern = next(item.match_format for item in policy.fields if item.field == name)
    if type(value) is str and pattern is None:
        return value
    if type(value) not in (int, float) or pattern is None:
        raise ValueError("explicit native matching format required")
    return format(value, pattern)


def same_native_value(original: Any, replacement: Any) -> bool:
    """Conservative reuse guard, not mapping-key or formatting semantics."""
    if type(original) is datetime and isinstance(replacement, str):
        try:
            return original == datetime.fromisoformat(replacement)
        except ValueError:
            return False
    if type(original) is date and isinstance(replacement, str):
        try:
            return original == date.fromisoformat(replacement)
        except ValueError:
            return False
    if type(original) is bool and isinstance(replacement, str):
        return parse_bool(replacement) is original
    if type(original) in (int, float, Decimal) and isinstance(replacement, str):
        try:
            return Decimal(str(original)) == Decimal(replacement)
        except InvalidOperation:
            return False
    return bool(original == replacement)
