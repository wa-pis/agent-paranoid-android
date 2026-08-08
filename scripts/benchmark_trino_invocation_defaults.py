#!/usr/bin/env python3
"""Benchmark representative aggregate-only Trino profiling fan-out."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any

from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_masking import TrinoMasker
from test_data_agent.trino_profiling import TrinoProfiler
from test_data_agent.trino_query_builders import TrinoQuery
from test_data_agent.trino_sql_policy import consume_query_execution_work
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudget,
    with_query_work_budget,
)


REPRESENTATIVE_COLUMNS = 100
REPRESENTATIVE_ENUM_COLUMNS = 20
REPRESENTATIVE_SENSITIVE_COLUMNS = 20


@dataclass(frozen=True, slots=True)
class InvocationDefaultMetrics:
    profiled_columns: int
    profile_completion_ratio: float
    sensitive_columns_aggregate_only: int
    statements: int
    statement_headroom: int
    configured_deadline_seconds: float
    elapsed_seconds: float
    remaining_deadline_seconds: float


def _benchmark_config() -> TrinoConfig:
    return TrinoConfig(
        host="synthetic.invalid",
        port=8443,
        user="benchmark",
        http_scheme="https",
        allowed_catalogs=frozenset({"synthetic"}),
        allowed_schemas=frozenset({"benchmark"}),
    )


def _representative_columns() -> list[dict[str, str]]:
    sensitive = [
        {
            "column_name": f"customer_email_{index:03d}",
            "data_type": "varchar",
            "is_nullable": "NO",
        }
        for index in range(REPRESENTATIVE_SENSITIVE_COLUMNS)
    ]
    enum = [
        {
            "column_name": f"status_{index:03d}",
            "data_type": "varchar",
            "is_nullable": "YES",
        }
        for index in range(REPRESENTATIVE_ENUM_COLUMNS)
    ]
    numeric_count = REPRESENTATIVE_COLUMNS - len(sensitive) - len(enum)
    numeric = [
        {
            "column_name": f"metric_{index:03d}",
            "data_type": "double",
            "is_nullable": "NO",
        }
        for index in range(numeric_count)
    ]
    return sensitive + enum + numeric


def run_invocation_default_benchmark() -> InvocationDefaultMetrics:
    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS)
    columns = _representative_columns()

    def fetch_query(query: TrinoQuery) -> list[dict[str, Any]]:
        consume_query_execution_work(query.sql)
        sql = query.sql
        if "information_schema.columns" in sql:
            return columns
        if "GROUP BY" in sql:
            return [
                {"value": "synthetic_open", "count": 6_000},
                {"value": "synthetic_closed", "count": 4_000},
            ]
        if "approx_distinct" in sql:
            distinct = 4 if '"status_' in sql else 9_000
            return [
                {
                    "row_count": 10_000,
                    "non_null_count": 9_900,
                    "approx_distinct_count": distinct,
                    "min_value": 0.0,
                    "max_value": 1_000.0,
                    "p05": 10.0,
                    "p95": 900.0,
                }
            ]
        if sql.startswith("SELECT count(*) AS row_count FROM"):
            return [{"row_count": 10_000}]
        raise AssertionError(f"unexpected benchmark query: {sql}")

    config = _benchmark_config()
    profiler = TrinoProfiler(config=config, fetch_query=fetch_query)
    masker = TrinoMasker(
        config=config,
        fetch_query=fetch_query,
        fetch_sql=lambda _sql: [],
    )

    def profile_column(
        catalog: str,
        schema: str,
        table: str,
        column: str,
        data_type: str,
        nullable: bool,
        max_top_values: int,
    ) -> dict[str, Any]:
        return masker.profile_column_safe(
            catalog,
            schema,
            table,
            column,
            data_type,
            nullable,
            max_top_values,
        )

    def profile_table() -> dict[str, Any]:
        return profiler.profile_table_safe(
            "synthetic",
            "benchmark",
            "representative",
            max_top_values=20,
            column_profiler=profile_column,
        )

    started = time.perf_counter()
    profile = with_query_work_budget(
        profile_table,
        budget.limits,
        budget_provider=lambda: budget,
    )()
    elapsed = time.perf_counter() - started
    snapshot = budget.snapshot()
    profiled_columns = profile["columns"]
    if len(profiled_columns) != REPRESENTATIVE_COLUMNS:
        raise RuntimeError("benchmark did not profile every representative column")
    if snapshot.profiled_columns != REPRESENTATIVE_COLUMNS:
        raise RuntimeError("profiled-column accounting differs from the workload")
    expected_statements = (
        2 + REPRESENTATIVE_COLUMNS + REPRESENTATIVE_ENUM_COLUMNS
    )
    if snapshot.statements != expected_statements:
        raise RuntimeError("statement accounting differs from the workload")
    sensitive_columns_aggregate_only = sum(
        column.get("sensitive") is True
        and "top_values" not in column
        and "masked_patterns" not in column
        for column in profiled_columns
    )
    if sensitive_columns_aggregate_only != REPRESENTATIVE_SENSITIVE_COLUMNS:
        raise RuntimeError("sensitive-column profiling left aggregate-only mode")

    return InvocationDefaultMetrics(
        profiled_columns=snapshot.profiled_columns,
        profile_completion_ratio=round(
            len(profiled_columns) / REPRESENTATIVE_COLUMNS,
            6,
        ),
        sensitive_columns_aggregate_only=sensitive_columns_aggregate_only,
        statements=snapshot.statements,
        statement_headroom=DEFAULT_QUERY_WORK_LIMITS.statements
        - snapshot.statements,
        configured_deadline_seconds=(
            DEFAULT_QUERY_WORK_LIMITS.max_invocation_seconds
        ),
        elapsed_seconds=round(elapsed, 6),
        remaining_deadline_seconds=round(
            budget.remaining_invocation_seconds(),
            6,
        ),
    )


def main() -> int:
    metrics = run_invocation_default_benchmark()
    print(json.dumps(asdict(metrics), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
