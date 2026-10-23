"""Fictional category limits must reject before unnecessary source work."""
import pytest

from test_data_agent.core.privacy import LocalCategoryField, validate_local_category_values
from test_data_agent.sql_query_source import SqlQueryAdapter, ValidatedSqlQuery
from test_data_agent.sql_query_profiling import QueryResultColumn, SqlQueryProfileError, profile_validated_query


def test_category_cardinality_rejection_does_not_exhaust_an_iterable():
    consumed = []
    def values():
        for index in range(100):
            consumed.append(index)
            if index > 20:
                pytest.fail("category validator read beyond its overflow sentinel")
            yield f"state_{index}"
    with pytest.raises(ValueError, match="cardinality exceeds"):
        validate_local_category_values(field_name="status", semantic_type=None,
            sensitive=False, values=values())
    assert len(consumed) == 21


@pytest.mark.parametrize("limit", [True, 1.5, "20"])
@pytest.mark.parametrize("option", ["max_categories", "max_value_length"])
def test_category_limits_are_positive_integers_before_iteration(limit, option):
    def values():
        pytest.fail("invalid limits inspected source values")
        yield "state"
    with pytest.raises(ValueError, match="positive"):
        validate_local_category_values(field_name="status", semantic_type=None,
            sensitive=False, values=values(), **{option: limit})


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("category", [
    LocalCategoryField(entity="fictional.summary", field="missing"),
    LocalCategoryField(entity="other.summary", field="status"),
])
def test_query_category_scope_rejects_before_row_count(adapter, category):
    plan = ValidatedSqlQuery(adapter, "fictional", "fictional.summary", ("public", "orders"),
        ("status",), "a" * 64, "SELECT status FROM public.orders",
        safe_local_category_output_fields=frozenset({"status"}))
    def fetch(query):
        pytest.fail("invalid category fetched a source aggregate")
    with pytest.raises(SqlQueryProfileError):
        profile_validated_query(plan,
            describe_query=lambda query: (QueryResultColumn("status", "varchar", True),),
            fetch_query=fetch, local_category_fields=[category])


@pytest.mark.parametrize("limit", [True, 1.5, "20"])
def test_query_category_builder_rejects_untyped_limits(limit):
    from test_data_agent.sql_query_profiling import build_query_local_category_query
    plan = ValidatedSqlQuery(SqlQueryAdapter.POSTGRES, "fictional", "fictional.summary",
        ("public", "orders"), ("status",), "a" * 64, "SELECT status FROM public.orders",
        safe_local_category_output_fields=frozenset({"status"}))
    with pytest.raises(SqlQueryProfileError, match="budget is invalid"):
        build_query_local_category_query(plan, "status", max_categories=limit)


@pytest.mark.parametrize("limit", [True, 1.5, "20"])
def test_postgres_category_builder_rejects_untyped_limits(limit):
    from test_data_agent.postgres_config import PostgresConfig
    from test_data_agent.postgres_query_builders import PostgresScopeError, build_local_category_candidates_query
    config = PostgresConfig(source_id="fictional", host="fictional.test", port=5432,
        database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
        allowed_tables=frozenset({"public.orders"}), allowed_columns=frozenset({"public.orders.status"}))
    with pytest.raises(PostgresScopeError, match="positive"):
        build_local_category_candidates_query(config,
            LocalCategoryField(entity="fictional.public.orders", field="status"), max_categories=limit)


def test_sensitive_field_rejects_before_category_iteration():
    class Source:
        def __iter__(self):
            pytest.fail("sensitive category field accessed source values")
    with pytest.raises(ValueError, match="sensitive"):
        validate_local_category_values(field_name="phone", semantic_type=None,
            sensitive=False, values=Source())


def test_csv_cardinality_recovery_omits_raw_preservation_without_raising_limit(tmp_path, capsys):
    from test_data_agent.cli import main
    path = tmp_path / "events.csv"
    source_values = [f"state_{index:02d}" for index in range(21)]
    path.write_text("status\n" + "\n".join(source_values) + "\n")
    output = tmp_path / "profile.json"
    assert main(["--json", "profile-csv", str(path), "--output", str(output),
        "--local-category", "events.status"]) != 0
    failed = capsys.readouterr()
    assert not output.exists()
    assert all(value not in failed.out + failed.err for value in source_values)
    assert main(["profile-csv", str(path), "--output", str(output)]) == 0
    assert all(value not in output.read_text() for value in source_values)
