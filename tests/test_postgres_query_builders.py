from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import pytest

from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits
from test_data_agent.postgres_query_builders import (
    PostgresScopeError,
    build_check_constraints_query,
    build_column_summary_query,
    build_columns_query,
    build_foreign_key_coverage_query,
    build_foreign_keys_query,
    build_list_tables_query,
    build_local_category_candidates_query,
    build_numeric_shape_query,
    build_primary_keys_query,
    build_table_row_count_query,
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


def test_table_and_column_aggregates_quote_only_allowlisted_identifiers() -> None:
    table_query = build_table_row_count_query(postgres_config(), "public", "orders")
    column_query = build_column_summary_query(
        postgres_config(), "public", "orders", "status"
    )

    assert table_query.sql == ('SELECT count(*) AS row_count FROM "public"."orders"')
    assert column_query.sql == (
        'SELECT count(*) AS row_count, count("status") AS non_null_count, '
        'count(DISTINCT "status") AS distinct_count FROM "public"."orders"'
    )
    assert table_query.parameters == column_query.parameters == ()


def test_numeric_shape_does_not_select_exact_extrema() -> None:
    query = build_numeric_shape_query(
        postgres_config(), "public", "orders", "customer_id"
    )

    assert "max_abs_magnitude" in query.sql
    assert "has_negative" in query.sql
    assert "has_positive" in query.sql
    assert " min(" not in query.sql.lower()
    assert ' max("customer_id")' not in query.sql.lower()


def test_local_category_candidates_require_qualified_explicit_field() -> None:
    field = LocalCategoryField(entity="warehouse.public.orders", field="status")
    query = build_local_category_candidates_query(postgres_config(), field)

    assert query.parameters == (21,)
    assert query.sql == (
        'SELECT "status" AS value, count(*) AS count FROM "public"."orders" '
        'WHERE "status" IS NOT NULL GROUP BY "status" '
        "ORDER BY count DESC, value ASC LIMIT %s"
    )


def test_local_category_candidates_reject_ambiguous_or_sensitive_fields() -> None:
    with pytest.raises(PostgresScopeError, match="qualified allowlist"):
        build_local_category_candidates_query(
            postgres_config(),
            LocalCategoryField(entity="public.orders", field="status"),
        )

    base_config = postgres_config()
    config = replace(
        base_config,
        allowed_columns=frozenset(
            {*base_config.allowed_columns, "public.orders.api_token"}
        ),
    )
    with pytest.raises(PostgresScopeError, match="sensitive identifier"):
        build_local_category_candidates_query(
            config,
            LocalCategoryField(entity="warehouse.public.orders", field="api_token"),
        )


def test_local_category_candidate_limit_is_bounded_by_session_rows() -> None:
    config = postgres_config(limits=PostgresProfileLimits(max_result_rows=20))
    with pytest.raises(PostgresScopeError, match="result row budget"):
        build_local_category_candidates_query(
            config,
            LocalCategoryField(entity="warehouse.public.orders", field="status"),
            max_categories=20,
        )


def test_foreign_key_coverage_returns_aggregate_counts_only() -> None:
    query = build_foreign_key_coverage_query(
        postgres_config(),
        parent_schema="crm",
        parent_table="customers",
        parent_column="id",
        child_schema="public",
        child_table="orders",
        child_column="customer_id",
    )

    assert "matched_count" in query.sql
    assert "orphan_count" in query.sql
    assert 'FROM "public"."orders" AS c' in query.sql
    assert 'FROM "crm"."customers"' in query.sql
    assert query.parameters == ()


def test_aggregate_query_rejects_unallowed_column() -> None:
    with pytest.raises(PostgresScopeError, match="column is outside"):
        build_column_summary_query(
            postgres_config(), "public", "orders", "payment_card"
        )


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
