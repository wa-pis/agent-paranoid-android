from __future__ import annotations

from typing import Any

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent.trino_client import (
    TrinoClient,
    TrinoResultLimitError,
    rows_to_dicts,
)
from test_data_agent.trino_config import TrinoConfig


class FakeCursor:
    description = [("synthetic_id",), ("status",)]

    def __init__(
        self,
        rows: list[tuple[Any, ...]],
        *,
        execute_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.execute_error = execute_error
        self.executed: list[tuple[str, list[Any]]] = []
        self.fetch_size: int | None = None
        self.closed = False

    def execute(self, sql: str, parameters: list[Any]) -> None:
        self.executed.append((sql, parameters))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchmany(self, size: int) -> list[tuple[Any, ...]]:
        self.fetch_size = size
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_instance = cursor
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True


class FakeDbApi:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.connect_kwargs: dict[str, Any] | None = None

    def connect(self, **kwargs: Any) -> FakeConnection:
        self.connect_kwargs = kwargs
        return self.connection


class FakeDriver:
    def __init__(self, cursor: FakeCursor) -> None:
        self.dbapi = FakeDbApi(FakeConnection(cursor))


def client_config(*, max_result_rows: int = 2) -> TrinoConfig:
    return TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=None,
        allowed_schemas=None,
        request_timeout=12.0,
        query_max_execution_time="20s",
        query_max_run_time="25s",
        query_max_scan_physical_bytes="128MB",
        max_result_rows=max_result_rows,
    )


def test_client_applies_budgets_and_closes_resources() -> None:
    cursor = FakeCursor([(1, "synthetic")])
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)

    rows = client.fetch_dicts("SELECT synthetic_id, status FROM safe_table LIMIT 1")

    assert rows == [{"synthetic_id": 1, "status": "synthetic"}]
    assert cursor.executed == [
        ("SELECT synthetic_id, status FROM safe_table LIMIT 1", [])
    ]
    assert cursor.fetch_size == 3
    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True
    assert driver.dbapi.connect_kwargs == {
        "host": "trino.internal",
        "port": 8443,
        "user": "synthetic-agent",
        "http_scheme": "https",
        "request_timeout": 12.0,
        "session_properties": {
            "query_max_execution_time": "20s",
            "query_max_run_time": "25s",
            "query_max_scan_physical_bytes": "128MB",
        },
    }


def test_client_rejects_oversized_results_and_closes_resources() -> None:
    cursor = FakeCursor([(1, "a"), (2, "b"), (3, "c")])
    driver = FakeDriver(cursor)

    with pytest.raises(TrinoResultLimitError, match="limit of 2 rows"):
        TrinoClient(config=client_config(), driver=driver).execute_query(
            "SELECT bounded"
        )

    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True


def test_client_closes_resources_when_execution_fails() -> None:
    cursor = FakeCursor([], execute_error=RuntimeError("query failed"))
    driver = FakeDriver(cursor)

    with pytest.raises(RuntimeError, match="query failed"):
        TrinoClient(config=client_config(), driver=driver).execute_query(
            "SELECT bounded"
        )

    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True


def test_client_requires_optional_trino_driver() -> None:
    with pytest.raises(RuntimeError, match="trino package is not installed"):
        TrinoClient(config=client_config(), driver=None).execute_query("SELECT bounded")


def test_server_keeps_client_compatibility_exports() -> None:
    assert mcp_trino_server.TrinoClient is TrinoClient
    assert mcp_trino_server.TrinoResultLimitError is TrinoResultLimitError
    assert mcp_trino_server.rows_to_dicts is rows_to_dicts
