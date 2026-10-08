from __future__ import annotations

import json
from dataclasses import replace

import pytest

from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.core.field import FieldType
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


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("exhausted", [False, True])
def test_authorized_grouped_profile_is_wrapped_and_bounded(tmp_path, adapter, exhausted):
    from test_data_agent.sql_query_source import (QuerySourceColumn, SqlQueryProfileRequest,
        authorize_query_source, inspect_query_source)
    path = tmp_path / "query.sql"
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    path.write_text(f"SELECT status, COUNT(*) AS measured FROM {table} GROUP BY status")
    query_plan = authorize_query_source(inspect_query_source(SqlQueryProfileRequest(
        adapter, "warehouse", "summary", path)), (QuerySourceColumn("status", "text", False),))
    seen = []

    def describe(query):
        assert query.sql.endswith("WHERE FALSE")
        assert query.sql != query_plan.sql
        return (QueryResultColumn("status", "text", False), QueryResultColumn("measured", "bigint", False))

    def fetch(query):
        seen.append(query.sql)
        assert query.sql != query_plan.sql
        if exhausted:
            raise RuntimeError("fictional backend budget detail must stay private")
        if "non_null_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2,
                "has_negative": False, "has_positive": True, "max_abs_magnitude": 1}]
        return [{"row_count": 2}]

    if exhausted:
        with pytest.raises(SqlQueryProfileError, match="^SQL query source profiling failed$"):
            profile_validated_query(query_plan, describe_query=describe, fetch_query=fetch)
        assert len(seen) == 1
    else:
        profile = profile_validated_query(query_plan, describe_query=describe, fetch_query=fetch)
        assert profile.entities[0].row_count == 2
        assert profile.has_unmodeled_expressions
        assert query_plan.sql not in profile.model_dump_json()
        with pytest.raises(ValueError, match="SQL expression dependencies"):
            infer_dataset_spec(profile)


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
        safe_local_category_output_fields=frozenset({"state"}),
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
    assert profile.source_policy_version == "1.1"
    assert profile.entities[0].name == "warehouse.paid_orders"
    assert profile.entities[0].row_count == 3
    state = profile.entities[0].field("state")
    assert {
        item["value"] for item in state.distribution["categories"]
    } == {"paid", "shipped"}
    serialized = profile.model_dump_json()
    assert "source-only" not in serialized
    assert all("SELECT *" not in query.sql.upper() for query in results.queries)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_expression_profile_remains_available_but_inferred_generation_rejects(adapter):
    results = FakeResults()
    profile = profile_validated_query(replace(plan(adapter=adapter), has_unmodeled_expressions=True),
        describe_query=results.describe, fetch_query=results.fetch)
    restored = type(profile).model_validate_json(profile.model_dump_json())
    assert restored.has_unmodeled_expressions
    with pytest.raises(ValueError, match="^SQL expression dependencies are unsupported for inferred generation$"):
        infer_dataset_spec(restored)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_legacy_query_profile_requires_expression_reprofiling(adapter):
    results = FakeResults()
    profile = profile_validated_query(plan(adapter=adapter),
        describe_query=results.describe, fetch_query=results.fetch)
    payload = profile.model_dump()
    payload.pop("has_unmodeled_expressions")
    restored = type(profile).model_validate(payload)
    with pytest.raises(ValueError, match="requires reprofiling"):
        infer_dataset_spec(restored)
    payload["source_type"] = "csv_folder"
    assert infer_dataset_spec(type(profile).model_validate(payload)).entities


def test_expression_marker_binds_fingerprint_and_blocks_cli_advisor(tmp_path):
    from test_data_agent.advisor import build_advisor_request
    from test_data_agent.cli import main
    from test_data_agent.io.artifacts import dataset_profile_fingerprint

    results = FakeResults()
    profile = profile_validated_query(replace(plan(), has_unmodeled_expressions=True),
        describe_query=results.describe, fetch_query=results.fetch)
    assert dataset_profile_fingerprint(profile) != dataset_profile_fingerprint(
        profile.model_copy(update={"has_unmodeled_expressions": False}))
    with pytest.raises(ValueError, match="expression dependencies are unsupported"):
        build_advisor_request(profile)
    source = tmp_path / "profile.json"
    target = tmp_path / "spec.yaml"
    source.write_text(profile.model_dump_json())
    assert main(["infer-spec", str(source), "--output", str(target)]) != 0
    assert not target.exists()


def test_unknown_expression_marker_preserves_legacy_profile_fingerprint():
    import hashlib
    from test_data_agent.core.dataset import DatasetProfile
    from test_data_agent.io.artifacts import dataset_profile_fingerprint

    profile = DatasetProfile()
    old_payload = profile.model_dump(mode="json")
    old_payload.pop("has_unmodeled_expressions")
    old_payload.pop("local_category_fields")
    expected = hashlib.sha256(json.dumps(old_payload, sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    assert dataset_profile_fingerprint(profile) == expected


def test_query_profile_feeds_deterministic_synthetic_generation() -> None:
    results = FakeResults()
    profile = profile_validated_query(
        plan(),
        describe_query=results.describe,
        fetch_query=results.fetch,
    )
    spec = infer_dataset_spec(profile, count=8)
    assert profile.entities[0].field("amount").data_type == FieldType.FLOAT

    first = generate_dataset(spec, seed=73)
    second = generate_dataset(spec, seed=73)

    assert first == second
    assert validate_dataset(first, spec).valid is True
    assert "source-only" not in json.dumps(first, sort_keys=True)


def test_declared_query_decimal_keeps_shape_and_requires_reviewed_bounds() -> None:
    class ExactResults(FakeResults):
        def describe(self, query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
            columns = super().describe(query)
            return (*columns[:2], QueryResultColumn("amount", "numeric(12,2)", True))

    results = ExactResults()
    profile = profile_validated_query(
        plan(), describe_query=results.describe, fetch_query=results.fetch,
    )
    field = profile.entities[0].field("amount")
    assert field.data_type == FieldType.DECIMAL
    assert (field.decimal_precision, field.decimal_scale) == (12, 2)
    assert "min_value" not in field.distribution
    with pytest.raises(ValueError, match="decimal_range distribution"):
        infer_dataset_spec(profile, count=8)


def test_default_profile_does_not_query_or_store_category_literals() -> None:
    results = FakeResults()

    profile = profile_validated_query(
        plan(),
        describe_query=results.describe,
        fetch_query=results.fetch,
    )

    assert profile.entities[0].field("state").distribution == {}
    assert all("GROUP BY" not in query.sql for query in results.queries)


@pytest.mark.parametrize("adapter", [SqlQueryAdapter.POSTGRES, SqlQueryAdapter.TRINO])
@pytest.mark.parametrize("preserve_category", [False, True])
def test_query_profile_statement_count_scales_with_fields(
    adapter: SqlQueryAdapter,
    preserve_category: bool,
) -> None:
    results = FakeResults()
    profile_validated_query(
        plan(adapter=adapter),
        describe_query=results.describe,
        fetch_query=results.fetch,
        local_category_fields=(
            (LocalCategoryField(entity="warehouse.paid_orders", field="state"),)
            if preserve_category
            else ()
        ),
    )

    # One no-row schema request, one row count, and one aggregate per column;
    # only an explicit local category adds one.
    assert len(results.queries) == 5 + preserve_category
    assert sum("AS distinct_count" in query.sql for query in results.queries) == 3
    assert sum("AS max_abs_magnitude" in query.sql for query in results.queries) == 2
    assert sum("GROUP BY" in query.sql for query in results.queries) == preserve_category


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


def test_local_categories_fail_closed_without_authorized_lineage():
    backend = FakeResults()
    query_plan = replace(plan(), safe_local_category_output_fields=frozenset())
    with pytest.raises(SqlQueryProfileError, match="not allowed"):
        profile_validated_query(
            query_plan, describe_query=backend.describe, fetch_query=backend.fetch,
            local_category_fields=[LocalCategoryField(entity=query_plan.entity_name, field="state")],
        )
    assert not any("GROUP BY" in query.sql for query in backend.queries)


@pytest.mark.parametrize("adapter", [SqlQueryAdapter.POSTGRES, SqlQueryAdapter.TRINO])
def test_category_projection_bounds_values_in_same_statement(adapter):
    from dataclasses import replace
    from test_data_agent.sql_query_profiling import build_query_local_category_query

    query = build_query_local_category_query(replace(plan(), adapter=adapter), "state")
    assert 'CASE WHEN' in query.sql
    assert 'THEN "state" ELSE NULL END AS value' in query.sql
    assert 'GROUP BY "state"' in query.sql
    assert 'LIMIT 21' in query.sql
    if adapter == SqlQueryAdapter.POSTGRES:
        assert 'to_json("state")' in query.sql  # includes native CHAR padding
        assert '<= 1024' in query.sql
    else:
        assert 'to_utf8(CAST("state" AS varchar))' in query.sql
        assert '<= 256' in query.sql


@pytest.mark.parametrize("adapter", [SqlQueryAdapter.POSTGRES, SqlQueryAdapter.TRINO])
def test_category_null_rejection_sentinel_prevents_profile_publication(adapter):
    results = FakeResults()

    def fetch(query):
        if "GROUP BY" in query.sql:
            # Source changed after the summary; bounded projection fails closed.
            return [{"value": None, "count": 2}, {"value": "shipped", "count": 1}]
        return results.fetch(query)

    with pytest.raises(SqlQueryProfileError):
        profile_validated_query(plan(adapter=adapter), describe_query=results.describe,
            fetch_query=fetch, local_category_fields=(
                LocalCategoryField(entity="warehouse.paid_orders", field="state"),))
