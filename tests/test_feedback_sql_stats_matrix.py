"""Source-free numeric evidence and aggregate cost across narrow/wide schemas."""
import pytest

from test_data_agent.sql_query_source import SqlQueryAdapter, ValidatedSqlQuery
from test_data_agent.sql_query_profiling import QueryResultColumn, profile_validated_query
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_masking import TrinoMasker
from test_data_agent.trino_profiling import TrinoProfiler


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("data_type", ["bigint", "double", "decimal(12,2)"])
@pytest.mark.parametrize("width", [1, 48])
@pytest.mark.parametrize("all_zero", [False, True])
def test_query_numeric_evidence_and_aggregate_count(adapter, data_type, width, all_zero):
    names = tuple(f"measure_{index}" for index in range(width))
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    plan = ValidatedSqlQuery(adapter, "fictional", "fictional.summary", tuple(table.split(".")),
        names, "a" * 64, f"SELECT {', '.join(names)} FROM {table}")
    seen = []
    def describe(query):
        seen.append(query.sql)
        assert query.sql.endswith("WHERE FALSE")
        return tuple(QueryResultColumn(name, data_type, True) for name in names)
    def fetch(query):
        seen.append(query.sql)
        assert "SELECT *" not in query.sql.upper()
        if "non_null_count" not in query.sql:
            return [{"row_count": 4}]
        return [{"row_count": 4, "non_null_count": 3, "distinct_count": 1 if all_zero else 2,
            "has_negative": False, "has_positive": not all_zero,
            "max_abs_magnitude": None if all_zero else -1,
            "zero_count": 3 if all_zero else 1, "subunit_count": 0 if all_zero else 2,
            "min_subunit_magnitude": None if all_zero else -3}]
    profile = profile_validated_query(plan, describe_query=describe, fetch_query=fetch)
    assert len(seen) == width + 2  # no-row schema, row count, one summary per field
    assert sum("max_abs_magnitude" in query for query in seen) == width
    for field in profile.entities[0].fields:
        assert field.null_ratio == 0.25
        assert field.distribution["kind"] == "numeric_shape"
        assert field.distribution["max_abs_magnitude"] == (0 if all_zero else -1)
        assert field.distribution["zero_ratio"] == (1.0 if all_zero else 1 / 3)
        assert field.distribution["subunit_ratio"] == (0.0 if all_zero else 2 / 3)
    assert "SELECT" not in profile.model_dump_json()


@pytest.mark.parametrize("width", [1, 48])
def test_trino_decimal_table_profile_cost_and_shape_remain_aggregate_only(width):
    names = [f"amount_{index}" for index in range(width)]
    seen = []
    def fetch(query):
        seen.append(query.sql)
        assert "SELECT *" not in query.sql.upper()
        if "information_schema.columns" in query.sql:
            return [{"column_name": name, "data_type": "decimal(12,2)", "is_nullable": "YES"}
                    for name in names]
        if "max_abs_magnitude" in query.sql:
            return [{"row_count": 4, "non_null_count": 3, "approx_distinct_count": 2,
                "has_negative": False, "has_positive": True, "max_abs_magnitude": -1,
                "zero_count": 1, "subunit_count": 2, "min_subunit_magnitude": -3}]
        return [{"row_count": 4}]
    config = TrinoConfig(host="fictional.test", port=8443, user="fictional", http_scheme="https",
        allowed_catalogs=frozenset({"lake"}), allowed_schemas=frozenset({"safe"}))
    masker = TrinoMasker(config, fetch, lambda *args: pytest.fail("raw SQL port used"))
    profile = TrinoProfiler(config, fetch).profile_table_safe(
        "lake", "safe", "orders", 20, masker.profile_column_safe)
    assert len(seen) == width + 2  # metadata, row count, one shape summary per field
    assert len(profile["columns"]) == width
    for column in profile["columns"]:
        assert column["numeric_shape"]["max_abs_magnitude"] == -1
        assert column["numeric_shape"]["subunit_ratio"] == 2 / 3
        assert column["numeric_shape"]["min_subunit_magnitude"] == -3
        assert "min_value" not in column and "max_value" not in column
