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
    assert len(plan.fingerprint) == 64
    assert "source-only-literal" not in repr(plan)
    assert str(path) not in repr(request(path))


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
