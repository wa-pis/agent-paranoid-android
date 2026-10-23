"""Fictional aggregate batches preserve evidence while bounding repeated work."""
import re

import pytest
import sqlglot
from sqlglot import exp

from test_data_agent.sql_query_source import SqlQueryAdapter, ValidatedSqlQuery
from test_data_agent.sql_query_profiling import QueryResultColumn, SqlQueryProfileError, profile_validated_query


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("width", [1, 2, 8, 9, 48])
def test_query_batches_bound_width_and_preserve_numeric_evidence(adapter, width):
    names = tuple(f"measure_{i}" for i in range(width))
    table = ("public", "events") if adapter == SqlQueryAdapter.POSTGRES else ("lake", "safe", "events")
    plan = ValidatedSqlQuery(adapter, "fictional", "fictional.summary", table, names,
        "a" * 64, f"SELECT {', '.join(names)} FROM {'.'.join(table)}")
    seen = []
    metrics = {"row_count": 4, "non_null_count": 3, "distinct_count": 2,
        "has_negative": False, "has_positive": True, "max_abs_magnitude": -1,
        "zero_count": 1, "subunit_count": 2, "min_subunit_magnitude": -3}
    def describe(query):
        seen.append(query.sql)
        return tuple(QueryResultColumn(name, "decimal(12,2)") for name in names)
    def fetch(query):
        seen.append(query.sql)
        if "non_null_count" not in query.sql:
            return [{"row_count": 4}]
        aliases = re.findall(r'AS "(__apa_(\d+)_([a-z_]+))"', query.sql)
        if not aliases:
            return [metrics]
        assert 1 <= len({index for _, index, _ in aliases}) <= 8
        assert query.sql.count(plan.sql) == 1
        parsed = sqlglot.parse_one(query.sql, read=adapter.value)
        assert isinstance(parsed, exp.Select)
        assert isinstance(parsed.args["from_"].this, exp.Subquery)
        return [{alias: metrics[name] for alias, _, name in aliases}]
    profile = profile_validated_query(plan, describe_query=describe, fetch_query=fetch)
    assert len(seen) == 2 + (width + 7) // 8
    for field in profile.entities[0].fields:
        assert field.null_ratio == 0.25
        assert field.distribution["zero_ratio"] == 1 / 3
        assert field.distribution["subunit_ratio"] == 2 / 3
        assert field.distribution["max_abs_magnitude"] == -1
    assert "SELECT" not in profile.model_dump_json()


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_missing_batch_column_fails_without_partial_profile(adapter):
    plan = ValidatedSqlQuery(adapter, "fictional", "fictional.summary", ("public", "events"),
        ("first", "second"), "a" * 64, "SELECT first, second FROM public.events")
    def fetch(query):
        if "non_null_count" not in query.sql:
            return [{"row_count": 2}]
        return [{"__apa_0_row_count": 2, "__apa_0_non_null_count": 2, "__apa_0_distinct_count": 2}]
    with pytest.raises(SqlQueryProfileError):
        profile_validated_query(plan, describe_query=lambda query: (
            QueryResultColumn("first", "text"), QueryResultColumn("second", "text")), fetch_query=fetch)


@pytest.mark.parametrize("ceiling", [None, "statements", "scan", "columns"])
def test_batching_retains_separate_statement_scan_and_column_budgets(ceiling):
    from dataclasses import replace
    from test_data_agent.trino_sql_policy import consume_query_execution_work
    from test_data_agent.trino_work_budget import (
        DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget, QueryWorkBudgetExceeded,
        consume_profiled_column_work, with_query_work_budget,
    )
    names = tuple(f"measure_{i}" for i in range(9))
    plan = ValidatedSqlQuery(SqlQueryAdapter.TRINO, "fictional", "fictional.summary",
        ("lake", "safe", "events"), names, "a" * 64,
        f"SELECT {', '.join(names)} FROM lake.safe.events")
    limits = replace(DEFAULT_QUERY_WORK_LIMITS,
        statements=3 if ceiling == "statements" else 4,
        max_profiled_columns=8 if ceiling == "columns" else 9,
        max_cumulative_estimated_scan_bytes=300 if ceiling == "scan" else 400)
    budget = QueryWorkBudget(limits)
    executed = []
    metrics = {"row_count": 4, "non_null_count": 3, "distinct_count": 2,
        "has_negative": False, "has_positive": True, "max_abs_magnitude": -1,
        "zero_count": 1, "subunit_count": 2, "min_subunit_magnitude": -3}
    def charge(query):
        consume_query_execution_work(query.sql, estimated_scan_bytes_per_statement=100)
        executed.append(query.sql)
    def describe(query):
        charge(query)
        return tuple(QueryResultColumn(name, "decimal(12,2)") for name in names)
    def fetch(query):
        charge(query)
        if "non_null_count" not in query.sql:
            return [{"row_count": 4}]
        aliases = re.findall(r'AS "(__apa_(\d+)_([a-z_]+))"', query.sql)
        return [{alias: metrics[name] for alias, _, name in aliases}] if aliases else [metrics]
    def run():
        consume_profiled_column_work(len(names))
        return profile_validated_query(plan, describe_query=describe, fetch_query=fetch)
    operation = with_query_work_budget(run, limits, budget_provider=lambda: budget)
    if ceiling:
        with pytest.raises((QueryWorkBudgetExceeded, SqlQueryProfileError)):
            operation()
        assert len(executed) == (0 if ceiling == "columns" else 3)
    else:
        assert len(operation().entities[0].fields) == 9
        assert len(executed) == 4
        snapshot = budget.snapshot()
        assert snapshot.statements == 4
        assert snapshot.profiled_columns == 9
        assert snapshot.cumulative_estimated_scan_bytes == 400


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_batching_preserves_profile_fingerprint_against_single_column_reference(adapter, monkeypatch):
    import test_data_agent.sql_query_profiling as profiling
    from test_data_agent.core.fingerprints import model_fingerprint
    from tests.test_sql_query_profiling import FakeResults, plan

    batch_results = FakeResults()
    batched = profile_validated_query(plan(adapter=adapter), describe_query=batch_results.describe,
        fetch_query=batch_results.fetch)
    original = profiling._fetch_column_summaries
    monkeypatch.setattr(profiling, "_fetch_column_summaries",
        lambda query_plan, columns, fetch: [original(query_plan, [column], fetch)[0] for column in columns])
    single_results = FakeResults()
    reference = profile_validated_query(plan(adapter=adapter), describe_query=single_results.describe,
        fetch_query=single_results.fetch)
    assert batched.model_dump(mode="json") == reference.model_dump(mode="json")
    assert model_fingerprint(batched) == model_fingerprint(reference)
    assert len(batch_results.queries) == 3 and len(single_results.queries) == 5
