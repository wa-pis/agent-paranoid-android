from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import test_data_agent.sql_query_adapters as adapters_module
from test_data_agent.postgres_client import PostgresResultColumn
from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits
from test_data_agent.sql_query_adapters import (
    profile_postgres_query_source,
    profile_trino_query_source,
)
from test_data_agent.sql_query_profiling import SqlQueryProfileError
from test_data_agent.sql_query_source import (
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    SqlQuerySourceError,
)
from test_data_agent.trino_config import TrinoConfig


def request(path: Path, adapter: SqlQueryAdapter) -> SqlQueryProfileRequest:
    return SqlQueryProfileRequest(
        adapter=adapter,
        source_id="warehouse",
        entity="orders_view",
        query_file=path,
    )


def postgres_config() -> PostgresConfig:
    return PostgresConfig(
        source_id="physical",
        host="db.example.test",
        port=5432,
        database="analytics",
        user="reader",
        allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset(
            {
                "public.orders.order_id",
                "public.orders.state",
                "public.orders.amount",
            }
        ),
        limits=PostgresProfileLimits(max_statements=20),
    )


def trino_config() -> TrinoConfig:
    return TrinoConfig(
        host="trino.example.test",
        port=8443,
        user="reader",
        http_scheme="https",
        allowed_catalogs=frozenset({"lake"}),
        allowed_schemas=frozenset({"safe"}),
        allowed_table_columns=frozenset({"lake.safe.orders.*"}),
    )


def aggregate_rows(sql: str) -> list[dict[str, object]]:
    if "max_abs_magnitude" in sql:
        is_id = 'count("order_id")' in sql
        return [
            {
                "row_count": 3,
                "non_null_count": 3 if is_id else 2,
                "distinct_count": 3 if is_id else 2,
                "has_negative": False,
                "has_positive": True,
                "max_abs_magnitude": 2,
            }
        ]
    if "non_null_count" in sql:
        if 'count("state")' in sql:
            non_null, distinct = 3, 2
        elif 'count("amount")' in sql:
            non_null, distinct = 2, 2
        else:
            non_null, distinct = 3, 3
        return [
            {
                "row_count": 3,
                "non_null_count": non_null,
                "distinct_count": distinct,
            }
        ]
    return [{"row_count": 3}]


class FakePostgresSession:
    def __init__(self) -> None:
        self.sql: list[str] = []

    def __enter__(self) -> FakePostgresSession:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def fetch_aggregate_dicts(self, query: object) -> list[dict[str, object]]:
        sql = str(getattr(query, "sql"))
        self.sql.append(sql)
        if sql.startswith("SELECT a.attname AS column_name"):
            return [
                {
                    "column_name": "order_id",
                    "data_type": "bigint",
                    "is_nullable": False,
                    "ordinal_position": 1,
                },
                {
                    "column_name": "state",
                    "data_type": "text",
                    "is_nullable": False,
                    "ordinal_position": 2,
                },
                {
                    "column_name": "amount",
                    "data_type": "numeric",
                    "is_nullable": True,
                    "ordinal_position": 3,
                },
            ]
        return aggregate_rows(sql)

    def describe_no_rows(self, query: object) -> tuple[PostgresResultColumn, ...]:
        sql = str(getattr(query, "sql"))
        self.sql.append(sql)
        return (
            PostgresResultColumn("order_id", "bigint", False),
            PostgresResultColumn("state", "text", False),
            PostgresResultColumn("amount", "numeric", True),
        )


def test_postgres_query_source_uses_metadata_then_aggregates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = tmp_path / "query.sql"
    query.write_text(
        "SELECT order_id, state, amount FROM public.orders "
        "WHERE state = 'source-only'",
        encoding="utf-8",
    )
    session = FakePostgresSession()

    class Client:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def session(self) -> FakePostgresSession:
            return session

    monkeypatch.setattr(adapters_module, "PostgresClient", Client)

    profile = profile_postgres_query_source(
        request(query, SqlQueryAdapter.POSTGRES),
        config=postgres_config(),
        driver=object(),
    )

    assert profile.source_type == "postgres_query"
    assert profile.entities[0].name == "warehouse.orders_view"
    assert "source-only" not in profile.model_dump_json()
    assert all("SELECT *" not in sql.upper() for sql in session.sql)


class FakeTrinoClient:
    sql: list[str] = []

    def __init__(self, **_kwargs: object) -> None:
        self.sql = []
        type(self).sql = self.sql

    def fetch_dicts(
        self,
        sql: str,
        _parameters: object = None,
    ) -> list[dict[str, object]]:
        self.sql.append(sql)
        if "information_schema.columns" in sql:
            return [
                {"column_name": "order_id", "data_type": "bigint", "is_nullable": "NO"},
                {"column_name": "state", "data_type": "varchar", "is_nullable": "NO"},
                {"column_name": "amount", "data_type": "decimal(12,2)", "is_nullable": "YES"},
            ]
        return aggregate_rows(sql)

    def execute_query(self, sql: str) -> tuple[list[tuple[object, ...]], list[object]]:
        self.sql.append(sql)
        description = [
            ("order_id", SimpleNamespace(name="bigint"), None, None, None, None, False),
            ("state", SimpleNamespace(name="varchar"), None, None, None, None, False),
            ("amount", SimpleNamespace(name="decimal(12,2)"), None, None, None, None, True),
        ]
        return [], description


def test_trino_query_source_requires_and_uses_table_column_allowlist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = tmp_path / "query.sql"
    query.write_text(
        "SELECT order_id, state, amount FROM lake.safe.orders",
        encoding="utf-8",
    )
    monkeypatch.setattr(adapters_module, "TrinoClient", FakeTrinoClient)

    profile = profile_trino_query_source(
        request(query, SqlQueryAdapter.TRINO),
        config=trino_config(),
        driver=object(),
    )

    assert profile.source_type == "trino_query"
    assert profile.entities[0].row_count == 3
    assert all("SELECT *" not in sql.upper() for sql in FakeTrinoClient.sql)


def test_trino_query_source_rejects_missing_column_allowlist_before_client(
    tmp_path: Path,
) -> None:
    query = tmp_path / "query.sql"
    query.write_text("SELECT order_id FROM lake.safe.orders", encoding="utf-8")
    config = trino_config()
    config = TrinoConfig(
        **{
            **config.__dict__,
            "allowed_table_columns": None,
        }
    )

    with pytest.raises(SqlQuerySourceError, match="requires exact"):
        profile_trino_query_source(
            request(query, SqlQueryAdapter.TRINO),
            config=config,
            driver=object(),
        )


def test_backend_error_is_redacted_by_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "backend-secret-literal"
    query = tmp_path / "query.sql"
    query.write_text("SELECT order_id FROM public.orders", encoding="utf-8")

    class BrokenClient:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def session(self) -> object:
            raise RuntimeError(secret)

    monkeypatch.setattr(adapters_module, "PostgresClient", BrokenClient)

    with pytest.raises(SqlQueryProfileError) as exc_info:
        profile_postgres_query_source(
            request(query, SqlQueryAdapter.POSTGRES),
            config=postgres_config(),
            driver=object(),
        )

    assert secret not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
