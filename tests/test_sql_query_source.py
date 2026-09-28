from __future__ import annotations

from pathlib import Path

import pytest

from test_data_agent.sql_query_source import (
    QuerySourceColumn,
    SqlQueryAdapter,
    SqlQueryProfileLimits,
    SqlQueryProfileRequest,
    SqlQuerySourceError,
    authorize_query_source,
    inspect_query_source,
)


def request(
    path: Path,
    *,
    adapter: SqlQueryAdapter = SqlQueryAdapter.POSTGRES,
    limits: SqlQueryProfileLimits | None = None,
) -> SqlQueryProfileRequest:
    return SqlQueryProfileRequest(
        adapter=adapter,
        source_id="warehouse",
        entity="paid_orders",
        query_file=path,
        limits=limits or SqlQueryProfileLimits(),
    )


def write_query(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "query.sql"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("sql,hint", [
    ("WITH private_marker AS (SELECT id FROM public.private_table) "
     "SELECT id FROM private_marker", "CTE/WITH is not supported"),
    ("SELECT a.id FROM public.private_table a "
     "JOIN public.other_table b ON a.id = b.id", "JOIN is not supported"),
])
def test_structural_rejections_have_safe_recovery_hint(tmp_path, adapter, sql, hint):
    path = write_query(tmp_path, sql)
    with pytest.raises(SqlQuerySourceError) as caught:
        inspect_query_source(request(path, adapter=adapter))
    assert hint in str(caught.value)
    assert "private" not in str(caught.value)
    assert "other_table" not in str(caught.value)


def columns() -> tuple[QuerySourceColumn, ...]:
    return (
        QuerySourceColumn("amount", "numeric", False),
        QuerySourceColumn("order_id", "bigint", False),
        QuerySourceColumn("status", "text", True),
    )


def test_explicit_query_is_canonicalized_and_fingerprinted(tmp_path: Path) -> None:
    path = write_query(
        tmp_path,
        "SELECT o.order_id, lower(o.status) AS state, o.amount * 2 AS doubled "
        "FROM public.orders AS o WHERE o.status = 'source-only-literal'",
    )

    plan = authorize_query_source(inspect_query_source(request(path)), columns())

    assert plan.table_parts == ("public", "orders")
    assert plan.entity_name == "warehouse.paid_orders"
    assert plan.output_fields == ("order_id", "state", "doubled")
    assert plan.has_unmodeled_expressions
    assert len(plan.fingerprint) == 64
    assert "source-only-literal" not in repr(plan)
    assert str(path) not in repr(request(path))


@pytest.mark.parametrize("projection,expected", [("amount AS renamed", False),
    ("amount / 10.0 AS scaled", True), ("ROUND(-amount, 2) AS rounded", True)])
@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_projection_dependency_capability(tmp_path, projection, expected, adapter):
    table = "public.orders" if adapter == SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    path = write_query(tmp_path, f"SELECT {projection} FROM {table}")
    query = authorize_query_source(inspect_query_source(request(path, adapter=adapter)), columns())
    assert query.has_unmodeled_expressions is expected


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize(
    "condition",
    [
        "status = 'pending' AND amount > 0",
        "status = 'pending' OR status = 'settled'",
        "(status IN ('pending', 'settled') AND amount BETWEEN 1 AND 9) "
        "OR status IS NULL",
        "NOT (status IS NULL OR amount < 0)",
    ],
)
def test_allowed_boolean_predicates_are_not_classified_as_functions(
    tmp_path: Path, adapter: SqlQueryAdapter, condition: str
) -> None:
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    path = write_query(
        tmp_path,
        f"SELECT order_id FROM {table} WHERE {condition}",
    )

    plan = authorize_query_source(inspect_query_source(request(path, adapter=adapter)), columns())

    assert plan.output_fields == ("order_id",)
    assert " WHERE " in plan.sql


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
def test_boolean_predicate_does_not_allow_unknown_functions(
    tmp_path: Path, adapter: SqlQueryAdapter
) -> None:
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    path = write_query(
        tmp_path,
        f"SELECT order_id FROM {table} WHERE status = 'pending' AND random() > 0",
    )

    with pytest.raises(SqlQuerySourceError) as caught:
        inspect_query_source(request(path, adapter=adapter))

    assert "pending" not in str(caught.value)


def test_wildcard_expands_to_sorted_explicit_columns(tmp_path: Path) -> None:
    path = write_query(tmp_path, "SELECT o.* FROM public.orders AS o")

    plan = authorize_query_source(inspect_query_source(request(path)), columns())

    assert plan.output_fields == ("amount", "order_id", "status")
    assert "*" not in plan.sql


def test_cast_is_allowed_and_wrong_wildcard_alias_is_rejected(
    tmp_path: Path,
) -> None:
    cast_path = write_query(
        tmp_path,
        "SELECT CAST(o.amount AS numeric) AS amount "
        "FROM public.orders AS o",
    )
    plan = authorize_query_source(
        inspect_query_source(request(cast_path)),
        columns(),
    )
    assert plan.output_fields == ("amount",)

    wildcard_path = write_query(
        tmp_path,
        "SELECT wrong.* FROM public.orders AS o",
    )
    with pytest.raises(SqlQuerySourceError, match="qualification"):
        authorize_query_source(
            inspect_query_source(request(wildcard_path)),
            columns(),
        )


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM public.orders",
        "SELECT order_id FROM public.orders; SELECT order_id FROM public.orders",
        "WITH source AS (SELECT order_id FROM public.orders) SELECT order_id FROM source",
        "SELECT o.order_id FROM public.orders o JOIN public.customers c ON true",
        "SELECT (SELECT max(order_id) FROM public.orders) AS value FROM public.orders",
        "SELECT row_number() OVER () AS value FROM public.orders",
        "SELECT random() AS value FROM public.orders",
        "SELECT order_id FROM public.orders -- directive",
        "SELECT order_id FROM orders",
    ],
)
def test_forbidden_queries_fail_without_echoing_sql(
    tmp_path: Path,
    query: str,
) -> None:
    path = write_query(tmp_path, query)

    with pytest.raises(SqlQuerySourceError) as exc_info:
        inspect_query_source(request(path))

    assert query not in str(exc_info.value)


def test_trino_requires_catalog_schema_and_table(tmp_path: Path) -> None:
    path = write_query(tmp_path, "SELECT n.name FROM tpch.tiny.nation AS n")
    draft = inspect_query_source(
        request(path, adapter=SqlQueryAdapter.TRINO)
    )

    assert draft.table_parts == ("tpch", "tiny", "nation")


def test_unauthorized_column_is_rejected_without_name(tmp_path: Path) -> None:
    secret_name = "private_token"
    path = write_query(
        tmp_path,
        f"SELECT {secret_name} FROM public.orders",
    )

    with pytest.raises(SqlQuerySourceError) as exc_info:
        authorize_query_source(inspect_query_source(request(path)), columns())

    assert secret_name not in str(exc_info.value)


def test_duplicate_output_names_are_rejected(tmp_path: Path) -> None:
    path = write_query(
        tmp_path,
        "SELECT order_id, amount AS order_id FROM public.orders",
    )

    with pytest.raises(SqlQuerySourceError, match="must be unique"):
        authorize_query_source(inspect_query_source(request(path)), columns())


def test_expression_requires_explicit_alias(tmp_path: Path) -> None:
    path = write_query(tmp_path, "SELECT amount * 2 FROM public.orders")

    with pytest.raises(SqlQuerySourceError, match="explicit aliases"):
        authorize_query_source(inspect_query_source(request(path)), columns())


def test_file_byte_and_ast_budgets_fail_closed(tmp_path: Path) -> None:
    path = write_query(tmp_path, "SELECT order_id FROM public.orders")

    with pytest.raises(SqlQuerySourceError, match="byte budget"):
        inspect_query_source(
            request(path, limits=SqlQueryProfileLimits(max_query_bytes=8))
        )
    with pytest.raises(SqlQuerySourceError, match="AST node budget"):
        inspect_query_source(
            request(path, limits=SqlQueryProfileLimits(max_ast_nodes=2))
        )
    projected_path = write_query(
        tmp_path,
        "SELECT order_id, status FROM public.orders",
    )
    with pytest.raises(SqlQuerySourceError, match="projected-column budget"):
        inspect_query_source(
            request(
                projected_path,
                limits=SqlQueryProfileLimits(max_projected_columns=1),
            )
        )


def test_non_utf8_and_empty_files_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "query.sql"
    path.write_bytes(b"\xff")
    with pytest.raises(SqlQuerySourceError, match="UTF-8"):
        inspect_query_source(request(path))

    path.write_text("   ", encoding="utf-8")
    with pytest.raises(SqlQuerySourceError, match="empty"):
        inspect_query_source(request(path))


def test_query_limits_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SQL_QUERY_MAX_BYTES", "4096")
    monkeypatch.setenv("SQL_QUERY_MAX_AST_NODES", "120")
    monkeypatch.setenv("SQL_QUERY_MAX_AST_DEPTH", "16")
    monkeypatch.setenv("SQL_QUERY_MAX_PROJECTED_COLUMNS", "20")

    assert SqlQueryProfileLimits.from_env() == SqlQueryProfileLimits(
        max_query_bytes=4096,
        max_ast_nodes=120,
        max_ast_depth=16,
        max_projected_columns=20,
    )


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("projection", ["SUM(amount)", "COUNT(*)", "COUNT(amount)",
    "COUNT(1)", "MIN(amount)", "MAX(amount)", "AVG(amount)", "SUM(amount * 2)"])
@pytest.mark.parametrize("grouped", [False, True])
def test_allowed_aggregate_sources(tmp_path, adapter, projection, grouped):
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    sql = f"SELECT {'status, ' if grouped else ''}{projection} AS measured FROM {table}"
    if grouped:
        sql += " WHERE amount > 0 GROUP BY status"
    plan = authorize_query_source(inspect_query_source(request(write_query(tmp_path, sql), adapter=adapter)), columns())
    assert plan.output_fields == (("status", "measured") if grouped else ("measured",))
    assert plan.has_unmodeled_expressions
    assert "GROUP BY" in plan.sql if grouped else "GROUP BY" not in plan.sql


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("body", [
    "SUM(SUM(amount)) AS measured FROM {table}",
    "SUM(amount) + 1 AS measured FROM {table}",
    "COUNT(amount, status) AS measured FROM {table}",
    "SUM(*) AS measured FROM {table}",
    "COUNT(o.*) AS measured FROM {table} o",
    "status, SUM(amount) AS measured FROM {table}",
    "SUM(amount) AS measured FROM {table} WHERE COUNT(*) > 1",
    "status, SUM(amount) AS measured FROM {table} GROUP BY 1",
    "status, SUM(amount) AS measured FROM {table} GROUP BY LOWER(status)",
    "status, SUM(amount) AS measured FROM {table} GROUP BY status HAVING COUNT(*) > 1",
    "SUM(amount) OVER () AS measured FROM {table}",
    "COUNT(DISTINCT status) AS measured FROM {table}",
    "status, SUM(amount) AS measured FROM {table} GROUP BY ROLLUP(status)",
    "STRING_AGG(status, ',') AS measured FROM {table}",
    "MAX(private_token) AS harmless FROM {table}",
    "private_token AS harmless, COUNT(*) AS measured FROM {table} GROUP BY private_token",
])
def test_aggregate_expansion_keeps_rejection_boundary(tmp_path, adapter, body):
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    sql = "SELECT " + body.format(table=table)
    with pytest.raises(SqlQuerySourceError) as caught:
        authorize_query_source(inspect_query_source(request(write_query(tmp_path, sql), adapter=adapter)),
            columns() + (QuerySourceColumn("private_token", "text", True),))
    assert "private_token" not in str(caught.value)
    assert sql not in str(caught.value)


@pytest.mark.parametrize("adapter", list(SqlQueryAdapter))
@pytest.mark.parametrize("sql", ["SELECT SUM(unlisted) AS measured FROM {table}",
    "SELECT COUNT(*) AS measured FROM {table} GROUP BY unlisted"])
def test_aggregate_columns_still_need_authorization(tmp_path, adapter, sql):
    table = "public.orders" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.orders"
    with pytest.raises(SqlQuerySourceError, match="unauthorized column"):
        authorize_query_source(inspect_query_source(request(
            write_query(tmp_path, sql.format(table=table)), adapter=adapter)), columns())


def test_aggregate_ast_budget_is_not_relaxed(tmp_path):
    path = write_query(tmp_path, "SELECT status, COUNT(*) AS measured FROM public.orders GROUP BY status")
    with pytest.raises(SqlQuerySourceError, match="AST node budget"):
        inspect_query_source(request(path, limits=SqlQueryProfileLimits(max_ast_nodes=3)))
