"""Fictional SQL-query temporal aggregates, without database access."""

from datetime import date, datetime

import pytest

from test_data_agent.generation import generate_dataset, infer_dataset_spec
from test_data_agent.sql_query_profiling import (
    QueryResultColumn,
    SqlQueryProfileError,
    profile_validated_query,
)
from test_data_agent.sql_query_source import SqlQueryAdapter, ValidatedSqlQuery


def _plan(adapter: SqlQueryAdapter, name: str) -> ValidatedSqlQuery:
    return ValidatedSqlQuery(
        adapter=adapter, source_id="fixture", entity_name="fixture.events",
        table_parts=("public", "events"), output_fields=(name,),
        fingerprint="a" * 64,
        sql=f'SELECT "{name}" FROM "public"."events"',
    )


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("name,sql_type,lower,upper,kind", [
    ("event_day", "date", date(2031, 1, 2), date(2031, 1, 8), "date_range"),
    ("created_at", "timestamp with time zone",
     datetime.fromisoformat("2031-01-02T12:00:00+03:00"),
     datetime.fromisoformat("2031-01-08T12:00:00+03:00"), "datetime_range"),
])
def test_query_temporal_bounds_reach_generation(adapter, name, sql_type, lower, upper, kind):
    queries = []

    def describe(query):
        queries.append(query.sql)
        return (QueryResultColumn(name, sql_type, False),)

    def fetch(query):
        queries.append(query.sql)
        if "non_null_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2,
                     "min_temporal": lower, "max_temporal": upper}]
        return [{"row_count": 2}]

    profile = profile_validated_query(_plan(adapter, name), describe_query=describe, fetch_query=fetch)
    spec = infer_dataset_spec(profile, count=10)
    field = spec.entities[0].fields[0]
    assert field.distribution["kind"] == kind
    parser = datetime.fromisoformat if isinstance(lower, datetime) else date.fromisoformat
    rows = generate_dataset(spec, seed=7)["fixture.events"]
    assert all(lower <= parser(row[name]) <= upper for row in rows)
    assert len(queries) == 3
    assert "AS min_temporal" in queries[-1]
    assert "AS max_temporal" in queries[-1]


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_sensitive_temporal_bounds_not_requested(adapter):
    queries = []

    def fetch(query):
        queries.append(query.sql)
        if "non_null_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2}]
        return [{"row_count": 2}]

    profile = profile_validated_query(
        _plan(adapter, "birth_date"),
        describe_query=lambda query: (QueryResultColumn("birth_date", "date"),),
        fetch_query=fetch,
    )
    assert profile.entities[0].field("birth_date").distribution == {}
    assert all("min_temporal" not in query for query in queries)


@pytest.mark.parametrize("lower,upper", [
    (None, date(2031, 1, 8)),
    ("private-date", "private-date"),
    (date(2031, 1, 8), date(2031, 1, 2)),
    (datetime(2031, 1, 2), datetime(2031, 1, 8)),
])
def test_malformed_query_bounds_fail_without_values(lower, upper):
    def fetch(query):
        if "non_null_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2,
                     "min_temporal": lower, "max_temporal": upper}]
        return [{"row_count": 2}]

    with pytest.raises(SqlQueryProfileError) as caught:
        profile_validated_query(
            _plan(SqlQueryAdapter.POSTGRES, "event_day"),
            describe_query=lambda query: (QueryResultColumn("event_day", "date"),),
            fetch_query=fetch,
        )
    assert "private-date" not in str(caught.value)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_all_null_query_dates_have_no_observed_bounds(adapter):
    def fetch(query):
        if "non_null_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 0, "distinct_count": 0,
                     "min_temporal": None, "max_temporal": None}]
        return [{"row_count": 2}]

    profile = profile_validated_query(
        _plan(adapter, "event_day"),
        describe_query=lambda query: (QueryResultColumn("event_day", "date"),),
        fetch_query=fetch,
    )
    assert profile.entities[0].field("event_day").distribution == {}


def test_query_timestamp_timezone_mismatch_fails_closed():
    def fetch(query):
        if "non_null_count" in query.sql:
            return [{"row_count": 2, "non_null_count": 2, "distinct_count": 2,
                     "min_temporal": datetime(2031, 1, 2),
                     "max_temporal": datetime.fromisoformat("2031-01-08T12:00:00+03:00")}]
        return [{"row_count": 2}]

    with pytest.raises(SqlQueryProfileError, match="timezone metadata"):
        profile_validated_query(
            _plan(SqlQueryAdapter.TRINO, "created_at"),
            describe_query=lambda query: (QueryResultColumn("created_at", "timestamp with time zone"),),
            fetch_query=fetch,
        )
