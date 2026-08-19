"""Read-only, resource-bounded PostgreSQL session boundary."""

from __future__ import annotations

import math
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Literal

from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.postgres_query_builders import PostgresQuery


class PostgresClientError(RuntimeError):
    """Base error for PostgreSQL boundary failures."""


class PostgresConnectionError(PostgresClientError):
    """Raised when a bounded PostgreSQL session cannot be opened."""


class PostgresQueryError(PostgresClientError):
    """Raised when an aggregate profiling query fails."""


class PostgresBudgetExceeded(PostgresClientError):
    """Raised when cumulative PostgreSQL profiling work exceeds its budget."""


_POSTGRES_TYPE_ALIASES = {
    "bool": "boolean",
    "bpchar": "character",
    "float4": "real",
    "float8": "double precision",
    "int2": "smallint",
    "int4": "integer",
    "int8": "bigint",
    "timestamptz": "timestamp with time zone",
}


@dataclass(frozen=True, slots=True)
class PostgresResultColumn:
    name: str
    data_type: str
    nullable: bool


@dataclass(frozen=True)
class PostgresClient:
    """Create injected-driver sessions with PostgreSQL read-only defaults."""

    config: PostgresConfig
    driver: Any
    getenv: Callable[[str], str | None] = os.getenv
    clock: Callable[[], float] = time.monotonic

    def session(self) -> PostgresProfileSession:
        return PostgresProfileSession(
            config=self.config,
            driver=self.driver,
            getenv=self.getenv,
            clock=self.clock,
        )


class PostgresProfileSession:
    """Execute trusted metadata or aggregate queries within one shared budget."""

    def __init__(
        self,
        *,
        config: PostgresConfig,
        driver: Any,
        getenv: Callable[[str], str | None],
        clock: Callable[[], float],
    ) -> None:
        self._config = config
        self._driver = driver
        self._getenv = getenv
        self._clock = clock
        self._connection: Any = None
        self._deadline = 0.0
        self._statements = 0
        self._result_rows = 0
        self._result_cells = 0

    def __enter__(self) -> PostgresProfileSession:
        if self._connection is not None:
            raise PostgresConnectionError("PostgreSQL session is already open")
        self._config.validate()
        password = self._resolve_password()
        options = (
            "-c default_transaction_read_only=on "
            f"-c statement_timeout={self._config.statement_timeout_ms} "
            f"-c lock_timeout={self._config.lock_timeout_ms}"
        )
        connect_kwargs: dict[str, object] = {
            "host": self._config.host,
            "port": self._config.port,
            "dbname": self._config.database,
            "user": self._config.user,
            "sslmode": self._config.sslmode,
            "connect_timeout": max(1, math.ceil(self._config.limits.max_seconds)),
            "options": options,
        }
        if password is not None:
            connect_kwargs["password"] = password
        try:
            self._connection = self._driver.connect(**connect_kwargs)
        except Exception:
            raise PostgresConnectionError("PostgreSQL connection failed") from None
        self._deadline = self._clock() + self._config.limits.max_seconds
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        return False

    def fetch_aggregate_dicts(
        self,
        query: PostgresQuery,
    ) -> list[dict[str, object]]:
        """Fetch trusted metadata or aggregate rows without exposing backend errors."""

        if not isinstance(query, PostgresQuery):
            raise TypeError("PostgreSQL execution requires a trusted PostgresQuery")
        if self._connection is None:
            raise PostgresConnectionError("PostgreSQL session is not open")
        self._check_deadline()
        if self._statements >= self._config.limits.max_statements:
            raise PostgresBudgetExceeded("PostgreSQL statement budget exceeded")
        self._statements += 1
        cursor: Any = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(query.sql, query.parameters)
            self._check_deadline()
            description = cursor.description or ()
            names = [str(column[0]) for column in description]
            rows: list[dict[str, object]] = []
            while True:
                self._check_deadline()
                batch = cursor.fetchmany(1)
                self._check_deadline()
                if not batch:
                    return rows
                row = batch[0]
                next_rows = self._result_rows + 1
                next_cells = self._result_cells + len(row)
                if next_rows > self._config.limits.max_result_rows:
                    raise PostgresBudgetExceeded(
                        "PostgreSQL result row budget exceeded"
                    )
                if next_cells > self._config.limits.max_result_cells:
                    raise PostgresBudgetExceeded(
                        "PostgreSQL result cell budget exceeded"
                    )
                rows.append(dict(zip(names, row, strict=True)))
                self._result_rows = next_rows
                self._result_cells = next_cells
        except PostgresBudgetExceeded:
            raise
        except Exception:
            raise PostgresQueryError("PostgreSQL profiling query failed") from None
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def describe_no_rows(
        self,
        query: PostgresQuery,
    ) -> tuple[PostgresResultColumn, ...]:
        """Inspect a trusted zero-row query without retaining source values."""

        if not isinstance(query, PostgresQuery):
            raise TypeError("PostgreSQL execution requires a trusted PostgresQuery")
        if self._connection is None:
            raise PostgresConnectionError("PostgreSQL session is not open")
        self._check_deadline()
        if self._statements >= self._config.limits.max_statements:
            raise PostgresBudgetExceeded("PostgreSQL statement budget exceeded")
        self._statements += 1
        cursor: Any = None
        try:
            cursor = self._connection.cursor()
            cursor.execute(query.sql, query.parameters)
            self._check_deadline()
            description = tuple(cursor.description or ())
            next_cells = self._result_cells + len(description)
            if next_cells > self._config.limits.max_result_cells:
                raise PostgresBudgetExceeded(
                    "PostgreSQL result cell budget exceeded"
                )
            if cursor.fetchmany(1):
                raise PostgresQueryError(
                    "PostgreSQL schema inspection returned an unexpected row"
                )
            self._result_cells = next_cells
            return tuple(
                PostgresResultColumn(
                    name=_description_value(item, "name", 0),
                    data_type=_postgres_type_name(self._connection, item),
                    nullable=_description_nullable(item),
                )
                for item in description
            )
        except (PostgresBudgetExceeded, PostgresQueryError):
            raise
        except Exception:
            raise PostgresQueryError("PostgreSQL profiling query failed") from None
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def _resolve_password(self) -> str | None:
        if self._config.password_env is None:
            return None
        password = self._getenv(self._config.password_env)
        if password is None:
            raise PostgresConnectionError(
                "PostgreSQL password environment variable is not set"
            )
        return password

    def _check_deadline(self) -> None:
        if self._clock() >= self._deadline:
            raise PostgresBudgetExceeded("PostgreSQL session deadline exceeded")


def _description_value(item: Any, attribute: str, index: int) -> str:
    value = getattr(item, attribute, None)
    if value is None:
        try:
            value = item[index]
        except (IndexError, TypeError):
            value = None
    if not isinstance(value, str) or not value:
        raise PostgresQueryError("PostgreSQL schema metadata is invalid")
    return value


def _postgres_type_name(connection: Any, item: Any) -> str:
    type_code = getattr(item, "type_code", None)
    if type_code is None:
        try:
            type_code = item[1]
        except (IndexError, TypeError):
            type_code = None
    name = getattr(type_code, "name", None)
    if isinstance(name, str) and name:
        return _POSTGRES_TYPE_ALIASES.get(name, name)
    try:
        type_info = connection.adapters.types.get(type_code)
    except (AttributeError, KeyError, TypeError):
        type_info = None
    name = getattr(type_info, "name", None)
    if not isinstance(name, str) or not name:
        raise PostgresQueryError("PostgreSQL schema metadata is invalid")
    return _POSTGRES_TYPE_ALIASES.get(name, name)


def _description_nullable(item: Any) -> bool:
    value = getattr(item, "null_ok", None)
    if value is None:
        try:
            value = item[6]
        except (IndexError, TypeError):
            value = None
    return True if value is None else bool(value)
