"""Private bounded Parquet encoding; no caller-selected output paths."""

import io
from typing import Any
from collections.abc import Iterator

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import InputDimension, TransformationLimitError
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
                raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
                    self.tell() + len(data), max_bytes, "parquet_output_run")
            return super().write(data)

    # Discover timestamp offsets without retaining normalized rows or consuming
    # the one-shot source iterator. The encoding pass enforces source reuse.
    offsets: dict[str, str] = {}
    if any(item.type == "datetime" for item in output.fields):
        for _, values in normalized_output_rows(result, output, budget=budget):
            for item, value in zip(output.fields, values, strict=True):
                if item.type == "datetime" and value is not None:
                    offset = value.strftime("%z")
                    if len(offset) != 5 or offsets.get(item.name, offset) != offset:
                        raise ValueError("Parquet requires one explicit timestamp offset")
                    offsets[item.name] = offset
    types = {"string": pa.string(), "integer": pa.int64(), "float": pa.float64(),
             "boolean": pa.bool_(), "date": pa.date32()}
    fields = []
    for item in output.fields:
        budget.check("transformation Parquet schema")
        if item.decimal_type:
            kind = pa.decimal128(item.decimal_type.precision, item.decimal_type.scale)
        elif item.type == "datetime":
            # All-null timestamps carry no instant to convert; retain declared target/source zone.
            temporal = item.temporal_type
            assert temporal is not None
            offset = offsets.get(item.name)
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
        schema = pa.schema(fields)
        with BoundedBuffer() as buffer:
            with pq.ParquetWriter(buffer, schema) as writer:
                rows: list[dict[str, Any]] = []
                for _, values in normalized_output_rows(result, output, budget=budget, source_rows=source_rows):
                    rows.append({item.name: int(value) if value is not None and item.type == "integer" else value
                                 for item, value in zip(output.fields, values, strict=True)})
                    if len(rows) == 1024:
                        budget.check("transformation Parquet batch")
                        writer.write_table(pa.Table.from_pylist(rows, schema=schema))
                        rows.clear()
                if rows:
                    budget.check("transformation Parquet batch")
                    writer.write_table(pa.Table.from_pylist(rows, schema=schema))
            budget.check("transformation Parquet complete")
            return buffer.getvalue()
    except (pa.ArrowException, OverflowError):
        raise ValueError("invalid typed Parquet output") from None
