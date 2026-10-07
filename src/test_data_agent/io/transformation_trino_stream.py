"""Closed typed Trino result stream; public capture registration remains gated."""

from collections.abc import Iterator, Callable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
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
                or parts[0] not in (config.allowed_catalogs or frozenset()) or parts[1] not in (config.allowed_schemas or frozenset())
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
                or draft.table_parts[0] not in (config.allowed_catalogs or frozenset())
                or draft.table_parts[1] not in (config.allowed_schemas or frozenset())):
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


def _capture_trino_result(request: SqlQueryProfileRequest, *, config: TrinoConfig,
                          source_id: str, policy: BehaviorPolicy, max_rows: int, max_bytes: int,
                          budget: GenerationBudget, driver: Any) -> SnapshotPart:
    """Closed composition: metadata and rows consume one invocation budget."""
    from dataclasses import replace
    from functools import partial
    from test_data_agent.io.transformation_query_capture import _capture_authorized_result
    from test_data_agent.trino_work_budget import query_work_limits_from_env, with_query_work_budget

    def capture() -> SnapshotPart:
        budget.check("Trino capture metadata")
        columns, metadata, plan = _discover_trino_capture_metadata(request,
            config=config, source_id=source_id, driver=driver)
        budget.check("Trino capture metadata")
        schema = _trino_capture_schema(metadata)
        table = ".".join(plan.table_parts)
        resolved = replace(config, allowed_table_columns=frozenset(
            f"{table}.{column.name}" for column in columns))
        return _capture_authorized_result(request, allowed_tables=frozenset({table}),
            source_columns=columns, schema=schema, policy=policy, max_rows=max_rows,
            max_bytes=max_bytes, budget=budget, expected_query_sha256=plan.fingerprint,
            stream=partial(_trino_result_stream, config=resolved, source_id=source_id,
                schema=schema, driver=driver))

    return with_query_work_budget(capture,
        query_work_limits_from_env(deployment_profile=config.deployment_profile))()


@dataclass(frozen=True, repr=False)
class _TrinoCapture:
    request: SqlQueryProfileRequest
    config: TrinoConfig
    source_id: str
    policy: BehaviorPolicy
    max_rows: int
    max_bytes: int


def _trino_capture_worker(capture: _TrinoCapture, driver_factory: Callable[[], Any],
                          deadline: float, result: Any, length: Any, diagnostic: Any) -> None:
    import json
    import os
    import time

    try:
        with open(os.devnull, "wb") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        source = _capture_trino_result(capture.request, config=capture.config,
            source_id=capture.source_id, policy=capture.policy, max_rows=capture.max_rows,
            max_bytes=capture.max_bytes, budget=GenerationBudget(remaining),
            driver=driver_factory())
        if len(source.payload) > len(result) or time.monotonic() >= deadline:
            return
        memoryview(result).cast("B")[:len(source.payload)] = source.payload
        length.value = len(source.payload)
    except TransformationLimitError as error:
        data = json.dumps([error.dimension.value, error.amount, error.limit,
            error.origin, error.code == "requested_above_limit"], separators=(",", ":")).encode("ascii")
        if len(data) < len(diagnostic):
            diagnostic[:len(data)] = data
            length.value = -2
        else:
            length.value = -1
    except QueryWorkBudgetExceeded as error:
        data = json.dumps([error.dimension.value, error.attempted, error.limit],
            separators=(",", ":")).encode("ascii")
        if len(data) < len(diagnostic):
            diagnostic[:len(data)] = data
            length.value = -3
        else:
            length.value = -1
    except BaseException:
        length.value = -1


def _capture_trino_isolated(capture: _TrinoCapture, *, driver_factory: Callable[[], Any],
                            max_seconds: float) -> SnapshotPart:
    from test_data_agent.io.transformation_sql_isolation import _capture_sql_isolated

    if type(capture) is not _TrinoCapture:
        raise ValueError("invalid isolated Trino capture") from None
    return _capture_sql_isolated(capture, worker=_trino_capture_worker,
        driver_factory=driver_factory, max_seconds=max_seconds, adapter="Trino")


def _configured_trino_driver() -> Any:
    import trino

    return trino


def _capture_configured_trino(capture: _TrinoCapture, *, max_seconds: float) -> SnapshotPart:
    """Closed configured driver; no public registration or user-supplied factory."""
    return _capture_trino_isolated(capture, driver_factory=_configured_trino_driver,
        max_seconds=max_seconds)
