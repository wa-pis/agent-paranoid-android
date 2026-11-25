"""Query aliases preserve sensitivity without fetching source rows."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from tests.query_summary_fixtures import batch_aggregate_rows

from test_data_agent.core.privacy import LocalCategoryField
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.postgres_profiler import PostgresProfiler
from test_data_agent.sql_query_profiling import (
    QueryResultColumn,
    SqlQueryProfileError,
    TrustedProfileQuery,
    build_query_column_summary_query,
    profile_validated_query,
)
from test_data_agent.sql_query_source import (
    QUERY_SOURCE_POLICY_VERSION,
    QuerySourceColumn,
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    ValidatedSqlQuery,
    authorize_query_source,
    inspect_query_source,
)


def _plan(
    tmp_path: Path,
    adapter: SqlQueryAdapter,
    projection: str,
    columns: tuple[QuerySourceColumn, ...],
    *,
    predicate: str = "",
) -> ValidatedSqlQuery:
    table = "public.records" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.records"
    path = tmp_path / "query.sql"
    path.write_text(f"SELECT {projection} FROM {table}{predicate}", encoding="utf-8")
    request = SqlQueryProfileRequest(adapter, "synthetic", "records", path)
    return authorize_query_source(inspect_query_source(request), columns)


class _Aggregates:
    def __init__(self, columns: tuple[QueryResultColumn, ...]) -> None:
        self.columns = columns
        self.queries: list[TrustedProfileQuery] = []

    def describe(self, query: TrustedProfileQuery) -> tuple[QueryResultColumn, ...]:
        self.queries.append(query)
        assert "WHERE FALSE" in query.sql
        return self.columns

    def fetch(self, query: TrustedProfileQuery) -> list[dict[str, object]]:
        self.queries.append(query)
        if 'AS "__apa_0_' in query.sql:
            return batch_aggregate_rows(query.sql, [{
                "row_count": 100, "non_null_count": 100, "distinct_count": 1,
                "has_negative": False, "has_positive": True, "max_abs_magnitude": 2,
            } for _ in self.columns])
        if "GROUP BY" in query.sql:
            return [{"value": "category_1", "count": 100}]
        if "non_null_count" in query.sql:
            return [{
                "row_count": 100, "non_null_count": 100, "distinct_count": 1,
                "has_negative": False, "has_positive": True, "max_abs_magnitude": 2,
            }]
        return [{"row_count": 100}]


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("source,projection,output,data_type,sensitive", [
    ("customer_email", "customer_email AS payload", "payload", "varchar", True),
    ("full_name", "lower(full_name) AS status", "status", "varchar", True),
    ("card_number", "card_number + 1 AS quantity", "quantity", "bigint", True),
    ("ssn", "CAST(ssn AS bigint) AS metric", "metric", "bigint", True),
    ("email_count", "email_count AS quantity", "quantity", "bigint", True),
    ("amount", "amount AS phone_count", "phone_count", "bigint", True),
    ("discount", "discount AS result", "result", "bigint", False),
])
def test_projected_source_sensitivity_survives_aliases_and_expressions(
    tmp_path: Path,
    adapter: SqlQueryAdapter,
    source: str,
    projection: str,
    output: str,
    data_type: str,
    sensitive: bool,
) -> None:
    plan = _plan(tmp_path, adapter, projection, (QuerySourceColumn(source, data_type, False),))
    expected = frozenset((output,)) if sensitive else frozenset()
    assert plan.sensitive_output_fields == expected
    results = _Aggregates((QueryResultColumn(output, data_type, False),))

    profile = profile_validated_query(plan, describe_query=results.describe, fetch_query=results.fetch)
    field = profile.entities[0].field(output)

    assert field.sensitive is sensitive
    assert field.semantic_type is None
    assert field.data_type.value == ("string" if data_type == "varchar" else "integer")
    assert profile.source_policy_version == "1.2"
    assert len(results.queries) == 3
    assert not any("GROUP BY" in query.sql for query in results.queries)
    assert "SELECT " not in profile.model_dump_json()


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_wildcard_keeps_individual_source_sensitivity(tmp_path: Path, adapter: SqlQueryAdapter) -> None:
    columns = (
        QuerySourceColumn("ssn", "bigint", False),
        QuerySourceColumn("amount", "bigint", False),
        QuerySourceColumn("status", "varchar", False),
    )
    plan = _plan(tmp_path, adapter, "*", columns)
    results = _Aggregates(tuple(
        QueryResultColumn(column.name, column.data_type, column.nullable)
        for column in sorted(columns, key=lambda column: column.name)
    ))
    profile = profile_validated_query(plan, describe_query=results.describe, fetch_query=results.fetch)

    assert plan.sensitive_output_fields == frozenset(("ssn",))
    assert {field.name: field.sensitive for field in profile.entities[0].fields} == {
        "amount": False, "ssn": True, "status": False,
    }
    assert all("SELECT *" not in query.sql for query in results.queries)
    assert len(results.queries) == 3


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("source,projection", [
    ("username", "username AS status"),
    ("full_name", "lower(full_name) AS status"),
    ("customer_email", "customer_email AS status"),
    ("ssn", "CAST(ssn AS varchar) AS status"),
])
def test_sensitive_source_cannot_be_preserved_as_an_aliased_local_category(
    tmp_path: Path, adapter: SqlQueryAdapter, source: str, projection: str,
) -> None:
    plan = _plan(tmp_path, adapter, projection, (QuerySourceColumn(source, "varchar", False),))
    results = _Aggregates((QueryResultColumn("status", "varchar", False),))

    with pytest.raises(SqlQueryProfileError, match="local category field is not allowed"):
        profile_validated_query(
            plan, describe_query=results.describe, fetch_query=results.fetch,
            local_category_fields=(LocalCategoryField(entity=plan.entity_name, field="status"),),
        )

    assert len(results.queries) == 1
    assert not any("GROUP BY" in query.sql for query in results.queries)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_non_sensitive_alias_still_supports_explicit_local_categories(
    tmp_path: Path, adapter: SqlQueryAdapter,
) -> None:
    plan = _plan(tmp_path, adapter, "status AS state", (QuerySourceColumn("status", "varchar", False),))
    results = _Aggregates((QueryResultColumn("state", "varchar", False),))
    profile = profile_validated_query(
        plan, describe_query=results.describe, fetch_query=results.fetch,
        local_category_fields=(LocalCategoryField(entity=plan.entity_name, field="state"),),
    )

    assert not profile.entities[0].field("state").sensitive
    assert len(results.queries) == 4
    assert sum("GROUP BY" in query.sql for query in results.queries) == 1


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_sensitive_predicate_does_not_reclassify_an_independent_projection(
    tmp_path: Path, adapter: SqlQueryAdapter,
) -> None:
    plan = _plan(
        tmp_path, adapter, "amount AS metric",
        (QuerySourceColumn("amount", "bigint", False), QuerySourceColumn("customer_email", "varchar", True)),
        predicate=" WHERE customer_email IS NOT NULL",
    )
    results = _Aggregates((QueryResultColumn("metric", "bigint", False),))
    profile = profile_validated_query(plan, describe_query=results.describe, fetch_query=results.fetch)

    assert not plan.sensitive_output_fields
    assert not plan.safe_temporal_output_fields
    assert not profile.entities[0].field("metric").sensitive


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_sensitive_provenance_cannot_enable_temporal_bounds(tmp_path: Path, adapter: SqlQueryAdapter) -> None:
    plan = _plan(tmp_path, adapter, "birth_date AS observed", (QuerySourceColumn("birth_date", "date", False),))
    plan = replace(plan, safe_temporal_output_fields=frozenset(("observed",)))

    with pytest.raises(SqlQueryProfileError, match="non-sensitive field"):
        build_query_column_summary_query(plan, "observed", temporal_bounds=True)

    results = _Aggregates((QueryResultColumn("observed", "date", False),))
    profile = profile_validated_query(plan, describe_query=results.describe, fetch_query=results.fetch)
    assert profile.entities[0].field("observed").sensitive
    assert not any("min_temporal" in query.sql for query in results.queries)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_query_adapter_forwards_exact_non_null_counts(
    tmp_path: Path, adapter: SqlQueryAdapter, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import test_data_agent.sql_query_profiling as module

    plan = _plan(tmp_path, adapter, "status", (QuerySourceColumn("status", "varchar", False),))
    results = _Aggregates((QueryResultColumn("status", "varchar", False),))
    normalize = module.legacy_profile_to_dataset_profile
    captured: list[dict[str, Any]] = []

    def capture(profile: dict[str, Any], **kwargs: Any) -> Any:
        captured.extend(profile["columns"])
        return normalize(profile, **kwargs)

    monkeypatch.setattr(module, "legacy_profile_to_dataset_profile", capture)
    profile_validated_query(plan, describe_query=results.describe, fetch_query=results.fetch)
    assert captured[0]["non_null_count"] == 100
    assert captured[0]["null_count"] == 0
    assert len(results.queries) == 3


def test_postgres_forwards_exact_non_null_counts_without_extra_queries() -> None:
    config = PostgresConfig(
        source_id="synthetic", host="synthetic.invalid", port=5432, database="synthetic",
        user="synthetic", password_env=None, allowed_schemas=frozenset(("public",)),
        allowed_tables=frozenset(("public.records",)), allowed_columns=frozenset(("public.records.status",)),
    )
    queries = []

    def fetch(query: Any) -> list[dict[str, object]]:
        queries.append(query)
        return [{"row_count": 125_000, "non_null_count": 100_001, "distinct_count": 2}]

    column = PostgresProfiler(config, fetch)._profile_column(
        "public", "records", 125_000,
        {"column_name": "status", "data_type": "text", "is_nullable": True}, None,
    )
    assert column["non_null_count"] == 100_001
    assert column["null_count"] == 24_999
    assert len(queries) == 1


def test_query_policy_version_changes_old_fingerprints(tmp_path: Path) -> None:
    plan = _plan(
        tmp_path, SqlQueryAdapter.POSTGRES, "customer_email AS payload",
        (QuerySourceColumn("customer_email", "varchar", False),),
    )
    old_fingerprint = hashlib.sha256(f"1.1\npostgres\n{plan.sql}".encode()).hexdigest()
    assert QUERY_SOURCE_POLICY_VERSION == "1.2"
    assert plan.fingerprint != old_fingerprint
