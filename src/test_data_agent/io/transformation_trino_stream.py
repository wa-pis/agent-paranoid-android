"""Closed typed Trino result stream; public capture registration remains gated."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.trino_work_budget import QueryWorkBudgetExceeded
from test_data_agent.io.transformation_query_capture import _ResultQuery
from test_data_agent.io.transformation_postgres_stream import _native_capture_value
from test_data_agent.sql_query_adapters import _trino_table_selectors
from test_data_agent.trino_client import TrinoClient, _identity_row_converter
from test_data_agent.trino_config import TrinoConfig


@contextmanager
def _trino_result_stream(query: _ResultQuery, *, config: TrinoConfig,
                         source_id: str, schema: Any, driver: Any) -> Iterator[Iterator[Any]]:
    import pyarrow as pa

    valid = False
    try:
        config.validate_security()
        selectors = _trino_table_selectors(config, query.table)
        allowed = {item.column for item in selectors if not item.is_wildcard}
        parts = query.table.split(".")
        if (type(query) is not _ResultQuery or query.adapter != "trino"
                or query.source_id != source_id or len(parts) != 3
                or parts[0] not in config.allowed_catalogs or parts[1] not in config.allowed_schemas
                or any(item.is_wildcard for item in selectors)
                or not set(query.columns).issubset(allowed)
                or not query.columns or query.max_rows > config.max_result_rows
                or not isinstance(schema, pa.Schema) or not len(schema)):
            raise ValueError
        client = TrinoClient(config=config, driver=driver)
        with client._query_rows(query.sql, None, row_converter_factory=_identity_row_converter) as result:
            rows, description = result
            if tuple(item[0] for item in description) != tuple(schema.names):
                raise ValueError

            def batches() -> Iterator[Any]:
                values: list[list[Any]] = [[] for _ in schema]
                buffered = 0
                for row in rows:
                    if len(row) != len(schema):
                        raise ValueError
                    for index, (value, field) in enumerate(zip(row, schema, strict=True)):
                        if not _native_capture_value(value, field, pa):
                            raise ValueError
                        if type(value) is str:
                            query.cell_chars.check(len(value))
                        values[index].append(value)
                        buffered += 4 + 4 * len(value) if type(value) is str else 16
                    if len(values[0]) >= 1024 or buffered >= 1024 * 1024:
                        yield pa.RecordBatch.from_arrays([
                            pa.array(column, type=field.type, safe=True)
                            for column, field in zip(values, schema, strict=True)], schema=schema)
                        values = [[] for _ in schema]
                        buffered = 0
                if values[0]:
                    yield pa.RecordBatch.from_arrays([
                        pa.array(column, type=field.type, safe=True)
                        for column, field in zip(values, schema, strict=True)], schema=schema)

            yield batches()
        valid = True
    except (TransformationLimitError, QueryWorkBudgetExceeded):
        raise
    except Exception:
        pass
    if not valid:
        raise ValueError("invalid Trino result stream") from None
