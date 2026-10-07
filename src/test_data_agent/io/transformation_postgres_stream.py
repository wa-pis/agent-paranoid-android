"""Private injected-driver development boundary; never wired to public execution.

Named cursors bound fetched row counts, not wire bytes or driver allocations.
Server statement timeouts bound server work, not stalled client transport.
Those remaining activation gates require separate evidence before real use.
"""

import math
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from test_data_agent.core.transformation_limits import TransformationLimitError
from test_data_agent.io.transformation_query_capture import _ResultQuery
from test_data_agent.postgres_config import PostgresConfig


@contextmanager
def _postgres_result_stream(
    query: _ResultQuery, *, config: PostgresConfig, schema: Any,
    driver: Any, getenv: Callable[[str], str | None], clock: Callable[[], float],
) -> Iterator[Iterator[Any]]:
    """One authorized query, forward-only cursor, rollback/close on every exit.

Only fictional injected drivers are exercised at this development stage.
The query originates in capture authorization, not caller SQL or a receipt.
"""
    connection = cursor = None
    failed = False
    try:
        import pyarrow as pa

        config.validate()
        columns = config.resolved_columns or config.allowed_columns
        if (type(query) is not _ResultQuery or query.adapter != "postgres"
                or query.source_id != config.source_id
                or query.table not in config.allowed_tables
                or not query.columns
                or any(f"{query.table}.{name}" not in columns for name in query.columns)
                or type(query.max_rows) is not int
                or not 0 < query.max_rows <= 2**63 - 1
                or not isinstance(schema, pa.Schema)
                or not len(schema)):
            raise ValueError
        password = None if config.password_env is None else getenv(config.password_env)
        if config.password_env is not None and password is None:
            raise ValueError
        deadline = clock() + config.limits.max_seconds

        def check() -> None:
            if clock() >= deadline:
                raise ValueError

        timeout = min(config.statement_timeout_ms, max(1, int(config.limits.max_seconds * 1000)))
        kwargs = dict(host=config.host, port=config.port, dbname=config.database,
            user=config.user, sslmode=config.sslmode,
            connect_timeout=max(1, math.ceil(config.limits.max_seconds)),
            options=(f"-c default_transaction_read_only=on -c statement_timeout={timeout} "
                f"-c lock_timeout={min(config.lock_timeout_ms, timeout)} "
                f"-c idle_in_transaction_session_timeout={timeout}"))
        if password is not None:
            kwargs["password"] = password
        connection = driver.connect(**kwargs)
        check()
        cursor = connection.cursor(name="apa_transform", scrollable=False, withhold=False)
        cursor.execute(query.sql)
        check()
        # Psycopg's server cursor may populate description only after first FETCH.
        def batches() -> Iterator[Any]:
            count = 0
            values: list[list[Any]] = [[] for _ in schema]
            buffered_bytes = 0

            def batch() -> Any:
                check()
                return pa.RecordBatch.from_arrays([
                    pa.array(column, type=field.type, safe=True)
                    for column, field in zip(values, schema, strict=True)], schema=schema)

            while True:
                check()
                rows = cursor.fetchmany(1)
                check()
                names = tuple(item[0] for item in (cursor.description or ()))
                if names != tuple(schema.names) or len(rows) > 1:
                    raise ValueError
                if not rows:
                    if values[0]:
                        yield batch()
                    return
                count += 1
                row = rows[0]
                if count > query.max_rows or len(row) != len(schema):
                    raise ValueError
                for index, (value, field) in enumerate(zip(row, schema, strict=True)):
                    if type(value) is str:
                        query.cell_chars.check(len(value))
                    if value is None:
                        if not field.nullable:
                            raise ValueError
                    elif not (
                        (pa.types.is_string(field.type) and type(value) is str)
                        or (pa.types.is_signed_integer(field.type) and type(value) is int)
                        or (pa.types.is_float64(field.type) and type(value) is float and math.isfinite(value))
                        or (pa.types.is_boolean(field.type) and type(value) is bool)
                        or (pa.types.is_date32(field.type) and type(value) is date)
                        or (pa.types.is_timestamp(field.type) and field.type.unit == "us"
                            and field.type.tz == "UTC" and type(value) is datetime
                            and value.tzinfo is not None and value.utcoffset() is not None)
                        or (pa.types.is_decimal128(field.type) and type(value) is Decimal and value.is_finite())
                    ):
                        raise ValueError
                    values[index].append(value)
                    buffered_bytes += 4 + 4 * len(value) if type(value) is str else 16
                # ponytail: bounded chunks avoid one Parquet row group per row.
                # Estimate controls flushing, not a hard RSS/wire guarantee;
                # one fetched row and Arrow allocations retain existing limits.
                if len(values[0]) >= 1024 or buffered_bytes >= 1024 * 1024:
                    yield batch()
                    values = [[] for _ in schema]
                    buffered_bytes = 0

        yield batches()
    except TransformationLimitError:
        raise
    except Exception:
        failed = True
    finally:
        if cursor is not None:
            with suppress(Exception):
                cursor.close()
        if connection is not None:
            with suppress(Exception):
                connection.rollback()
            with suppress(Exception):
                connection.close()
    if failed:
        raise ValueError("invalid PostgreSQL result stream")
