"""Transport-neutral orchestration for bounded Trino profiling queries."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_query_builders import (
    TrinoQuery,
    build_aggregate_mapping_profile_query,
    build_column_cardinality_query,
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
    require_non_negative_float,
)
from test_data_agent.trino_sql_policy import check_allowlist

MIN_RULE_CONFIDENCE = 0.9

QueryFetcher = Callable[[TrinoQuery], list[dict[str, Any]]]


class SafeColumnProfiler(Protocol):
    def __call__(
        self,
        catalog: str,
        schema: str,
        table: str,
        column: str,
        data_type: str,
        nullable: bool,
        max_top_values: int,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class TrinoProfiler:
    """Coordinate allowlisted metadata and aggregate-only profiling queries."""

    config: TrinoConfig
    fetch_query: QueryFetcher

    def list_catalogs(self) -> list[str]:
        rows = self.fetch_query(build_list_catalogs_query())
        allowed = self.config.allowed_catalogs
        return [
            row["Catalog"]
            for row in rows
            if allowed is None or row["Catalog"] in allowed
        ]

    def list_schemas(self, catalog: str) -> list[str]:
        self._check_allowlist(catalog=catalog)
        rows = self.fetch_query(build_list_schemas_query(catalog))
        allowed = self.config.allowed_schemas
        return [
            row["Schema"]
            for row in rows
            if allowed is None or row["Schema"] in allowed
        ]

    def list_tables(self, catalog: str, schema: str) -> list[str]:
        self._check_allowlist(catalog=catalog, schema=schema)
        rows = self.fetch_query(build_list_tables_query(catalog, schema))
        return [next(iter(row.values())) for row in rows]

    def describe_table(
        self, catalog: str, schema: str, table: str
    ) -> list[dict[str, Any]]:
        self._check_allowlist(catalog=catalog, schema=schema)
        return self.fetch_query(build_describe_table_query(catalog, schema, table))

    def profile_table(self, catalog: str, schema: str, table: str) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        rows = self.fetch_query(build_table_profile_query(catalog, schema, table))
        return {"table": table, "row_count": rows[0]["row_count"] if rows else 0}

    def profile_column(
        self, catalog: str, schema: str, table: str, column: str
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        rows = self.fetch_query(
            build_column_cardinality_query(catalog, schema, table, column)
        )
        return (
            rows[0]
            if rows
            else {
                "row_count": 0,
                "non_null_count": 0,
                "approx_distinct_count": 0,
            }
        )

    def profile_table_safe(
        self,
        catalog: str,
        schema: str,
        table: str,
        max_top_values: int,
        column_profiler: SafeColumnProfiler,
    ) -> dict[str, Any]:
        """Build a safe table profile through an injected column summarizer."""
        self._check_allowlist(catalog=catalog, schema=schema)
        bounded_top_values = min(max(1, max_top_values), 50)
        table_profile = self.profile_table(catalog, schema, table)
        columns = [
            column_profiler(
                catalog,
                schema,
                table,
                column["column_name"],
                column.get("data_type", "varchar"),
                str(column.get("is_nullable", "")).upper() == "YES",
                bounded_top_values,
            )
            for column in self.describe_table(catalog, schema, table)
        ]
        return {
            "source_type": "trino",
            "table": table,
            "row_count": table_profile["row_count"],
            "columns": columns,
        }

    def profile_foreign_key(
        self,
        catalog: str,
        schema: str,
        parent_table: str,
        parent_field: str,
        child_table: str,
        child_field: str,
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        row = first_row(
            self.fetch_query(
                build_foreign_key_profile_query(
                    catalog,
                    schema,
                    parent_table,
                    parent_field,
                    child_table,
                    child_field,
                )
            )
        )
        checked = int(row.get("checked_count") or 0)
        passed = int(row.get("matched_count") or 0)
        return rule_profile(
            "foreign_key",
            row,
            checked=checked,
            passed=passed,
            failed=int(row.get("orphan_count") or max(0, checked - passed)),
            metadata={
                "parent_table": parent_table,
                "parent_field": parent_field,
                "child_table": child_table,
                "child_field": child_field,
            },
        )

    def profile_temporal_ordering(
        self,
        catalog: str,
        schema: str,
        table: str,
        start_field: str,
        end_field: str,
        allow_equal: bool = True,
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        row = first_row(
            self.fetch_query(
                build_temporal_ordering_profile_query(
                    catalog,
                    schema,
                    table,
                    start_field,
                    end_field,
                    allow_equal=allow_equal,
                )
            )
        )
        return rule_profile(
            "temporal",
            row,
            checked=int(row.get("checked_count") or 0),
            passed=int(row.get("passed_count") or 0),
            failed=int(row.get("failed_count") or 0),
            metadata={
                "table": table,
                "start_field": start_field,
                "end_field": end_field,
                "allow_equal": allow_equal,
            },
        )

    def profile_formula_rule(
        self,
        catalog: str,
        schema: str,
        table: str,
        target_field: str,
        expression: str,
        tolerance: float = 0.000001,
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        query = build_formula_rule_profile_query(
            catalog,
            schema,
            table,
            target_field,
            expression,
            tolerance,
        )
        safe_tolerance = require_non_negative_float(tolerance, "tolerance")
        row = first_row(self.fetch_query(query))
        return rule_profile(
            "formula",
            row,
            checked=int(row.get("checked_count") or 0),
            passed=int(row.get("passed_count") or 0),
            failed=int(row.get("failed_count") or 0),
            metadata={
                "table": table,
                "target_field": target_field,
                "expression": expression,
                "tolerance": safe_tolerance,
            },
        )

    def profile_conditional_required(
        self,
        catalog: str,
        schema: str,
        table: str,
        condition_field: str,
        condition_equals: Any,
        required_field: str,
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        row = first_row(
            self.fetch_query(
                build_conditional_required_profile_query(
                    catalog,
                    schema,
                    table,
                    condition_field,
                    condition_equals,
                    required_field,
                )
            )
        )
        return rule_profile(
            "conditional_required",
            row,
            checked=int(row.get("checked_count") or 0),
            passed=int(row.get("passed_count") or 0),
            failed=int(row.get("failed_count") or 0),
            metadata={
                "table": table,
                "condition_field": condition_field,
                "required_field": required_field,
            },
        )

    def profile_conditional_allowed_values(
        self,
        catalog: str,
        schema: str,
        table: str,
        condition_field: str,
        condition_equals: Any,
        value_field: str,
        allowed_values: list[Any],
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        if not allowed_values:
            raise ValueError("allowed_values must not be empty")
        if len(allowed_values) > 50:
            raise ValueError("allowed_values is limited to 50 entries")
        row = first_row(
            self.fetch_query(
                build_conditional_allowed_values_profile_query(
                    catalog,
                    schema,
                    table,
                    condition_field,
                    condition_equals,
                    value_field,
                    allowed_values,
                )
            )
        )
        return rule_profile(
            "conditional_allowed_values",
            row,
            checked=int(row.get("checked_count") or 0),
            passed=int(row.get("passed_count") or 0),
            failed=int(row.get("failed_count") or 0),
            metadata={
                "table": table,
                "condition_field": condition_field,
                "value_field": value_field,
            },
        )

    def profile_aggregate_mapping(
        self,
        catalog: str,
        schema: str,
        parent_table: str,
        parent_key: str,
        parent_value_field: str,
        child_table: str,
        child_key: str,
        child_value_field: str | None = None,
        aggregate: str = "sum",
        tolerance: float = 0.000001,
    ) -> dict[str, Any]:
        self._check_allowlist(catalog=catalog, schema=schema)
        if aggregate not in {"sum", "count", "avg"}:
            raise ValueError("aggregate must be 'sum', 'count', or 'avg'")
        if aggregate != "count" and not child_value_field:
            raise ValueError("child_value_field is required for numeric aggregates")
        safe_tolerance = require_non_negative_float(tolerance, "tolerance")
        row = first_row(
            self.fetch_query(
                build_aggregate_mapping_profile_query(
                    catalog,
                    schema,
                    parent_table,
                    parent_key,
                    parent_value_field,
                    child_table,
                    child_key,
                    child_value_field,
                    aggregate,
                    safe_tolerance,
                )
            )
        )
        return rule_profile(
            "aggregate_mapping",
            row,
            checked=int(row.get("checked_count") or 0),
            passed=int(row.get("passed_count") or 0),
            failed=int(row.get("failed_count") or 0),
            metadata={
                "parent_table": parent_table,
                "parent_key": parent_key,
                "parent_value_field": parent_value_field,
                "child_table": child_table,
                "child_key": child_key,
                "child_value_field": child_value_field,
                "aggregate": aggregate,
                "tolerance": safe_tolerance,
            },
        )

    def _check_allowlist(self, *, catalog: str, schema: str | None = None) -> None:
        check_allowlist(catalog=catalog, schema=schema, config=self.config)


def first_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def rule_profile(
    rule_type: str,
    row: dict[str, Any],
    *,
    checked: int,
    passed: int,
    failed: int,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    confidence = round(passed / checked, 6) if checked else 0.0
    return {
        "type": rule_type,
        **metadata,
        **row,
        "checked_count": checked,
        "passed_count": passed,
        "failed_count": failed,
        "confidence": confidence,
        "status": "inferred" if confidence >= MIN_RULE_CONFIDENCE else "rejected",
    }
