from __future__ import annotations

from dataclasses import dataclass, field, replace
from types import SimpleNamespace

import pytest

from test_data_agent.core.field import FieldType
from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits
from test_data_agent.postgres_profiler import (
    PostgresProfileError, PostgresProfiler, dataset_profile_from_postgres,
)
from test_data_agent.postgres_query_builders import PostgresQuery
from test_data_agent.postgres_query_builders import PostgresScopeError


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
        if sql.startswith("SELECT a.attname AS column_name "):
            schema, table = query.parameters[:2]
            if (schema, table) == ("crm", "customers"):
                return [{"column_name": "tier"}, {"column_name": "id"}]
            return [{"column_name": "customer_id"}, {"column_name": "amount"}]
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
                        "row_count": 3,
                        "non_null_count": 2,
                        "distinct_count": 2,
                        "max_abs_magnitude": 2,
                        "has_negative": False,
                        "has_positive": True,
                    }
                ]
            return [
                {
                    "row_count": 2 if '"customers"' in sql else 3,
                    "non_null_count": 2 if '"customers"' in sql else 3,
                    "distinct_count": 2 if '"customers"' in sql else 3,
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
                        "key_column_count": 1,
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
    assert orders.field("amount").data_type == FieldType.DECIMAL
    assert (orders.field("amount").decimal_precision, orders.field("amount").decimal_scale) == (12, 2)
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
    serialized = profile.model_dump_json()
    assert "db.example.test" not in serialized
    assert '"database":"analytics"' not in serialized
    assert all("SELECT *" not in query.sql.upper() for query in results.queries)


@pytest.mark.parametrize("with_category,expected_queries", [(False, 12), (True, 13)])
def test_numeric_summary_uses_one_aggregate_per_column(
    with_category: bool, expected_queries: int,
) -> None:
    results = SyntheticPostgresResults()
    categories = (
        [LocalCategoryField(entity="warehouse.crm.customers", field="tier")]
        if with_category else []
    )
    PostgresProfiler(postgres_config(), results.fetch).profile(
        local_category_fields=categories,
    )

    assert len(results.queries) == expected_queries
    assert sum("AS distinct_count" in query.sql for query in results.queries) == 4
    assert sum("AS max_abs_magnitude" in query.sql for query in results.queries) == 3


def test_missing_allowlisted_table_fails_without_partial_profile() -> None:
    results = SyntheticPostgresResults(omit_orders=True)

    with pytest.raises(PostgresProfileError, match="configured allowlist"):
        PostgresProfiler(postgres_config(), results.fetch).profile()

    assert len(results.queries) == 1


@pytest.mark.parametrize("entity,column", [
    ("warehouse.crm.customers", "missing"),
    ("warehouse.private.records", "tier"),
])
def test_invalid_category_scope_rejected_before_any_query(entity, column):
    results = SyntheticPostgresResults()
    with pytest.raises(PostgresScopeError):
        PostgresProfiler(postgres_config(), results.fetch).profile(
            local_category_fields=[LocalCategoryField(entity=entity, field=column)]
        )
    assert results.queries == []


def test_invalid_category_scope_rejected_before_connection():
    client = SimpleNamespace(
        config=postgres_config(),
        session=lambda: pytest.fail("invalid category must not open a session"),
    )
    with pytest.raises(PostgresScopeError):
        dataset_profile_from_postgres(client, local_category_fields=[
            LocalCategoryField(entity="warehouse.crm.customers", field="missing")
        ])


def test_invalid_wildcard_category_rejected_before_aggregates():
    results = SyntheticPostgresResults()
    config = replace(postgres_config(), allowed_columns=frozenset({
        "public.orders.*", "crm.customers.*",
    }))
    with pytest.raises(PostgresScopeError):
        PostgresProfiler(config, results.fetch).profile(local_category_fields=[
            LocalCategoryField(entity="warehouse.crm.customers", field="missing")
        ])
    assert len(results.queries) == 3  # Table list and two bounded column snapshots.
    assert not any("count(*)" in query.sql for query in results.queries)


def test_qualified_wildcards_expand_to_stable_explicit_snapshot() -> None:
    results = SyntheticPostgresResults()
    config = replace(
        postgres_config(),
        allowed_columns=frozenset({"public.orders.*", "crm.customers.*"}),
    )
    category = LocalCategoryField(
        entity="warehouse.crm.customers",
        field="tier",
    )

    profile = PostgresProfiler(config, results.fetch).profile(
        local_category_fields=[category]
    )

    assert [field.name for field in profile.entity("warehouse.crm.customers").fields] == [
        "id",
        "tier",
    ]
    assert [field.name for field in profile.entity("warehouse.public.orders").fields] == [
        "customer_id",
        "amount",
    ]
    assert profile.entity("warehouse.crm.customers").field("tier").distribution[
        "kind"
    ] == "categorical"
    columns_queries = [
        query for query in results.queries if "pg_catalog.format_type" in query.sql
    ]
    assert columns_queries[0].parameters == ("crm", "customers", "id", "tier")
    assert columns_queries[1].parameters == (
        "public",
        "orders",
        "amount",
        "customer_id",
    )
    assert all("SELECT *" not in query.sql.upper() for query in results.queries)


def test_wildcard_alone_does_not_preserve_local_category_values() -> None:
    results = SyntheticPostgresResults()
    config = replace(
        postgres_config(),
        allowed_columns=frozenset({"public.orders.*", "crm.customers.*"}),
    )

    profile = PostgresProfiler(config, results.fetch).profile()

    serialized = profile.model_dump_json()
    assert "gold" not in serialized
    assert "silver" not in serialized
    assert not any(
        "AS value, count(*) AS count" in query.sql for query in results.queries
    )


def test_wildcard_metadata_failure_publishes_no_partial_profile() -> None:
    results = SyntheticPostgresResults()

    def duplicate_metadata(query: PostgresQuery) -> list[dict[str, object]]:
        rows = results.fetch(query)
        if query.sql.startswith("SELECT a.attname AS column_name "):
            return [{"column_name": "id"}, {"column_name": "id"}]
        return rows

    config = replace(
        postgres_config(),
        allowed_columns=frozenset({"public.orders.*", "crm.customers.*"}),
    )

    with pytest.raises(PostgresProfileError, match="metadata is incomplete"):
        PostgresProfiler(config, duplicate_metadata).profile()

    assert not any(
        query.sql.startswith("SELECT count(*) AS row_count FROM")
        for query in results.queries
    )


def test_wildcard_expansion_fails_before_aggregate_when_over_budget() -> None:
    results = SyntheticPostgresResults()
    config = replace(
        postgres_config(),
        allowed_columns=frozenset({"public.orders.*", "crm.customers.*"}),
        limits=replace(postgres_config().limits, max_columns=3),
    )

    with pytest.raises(PostgresProfileError, match="exceeds its budget"):
        PostgresProfiler(config, results.fetch).profile()

    assert not any(
        query.sql.startswith("SELECT count(*) AS row_count FROM")
        for query in results.queries
    )


def test_wildcard_snapshot_rejects_schema_drift_before_aggregate() -> None:
    queries: list[PostgresQuery] = []

    def fetch(query: PostgresQuery) -> list[dict[str, object]]:
        queries.append(query)
        if "table_schema" in query.sql:
            return [{"table_schema": "public", "table_name": "orders"}]
        if query.sql.startswith("SELECT a.attname AS column_name "):
            return [{"column_name": "amount"}, {"column_name": "customer_id"}]
        if "pg_catalog.format_type" in query.sql:
            return [
                {
                    "column_name": "customer_id",
                    "data_type": "bigint",
                    "is_nullable": False,
                    "ordinal_position": 1,
                }
            ]
        raise AssertionError("aggregate query must not execute")

    config = replace(
        postgres_config(),
        allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}),
        allowed_columns=frozenset({"public.orders.*"}),
    )

    with pytest.raises(PostgresProfileError, match="configured allowlist"):
        PostgresProfiler(config, fetch).profile()

    assert not any(
        query.sql.startswith("SELECT count(*) AS row_count FROM")
        for query in queries
    )



def test_category_null_rejection_sentinel_prevents_table_profile():
    results = SyntheticPostgresResults()

    def fetch(query):
        if "ELSE NULL END AS value" in query.sql:
            return [{"value": None, "count": 2}]
        return results.fetch(query)

    with pytest.raises(ValueError, match="bounded scalars"):
        PostgresProfiler(postgres_config(), fetch).profile(local_category_fields=[
            LocalCategoryField(entity="warehouse.crm.customers", field="tier")])


def declared_key_profiler(
    key_rows: list[dict[str, object]], *, key_name: str = "ticket_no",
    key_type: str = "bigint", include_tier: bool = True,
) -> tuple[PostgresProfiler, SyntheticPostgresResults]:
    results = SyntheticPostgresResults(omit_orders=True)
    allowed_names = {key_name, "tier"} if include_tier else {key_name}
    config = replace(
        postgres_config(), allowed_schemas=frozenset({"crm"}),
        allowed_tables=frozenset({"crm.customers"}),
        allowed_columns=frozenset(f"crm.customers.{name}" for name in allowed_names),
    )

    def fetch(query: PostgresQuery) -> list[dict[str, object]]:
        if "con.contype = 'p'" in query.sql:
            results.queries.append(query)
            return key_rows
        if "con.contype = 'f'" in query.sql:
            results.queries.append(query)
            return []
        rows = results.fetch(query)
        if "pg_catalog.format_type" in query.sql:
            return [
                {**row, "column_name": key_name, "data_type": key_type}
                if row["column_name"] == "id" else row
                for row in rows
                if row["column_name"] == "id" or include_tier
            ]
        return rows

    return PostgresProfiler(config, fetch), results


@pytest.mark.parametrize(
    "name,data_type,sensitive",
    [("ticket_no", "bigint", False), ("record_code", "text", False), ("email", "text", True)],
)
def test_declared_primary_key_generates_without_identifier_name_suffix(
    name: str, data_type: str, sensitive: bool,
) -> None:
    from test_data_agent.generation.entity_generator import generate_dataset
    from test_data_agent.generation.planner import infer_dataset_spec
    from test_data_agent.validation.reconciliation import validate_dataset

    profiler, _ = declared_key_profiler(
        [{"column_name": name, "ordinal_position": 1, "key_column_count": 1}],
        key_name=name, key_type=data_type,
    )
    profile = profiler.profile()
    entity = profile.entities[0]
    key = entity.field(name)
    assert entity.primary_key_candidates == [name]
    assert key.is_identifier
    assert key.sensitive is sensitive
    assert key.distribution["kind"] == "synthetic_identifier"
    spec = infer_dataset_spec(profile, count=7)
    assert spec.entities[0].primary_key == name
    rows = generate_dataset(spec, seed=42)
    assert rows == generate_dataset(spec, seed=42)
    assert len({row[name] for row in rows[entity.name]}) == 7
    assert validate_dataset(rows, spec).valid
    if data_type == "text":
        assert all(str(row[name]).startswith("synthetic_") for row in rows[entity.name])


@pytest.mark.parametrize("include_tier,position", [(True, 1), (False, 1), (False, 2)])
def test_composite_primary_key_rejects_before_aggregates(
    include_tier: bool, position: int,
) -> None:
    key_rows: list[dict[str, object]] = [
        {"column_name": "ticket_no", "ordinal_position": position, "key_column_count": 2},
    ]
    if include_tier:
        key_rows.append({"column_name": "tier", "ordinal_position": 2, "key_column_count": 2})
    profiler, results = declared_key_profiler(key_rows, include_tier=include_tier)
    with pytest.raises(PostgresProfileError, match="composite primary keys are unsupported"):
        profiler.profile()
    assert not any("count(*)" in query.sql for query in results.queries)


@pytest.mark.parametrize("count", [None, True, 0, -1, 1.5, "private-value"])
def test_invalid_primary_key_size_rejects_without_aggregates_or_value_disclosure(
    count: object,
) -> None:
    profiler, results = declared_key_profiler(
        [{"column_name": "ticket_no", "ordinal_position": 1, "key_column_count": count}],
    )
    with pytest.raises(PostgresProfileError) as error:
        profiler.profile()
    assert "private-value" not in str(error.value)
    assert not any("count(*)" in query.sql for query in results.queries)


def test_unsupported_native_primary_key_type_requires_reviewed_spec() -> None:
    profiler, _ = declared_key_profiler(
        [{"column_name": "ticket_no", "ordinal_position": 1, "key_column_count": 1}],
        key_type="boolean",
    )
    with pytest.raises(PostgresProfileError, match="primary-key type is unsupported"):
        profiler.profile()


@pytest.mark.parametrize("key_rows", [
    [{"column_name": "ticket_no", "ordinal_position": 2, "key_column_count": 1}],
    [{"column_name": "unauthorized", "ordinal_position": 1, "key_column_count": 1}],
    [
        {"column_name": "ticket_no", "ordinal_position": 1, "key_column_count": 1},
        {"column_name": "ticket_no", "ordinal_position": 1, "key_column_count": 1},
    ],
    [
        {"column_name": "ticket_no", "ordinal_position": 1, "key_column_count": 1},
        {"column_name": "tier", "ordinal_position": 1, "key_column_count": 1},
    ],
])
def test_inconsistent_primary_key_metadata_fails_closed_before_aggregates(
    key_rows: list[dict[str, object]],
) -> None:
    profiler, results = declared_key_profiler(key_rows)
    with pytest.raises(PostgresProfileError, match="primary-key metadata is invalid"):
        profiler.profile()
    assert not any("count(*)" in query.sql for query in results.queries)
