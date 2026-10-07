"""Bounded Trino client boundary with explicit configuration and cleanup."""

from __future__ import annotations

import os

from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from threading import BoundedSemaphore
from typing import Any, TypeVar, cast

from test_data_agent.trino_auth import bounded_oauth_session
from test_data_agent.trino_config import (
    MAX_QUERY_EXECUTION_TIME_MS,
    MAX_QUERY_RUN_TIME_MS,
    MAX_QUERY_SCAN_BYTES,
    TrinoConfig,
    TrinoConfigurationError,
    parse_data_size_value,
    parse_duration_value,
)
from test_data_agent.trino_sql_policy import consume_query_execution_work
from test_data_agent.trino_work_budget import (
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    consume_database_result_payload,
    current_query_work_budget,
)

try:  # pragma: no cover - live Trino is not used in unit tests.
    import trino as trino
except ImportError:  # pragma: no cover
    trino = None  # type: ignore[assignment]


class TrinoResultLimitError(ValueError):
    """Raised when a Trino response exceeds the client-side safety limit."""


class TrinoCapacityError(RuntimeError):
    """Raised when the shared in-process Trino work cap is exhausted."""


DEFAULT_MAX_CONCURRENT_TRINO_QUERIES = 8
_TRINO_WORK_SLOTS = BoundedSemaphore(DEFAULT_MAX_CONCURRENT_TRINO_QUERIES)


RowT = TypeVar("RowT")


@dataclass(frozen=True)
class TrinoClient:
    """Execute Trino queries within configured result and resource budgets."""

    config: TrinoConfig
    driver: Any
    oauth_redirect: Callable[[str], None] | None = field(default=None, repr=False)

    @cached_property
    def _authentication(self) -> Any:
        if self.config.authentication is None:
            return None
        return self.config.authentication.build(
            driver_auth=getattr(self.driver, "auth", None), environ=os.environ,
            username=self.config.user, http_scheme=self.config.http_scheme,
            oauth_redirect=self.oauth_redirect,
        )

    @classmethod
    def from_env(cls, *, driver: Any = None) -> TrinoClient:
        return cls(
            config=TrinoConfig.from_env(),
            driver=trino if driver is None else driver,
        )

    def execute_query(
        self,
        sql: str,
        parameters: Sequence[Any] | None = None,
    ) -> tuple[list[tuple[Any, ...]], list[Any]]:
        return self._fetch_rows(
            sql,
            parameters,
            row_converter_factory=_identity_row_converter,
        )

    def fetch_dicts(
        self,
        sql: str,
        parameters: Sequence[Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows, _ = self._fetch_rows(
            sql,
            parameters,
            row_converter_factory=_dict_row_converter,
        )
        return rows

    def _fetch_rows(
        self,
        sql: str,
        parameters: Sequence[Any] | None,
        *,
        row_converter_factory: Callable[
            [Sequence[Any]],
            Callable[[Any], RowT],
        ],
    ) -> tuple[list[RowT], list[Any]]:
        with self._query_rows(sql, parameters, row_converter_factory=row_converter_factory) as result:
            rows, description = result
            return list(rows), description

    @contextmanager
    def _query_rows(
        self,
        sql: str,
        parameters: Sequence[Any] | None,
        *,
        row_converter_factory: Callable[
            [Sequence[Any]],
            Callable[[Any], RowT],
        ],
    ) -> Iterator[tuple[Iterator[RowT], list[Any]]]:
        if self.driver is None:
            raise RuntimeError("trino package is not installed")

        authentication = self._authentication
        auth_config = self.config.authentication

        estimated_scan_bytes = parse_data_size_value(
            self.config.query_max_scan_physical_bytes,
            "TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES",
            MAX_QUERY_SCAN_BYTES,
        )
        consume_query_execution_work(
            sql,
            estimated_scan_bytes_per_statement=estimated_scan_bytes,
        )
        budget = current_query_work_budget()
        request_timeout, execution_timeout, run_timeout = _bounded_query_timeouts(
            self.config,
            budget,
        )
        if not _TRINO_WORK_SLOTS.acquire(blocking=False):
            raise TrinoCapacityError("Trino request capacity exhausted")
        oauth_session = None
        try:
            connection_options: dict[str, Any] = dict(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                http_scheme=self.config.http_scheme,
                request_timeout=request_timeout,
                session_properties={
                    "query_max_execution_time": execution_timeout,
                    "query_max_run_time": run_timeout,
                    "query_max_scan_physical_bytes": self.config.query_max_scan_physical_bytes,
                },
            )
            if self.config.default_catalog is not None:
                connection_options["catalog"] = self.config.default_catalog
            if self.config.default_schema is not None:
                connection_options["schema"] = self.config.default_schema
            if authentication is not None:
                connection_options["auth"] = authentication
                connection_options["verify"] = True
            if auth_config is not None and auth_config.method == "oauth2":
                oauth_session = bounded_oauth_session(
                    host=self.config.host, port=self.config.port,
                    request_timeout=request_timeout, budget=budget,
                )
                connection_options["http_session"] = oauth_session
            connection = self.driver.dbapi.connect(**connection_options)
            with closing(connection), closing(connection.cursor()) as cursor:
                try:
                    cursor.execute(sql, parameters or [])
                    _check_invocation_deadline(budget)
                    description = cursor.description or []
                    consume_database_result_payload(description)
                    _check_invocation_deadline(budget)
                    convert_row = row_converter_factory(description)
                    def rows() -> Iterator[RowT]:
                        count = 0
                        while True:
                            _check_invocation_deadline(budget)
                            batch = cursor.fetchmany(1)
                            _check_invocation_deadline(budget)
                            if not batch:
                                return
                            if len(batch) != 1 or count >= self.config.max_result_rows:
                                raise TrinoResultLimitError(
                                    "Trino result exceeds the client limit of "
                                    f"{self.config.max_result_rows} rows"
                                )
                            row = convert_row(batch[0])
                            consume_database_result_payload(row)
                            count += 1
                            yield row
                    iterator = rows()
                    try:
                        yield iterator, description
                    finally:
                        iterator.close()
                    return
                except QueryWorkBudgetExceeded:
                    raise
                except Exception as error:
                    try:
                        _check_invocation_deadline(budget)
                    except QueryWorkBudgetExceeded as deadline_error:
                        raise deadline_error from error
                    raise
        except Exception as error:
            auth_error_type = getattr(getattr(self.driver, "exceptions", None), "TrinoAuthError", None)
            if not isinstance(auth_error_type, type) or not isinstance(error, auth_error_type):
                raise
        finally:
            try:
                if oauth_session is not None:
                    oauth_session.close()
            finally:
                _TRINO_WORK_SLOTS.release()
        # Raise outside the driver exception handler to detach backend content.
        raise TrinoConfigurationError("Trino authentication failed")


def _bounded_query_timeouts(
    config: TrinoConfig,
    budget: QueryWorkBudget | None,
) -> tuple[float, str, str]:
    if budget is None:
        return (
            config.request_timeout,
            config.query_max_execution_time,
            config.query_max_run_time,
        )

    remaining_seconds = budget.remaining_invocation_seconds()
    remaining_ms = max(1, int(remaining_seconds * 1_000))
    return (
        min(config.request_timeout, remaining_seconds),
        _bounded_duration(
            config.query_max_execution_time,
            "TRINO_QUERY_MAX_EXECUTION_TIME",
            MAX_QUERY_EXECUTION_TIME_MS,
            remaining_ms,
        ),
        _bounded_duration(
            config.query_max_run_time,
            "TRINO_QUERY_MAX_RUN_TIME",
            MAX_QUERY_RUN_TIME_MS,
            remaining_ms,
        ),
    )


def _bounded_duration(
    configured: str,
    name: str,
    maximum_ms: int,
    remaining_ms: int,
) -> str:
    configured_ms = parse_duration_value(configured, name, maximum_ms)
    if configured_ms <= remaining_ms:
        return configured
    return f"{remaining_ms}ms"


def _check_invocation_deadline(budget: QueryWorkBudget | None) -> None:
    if budget is not None:
        budget.check_invocation_deadline()


def _identity_row_converter(
    _description: Sequence[Any],
) -> Callable[[Any], tuple[Any, ...]]:
    def convert(row: Any) -> tuple[Any, ...]:
        return cast(tuple[Any, ...], row)

    return convert


def _dict_row_converter(
    description: Sequence[Any],
) -> Callable[[Sequence[Any]], dict[str, Any]]:
    names = [column[0] for column in description]

    def convert(row: Sequence[Any]) -> dict[str, Any]:
        return dict(zip(names, row, strict=True))

    return convert


def rows_to_dicts(
    description: Sequence[Any],
    rows: Iterable[Sequence[Any]],
) -> list[dict[str, Any]]:
    convert_row = _dict_row_converter(description)
    return [convert_row(row) for row in rows]
