from __future__ import annotations

import json

import pytest

from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.sql_query_profiling import (
    QueryResultColumn,
    SqlQueryProfileError,
    TrustedProfileQuery,
    build_no_row_schema_query,
    build_query_column_summary_query,
    build_query_numeric_shape_query,
    build_query_row_count_query,
    profile_validated_query,
)
from test_data_agent.sql_query_source import SqlQueryAdapter, ValidatedSqlQuery
from test_data_agent.validation import validate_dataset


def plan(
    *,
    adapter: SqlQueryAdapter = SqlQueryAdapter.POSTGRES,
) -> ValidatedSqlQuery:
    return ValidatedSqlQuery(
        adapter=adapter,
        source_id="warehouse",
        entity_name="warehouse.paid_orders",
        table_parts=("public", "orders")
        if adapter is SqlQueryAdapter.POSTGRES
        else ("lake", "safe", "orders"),
        output_fields=("order_id", "state", "amount"),
        fingerprint="a" * 64,
        sql=(
            'SELECT "order_id", "state", "amount" '
            'FROM "public"."orders" WHERE "state" = \'source-only\''
        ),
    )


class FakeResults:
    def __init__(self, *, backend_error: Exception | None = None) -> None:
        self.queries: list[TrustedProfileQuery] = []
        self.backend_error = backend_error

    def describe(self, query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
        self.queries.append(query)
        if self.backend_error is not None:
            raise self.backend_error
        return (
            QueryResultColumn("order_id", "bigint", False),
            QueryResultColumn("state", "text", False),
            QueryResultColumn("amount", "numeric", True),
        )

    def fetch(self, query: TrustedProfileQuery) -> list[dict[str, object]]:
        self.queries.append(query)
        if "GROUP BY" in query.sql:
            return [
                {"value": "paid", "count": 2},
                {"value": "shipped", "count": 1},
            ]
        if "max_abs_magnitude" in query.sql:
            is_order_id = 'count("order_id")' in query.sql
            non_null = 3 if is_order_id else 2
            distinct = 3 if is_order_id else 2
            return [
                {
                    "row_count": 3,
                    "non_null_count": non_null,
                    "distinct_count": distinct,
                    "has_negative": False,
                    "has_positive": True,
                    "max_abs_magnitude": 2,
                }
            ]
        if "non_null_count" in query.sql:
            if 'count("state")' in query.sql:
                non_null, distinct = 3, 2
            elif 'count("amount")' in query.sql:
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


def test_profile_is_source_free_and_keeps_exact_local_category_values() -> None:
    results = FakeResults()

    profile = profile_validated_query(
        plan(),
        describe_query=results.describe,
        fetch_query=results.fetch,
        local_category_fields=(
            LocalCategoryField(entity="warehouse.paid_orders", field="state"),
        ),
    )

    assert profile.source_type == "postgres_query"
    assert profile.source_fingerprint == "a" * 64
    assert profile.source_policy_version == "1.0"
    assert profile.entities[0].name == "warehouse.paid_orders"
    assert profile.entities[0].row_count == 3
    state = profile.entities[0].field("state")
    assert {
        item["value"] for item in state.distribution["categories"]
    } == {"paid", "shipped"}
    serialized = profile.model_dump_json()
    assert "source-only" not in serialized
    assert all("SELECT *" not in query.sql.upper() for query in results.queries)


def test_query_profile_feeds_deterministic_synthetic_generation() -> None:
    results = FakeResults()
    profile = profile_validated_query(
        plan(),
        describe_query=results.describe,
        fetch_query=results.fetch,
    )
    spec = infer_dataset_spec(profile, count=8)

    first = generate_dataset(spec, seed=73)
    second = generate_dataset(spec, seed=73)

    assert first == second
    assert validate_dataset(first, spec).valid is True
    assert "source-only" not in json.dumps(first, sort_keys=True)


def test_default_profile_does_not_query_or_store_category_literals() -> None:
    results = FakeResults()

    profile = profile_validated_query(
        plan(),
        describe_query=results.describe,
        fetch_query=results.fetch,
    )

    assert profile.entities[0].field("state").distribution == {}
    assert all("GROUP BY" not in query.sql for query in results.queries)


def test_trino_builders_use_explicit_outer_projection() -> None:
    query_plan = plan(adapter=SqlQueryAdapter.TRINO)

    queries = (
        build_no_row_schema_query(query_plan),
        build_query_row_count_query(query_plan),
        build_query_column_summary_query(query_plan, "amount"),
        build_query_numeric_shape_query(query_plan, "amount"),
    )

    assert all("SELECT *" not in query.sql.upper() for query in queries)
    assert "log10" in queries[-1].sql


def test_unsupported_type_fails_before_aggregates() -> None:
    results = FakeResults()

    def describe(_query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
        return (
            QueryResultColumn("order_id", "bigint"),
            QueryResultColumn("state", "json"),
            QueryResultColumn("amount", "numeric"),
        )

    with pytest.raises(SqlQueryProfileError, match="unsupported"):
        profile_validated_query(
            plan(),
            describe_query=describe,
            fetch_query=results.fetch,
        )

    assert results.queries == []


@pytest.mark.parametrize("data_type", ["point", "json", "array(varchar)"])
def test_unsupported_types_fail_closed(data_type: str) -> None:
    results = FakeResults()

    def describe(_query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
        return (
            QueryResultColumn("order_id", "bigint"),
            QueryResultColumn("state", data_type),
            QueryResultColumn("amount", "numeric"),
        )

    with pytest.raises(SqlQueryProfileError, match="unsupported"):
        profile_validated_query(
            plan(),
            describe_query=describe,
            fetch_query=results.fetch,
        )


def test_backend_error_is_redacted() -> None:
    secret = "backend-source-literal"
    results = FakeResults(backend_error=RuntimeError(secret))

    with pytest.raises(SqlQueryProfileError) as exc_info:
        profile_validated_query(
            plan(),
            describe_query=results.describe,
            fetch_query=results.fetch,
        )

    assert secret not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_schema_drift_and_aggregate_mismatch_fail_closed() -> None:
    results = FakeResults()

    def incomplete(_query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
        return (QueryResultColumn("order_id", "bigint"),)

    with pytest.raises(SqlQueryProfileError, match="schema metadata"):
        profile_validated_query(
            plan(),
            describe_query=incomplete,
            fetch_query=results.fetch,
        )

    def invalid_counts(query: TrustedProfileQuery) -> list[dict[str, object]]:
        if "non_null_count" in query.sql:
            return [{"row_count": 3, "non_null_count": 4, "distinct_count": 4}]
        return [{"row_count": 3}]

    with pytest.raises(SqlQueryProfileError, match="aggregate counts"):
        profile_validated_query(
            plan(),
            describe_query=results.describe,
            fetch_query=invalid_counts,
        )
