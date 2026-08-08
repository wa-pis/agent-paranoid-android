from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent import trino_profiling
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_profiling import TrinoProfiler
from test_data_agent.trino_query_builders import TrinoQuery
from test_data_agent.trino_sql_policy import (
    AllowlistError,
    consume_query_execution_work,
)
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudget,
    QueryWorkBudgetExceeded,
    QueryWorkDimension,
    current_query_work_budget,
    with_query_work_budget,
)


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


def test_nested_table_profile_shares_monotonic_cumulative_budget() -> None:
    columns = [
        {
            "column_name": f"column_{index}",
            "data_type": "bigint",
            "is_nullable": "NO",
        }
        for index in range(3)
    ]
    queries: list[str] = []
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        max_profiled_columns=2,
        statements=10,
        max_cumulative_estimated_scan_bytes=40,
    )
    budget = QueryWorkBudget(limits)

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        consume_query_execution_work(
            query.sql,
            estimated_scan_bytes_per_statement=10,
        )
        queries.append(query.sql)
        if query.sql.startswith("SELECT count(*) AS row_count"):
            return [{"row_count": 12}]
        if "information_schema.columns" in query.sql:
            return columns
        return [{"name": "synthetic"}]

    def profile_column(*_args: Any) -> dict[str, Any]:
        assert current_query_work_budget() is budget
        fetch_query(TrinoQuery("SELECT 1 AS synthetic"))
        return {"name": "synthetic", "sensitive": False}

    nested_column_profiler = with_query_work_budget(profile_column, limits)
    profiler = TrinoProfiler(config=profiler_config(), fetch_query=fetch_query)

    def profile_table() -> dict[str, Any]:
        return profiler.profile_table_safe(
            "analytics",
            "safe_schema",
            "orders",
            max_top_values=20,
            column_profiler=nested_column_profiler,
        )

    invoke = with_query_work_budget(
        profile_table,
        limits,
        budget_provider=lambda: budget,
    )

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        invoke()

    assert error.value.dimension is QueryWorkDimension.PROFILED_COLUMNS
    assert len(queries) == 4
    assert budget.snapshot().profiled_columns == 2
    assert budget.snapshot().statements == 4
    assert budget.snapshot().cumulative_estimated_scan_bytes == 40
    assert current_query_work_budget() is None


def test_wide_table_profile_stops_before_default_101st_column() -> None:
    columns = [
        {
            "column_name": f"column_{index}",
            "data_type": "bigint",
            "is_nullable": "NO",
        }
        for index in range(DEFAULT_QUERY_WORK_LIMITS.max_profiled_columns + 1)
    ]
    profiled_columns: list[str] = []
    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS)

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        if query.sql.startswith("SELECT count(*) AS row_count"):
            return [{"row_count": 12}]
        if "information_schema.columns" in query.sql:
            return columns
        raise AssertionError(query.sql)

    def profile_column(*args: Any) -> dict[str, Any]:
        column = str(args[3])
        profiled_columns.append(column)
        return {"name": column, "sensitive": False}

    profiler = TrinoProfiler(config=profiler_config(), fetch_query=fetch_query)

    def profile_table() -> dict[str, Any]:
        return profiler.profile_table_safe(
            "analytics",
            "safe_schema",
            "wide_orders",
            max_top_values=20,
            column_profiler=profile_column,
        )

    invoke = with_query_work_budget(
        profile_table,
        DEFAULT_QUERY_WORK_LIMITS,
        budget_provider=lambda: budget,
    )

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        invoke()

    assert error.value.dimension is QueryWorkDimension.PROFILED_COLUMNS
    assert error.value.attempted == 101
    assert error.value.limit == 100
    assert profiled_columns == [f"column_{index}" for index in range(100)]
    assert budget.snapshot().profiled_columns == 100


def test_nested_table_profile_stops_before_column_after_shared_deadline() -> None:
    now = 0.0
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        max_invocation_seconds=2.0,
    )
    budget = QueryWorkBudget(limits, monotonic_clock=lambda: now)
    queries: list[str] = []

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        nonlocal now
        consume_query_execution_work(query.sql)
        queries.append(query.sql)
        now += 1.0
        if query.sql.startswith("SELECT count(*) AS row_count"):
            return [{"row_count": 12}]
        return [
            {
                "column_name": "status",
                "data_type": "varchar",
                "is_nullable": "YES",
            }
        ]

    profiler = TrinoProfiler(config=profiler_config(), fetch_query=fetch_query)

    def profile_table() -> dict[str, Any]:
        return profiler.profile_table_safe(
            "analytics",
            "safe_schema",
            "orders",
            max_top_values=20,
            column_profiler=lambda *_args: {"name": "must-not-run"},
        )

    invoke = with_query_work_budget(
        profile_table,
        limits,
        budget_provider=lambda: budget,
    )

    with pytest.raises(QueryWorkBudgetExceeded) as error:
        invoke()

    assert error.value.dimension is QueryWorkDimension.INVOCATION_SECONDS
    assert len(queries) == 2
    assert budget.snapshot().statements == 2
    assert budget.snapshot().profiled_columns == 0
    assert current_query_work_budget() is None


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
