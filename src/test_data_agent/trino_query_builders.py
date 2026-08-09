"""Non-executing builders for bounded Trino metadata and profiling queries."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from test_data_agent.trino_sql_policy import (
    MAX_LIMIT,
    SqlSafetyError,
    quote_identifier,
    require_identifier,
)
from test_data_agent.trino_work_budget import (
    consume_ast_work,
    consume_sql_formula_chars,
)


@dataclass(frozen=True)
class TrinoQuery:
    """A parameterized Trino query that has not been executed."""

    sql: str
    parameters: tuple[Any, ...] = ()


@dataclass(frozen=True)
class FormulaSql:
    sql: str
    columns: frozenset[str]
    extra_conditions: tuple[str, ...] = ()


def build_list_catalogs_query() -> TrinoQuery:
    return TrinoQuery("SHOW CATALOGS")


def build_list_schemas_query(catalog: str) -> TrinoQuery:
    return TrinoQuery(f"SHOW SCHEMAS FROM {quote_identifier(catalog)}")


def build_list_tables_query(catalog: str, schema: str) -> TrinoQuery:
    return TrinoQuery(
        f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(schema)}"
    )


def build_describe_table_query(catalog: str, schema: str, table: str) -> TrinoQuery:
    return TrinoQuery(
        "SELECT column_name, data_type, is_nullable "
        f"FROM {quote_identifier(catalog)}.information_schema.columns "
        "WHERE table_catalog = ? AND table_schema = ? AND table_name = ? "
        "ORDER BY ordinal_position",
        (catalog, schema, table),
    )


def build_table_profile_query(catalog: str, schema: str, table: str) -> TrinoQuery:
    return TrinoQuery(
        f"SELECT count(*) AS row_count FROM {qualified_table(catalog, schema, table)}"
    )


def build_column_cardinality_query(
    catalog: str,
    schema: str,
    table: str,
    column: str,
) -> TrinoQuery:
    safe_table = qualified_table(catalog, schema, table)
    safe_column = quote_identifier(column)
    return TrinoQuery(
        f"SELECT count(*) AS row_count, count({safe_column}) AS non_null_count, "
        f"approx_distinct({safe_column}) AS approx_distinct_count "
        f"FROM {safe_table}"
    )


def build_column_profile_query(
    catalog: str,
    schema: str,
    table: str,
    column: str,
    data_type: str,
) -> TrinoQuery:
    return TrinoQuery(
        profile_column_sql(
            qualified_table(catalog, schema, table),
            quote_identifier(column),
            data_type,
        )
    )


def build_sensitive_numeric_shape_query(
    catalog: str,
    schema: str,
    table: str,
    column: str,
) -> TrinoQuery:
    safe_table = qualified_table(catalog, schema, table)
    safe_column = quote_identifier(column)
    magnitude = (
        f"TRY_CAST(floor(log10(abs(CAST({safe_column} AS double)))) AS integer)"
    )
    return TrinoQuery(
        f"SELECT count(*) AS row_count, count({safe_column}) AS non_null_count, "
        f"approx_distinct({safe_column}) AS approx_distinct_count, "
        f"max(CASE WHEN {safe_column} = 0 THEN NULL ELSE {magnitude} END) "
        "AS max_abs_magnitude, "
        f"count_if({safe_column} < 0) > 0 AS has_negative, "
        f"count_if({safe_column} > 0) > 0 AS has_positive "
        f"FROM {safe_table}"
    )


def build_top_values_query(
    catalog: str,
    schema: str,
    table: str,
    column: str,
    limit: int,
) -> TrinoQuery:
    safe_column = quote_identifier(column)
    safe_limit = bounded_limit(limit)
    return TrinoQuery(
        f"SELECT {safe_column} AS value, count(*) AS count "
        f"FROM {qualified_table(catalog, schema, table)} "
        f"WHERE {safe_column} IS NOT NULL "
        f"GROUP BY {safe_column} "
        "ORDER BY count DESC "
        f"LIMIT {safe_limit}"
    )


def build_foreign_key_profile_query(
    catalog: str,
    schema: str,
    parent_table: str,
    parent_field: str,
    child_table: str,
    child_field: str,
) -> TrinoQuery:
    parent = qualified_table(catalog, schema, parent_table)
    child = qualified_table(catalog, schema, child_table)
    parent_key = quote_identifier(parent_field)
    child_key = quote_identifier(child_field)
    return TrinoQuery(
        "SELECT "
        "count(*) AS child_row_count, "
        f"count(c.{child_key}) AS checked_count, "
        "count_if(p.parent_key IS NOT NULL) AS matched_count, "
        f"count_if(c.{child_key} IS NOT NULL AND p.parent_key IS NULL) AS orphan_count "
        f"FROM {child} c "
        f"LEFT JOIN (SELECT DISTINCT {parent_key} AS parent_key FROM {parent} "
        f"WHERE {parent_key} IS NOT NULL) p "
        f"ON c.{child_key} = p.parent_key"
    )


def build_temporal_ordering_profile_query(
    catalog: str,
    schema: str,
    table: str,
    start_field: str,
    end_field: str,
    *,
    allow_equal: bool,
) -> TrinoQuery:
    safe_table = qualified_table(catalog, schema, table)
    start = quote_identifier(start_field)
    end = quote_identifier(end_field)
    operator = "<=" if allow_equal else "<"
    fail_operator = ">" if allow_equal else ">="
    checked_condition = f"{start} IS NOT NULL AND {end} IS NOT NULL"
    return TrinoQuery(
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({checked_condition}) AS checked_count, "
        f"count_if({checked_condition} AND {start} {operator} {end}) AS passed_count, "
        f"count_if({checked_condition} AND {start} {fail_operator} {end}) AS failed_count "
        f"FROM {safe_table}"
    )


def build_formula_rule_profile_query(
    catalog: str,
    schema: str,
    table: str,
    target_field: str,
    expression: str,
    tolerance: float,
) -> TrinoQuery:
    safe_table = qualified_table(catalog, schema, table)
    safe_target = quote_identifier(target_field)
    formula = build_formula_sql(expression)
    safe_tolerance = require_non_negative_float(tolerance, "tolerance")
    checks = [f"{safe_target} IS NOT NULL"]
    checks.extend(
        f"{quote_identifier(column)} IS NOT NULL" for column in sorted(formula.columns)
    )
    checks.extend(formula.extra_conditions)
    checked_condition = " AND ".join(checks)
    residual = f"abs(CAST({safe_target} AS double) - CAST(({formula.sql}) AS double))"
    return TrinoQuery(
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({checked_condition}) AS checked_count, "
        f"count_if({checked_condition} AND {residual} <= {safe_tolerance}) AS passed_count, "
        f"count_if({checked_condition} AND {residual} > {safe_tolerance}) AS failed_count, "
        f"avg(CASE WHEN {checked_condition} THEN {residual} END) AS avg_abs_error, "
        f"max(CASE WHEN {checked_condition} THEN {residual} END) AS max_abs_error "
        f"FROM {safe_table}"
    )


def build_conditional_required_profile_query(
    catalog: str,
    schema: str,
    table: str,
    condition_field: str,
    condition_equals: Any,
    required_field: str,
) -> TrinoQuery:
    safe_table = qualified_table(catalog, schema, table)
    condition_column = quote_identifier(condition_field)
    present = present_sql(quote_identifier(required_field))
    return TrinoQuery(
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({condition_column} = ?) AS checked_count, "
        f"count_if({condition_column} = ? AND {present}) AS passed_count, "
        f"count_if({condition_column} = ? AND NOT ({present})) AS failed_count "
        f"FROM {safe_table}",
        (condition_equals, condition_equals, condition_equals),
    )


def build_conditional_allowed_values_profile_query(
    catalog: str,
    schema: str,
    table: str,
    condition_field: str,
    condition_equals: Any,
    value_field: str,
    allowed_values: list[Any],
) -> TrinoQuery:
    if not allowed_values:
        raise ValueError("allowed_values must not be empty")
    if len(allowed_values) > 50:
        raise ValueError("allowed_values is limited to 50 entries")
    safe_table = qualified_table(catalog, schema, table)
    condition_column = quote_identifier(condition_field)
    value_column = quote_identifier(value_field)
    placeholders = ", ".join("?" for _ in allowed_values)
    return TrinoQuery(
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({condition_column} = ?) AS checked_count, "
        f"count_if({condition_column} = ? AND {value_column} IN ({placeholders})) AS passed_count, "
        f"count_if({condition_column} = ? AND "
        f"({value_column} IS NULL OR {value_column} NOT IN ({placeholders}))) AS failed_count "
        f"FROM {safe_table}",
        (
            condition_equals,
            condition_equals,
            *allowed_values,
            condition_equals,
            *allowed_values,
        ),
    )


def build_aggregate_mapping_profile_query(
    catalog: str,
    schema: str,
    parent_table: str,
    parent_key: str,
    parent_value_field: str,
    child_table: str,
    child_key: str,
    child_value_field: str | None,
    aggregate: str,
    tolerance: float,
) -> TrinoQuery:
    if aggregate not in {"sum", "count", "avg"}:
        raise ValueError("aggregate must be 'sum', 'count', or 'avg'")
    if aggregate != "count" and not child_value_field:
        raise ValueError("child_value_field is required for numeric aggregates")
    safe_tolerance = require_non_negative_float(tolerance, "tolerance")
    parent = qualified_table(catalog, schema, parent_table)
    child = qualified_table(catalog, schema, child_table)
    parent_key_sql = quote_identifier(parent_key)
    parent_value_sql = quote_identifier(parent_value_field)
    child_key_sql = quote_identifier(child_key)
    child_value_sql = quote_identifier(child_value_field) if child_value_field else None
    child_aggregate_sql = (
        "count(*)"
        if aggregate == "count"
        else f"{aggregate}(CAST({child_value_sql} AS double))"
    )
    expected = "COALESCE(a.aggregate_value, 0.0)"
    residual = f"abs(CAST(p.{parent_value_sql} AS double) - {expected})"
    checked_condition = (
        f"p.{parent_key_sql} IS NOT NULL AND p.{parent_value_sql} IS NOT NULL"
    )
    return TrinoQuery(
        "WITH child_agg AS ("
        f"SELECT {child_key_sql} AS parent_key, {child_aggregate_sql} AS aggregate_value "
        f"FROM {child} "
        f"WHERE {child_key_sql} IS NOT NULL "
        f"GROUP BY {child_key_sql}"
        ") "
        "SELECT "
        "count(*) AS parent_row_count, "
        f"count_if({checked_condition}) AS checked_count, "
        f"count_if({checked_condition} AND {residual} <= {safe_tolerance}) AS passed_count, "
        f"count_if({checked_condition} AND {residual} > {safe_tolerance}) AS failed_count, "
        f"avg(CASE WHEN {checked_condition} THEN {residual} END) AS avg_abs_error, "
        f"max(CASE WHEN {checked_condition} THEN {residual} END) AS max_abs_error "
        f"FROM {parent} p "
        f"LEFT JOIN child_agg a ON p.{parent_key_sql} = a.parent_key"
    )


def profile_column_sql(safe_table: str, safe_column: str, data_type: str) -> str:
    metrics = [
        "count(*) AS row_count",
        f"count({safe_column}) AS non_null_count",
        f"approx_distinct({safe_column}) AS approx_distinct_count",
    ]
    if is_numeric_trino_type(data_type):
        metrics.extend(
            [
                f"min({safe_column}) AS min_value",
                f"max({safe_column}) AS max_value",
                f"approx_percentile({safe_column}, 0.05) AS p05",
                f"approx_percentile({safe_column}, 0.95) AS p95",
            ]
        )
    elif is_timestamp_trino_type(data_type):
        metrics.extend(
            [
                f"min({safe_column}) AS min_timestamp",
                f"max({safe_column}) AS max_timestamp",
            ]
        )
    elif is_date_trino_type(data_type):
        metrics.extend(
            [f"min({safe_column}) AS min_date", f"max({safe_column}) AS max_date"]
        )
    return f"SELECT {', '.join(metrics)} FROM {safe_table}"


def is_numeric_trino_type(data_type: str) -> bool:
    lowered = data_type.lower()
    return any(
        part in lowered for part in ("int", "decimal", "double", "float", "real")
    )


def is_timestamp_trino_type(data_type: str) -> bool:
    lowered = data_type.lower()
    return "timestamp" in lowered or "datetime" in lowered


def is_date_trino_type(data_type: str) -> bool:
    return "date" in data_type.lower() and not is_timestamp_trino_type(data_type)


def is_string_trino_type(data_type: str) -> bool:
    lowered = data_type.lower()
    return any(part in lowered for part in ("char", "varchar", "string"))


def present_sql(column: str) -> str:
    return f"{column} IS NOT NULL AND CAST({column} AS varchar) <> ''"


def require_non_negative_float(value: float, label: str) -> float:
    number = float(value)
    if number < 0:
        raise ValueError(f"{label} must be non-negative")
    return number


def build_formula_sql(expression: str) -> FormulaSql:
    consume_sql_formula_chars(expression)
    try:
        node = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise SqlSafetyError("formula expression is not valid arithmetic") from exc
    consume_ast_work(node, child_nodes=ast.iter_child_nodes)
    columns: set[str] = set()
    extra_conditions: list[str] = []
    sql = formula_node_to_sql(node.body, columns, extra_conditions)
    if not columns:
        raise SqlSafetyError("formula expression must reference at least one column")
    return FormulaSql(
        sql=sql, columns=frozenset(columns), extra_conditions=tuple(extra_conditions)
    )


def formula_node_to_sql(
    node: ast.AST, columns: set[str], extra_conditions: list[str]
) -> str:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise SqlSafetyError("formula constants must be numeric")
        return repr(float(node.value))
    if isinstance(node, ast.Name):
        columns.add(require_identifier(node.id, "formula column"))
        return f"CAST({quote_identifier(node.id)} AS double)"
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return f"(-{formula_node_to_sql(node.operand, columns, extra_conditions)})"
    if isinstance(node, ast.BinOp):
        left = formula_node_to_sql(node.left, columns, extra_conditions)
        right = formula_node_to_sql(node.right, columns, extra_conditions)
        if isinstance(node.op, ast.Add):
            return f"({left} + {right})"
        if isinstance(node.op, ast.Sub):
            return f"({left} - {right})"
        if isinstance(node.op, ast.Mult):
            return f"({left} * {right})"
        if isinstance(node.op, ast.Div):
            extra_conditions.append(f"({right}) <> 0")
            return f"({left} / NULLIF({right}, 0))"
    raise SqlSafetyError("formula expression uses unsupported syntax")


def qualified_table(catalog: str, schema: str, table: str) -> str:
    return ".".join(
        [
            quote_identifier(catalog),
            quote_identifier(schema),
            quote_identifier(table),
        ]
    )


def bounded_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("limit must be positive")
    return min(limit, MAX_LIMIT)
