"""Bounded exact counting of ephemeral keyed digests, never source values."""

from __future__ import annotations

from collections.abc import Iterator
import hmac
from math import ceil
import secrets
import tempfile
from typing import Any

from test_data_agent.core.limits import GenerationLimitError, InputLimitError
from test_data_agent.profiling.budget import (
    LocalProfileBudget,
    LocalProfileDimension,
    LocalProfileLimitError,
)

BATCH_DIGESTS = 50_000
MEMORY_LIMIT = "128MiB"
TEMP_LIMIT = "2GiB"


class DistinctTrackingError(ValueError):
    """A value-free failure of local distinct counting or scratch cleanup."""


def count_distinct_stream(
    initial_sets: list[set[bytes]],
    remaining: Iterator[tuple[int, bytes]],
    budget: LocalProfileBudget,
) -> list[int]:
    dependency_failure = False
    import_failure = False
    try:
        import duckdb
        import pyarrow as pa
    except ImportError:
        dependency_failure = True
    except Exception:
        import_failure = True
    if dependency_failure:
        raise DistinctTrackingError(
            "large CSV profiles require the profiling extra; install with: "
            'python -m pip install "agent-paranoid-android[profiling]"'
        )
    if import_failure:
        raise DistinctTrackingError(
            "local distinct backend initialization failed; reinstall the profiling extra"
        )

    key = secrets.token_bytes(32)
    producer_error: BaseException | None = None
    failed = False
    interrupted = False
    counts: list[int] = []

    def digests() -> Iterator[tuple[int, bytes]]:
        for column, values in enumerate(initial_sets):
            while values:
                yield column, values.pop()
            values.clear()
        yield from remaining

    def batches() -> Iterator[Any]:
        nonlocal producer_error
        try:
            columns: list[int] = []
            tokens: list[bytes] = []
            for column, digest in digests():
                budget.check_deadline("distinct digest streaming")
                columns.append(column)
                tokens.append(hmac.digest(key, digest, "sha256"))
                if len(tokens) == BATCH_DIGESTS:
                    yield pa.RecordBatch.from_arrays([
                        pa.array(columns, type=pa.int32()),
                        pa.array(tokens, type=pa.binary(32)),
                    ], schema=schema)
                    columns.clear()
                    tokens.clear()
            if tokens:
                yield pa.RecordBatch.from_arrays([
                    pa.array(columns, type=pa.int32()),
                    pa.array(tokens, type=pa.binary(32)),
                ], schema=schema)
        except BaseException as error:
            producer_error = error
            raise

    try:
        with tempfile.TemporaryDirectory(prefix="test-data-agent-distinct-") as scratch:
            connection = None
            reader = None
            try:
                connection = duckdb.connect(":memory:", config={
                    "memory_limit": MEMORY_LIMIT,
                    "threads": "1",
                    "async_threads": "1",
                    "temp_directory": scratch,
                    "enable_external_access": "false",
                    "autoinstall_known_extensions": "false",
                    "autoload_known_extensions": "false",
                    "python_enable_replacements": "false",
                })
                connection.execute("SET enable_logging = false")
                connection.execute("SET max_temp_directory_size = ?", [TEMP_LIMIT])
                connection.execute("SET preserve_insertion_order = false")
                schema = pa.schema([("column_id", pa.int32()), ("digest", pa.binary(32))])
                reader = pa.RecordBatchReader.from_batches(schema, batches())
                connection.register("digests", reader)
                budget.check_deadline("distinct counting")
                connection.execute("SET max_execution_time = ?", [
                    max(1, ceil(budget.remaining_seconds() * 1_000)),
                ])
                connection.execute("SET lock_configuration = true")
                by_column = dict(connection.execute(
                    "SELECT column_id, count(DISTINCT digest) FROM digests GROUP BY column_id"
                ).fetchall())
                budget.check_deadline("distinct counting")
                counts = [int(by_column.get(column, 0)) for column in range(len(initial_sets))]
            finally:
                try:
                    if reader is not None:
                        reader.close()
                finally:
                    if connection is not None:
                        connection.close()
    except LocalProfileLimitError:
        raise
    except duckdb.InterruptException:
        interrupted = True
    except Exception:
        failed = True

    # Arrow wraps producer failures; re-raise only safe budget/cancellation errors.
    if isinstance(producer_error, (InputLimitError, GenerationLimitError, KeyboardInterrupt, SystemExit)):
        raise producer_error from None
    if interrupted:
        raise LocalProfileLimitError(
            LocalProfileDimension.DEADLINE_SECONDS,
            attempted=budget.limits.max_seconds,
            limit=budget.limits.max_seconds,
            stage="distinct counting",
        )
    if failed or producer_error is not None:
        raise DistinctTrackingError("local distinct counting or scratch cleanup failed")
    return counts
