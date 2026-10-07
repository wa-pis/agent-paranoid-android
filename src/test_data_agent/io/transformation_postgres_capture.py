"""Closed process-supervised PostgreSQL capture; public registration remains gated.

Bounds result IPC and parent wait, not worker memory/wire bytes or server work.
OS process start/termination can exceed requested deadlines under OS failure.
"""

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import partial
from typing import Any

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import (
    TransformationLimitError,
)
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryProfileRequest, ValidatedSqlQuery
from test_data_agent.postgres_config import PostgresConfig, with_resolved_postgres_columns
from test_data_agent.postgres_client import PostgresResultColumn


@dataclass(frozen=True, repr=False)
class _PostgresCapture:
    request: SqlQueryProfileRequest
    config: PostgresConfig
    source_columns: tuple[QuerySourceColumn, ...]
    schema: Any
    policy: BehaviorPolicy
    max_rows: int
    max_bytes: int


def _capture_worker(
    capture: _PostgresCapture, driver_factory: Callable[[], Any], deadline: float,
    result: Any, length: Any, diagnostic: Any,
) -> None:
    try:
        with open(os.devnull, "wb") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        driver = driver_factory()
        expected_query_sha256 = None
        if capture.schema is None:
            # Discovery and row access share this owned process and deadline.
            if capture.config.limits.max_statements < 3:
                raise ValueError
            config = replace(capture.config, limits=replace(capture.config.limits,
                max_seconds=min(capture.config.limits.max_seconds, remaining),
                max_statements=capture.config.limits.max_statements - 1))
            columns, metadata, plan = _discover_postgres_capture_metadata(
                capture.request, config, driver=driver)
            schema = _postgres_capture_schema(metadata)
            table = ".".join(plan.table_parts)
            expected_query_sha256 = plan.fingerprint
            config = with_resolved_postgres_columns(config, frozenset(
                f"{table}.{item.name}" for item in columns))
            capture = replace(capture, config=config, source_columns=columns, schema=schema)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
        source = _capture_authorized_result(capture.request,
            allowed_tables=capture.config.allowed_tables, source_columns=capture.source_columns,
            schema=capture.schema, policy=capture.policy, max_rows=capture.max_rows,
            max_bytes=capture.max_bytes, budget=GenerationBudget(remaining),
            expected_query_sha256=expected_query_sha256,
            stream=partial(_postgres_result_stream, config=capture.config,
                schema=capture.schema, driver=driver, getenv=os.getenv,
                clock=time.monotonic))
        if len(source.payload) > len(result) or time.monotonic() >= deadline:
            return
        memoryview(result).cast("B")[:len(source.payload)] = source.payload
        length.value = len(source.payload)
    except TransformationLimitError as error:
        # Fixed schema only: never serialize exception messages or backend text.
        data = json.dumps([error.dimension.value, error.amount, error.limit,
            error.origin, error.code == "requested_above_limit"], separators=(",", ":")).encode("ascii")
        if len(data) < len(diagnostic):
            diagnostic[:len(data)] = data
            length.value = -2
        else:
            length.value = -1
    except BaseException:
        # No pickled exceptions, driver logs or tracebacks cross the boundary.
        length.value = -1


def _capture_postgres_isolated(
    capture: _PostgresCapture, *, driver_factory: Callable[[], Any], max_seconds: float,
) -> SnapshotPart:
    from test_data_agent.io.transformation_sql_isolation import _capture_sql_isolated

    if type(capture) is not _PostgresCapture:
        raise ValueError("invalid isolated PostgreSQL capture") from None
    return _capture_sql_isolated(capture, worker=_capture_worker,
        driver_factory=driver_factory, max_seconds=max_seconds, adapter="PostgreSQL")


def _configured_postgres_driver() -> Any:
    """Resolve the optional driver inside the owned worker, never from user input."""
    import psycopg

    return psycopg


def _capture_configured_postgres(
    capture: _PostgresCapture, *, max_seconds: float,
) -> SnapshotPart:
    """Closed configured-driver increment; public registration remains gated.

    Explicit configuration and frozen metadata still come from the authorized
    adapter. No environment-driven connection discovery or automatic fallback.
    """
    if type(capture) is not _PostgresCapture:
        raise ValueError("invalid isolated PostgreSQL capture") from None
    # Never accept caller-supplied source/output metadata on configured access.
    return _capture_postgres_isolated(
        replace(capture, source_columns=(), schema=None),
        driver_factory=_configured_postgres_driver, max_seconds=max_seconds,
    )


def _discover_postgres_capture_metadata(
    request: SqlQueryProfileRequest, config: PostgresConfig, *, driver: Any,
) -> tuple[tuple[QuerySourceColumn, ...], tuple[PostgresResultColumn, ...], ValidatedSqlQuery]:
    """Closed bounded metadata discovery; never fetch the result rows."""
    from test_data_agent.postgres_client import PostgresClient
    from test_data_agent.postgres_query_builders import PostgresQuery
    from test_data_agent.sql_query_adapters import _postgres_source_columns
    from test_data_agent.sql_query_profiling import build_no_row_schema_query
    from test_data_agent.sql_query_source import (
        SqlQueryAdapter, authorize_query_source, inspect_query_source,
    )

    valid = False
    try:
        config.validate()
        draft = inspect_query_source(request)
        if (request.adapter is not SqlQueryAdapter.POSTGRES
                or request.source_id != config.source_id
                or draft.table_name not in config.allowed_tables):
            raise ValueError
        with PostgresClient(config=config, driver=driver).session() as session:
            columns = _postgres_source_columns(
                config, draft.table_parts, session.fetch_aggregate_dicts,
            )
            plan = authorize_query_source(draft, columns)
            result = session.describe_no_rows(PostgresQuery(build_no_row_schema_query(plan).sql))
            if tuple(item.name for item in result) != plan.output_fields:
                raise ValueError
        valid = True
    except Exception:
        pass
    if not valid:
        raise ValueError("invalid PostgreSQL capture metadata") from None
    return columns, result, plan


def _postgres_capture_schema(columns: tuple[PostgresResultColumn, ...]) -> Any:
    """Build exact native capture types; unsupported metadata fails closed."""
    import re
    import pyarrow as pa
    from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS

    types = {"text": pa.string(), "character varying": pa.string(),
        "character": pa.string(), "smallint": pa.int16(), "integer": pa.int32(),
        "bigint": pa.int64(), "real": pa.float64(), "double precision": pa.float64(),
        "boolean": pa.bool_(), "date": pa.date32(),
        "timestamp with time zone": pa.timestamp("us", tz="UTC")}
    valid = False
    try:
        if (type(columns) is not tuple or not 0 < len(columns) <= DEFAULT_MAX_INPUT_COLUMNS
                or any(type(item) is not PostgresResultColumn for item in columns)
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
                match = re.fullmatch(r"(?:numeric|decimal)\(([0-9]{1,2}),\s*([0-9]{1,2})\)", item.data_type)
                if match is None:
                    raise ValueError
                precision, scale = map(int, match.groups())
                if not 1 <= precision <= 38 or not 0 <= scale <= precision:
                    raise ValueError
                kind = pa.decimal128(precision, scale)
            fields.append(pa.field(item.name, kind, nullable=item.nullable))
        schema = pa.schema(fields)
        valid = True
    except Exception:
        pass
    if not valid:
        raise ValueError("unsupported PostgreSQL capture schema") from None
    return schema
