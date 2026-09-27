"""Private bounded Parquet encoding; no caller-selected output paths."""

import io
from typing import Any
from collections.abc import Iterator

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import ParquetOutput
from test_data_agent.io.transformation_execute import CsvTransformationResult
from test_data_agent.io.transformation_output import normalized_output_rows


def render_transformation_parquet(result: CsvTransformationResult, output: ParquetOutput, *,
                                 max_bytes: int, budget: GenerationBudget,
                                 source_rows: Iterator[tuple[str | None, ...]] | None = None) -> bytes:
    """Encode declared types after the same normalized-value gates as SQL."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("invalid Parquet output budget")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ValueError("Parquet output requires the parquet extra") from None

    class BoundedBuffer(io.BytesIO):
        def write(self, data: Any) -> int:
            budget.check("transformation Parquet write")
            if self.tell() + len(data) > max_bytes:
                raise ValueError("Parquet output budget exceeded")
            return super().write(data)

    rows: list[dict[str, Any]] = []
    for _, values in normalized_output_rows(result, output, budget=budget, source_rows=source_rows):
        rows.append({item.name: int(value) if value is not None and item.type == "integer" else value
                     for item, value in zip(output.fields, values, strict=True)})
    types = {"string": pa.string(), "integer": pa.int64(), "float": pa.float64(),
             "boolean": pa.bool_(), "date": pa.date32()}
    fields = []
    for item in output.fields:
        budget.check("transformation Parquet schema")
        if item.decimal_type:
            kind = pa.decimal128(item.decimal_type.precision, item.decimal_type.scale)
        elif item.type == "datetime":
            offsets = {value.strftime("%z") for row in rows if (value := row[item.name]) is not None}
            if len(offsets) > 1 or any(len(offset) != 5 for offset in offsets):
                raise ValueError("Parquet requires one explicit timestamp offset")
            # All-null timestamps carry no instant to convert; retain declared target/source zone.
            temporal = item.temporal_type
            assert temporal is not None
            offset = next(iter(offsets), None)
            zone = (f"{offset[:3]}:{offset[3:]}" if offset else
                    temporal.target_timezone or temporal.source_timezone)
            if zone is None:
                raise ValueError("all-null Parquet timestamp requires an explicit timezone")
            kind = pa.timestamp("us", tz=zone)
        else:
            kind = types[item.type]
        fields.append(pa.field(item.name, kind, nullable=item.nullable))
    try:
        budget.check("transformation Parquet encoding")
        table = pa.Table.from_pylist(rows, schema=pa.schema(fields))
        with BoundedBuffer() as buffer:
            pq.write_table(table, buffer)
            budget.check("transformation Parquet complete")
            return buffer.getvalue()
    except (pa.ArrowException, OverflowError):
        raise ValueError("invalid typed Parquet output") from None
