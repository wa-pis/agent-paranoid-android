from __future__ import annotations

from collections.abc import Sequence

import pytest

from test_data_agent.postgres_client import (
    PostgresBudgetExceeded,
    PostgresClient,
    PostgresConnectionError,
    PostgresQueryError,
)
from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits


class FakeCursor:
    def __init__(
        self,
        rows: Sequence[tuple[object, ...]],
        *,
        error: Exception | None = None,
    ) -> None:
        self.description = [("count",)]
        self._rows = list(rows)
        self._error = error
        self.executions: list[tuple[str, Sequence[object]]] = []
        self.fetch_sizes: list[int] = []
        self.closed = False

    def execute(self, sql: str, parameters: Sequence[object]) -> None:
        self.executions.append((sql, parameters))
        if self._error is not None:
            raise self._error

    def fetchmany(self, size: int) -> list[tuple[object, ...]]:
        self.fetch_sizes.append(size)
        if not self._rows:
            return []
        return [self._rows.pop(0)]

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, cursors: Sequence[FakeCursor]) -> None:
        self._cursors = list(cursors)
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self._cursors.pop(0)

    def close(self) -> None:
        self.closed = True


class FakeDriver:
    def __init__(self, connection: FakeConnection | Exception) -> None:
        self._connection = connection
        self.connect_kwargs: dict[str, object] = {}

    def connect(self, **kwargs: object) -> FakeConnection:
        self.connect_kwargs = kwargs
        if isinstance(self._connection, Exception):
            raise self._connection
        return self._connection


def postgres_config(
    *,
    limits: PostgresProfileLimits | None = None,
    password_env: str | None = "POSTGRES_TEST_PASSWORD",
) -> PostgresConfig:
    return PostgresConfig(
        source_id="warehouse",
        host="db.example.test",
        port=5432,
        database="analytics",
        user="profiler",
        allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.status"}),
        password_env=password_env,
        statement_timeout_ms=2_000,
        lock_timeout_ms=500,
        limits=limits or PostgresProfileLimits(max_seconds=3.2),
    )


def test_session_forces_read_only_timeouts_and_resolves_password_late() -> None:
    cursor = FakeCursor([(2,)])
    connection = FakeConnection([cursor])
    driver = FakeDriver(connection)
    requested_names: list[str] = []

    def getenv(name: str) -> str | None:
        requested_names.append(name)
        return "database-secret"

    client = PostgresClient(postgres_config(), driver, getenv=getenv)
    assert requested_names == []

    with client.session() as session:
        assert session.fetch_aggregate_dicts("SELECT count(*) FROM orders") == [
            {"count": 2}
        ]

    assert requested_names == ["POSTGRES_TEST_PASSWORD"]
    assert driver.connect_kwargs == {
        "host": "db.example.test",
        "port": 5432,
        "dbname": "analytics",
        "user": "profiler",
        "sslmode": "require",
        "connect_timeout": 4,
        "options": (
            "-c default_transaction_read_only=on "
            "-c statement_timeout=2000 -c lock_timeout=500"
        ),
        "password": "database-secret",
    }
    assert cursor.fetch_sizes == [1, 1]
    assert cursor.closed is True
    assert connection.closed is True


def test_statement_budget_is_cumulative_across_session() -> None:
    cursors = [FakeCursor([]), FakeCursor([])]
    connection = FakeConnection(cursors)
    limits = PostgresProfileLimits(max_statements=1)
    client = PostgresClient(
        postgres_config(limits=limits, password_env=None),
        FakeDriver(connection),
    )

    with client.session() as session:
        assert session.fetch_aggregate_dicts("SELECT 1") == []
        with pytest.raises(PostgresBudgetExceeded, match="statement budget"):
            session.fetch_aggregate_dicts("SELECT 2")

    assert cursors[1].executions == []


@pytest.mark.parametrize(
    ("limits", "message"),
    [
        (PostgresProfileLimits(max_result_rows=1), "result row budget"),
        (PostgresProfileLimits(max_result_cells=1), "result cell budget"),
    ],
)
def test_result_budgets_fail_closed(
    limits: PostgresProfileLimits,
    message: str,
) -> None:
    cursor = FakeCursor([(1,), (2,)])
    if message == "result cell budget":
        cursor.description = [("left",), ("right",)]
        cursor._rows = [(1, 2)]
    connection = FakeConnection([cursor])
    client = PostgresClient(
        postgres_config(limits=limits, password_env=None),
        FakeDriver(connection),
    )

    with client.session() as session:
        with pytest.raises(PostgresBudgetExceeded, match=message):
            session.fetch_aggregate_dicts("SELECT bounded_aggregate")

    assert cursor.closed is True
    assert connection.closed is True


def test_result_budget_is_cumulative_across_queries() -> None:
    cursors = [FakeCursor([(1,)]), FakeCursor([(2,)])]
    client = PostgresClient(
        postgres_config(
            limits=PostgresProfileLimits(max_result_rows=1),
            password_env=None,
        ),
        FakeDriver(FakeConnection(cursors)),
    )

    with client.session() as session:
        assert session.fetch_aggregate_dicts("SELECT first_aggregate") == [
            {"count": 1}
        ]
        with pytest.raises(PostgresBudgetExceeded, match="result row budget"):
            session.fetch_aggregate_dicts("SELECT second_aggregate")


def test_backend_error_text_is_not_exposed() -> None:
    secret = "source-literal-should-not-escape"
    cursor = FakeCursor([], error=RuntimeError(secret))
    client = PostgresClient(
        postgres_config(password_env=None),
        FakeDriver(FakeConnection([cursor])),
    )

    with client.session() as session:
        with pytest.raises(PostgresQueryError) as error:
            session.fetch_aggregate_dicts("SELECT aggregate")

    assert secret not in str(error.value)
    assert error.value.__cause__ is None


def test_connection_error_text_is_not_exposed() -> None:
    secret = "password=source-literal-should-not-escape"
    client = PostgresClient(
        postgres_config(password_env=None),
        FakeDriver(RuntimeError(secret)),
    )

    with pytest.raises(PostgresConnectionError) as error:
        with client.session():
            pass

    assert secret not in str(error.value)
    assert error.value.__cause__ is None


def test_deadline_is_checked_before_next_statement() -> None:
    now = 0.0

    def clock() -> float:
        return now

    cursors = [FakeCursor([]), FakeCursor([])]
    connection = FakeConnection(cursors)
    client = PostgresClient(
        postgres_config(
            limits=PostgresProfileLimits(max_seconds=1.0),
            password_env=None,
        ),
        FakeDriver(connection),
        clock=clock,
    )

    with client.session() as session:
        assert session.fetch_aggregate_dicts("SELECT 1") == []
        now = 1.0
        with pytest.raises(PostgresBudgetExceeded, match="session deadline"):
            session.fetch_aggregate_dicts("SELECT 2")

    assert cursors[1].executions == []


def test_missing_password_environment_variable_fails_before_connect() -> None:
    driver = FakeDriver(FakeConnection([]))
    client = PostgresClient(postgres_config(), driver, getenv=lambda _name: None)

    with pytest.raises(PostgresConnectionError, match="environment variable"):
        with client.session():
            pass

    assert driver.connect_kwargs == {}
