from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits
from test_data_agent.postgres_profiler import PostgresProfileError, PostgresProfiler
from test_data_agent.postgres_query_builders import PostgresQuery


def postgres_config() -> PostgresConfig:
    return PostgresConfig(
        source_id="warehouse",
        host="db.example.test",
        port=5432,
        database="analytics",
        user="profiler",
        allowed_schemas=frozenset({"crm", "public"}),
        allowed_tables=frozenset({"crm.customers", "public.orders"}),
        allowed_columns=frozenset(
            {
                "crm.customers.id",
                "crm.customers.tier",
                "public.orders.customer_id",
                "public.orders.amount",
            }
        ),
        password_env=None,
        limits=PostgresProfileLimits(),
    )


@dataclass
class SyntheticPostgresResults:
    omit_orders: bool = False
    queries: list[PostgresQuery] = field(default_factory=list)

    def fetch(self, query: PostgresQuery) -> list[dict[str, object]]:
        self.queries.append(query)
        sql = query.sql
        if "c.relkind IN ('r', 'p')" in sql and "table_schema" in sql:
            rows: list[dict[str, object]] = [
                {"table_schema": "crm", "table_name": "customers"},
                {"table_schema": "public", "table_name": "orders"},
            ]
            return rows[:1] if self.omit_orders else rows
        if "pg_catalog.format_type" in sql:
            schema, table = query.parameters[:2]
            if (schema, table) == ("crm", "customers"):
                return [
                    {
                        "column_name": "id",
                        "data_type": "bigint",
                        "is_nullable": False,
                        "ordinal_position": 1,
                    },
                    {
                        "column_name": "tier",
                        "data_type": "text",
                        "is_nullable": False,
                        "ordinal_position": 2,
                    },
                ]
            return [
                {
                    "column_name": "customer_id",
                    "data_type": "bigint",
                    "is_nullable": False,
                    "ordinal_position": 1,
                },
                {
                    "column_name": "amount",
                    "data_type": "numeric(12,2)",
                    "is_nullable": True,
                    "ordinal_position": 2,
                },
            ]
        if sql.startswith("SELECT count(*) AS row_count FROM"):
            return [{"row_count": 2 if '"customers"' in sql else 3}]
        if "AS distinct_count" in sql and "max_abs_magnitude" not in sql:
            if '"tier"' in sql:
                return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2}]
            if '"amount"' in sql:
                return [{"row_count": 3, "non_null_count": 2, "distinct_count": 2}]
            row_count = 2 if '"customers"' in sql else 3
            return [
                {
                    "row_count": row_count,
                    "non_null_count": row_count,
                    "distinct_count": row_count,
                }
            ]
        if "max_abs_magnitude" in sql:
            if '"amount"' in sql:
                return [
                    {
                        "max_abs_magnitude": 2,
                        "has_negative": False,
                        "has_positive": True,
                    }
                ]
            return [
                {
                    "max_abs_magnitude": 0,
                    "has_negative": False,
                    "has_positive": True,
                }
            ]
        if "AS value, count(*) AS count" in sql:
            return [
                {"value": "gold", "count": 1},
                {"value": "silver", "count": 1},
            ]
        if "con.contype = 'p'" in sql:
            if query.parameters[:2] == ("crm", "customers"):
                return [
                    {
                        "constraint_name": "customers_pkey",
                        "column_name": "id",
                        "ordinal_position": 1,
                    }
                ]
            return []
        if "con.contype = 'f'" in sql:
            return [
                {
                    "constraint_name": "orders_customer_fk",
                    "table_schema": "public",
                    "table_name": "orders",
                    "column_name": "customer_id",
                    "referenced_table_schema": "crm",
                    "referenced_table_name": "customers",
                    "referenced_column_name": "id",
                    "ordinal_position": 1,
                }
            ]
        raise AssertionError("unexpected PostgreSQL query")


def test_normalizes_bounded_results_into_relational_dataset_profile() -> None:
    results = SyntheticPostgresResults()
    category = LocalCategoryField(
        entity="warehouse.crm.customers",
        field="tier",
    )

    profile = PostgresProfiler(postgres_config(), results.fetch).profile(
        local_category_fields=[category]
    )

    assert profile.source_type == "postgres"
    assert [entity.name for entity in profile.entities] == [
        "warehouse.crm.customers",
        "warehouse.public.orders",
    ]
    customers = profile.entity("warehouse.crm.customers")
    orders = profile.entity("warehouse.public.orders")
    assert customers.primary_key_candidates == ["id"]
    assert customers.field("tier").distribution == {
        "kind": "categorical",
        "categories": [
            {"value": "gold", "count": 1.0},
            {"value": "silver", "count": 1.0},
        ],
    }
    assert orders.field("amount").nullable is True
    assert orders.field("amount").null_ratio == pytest.approx(1 / 3)
    assert orders.field("amount").distribution == {
        "kind": "numeric_shape",
        "max_abs_magnitude": 2,
        "has_negative": False,
        "has_positive": True,
    }
    relationship = profile.relationships[0]
    assert relationship.status == "declared"
    assert relationship.parent_entity == "warehouse.crm.customers"
    assert relationship.child_entity == "warehouse.public.orders"
    assert relationship.child_field == "customer_id"
    assert all("SELECT *" not in query.sql.upper() for query in results.queries)


def test_missing_allowlisted_table_fails_without_partial_profile() -> None:
    results = SyntheticPostgresResults(omit_orders=True)

    with pytest.raises(PostgresProfileError, match="configured allowlist"):
        PostgresProfiler(postgres_config(), results.fetch).profile()

    assert len(results.queries) == 1
