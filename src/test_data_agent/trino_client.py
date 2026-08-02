"""Bounded Trino client boundary with explicit configuration and cleanup."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_sql_policy import consume_projected_column_work

try:  # pragma: no cover - live Trino is not used in unit tests.
    import trino as trino
except ImportError:  # pragma: no cover
    trino = None  # type: ignore[assignment]


class TrinoResultLimitError(ValueError):
    """Raised when a Trino response exceeds the client-side safety limit."""


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
        if self.driver is None:
            raise RuntimeError("trino package is not installed")

        consume_projected_column_work(sql)
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
            rows = cursor.fetchmany(self.config.max_result_rows + 1)
            if len(rows) > self.config.max_result_rows:
                raise TrinoResultLimitError(
                    "Trino result exceeds the client limit of "
                    f"{self.config.max_result_rows} rows"
                )
            return rows, cursor.description or []
        finally:
            try:
                cursor.close()
            finally:
                connection.close()

    def fetch_dicts(
        self,
        sql: str,
        parameters: Sequence[Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows, description = self.execute_query(sql, parameters)
        return rows_to_dicts(description, rows)


def rows_to_dicts(
    description: Sequence[Any],
    rows: Iterable[Sequence[Any]],
) -> list[dict[str, Any]]:
    names = [column[0] for column in description]
    return [dict(zip(names, row, strict=True)) for row in rows]
