"""Private process-supervised capture. Fictional drivers only; no public wiring.

Bounds result IPC and parent wait, not worker memory/wire bytes or server work.
OS process start/termination can exceed requested deadlines under OS failure.
"""

import math
import multiprocessing
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_FILE_BYTES, GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_postgres_stream import _postgres_result_stream
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryProfileRequest
from test_data_agent.postgres_config import PostgresConfig


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
    result: Any, length: Any,
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
    try:
        if (type(capture) is not _PostgresCapture
                or type(capture.max_bytes) is not int
                or not 0 < capture.max_bytes <= DEFAULT_MAX_INPUT_FILE_BYTES
                or type(max_seconds) not in {int, float}
                or not math.isfinite(max_seconds) or not 0.1 <= max_seconds <= 3600):
            raise ValueError
        deadline = time.monotonic() + max_seconds
        reserve = min(2.0, max_seconds / 4)
        work_deadline = deadline - reserve
        context = multiprocessing.get_context("spawn")
        result = context.RawArray("B", capture.max_bytes)
        length = context.RawValue("i", 0)
        process = context.Process(target=_capture_worker,
            args=(capture, driver_factory, work_deadline, result, length))
        process.start()
        process.join(max(0.0, work_deadline - time.monotonic()))
        if (not process.is_alive() and process.exitcode == 0
                and 0 < length.value <= len(result) and time.monotonic() < work_deadline):
            payload = bytes(memoryview(result).cast("B")[:length.value])
            if time.monotonic() >= work_deadline:
                payload = None
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
    if payload is None:
        raise ValueError("invalid isolated PostgreSQL capture")
    return SnapshotPart("source", capture.request.entity_name, payload)
