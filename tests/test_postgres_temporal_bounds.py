"""Fictional PostgreSQL aggregate-to-generation date bounds."""

from datetime import date, datetime

import pytest

from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.postgres_profiler import PostgresProfiler, PostgresProfileError
from test_data_agent.postgres_query_builders import build_column_summary_query, PostgresScopeError


@pytest.mark.parametrize("sql_type,low,high,kind", [
    ("date", date(2031, 1, 2), date(2031, 1, 8), "date_range"),
    ("timestamp with time zone", datetime.fromisoformat("2031-01-02T12:00:00+03:00"),
     datetime.fromisoformat("2031-01-08T12:00:00+03:00"), "datetime_range"),
])
def test_temporal_aggregates_reach_real_generation(sql_type, low, high, kind):
    config = PostgresConfig(
        source_id="test", host="db.example.test", port=5432, database="test",
        user="reader", password_env=None, allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.events"}),
        allowed_columns=frozenset({"public.events.created_at"}),
    )
    queries = []

    def fetch(query):
        queries.append(query.sql)
        if "c.relkind IN" in query.sql and "table_schema" in query.sql:
            return [{"table_schema": "public", "table_name": "events"}]
        if "pg_catalog.format_type" in query.sql:
            return [{"column_name": "created_at", "data_type": sql_type,
                     "is_nullable": False, "ordinal_position": 1}]
        if "AS distinct_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2,
                     "min_temporal": low, "max_temporal": high}]
        if query.sql.startswith("SELECT count(*) AS row_count FROM"):
            return [{"row_count": 2}]
        if "con.contype" in query.sql:
            return []
        raise AssertionError("unexpected query")

    profile = PostgresProfiler(config, fetch).profile()
    spec = infer_dataset_spec(profile, count=10)
    assert spec.entities[0].fields[0].distribution["kind"] == kind
    rows = generate_dataset(spec, seed=7)["test.public.events"]
    parse = datetime.fromisoformat if isinstance(low, datetime) else date.fromisoformat
    assert all(low <= parse(row["created_at"]) <= high for row in rows)
    aggregate_queries = [sql for sql in queries if "AS distinct_count" in sql]
    assert len(aggregate_queries) == 1
    assert "AS min_temporal" in aggregate_queries[0]
    assert "AS max_temporal" in aggregate_queries[0]


@pytest.mark.parametrize("low,high", [
    (None, date(2031, 1, 2)), ("private-date", "private-date"),
    (date(2031, 1, 8), date(2031, 1, 2)),
    (datetime(2031, 1, 2), datetime(2031, 1, 8)),
])
def test_malformed_date_aggregates_fail_without_values(low, high):
    config = temporal_config("created_at")
    profiler = PostgresProfiler(config, lambda query: [{
        "row_count": 2, "non_null_count": 2, "distinct_count": 2,
        "min_temporal": low, "max_temporal": high,
    }])
    with pytest.raises(PostgresProfileError) as caught:
        profiler._profile_column("public", "events", 2, {
            "column_name": "created_at", "data_type": "date", "is_nullable": False,
        }, None)
    assert "private-date" not in str(caught.value)


def temporal_config(field):
    return PostgresConfig(
        source_id="test", host="db.example.test", port=5432, database="test",
        user="reader", password_env=None, allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.events"}),
        allowed_columns=frozenset({f"public.events.{field}"}),
    )


def test_sensitive_date_bounds_not_requested_or_retained():
    config = temporal_config("birth_date")
    queries = []

    def fetch(query):
        queries.append(query.sql)
        return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2,
                 "min_temporal": date(2031, 1, 2), "max_temporal": date(2031, 1, 8)}]

    column = PostgresProfiler(config, fetch)._profile_column("public", "events", 2, {
        "column_name": "birth_date", "data_type": "date", "is_nullable": False,
    }, None)
    assert "min_date" not in column and "max_date" not in column
    assert "min_temporal" not in queries[0]
    with pytest.raises(PostgresScopeError):
        build_column_summary_query(config, "public", "events", "birth_date", temporal_bounds=True)


def test_all_null_dates_have_no_claimed_bounds():
    profiler = PostgresProfiler(temporal_config("created_at"), lambda query: [{
        "row_count": 2, "non_null_count": 0, "distinct_count": 0,
        "min_temporal": None, "max_temporal": None,
    }])
    column = profiler._profile_column("public", "events", 2, {
        "column_name": "created_at", "data_type": "date", "is_nullable": True,
    }, None)
    assert "min_date" not in column and "max_date" not in column


def test_incompatible_timezone_metadata_fails_closed():
    profiler = PostgresProfiler(temporal_config("created_at"), lambda query: [{
        "row_count": 2, "non_null_count": 2, "distinct_count": 2,
        "min_temporal": datetime(2031, 1, 2),
        "max_temporal": datetime.fromisoformat("2031-01-08T12:00:00+03:00"),
    }])
    with pytest.raises(PostgresProfileError, match="inconsistent timezone"):
        profiler._profile_column("public", "events", 2, {
            "column_name": "created_at", "data_type": "timestamp with time zone",
            "is_nullable": False,
        }, None)
