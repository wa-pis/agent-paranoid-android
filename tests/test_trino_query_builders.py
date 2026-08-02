from __future__ import annotations

import ast
from dataclasses import replace

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent.trino_query_builders import (
    TrinoQuery,
    build_aggregate_mapping_profile_query,
    build_column_cardinality_query,
    build_column_profile_query,
    build_conditional_allowed_values_profile_query,
    build_conditional_required_profile_query,
    build_describe_table_query,
    build_foreign_key_profile_query,
    build_formula_rule_profile_query,
    build_list_catalogs_query,
    build_list_schemas_query,
    build_list_tables_query,
    build_table_profile_query,
    build_temporal_ordering_profile_query,
    build_top_values_query,
)
from test_data_agent.trino_sql_policy import SqlSafetyError
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudgetExceeded,
    with_query_work_budget,
)


def test_metadata_builders_return_parameterized_queries() -> None:
    assert build_list_catalogs_query() == TrinoQuery("SHOW CATALOGS")
    assert build_list_schemas_query("analytics") == TrinoQuery(
        'SHOW SCHEMAS FROM "analytics"'
    )
    assert build_list_tables_query("analytics", "safe_schema") == TrinoQuery(
        'SHOW TABLES FROM "analytics"."safe_schema"'
    )

    describe = build_describe_table_query(
        "analytics", "safe_schema", "synthetic_orders"
    )

    assert describe.parameters == ("analytics", "safe_schema", "synthetic_orders")
    assert describe.sql.endswith("ORDER BY ordinal_position")
    assert "synthetic_orders" not in describe.sql


def test_profile_builders_are_bounded_aggregate_queries() -> None:
    queries = [
        build_table_profile_query("analytics", "safe_schema", "synthetic_orders"),
        build_column_cardinality_query(
            "analytics", "safe_schema", "synthetic_orders", "amount"
        ),
        build_column_profile_query(
            "analytics", "safe_schema", "synthetic_orders", "amount", "double"
        ),
        build_top_values_query(
            "analytics", "safe_schema", "synthetic_orders", "status", 20
        ),
        build_foreign_key_profile_query(
            "analytics",
            "safe_schema",
            "synthetic_customers",
            "customer_id",
            "synthetic_orders",
            "customer_id",
        ),
        build_temporal_ordering_profile_query(
            "analytics",
            "safe_schema",
            "synthetic_orders",
            "created_at",
            "fulfilled_at",
            allow_equal=True,
        ),
        build_formula_rule_profile_query(
            "analytics",
            "safe_schema",
            "synthetic_orders",
            "total",
            "subtotal + tax",
            0.01,
        ),
        build_aggregate_mapping_profile_query(
            "analytics",
            "safe_schema",
            "synthetic_customers",
            "customer_id",
            "lifetime_value",
            "synthetic_orders",
            "customer_id",
            "amount",
            "sum",
            0.01,
        ),
    ]

    assert all(isinstance(query, TrinoQuery) for query in queries)
    assert all("SELECT *" not in query.sql.upper() for query in queries)
    assert queries[3].sql.endswith("LIMIT 20")


def test_conditional_builders_keep_values_out_of_sql() -> None:
    required = build_conditional_required_profile_query(
        "analytics",
        "safe_schema",
        "synthetic_orders",
        "status",
        "trigger-value",
        "fulfilled_at",
    )
    allowed = build_conditional_allowed_values_profile_query(
        "analytics",
        "safe_schema",
        "synthetic_orders",
        "kind",
        "subscription",
        "status",
        ["active", "paused"],
    )

    assert required.parameters == ("trigger-value", "trigger-value", "trigger-value")
    assert "trigger-value" not in required.sql
    assert allowed.parameters == (
        "subscription",
        "subscription",
        "active",
        "paused",
        "subscription",
        "active",
        "paused",
    )
    assert all(value not in allowed.sql for value in allowed.parameters)


def test_builders_reject_identifier_and_formula_injection() -> None:
    with pytest.raises(ValueError):
        build_list_schemas_query("analytics; DROP TABLE users")
    with pytest.raises(SqlSafetyError):
        build_formula_rule_profile_query(
            "analytics",
            "safe_schema",
            "synthetic_orders",
            "total",
            "__import__('os').system('id')",
            0.01,
        )


def test_formula_budget_fails_before_python_ast_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed: list[str] = []

    def parse_expression(expression: str, *, mode: str) -> None:
        parsed.append(f"{mode}:{expression}")

    monkeypatch.setattr(
        "test_data_agent.trino_query_builders.ast.parse",
        parse_expression,
    )
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, sql_formula_chars=5)
    wrapped = with_query_work_budget(
        build_formula_rule_profile_query,
        limits,
    )

    with pytest.raises(QueryWorkBudgetExceeded, match="SQL/formula characters"):
        wrapped(
            "analytics",
            "safe_schema",
            "synthetic_orders",
            "total",
            "subtotal + tax",
            0.01,
        )

    assert parsed == []


@pytest.mark.parametrize(
    ("limit_name", "error_match"),
    [
        ("ast_nodes", "AST nodes"),
        ("ast_depth", "AST depth"),
    ],
)
def test_formula_ast_budget_fails_before_sql_rendering(
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    error_match: str,
) -> None:
    rendered: list[ast.AST] = []

    def render_formula(
        node: ast.AST,
        columns: set[str],
        extra_conditions: list[str],
    ) -> str:
        rendered.append(node)
        return "0"

    monkeypatch.setattr(
        "test_data_agent.trino_query_builders.formula_node_to_sql",
        render_formula,
    )
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, **{limit_name: 1})
    wrapped = with_query_work_budget(
        build_formula_rule_profile_query,
        limits,
    )

    with pytest.raises(QueryWorkBudgetExceeded, match=error_match):
        wrapped(
            "analytics",
            "safe_schema",
            "synthetic_orders",
            "total",
            "subtotal + tax",
            0.01,
        )

    assert rendered == []


def test_server_keeps_query_builder_compatibility_exports() -> None:
    assert mcp_trino_server.TrinoQuery is TrinoQuery
    assert mcp_trino_server.build_describe_table_query is build_describe_table_query
    assert (
        mcp_trino_server.build_formula_rule_profile_query
        is build_formula_rule_profile_query
    )
