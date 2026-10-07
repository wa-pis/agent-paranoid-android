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
from test_data_agent.sql_query_source import SqlQueryProfileRequest, QuerySourceColumn, ValidatedSqlQuery
from test_data_agent.sql_query_profiling import QueryResultColumn


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


def _discover_trino_capture_metadata(request: SqlQueryProfileRequest, *, config: TrinoConfig,
                                     source_id: str, driver: Any) -> tuple[tuple[QuerySourceColumn, ...], tuple[QueryResultColumn, ...], ValidatedSqlQuery]:
    """Closed allowlisted discovery and no-row inspection under shared budgets."""
    from test_data_agent.sql_query_adapters import _trino_source_columns, _trino_description_column
    from test_data_agent.sql_query_source import SqlQueryAdapter, inspect_query_source, authorize_query_source
    from test_data_agent.sql_query_profiling import build_no_row_schema_query
    from test_data_agent.trino_query_builders import build_describe_table_query
    from test_data_agent.trino_work_budget import query_work_limits_from_env, with_query_work_budget

    valid = False
    try:
        config.validate_security()
        draft = inspect_query_source(request)
        if (request.adapter is not SqlQueryAdapter.TRINO or request.source_id != source_id
                or draft.table_parts[0] not in config.allowed_catalogs
                or draft.table_parts[1] not in config.allowed_schemas):
            raise ValueError
        selectors = _trino_table_selectors(config, draft.table_name)
        client = TrinoClient(config=config, driver=driver)

        def discover() -> tuple[tuple[QuerySourceColumn, ...], tuple[QueryResultColumn, ...], ValidatedSqlQuery]:
            query = build_describe_table_query(*draft.table_parts)
            columns = _trino_source_columns(client.fetch_dicts(query.sql, query.parameters), selectors)
            plan = authorize_query_source(draft, columns)
            rows, description = client.execute_query(build_no_row_schema_query(plan).sql)
            metadata = tuple(_trino_description_column(item) for item in description)
            if rows or tuple(item.name for item in metadata) != plan.output_fields:
                raise ValueError
            return columns, metadata, plan

        result = with_query_work_budget(discover,
            query_work_limits_from_env(deployment_profile=config.deployment_profile))()
        valid = True
    except (TransformationLimitError, QueryWorkBudgetExceeded):
        raise
    except Exception:
        pass
    if not valid:
        raise ValueError("invalid Trino capture metadata") from None
    return result


def _trino_capture_schema(columns: tuple[QueryResultColumn, ...]) -> Any:
    """Retain declared scalar types; ambiguous or composite types fail closed."""
    import re
    import pyarrow as pa
    from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS

    types = {"varchar": pa.string(), "tinyint": pa.int8(), "smallint": pa.int16(),
        "integer": pa.int32(), "bigint": pa.int64(), "real": pa.float64(),
        "double": pa.float64(), "boolean": pa.bool_(), "date": pa.date32()}
    valid = False
    try:
        if (type(columns) is not tuple or not 0 < len(columns) <= DEFAULT_MAX_INPUT_COLUMNS
                or any(type(item) is not QueryResultColumn for item in columns)
                or len({item.name for item in columns}) != len(columns)):
            raise ValueError
        fields = []
        for item in columns:
            if (type(item.name) is not str or not item.name or len(item.name) > 256
                    or type(item.data_type) is not str or len(item.data_type) > 128
                    or type(item.nullable) is not bool):
                raise ValueError
            kind = types.get(item.data_type)
            if kind is None:
                match = re.fullmatch(r"decimal\(([0-9]{1,2}),\s*([0-9]{1,2})\)", item.data_type)
                if match is None:
                    raise ValueError
                precision, scale = map(int, match.groups())
                if not 1 <= precision <= 38 or not 0 <= scale <= precision:
                    raise ValueError
                kind = pa.decimal128(precision, scale)
            fields.append(pa.field(item.name, kind, nullable=item.nullable))
        result = pa.schema(fields)
        valid = True
    except Exception:
        pass
    if not valid:
        raise ValueError("unsupported Trino capture schema") from None
    return result
