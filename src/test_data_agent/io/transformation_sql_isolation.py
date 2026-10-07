"""Shared bounded IPC and process lifecycle for closed SQL capture adapters."""

import math
import json
import multiprocessing
import os
import time
from collections.abc import Callable
from typing import Any, Literal

from test_data_agent.core.transformation_limits import (
    InputDimension, TransformationLimitError, resolve_input_limit,
)
from test_data_agent.core.transformation_policy import parse_behavior_policy
from test_data_agent.core.transformation_snapshot import SnapshotPart

def _capture_sql_isolated(
    capture: Any, *, worker: Callable[..., None],
    driver_factory: Callable[[], Any], max_seconds: float,
    adapter: Literal["PostgreSQL", "Trino"],
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
        if (type(capture.max_bytes) is not int
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
        process = context.Process(target=worker,
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
        raise ValueError(f"{adapter} capture worker could not be reaped")
    if limit_error is not None:
        raise limit_error
    if payload is None:
        raise ValueError(f"invalid isolated {adapter} capture")
    return SnapshotPart("source", capture.request.entity_name, payload)

