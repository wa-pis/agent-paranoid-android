from __future__ import annotations

from collections.abc import Callable

import pytest

from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits
from test_data_agent.postgres_query_builders import (
    PostgresScopeError,
    build_check_constraints_query,
    build_columns_query,
    build_foreign_keys_query,
    build_list_tables_query,
    build_primary_keys_query,
)


def postgres_config(
    *,
    limits: PostgresProfileLimits | None = None,
) -> PostgresConfig:
    return PostgresConfig(
        source_id="warehouse",
        host="db.example.test",
        port=5432,
        database="analytics",
        user="profiler",
        allowed_schemas=frozenset({"crm", "public"}),
        allowed_tables=frozenset({"public.orders", "crm.customers"}),
        allowed_columns=frozenset(
            {
                "public.orders.customer_id",
                "public.orders.status",
                "crm.customers.id",
                "crm.customers.tier",
            }
        ),
        limits=limits or PostgresProfileLimits(),
    )


def test_list_tables_query_is_allowlisted_parameterized_and_stable() -> None:
    query = build_list_tables_query(postgres_config())

    assert query.sql.startswith("SELECT n.nspname AS table_schema")
    assert query.sql.count("(%s, %s)") == 2
    assert query.parameters == ("crm", "customers", "public", "orders")
    assert "crm.customers" not in query.sql
    assert query.sql.endswith("ORDER BY n.nspname, c.relname")


def test_columns_query_only_requests_allowed_columns() -> None:
    query = build_columns_query(postgres_config(), "public", "orders")

    assert "pg_catalog.format_type" in query.sql
    assert "NOT a.attnotnull AS is_nullable" in query.sql
    assert query.parameters == (
        "public",
        "orders",
        "customer_id",
        "status",
    )
    assert "customer_id" not in query.sql
    assert query.sql.endswith("ORDER BY a.attnum")


def test_primary_key_query_keeps_key_order_and_column_scope() -> None:
    query = build_primary_keys_query(postgres_config(), "crm", "customers")

    assert "unnest(con.conkey) WITH ORDINALITY" in query.sql
    assert query.parameters == ("crm", "customers", "id", "tier")
    assert query.sql.endswith("ORDER BY con.conname, key.position")


def test_foreign_key_query_requires_both_sides_to_be_allowed() -> None:
    query = build_foreign_keys_query(postgres_config())
    columns = (
        "crm",
        "customers",
        "id",
        "crm",
        "customers",
        "tier",
        "public",
        "orders",
        "customer_id",
        "public",
        "orders",
        "status",
    )

    assert query.sql.count("(%s, %s, %s)") == 8
    assert query.parameters == (*columns, *columns)
    assert "unnest(con.conkey, con.confkey) WITH ORDINALITY" in query.sql
    assert "public.orders" not in query.sql


def test_check_constraint_query_is_limited_to_allowed_tables() -> None:
    query = build_check_constraints_query(postgres_config())

    assert "pg_catalog.pg_get_expr" in query.sql
    assert query.parameters == ("crm", "customers", "public", "orders")
    assert query.sql.endswith("ORDER BY n.nspname, c.relname, con.conname")


def test_unallowed_table_fails_before_query_construction() -> None:
    with pytest.raises(PostgresScopeError, match="outside the allowlist"):
        build_columns_query(postgres_config(), "public", "payments")


@pytest.mark.parametrize(
    ("limits", "builder", "message"),
    [
        (
            PostgresProfileLimits(max_tables=1),
            build_list_tables_query,
            "table allowlist",
        ),
        (
            PostgresProfileLimits(max_columns=1),
            build_foreign_keys_query,
            "column allowlist",
        ),
    ],
)
def test_allowlist_size_cannot_exceed_profile_budget(
    limits: PostgresProfileLimits,
    builder: Callable[[PostgresConfig], object],
    message: str,
) -> None:
    with pytest.raises(PostgresScopeError, match=message):
        builder(postgres_config(limits=limits))
