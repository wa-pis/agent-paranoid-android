from __future__ import annotations

import json
from dataclasses import replace
from threading import BoundedSemaphore
from typing import Any

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent.trino_client import (
    TrinoClient,
    TrinoCapacityError,
    TrinoResultLimitError,
    rows_to_dicts,
)
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    QueryWorkDimension,
    with_query_work_budget,
)


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
        self.fetch_sizes: list[int] = []
        self.row_offset = 0
        self.closed = False

    def execute(self, sql: str, parameters: list[Any]) -> None:
        self.executed.append((sql, parameters))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchmany(self, size: int) -> list[tuple[Any, ...]]:
        self.fetch_size = size
        self.fetch_sizes.append(size)
        batch = self.rows[self.row_offset : self.row_offset + size]
        self.row_offset += len(batch)
        return batch

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
    assert cursor.fetch_size == 1
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


def test_client_rejects_exhausted_shared_capacity_before_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import test_data_agent.trino_client as client_module

    slots = BoundedSemaphore(1)
    slots.acquire()
    monkeypatch.setattr(client_module, "_TRINO_WORK_SLOTS", slots)
    cursor = FakeCursor([])
    driver = FakeDriver(cursor)

    with pytest.raises(
        TrinoCapacityError,
        match="^Trino request capacity exhausted$",
    ) as error:
        TrinoClient(config=client_config(), driver=driver).execute_query(
            "SELECT bounded"
        )

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert driver.dbapi.connect_kwargs is None


def test_client_releases_shared_capacity_after_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import test_data_agent.trino_client as client_module

    monkeypatch.setattr(client_module, "_TRINO_WORK_SLOTS", BoundedSemaphore(1))
    cursor = FakeCursor([], execute_error=RuntimeError("query failed"))
    client = TrinoClient(config=client_config(), driver=FakeDriver(cursor))

    with pytest.raises(RuntimeError, match="query failed"):
        client.execute_query("SELECT bounded")
    cursor.execute_error = None
    assert client.execute_query("SELECT bounded") == ([], cursor.description)


def test_client_bounds_query_timeouts_by_remaining_invocation_time() -> None:
    now = 10.0
    cursor = FakeCursor([])
    driver = FakeDriver(cursor)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, max_invocation_seconds=5.0)
    budget = QueryWorkBudget(limits, monotonic_clock=lambda: now)
    execute = with_query_work_budget(
        TrinoClient(config=client_config(), driver=driver).execute_query,
        limits,
        budget_provider=lambda: budget,
    )

    execute("SELECT bounded")

    assert driver.dbapi.connect_kwargs is not None
    assert driver.dbapi.connect_kwargs["request_timeout"] == 5.0
    assert driver.dbapi.connect_kwargs["session_properties"] == {
        "query_max_execution_time": "5000ms",
        "query_max_run_time": "5000ms",
        "query_max_scan_physical_bytes": "128MB",
    }


def test_client_closes_active_query_when_invocation_deadline_expires() -> None:
    now = 10.0

    class ExpiringCursor(FakeCursor):
        def execute(self, sql: str, parameters: list[Any]) -> None:
            nonlocal now
            super().execute(sql, parameters)
            now = 15.0
            raise TimeoutError("request timed out")

    cursor = ExpiringCursor([])
    driver = FakeDriver(cursor)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, max_invocation_seconds=5.0)
    budget = QueryWorkBudget(limits, monotonic_clock=lambda: now)
    execute = with_query_work_budget(
        TrinoClient(config=client_config(), driver=driver).execute_query,
        limits,
        budget_provider=lambda: budget,
    )

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        execute("SELECT bounded")

    assert error.value.dimension is QueryWorkDimension.INVOCATION_SECONDS
    assert isinstance(error.value.__cause__, TimeoutError)
    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True


def test_client_requires_optional_trino_driver() -> None:
    with pytest.raises(RuntimeError, match="trino package is not installed"):
        TrinoClient(config=client_config(), driver=None).execute_query("SELECT bounded")


def test_client_rejects_sql_budget_before_opening_connection() -> None:
    cursor = FakeCursor([])
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, sql_formula_chars=5)
    execute = with_query_work_budget(client.execute_query, limits)

    with pytest.raises(QueryWorkBudgetExceeded, match="SQL/formula characters"):
        execute("SELECT bounded")

    assert driver.dbapi.connect_kwargs is None
    assert cursor.executed == []


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT first_value, second_value FROM safe_table",
        "SELECT * FROM safe_table",
    ],
)
def test_client_rejects_projected_column_budget_before_opening_connection(
    sql: str,
) -> None:
    cursor = FakeCursor([])
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, projected_columns=1)
    execute = with_query_work_budget(client.execute_query, limits)

    with pytest.raises(QueryWorkBudgetExceeded, match="projected columns"):
        execute(sql)

    assert driver.dbapi.connect_kwargs is None
    assert cursor.executed == []


def test_client_rejects_statement_budget_before_opening_connection() -> None:
    cursor = FakeCursor([])
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, statements=1)
    execute = with_query_work_budget(client.execute_query, limits)

    with pytest.raises(QueryWorkBudgetExceeded, match="statements"):
        execute("SELECT first_value; SELECT second_value")

    assert driver.dbapi.connect_kwargs is None
    assert cursor.executed == []


def test_client_rejects_cumulative_scan_estimate_before_opening_connection() -> None:
    cursor = FakeCursor([])
    driver = FakeDriver(cursor)
    config = client_config()
    estimated_scan_bytes = 128 * 1024**2
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        max_cumulative_estimated_scan_bytes=estimated_scan_bytes - 1,
    )
    budget = QueryWorkBudget(limits)
    execute = with_query_work_budget(
        TrinoClient(config=config, driver=driver).execute_query,
        limits,
        budget_provider=lambda: budget,
    )

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        execute("SELECT bounded")

    assert error.value.dimension is (
        QueryWorkDimension.CUMULATIVE_ESTIMATED_SCAN_BYTES
    )
    assert budget.snapshot().statements == 1
    assert budget.snapshot().cumulative_estimated_scan_bytes == 0
    assert driver.dbapi.connect_kwargs is None
    assert cursor.executed == []


def test_client_rejects_database_result_budget_before_retaining_result() -> None:
    cursor = FakeCursor([("x" * 256,), ("must-not-be-fetched",)])
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, database_result_bytes=128)
    execute = with_query_work_budget(client.execute_query, limits)

    with pytest.raises(QueryWorkBudgetExceeded, match="database result bytes"):
        execute("SELECT synthetic_value FROM safe_table")

    assert cursor.fetch_sizes == [1]
    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True


def test_fetch_dicts_accounts_for_row_conversion_before_retaining_result() -> None:
    row = (1, "synthetic")
    converted_row = {"synthetic_id": 1, "status": "synthetic"}

    def payload_size(value: Any) -> int:
        return len(
            json.dumps(
                value,
                default=str,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )

    description_size = payload_size(FakeCursor.description)
    tuple_result_size = payload_size(row)
    converted_result_size = payload_size(converted_row)
    assert converted_result_size > tuple_result_size

    cursor = FakeCursor([row, (2, "must-not-be-fetched")])
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        database_result_bytes=description_size + tuple_result_size,
    )
    fetch = with_query_work_budget(client.fetch_dicts, limits)

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        fetch("SELECT synthetic_id, status FROM safe_table")

    assert error.value.attempted == description_size + converted_result_size
    assert error.value.limit == description_size + tuple_result_size
    assert cursor.fetch_sizes == [1]
    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True


def test_fetch_dicts_rejects_wide_row_at_database_result_boundary() -> None:
    description = [(f"column_{index:03d}",) for index in range(64)]
    row = tuple(f"synthetic_{index:03d}" for index in range(64))
    converted_row = {
        column[0]: value for column, value in zip(description, row, strict=True)
    }

    def payload_size(value: Any) -> int:
        return len(
            json.dumps(
                value,
                default=str,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )

    description_size = payload_size(description)
    converted_row_size = payload_size(converted_row)
    cursor = FakeCursor([row, tuple("must-not-be-fetched" for _ in row)])
    cursor.description = description
    driver = FakeDriver(cursor)
    client = TrinoClient(config=client_config(), driver=driver)
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        database_result_bytes=description_size + converted_row_size - 1,
    )
    fetch = with_query_work_budget(client.fetch_dicts, limits)

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        fetch("SELECT synthetic_payload FROM safe_table")

    assert error.value.attempted == description_size + converted_row_size
    assert error.value.limit == description_size + converted_row_size - 1
    assert cursor.fetch_sizes == [1]
    assert cursor.closed is True
    assert driver.dbapi.connection.closed is True


def test_server_keeps_client_compatibility_exports() -> None:
    assert mcp_trino_server.TrinoClient is TrinoClient
    assert mcp_trino_server.TrinoResultLimitError is TrinoResultLimitError
    assert mcp_trino_server.rows_to_dicts is rows_to_dicts
