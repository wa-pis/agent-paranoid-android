"""Private process-supervised capture. Fictional drivers only; no public wiring.

Bounds result IPC and parent wait, not worker memory/wire bytes or server work.
OS process start/termination can exceed requested deadlines under OS failure.
"""

import math
import json
import multiprocessing
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_limits import (
    InputDimension, TransformationLimitError, resolve_input_limit,
)
from test_data_agent.core.transformation_policy import BehaviorPolicy, parse_behavior_policy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryProfileRequest
from test_data_agent.postgres_config import PostgresConfig
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
        source = _capture_authorized_result(capture.request,
            allowed_tables=capture.config.allowed_tables, source_columns=capture.source_columns,
            schema=capture.schema, policy=capture.policy, max_rows=capture.max_rows,
            max_bytes=capture.max_bytes, budget=GenerationBudget(remaining),
            stream=partial(_postgres_result_stream, config=capture.config,
                schema=capture.schema, driver=driver_factory(), getenv=os.getenv,
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
    """Capture only on clean child exit; reserve part of deadline for reaping.

    Factory is trusted code supplied by development tests, never a user path,
    script, module name or serialized callable accepted through an API.
    """
    process = None
    cleanup_failed = False
    payload = None
    limit_error = None
    try:
        if (type(capture) is not _PostgresCapture
                or type(capture.max_bytes) is not int
                or not 0 < capture.max_bytes <= 2**63 - 1
                or type(capture.max_rows) is not int
                or not 0 < capture.max_rows < 2**63 - 1
                or type(max_seconds) not in {int, float}
                or not math.isfinite(max_seconds) or not 0.1 <= max_seconds <= 3600):
            raise ValueError
        policy = parse_behavior_policy(capture.policy)
        for dimension, amount in ((InputDimension.BYTES, capture.max_bytes),
                                  (InputDimension.ROWS, capture.max_rows)):
            resolve_input_limit(dimension, policy.resource_limits, os.environ).check(amount, requested=True)
        deadline = time.monotonic() + max_seconds
        reserve = min(2.0, max_seconds / 4)
        work_deadline = deadline - reserve
        context = multiprocessing.get_context("spawn")
        result = context.RawArray("B", capture.max_bytes)
        length = context.RawValue("q", 0)
        diagnostic = context.RawArray("B", 512)
        process = context.Process(target=_capture_worker,
            args=(capture, driver_factory, work_deadline, result, length, diagnostic))
        process.start()
        process.join(max(0.0, work_deadline - time.monotonic()))
        if (not process.is_alive() and process.exitcode == 0
                and 0 < length.value <= len(result) and time.monotonic() < work_deadline):
            payload = bytes(memoryview(result).cast("B")[:length.value])
            if time.monotonic() >= work_deadline:
                payload = None
        elif (not process.is_alive() and process.exitcode == 0
                and length.value == -2 and time.monotonic() < work_deadline):
            dimension, amount, threshold, origin, requested = json.loads(
                bytes(diagnostic).split(b"\0", 1)[0])
            limit_error = TransformationLimitError(InputDimension(dimension), amount,
                threshold, origin, requested=requested)
    except TransformationLimitError as error:
        limit_error = error
    except Exception:
        payload = None
    finally:
        if process is not None:
            try:
                if process.pid is not None and process.is_alive():
                    process.terminate()
                    process.join(max(0.0, (deadline - time.monotonic()) / 2))
                    if process.is_alive():
                        process.kill()
                        process.join(max(0.0, deadline - time.monotonic()))
                    cleanup_failed = process.is_alive()
                if not cleanup_failed:
                    process.close()
            except Exception:
                cleanup_failed = True
    if cleanup_failed:
        raise ValueError("PostgreSQL capture worker could not be reaped")
    if limit_error is not None:
        raise limit_error
    if payload is None:
        raise ValueError("invalid isolated PostgreSQL capture")
    return SnapshotPart("source", capture.request.entity_name, payload)


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
    return _capture_postgres_isolated(
        capture, driver_factory=_configured_postgres_driver, max_seconds=max_seconds,
    )


def _discover_postgres_capture_metadata(
    request: SqlQueryProfileRequest, config: PostgresConfig, *, driver: Any,
) -> tuple[tuple[QuerySourceColumn, ...], tuple[PostgresResultColumn, ...]]:
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
    return columns, result
