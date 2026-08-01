from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent import trino_profiling
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_profiling import TrinoProfiler
from test_data_agent.trino_query_builders import TrinoQuery
from test_data_agent.trino_sql_policy import AllowlistError


def profiler_config() -> TrinoConfig:
    return TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe_schema"}),
    )


def test_profiler_rejects_disallowed_source_before_query_execution() -> None:
    def reject_fetch(query: TrinoQuery) -> list[dict[str, Any]]:
        raise AssertionError(f"query must not execute: {query.sql}")

    profiler = TrinoProfiler(config=profiler_config(), fetch_query=reject_fetch)

    with pytest.raises(AllowlistError, match="catalog is not allowed"):
        profiler.profile_table("production", "safe_schema", "customers")


def test_profiler_coordinates_aggregate_only_safe_table_profile() -> None:
    queries: list[TrinoQuery] = []
    column_calls: list[tuple[Any, ...]] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        queries.append(query)
        if query.sql.startswith("SELECT count(*) AS row_count"):
            return [{"row_count": 12}]
        if "information_schema.columns" in query.sql:
            return [
                {
                    "column_name": "status",
                    "data_type": "varchar",
                    "is_nullable": "YES",
                }
            ]
        raise AssertionError(query.sql)

    def profile_column(
        catalog: str,
        schema: str,
        table: str,
        column: str,
        data_type: str,
        nullable: bool,
        max_top_values: int,
    ) -> dict[str, Any]:
        column_calls.append(
            (
                catalog,
                schema,
                table,
                column,
                data_type,
                nullable,
                max_top_values,
            )
        )
        return {"name": column, "sensitive": False}

    profile = TrinoProfiler(
        config=profiler_config(), fetch_query=fetch_query
    ).profile_table_safe(
        "analytics",
        "safe_schema",
        "orders",
        max_top_values=500,
        column_profiler=profile_column,
    )

    assert profile == {
        "source_type": "trino",
        "table": "orders",
        "row_count": 12,
        "columns": [{"name": "status", "sensitive": False}],
    }
    assert column_calls == [
        ("analytics", "safe_schema", "orders", "status", "varchar", True, 50)
    ]
    assert all("SELECT *" not in query.sql.upper() for query in queries)


def test_profiler_keeps_condition_values_bound_and_out_of_results() -> None:
    captured: list[TrinoQuery] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        captured.append(query)
        return [
            {
                "row_count": 20,
                "checked_count": 5,
                "passed_count": 4,
                "failed_count": 1,
            }
        ]

    sensitive_condition = "customer@example.com"
    profile = TrinoProfiler(
        config=profiler_config(), fetch_query=fetch_query
    ).profile_conditional_required(
        "analytics",
        "safe_schema",
        "orders",
        "customer_email",
        sensitive_condition,
        "reviewed_at",
    )

    assert sensitive_condition not in captured[0].sql
    assert sensitive_condition in captured[0].parameters
    assert sensitive_condition not in str(profile)
    assert profile["status"] == "rejected"


def test_server_keeps_profiling_compatibility_exports() -> None:
    assert mcp_trino_server.TrinoProfiler is TrinoProfiler


def test_profiling_boundary_does_not_import_transport_or_client() -> None:
    module_path = Path(trino_profiling.__file__)
    tree = ast.parse(module_path.read_text())
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "test_data_agent.mcp_trino_server" not in imported_modules
    assert "test_data_agent.mcp_trino_transport" not in imported_modules
    assert "test_data_agent.trino_client" not in imported_modules
