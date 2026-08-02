"""Bounded Trino client boundary with explicit configuration and cleanup."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from test_data_agent.trino_config import (
    MAX_QUERY_SCAN_BYTES,
    TrinoConfig,
    parse_data_size_value,
)
from test_data_agent.trino_sql_policy import consume_query_execution_work
from test_data_agent.trino_work_budget import consume_database_result_payload

try:  # pragma: no cover - live Trino is not used in unit tests.
    import trino as trino
except ImportError:  # pragma: no cover
    trino = None  # type: ignore[assignment]


class TrinoResultLimitError(ValueError):
    """Raised when a Trino response exceeds the client-side safety limit."""


RowT = TypeVar("RowT")


@dataclass(frozen=True)
class TrinoClient:
    """Execute Trino queries within configured result and resource budgets."""

    config: TrinoConfig
    driver: Any

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
        if self.driver is None:
            raise RuntimeError("trino package is not installed")

        estimated_scan_bytes = parse_data_size_value(
            self.config.query_max_scan_physical_bytes,
            "TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES",
            MAX_QUERY_SCAN_BYTES,
        )
        consume_query_execution_work(
            sql,
            estimated_scan_bytes_per_statement=estimated_scan_bytes,
        )
        connection = self.driver.dbapi.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            http_scheme=self.config.http_scheme,
            request_timeout=self.config.request_timeout,
            session_properties={
                "query_max_execution_time": self.config.query_max_execution_time,
                "query_max_run_time": self.config.query_max_run_time,
                "query_max_scan_physical_bytes": self.config.query_max_scan_physical_bytes,
            },
        )
        cursor = connection.cursor()
        try:
            cursor.execute(sql, parameters or [])
            description = cursor.description or []
            consume_database_result_payload(description)
            convert_row = row_converter_factory(description)
            rows: list[RowT] = []
            while batch := cursor.fetchmany(1):
                if len(rows) >= self.config.max_result_rows:
                    raise TrinoResultLimitError(
                        "Trino result exceeds the client limit of "
                        f"{self.config.max_result_rows} rows"
                    )
                row = convert_row(batch[0])
                consume_database_result_payload(row)
                rows.append(row)
            return rows, description
        finally:
            try:
                cursor.close()
            finally:
                connection.close()


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
