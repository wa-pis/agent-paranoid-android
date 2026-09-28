"""Private fixed-byte source decoding; no file reopening or implicit stringify."""

import io
import math
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from dataclasses import dataclass, field
from collections.abc import Iterator

from test_data_agent.core.limits import (
    GenerationBudget, DEFAULT_MAX_INPUT_FILE_BYTES, DEFAULT_MAX_INPUT_CELL_CHARS,
    enforce_parquet_metadata_limits, max_parquet_expanded_bytes, InputLimitError,
)
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.field import FieldType
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.csv_profiler import _csv_reader_from_snapshot, validate_csv_headers, parse_bool
from test_data_agent.io.transformation_query_snapshot import _query_result_payload


@dataclass(repr=False)
class NativeSourceRows:
    fieldnames: list[str]
    rows: tuple[dict[str, str | int | float | Decimal | date | None], ...] = field(repr=False)
    types: dict[str, FieldType] = field(repr=False)
    decimal_shapes: dict[str, tuple[int, int]] = field(default_factory=dict, repr=False)

    def __iter__(self) -> Iterator[dict[str, str | int | float | Decimal | date | None]]:
        return iter(self.rows)


def source_reader(source: SnapshotPart, policy: BehaviorPolicy, *, budget: GenerationBudget) -> Any:
    """Decode supported nullable native scalars; never stringify for matching."""
    budget.check("transformation source decode")
    if len(source.payload) > DEFAULT_MAX_INPUT_FILE_BYTES:
        raise ValueError("transformation source byte limit exceeded")
    if policy.input_format == "csv":
        if any(item.match_format is not None for item in policy.fields):
            raise ValueError("native match format cannot reformat CSV text")
        return _csv_reader_from_snapshot(source.payload)
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
        enforce_parquet_metadata_limits(parquet.metadata, label="transformation Parquet")
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
        expanded_limit = max_parquet_expanded_bytes()
        for batch in parquet.iter_batches(batch_size=1024):
            budget.check("transformation Parquet input batch")
            # Arrow string buffers include dictionary expansion, unlike page metadata.
            # This bounds decoded payload, not Python object overhead or Arrow peak RSS.
            decoded_bytes += batch.nbytes
            if decoded_bytes > expanded_limit:
                raise InputLimitError("transformation Parquet decoded size exceeds limit")
            for row in batch.to_pylist():
                budget.check("transformation Parquet input row")
                if any(value is not None and (
                        type(value) not in {str, int, float, bool, Decimal, date}
                        or isinstance(value, str) and len(value) > DEFAULT_MAX_INPUT_CELL_CHARS
                        or isinstance(value, float) and not math.isfinite(value))
                       for value in row.values()):
                    raise ValueError("unsupported Parquet source cell")
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
