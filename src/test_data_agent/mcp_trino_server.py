"""Safe Trino MCP tools for schema inspection and profiling.

The public helpers in this module are intentionally small and conservative so
they can be tested without a live Trino cluster.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from test_data_agent.core.privacy import (
    infer_sensitive_from_name,
    infer_sensitive_type_from_values,
    infer_sensitive_value_type,
    looks_sensitive_value,
    mask_pattern,
    mask_value,
    synthetic_category_distribution,
)
from test_data_agent.audit import audit_logger_from_env
from test_data_agent.mcp_trino_transport import create_trino_mcp
from test_data_agent.trino_config import (
    ABSOLUTE_MAX_RESULT_ROWS as ABSOLUTE_MAX_RESULT_ROWS,
    DATA_SIZE_MULTIPLIERS as DATA_SIZE_MULTIPLIERS,
    DATA_SIZE_RE as DATA_SIZE_RE,
    DEFAULT_MAX_RESULT_ROWS as DEFAULT_MAX_RESULT_ROWS,
    DEFAULT_QUERY_MAX_EXECUTION_TIME as DEFAULT_QUERY_MAX_EXECUTION_TIME,
    DEFAULT_QUERY_MAX_RUN_TIME as DEFAULT_QUERY_MAX_RUN_TIME,
    DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES as DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES,
    DURATION_MULTIPLIERS_MS as DURATION_MULTIPLIERS_MS,
    DURATION_RE as DURATION_RE,
    MAX_QUERY_EXECUTION_TIME_MS as MAX_QUERY_EXECUTION_TIME_MS,
    MAX_QUERY_RUN_TIME_MS as MAX_QUERY_RUN_TIME_MS,
    MAX_QUERY_SCAN_BYTES as MAX_QUERY_SCAN_BYTES,
    TrinoConfig as TrinoConfig,
    TrinoConfigurationError as TrinoConfigurationError,
    parse_allowlist as parse_allowlist,
    parse_data_size_env as parse_data_size_env,
    parse_data_size_value as parse_data_size_value,
    parse_duration_env as parse_duration_env,
    parse_duration_value as parse_duration_value,
    parse_env_bool as parse_env_bool,
    parse_max_result_rows as parse_max_result_rows,
    parse_request_timeout as parse_request_timeout,
    parse_trino_port as parse_trino_port,
)
from test_data_agent.trino_sql_policy import (
    FORBIDDEN_SQL_RE as FORBIDDEN_SQL_RE,
    IDENTIFIER_RE as IDENTIFIER_RE,
    LIMIT_RE as LIMIT_RE,
    MAX_LIMIT as MAX_LIMIT,
    SELECT_STAR_RE as SELECT_STAR_RE,
    TABLE_STAR_RE as TABLE_STAR_RE,
    AllowlistError as AllowlistError,
    SqlSafetyError as SqlSafetyError,
    check_allowlist as check_allowlist,
    exp as exp,
    extract_table_references as extract_table_references,
    has_top_level_limit as has_top_level_limit,
    has_unrestricted_projection_star as has_unrestricted_projection_star,
    is_star_column as is_star_column,
    normalize_sql as normalize_sql,
    parse_select_ast as parse_select_ast,
    quote_identifier as quote_identifier,
    require_identifier as require_identifier,
    selected_sensitive_identifier_names as selected_sensitive_identifier_names,
    sqlglot as sqlglot,
    strip_sql_comments as strip_sql_comments,
    top_level_limit_value as top_level_limit_value,
    unquoted_char_positions as unquoted_char_positions,
    validate_safe_select as validate_safe_select,
    validate_safe_select_shape as validate_safe_select_shape,
    validate_table_references_allowed as validate_table_references_allowed,
)

try:  # pragma: no cover - live Trino is not used in unit tests.
    import trino
except ImportError:  # pragma: no cover
    trino = None  # type: ignore[assignment]


DEFAULT_LIMIT = 100
MIN_RULE_CONFIDENCE = 0.9
ENABLE_SAFE_SELECT_ENV = "TRINO_ENABLE_SAFE_SELECT"


class TrinoResultLimitError(ValueError):
    """Raised when a Trino response exceeds the client-side safety limit."""


def mask_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: mask_value(value)
        if infer_sensitive_from_name(key) or looks_sensitive_value(value)
        else value
        for key, value in row.items()
    }


def rows_to_dicts(description: Sequence[Any], rows: Iterable[Sequence[Any]]) -> list[dict[str, Any]]:
    names = [column[0] for column in description]
    return [dict(zip(names, row, strict=True)) for row in rows]


def _execute_query(sql: str, parameters: Sequence[Any] | None = None) -> tuple[list[tuple[Any, ...]], list[Any]]:
    if trino is None:
        raise RuntimeError("trino package is not installed")

    config = TrinoConfig.from_env()
    connection = trino.dbapi.connect(  # type: ignore[no-untyped-call]
        host=config.host,
        port=config.port,
        user=config.user,
        http_scheme=config.http_scheme,
        request_timeout=config.request_timeout,
        session_properties={
            "query_max_execution_time": config.query_max_execution_time,
            "query_max_run_time": config.query_max_run_time,
            "query_max_scan_physical_bytes": config.query_max_scan_physical_bytes,
        },
    )
    cursor = connection.cursor()
    try:
        cursor.execute(sql, parameters or [])
        rows = cursor.fetchmany(config.max_result_rows + 1)
        if len(rows) > config.max_result_rows:
            raise TrinoResultLimitError(
                f"Trino result exceeds the client limit of {config.max_result_rows} rows"
            )
        return rows, cursor.description or []
    finally:
        try:
            cursor.close()
        finally:
            connection.close()


def _fetch_dicts(sql: str, parameters: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    rows, description = _execute_query(sql, parameters)
    return rows_to_dicts(description, rows)


def list_catalogs() -> list[str]:
    rows = _fetch_dicts("SHOW CATALOGS")
    allowed = TrinoConfig.from_env().allowed_catalogs
    return [row["Catalog"] for row in rows if allowed is None or row["Catalog"] in allowed]


def list_schemas(catalog: str) -> list[str]:
    check_allowlist(catalog=catalog)
    rows = _fetch_dicts(f"SHOW SCHEMAS FROM {quote_identifier(catalog)}")
    allowed = TrinoConfig.from_env().allowed_schemas
    return [row["Schema"] for row in rows if allowed is None or row["Schema"] in allowed]


def list_tables(catalog: str, schema: str) -> list[str]:
    check_allowlist(catalog=catalog, schema=schema)
    rows = _fetch_dicts(f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(schema)}")
    return [next(iter(row.values())) for row in rows]


def describe_table(catalog: str, schema: str, table: str) -> list[dict[str, Any]]:
    check_allowlist(catalog=catalog, schema=schema)
    sql = (
        "SELECT column_name, data_type, is_nullable "
        f"FROM {quote_identifier(catalog)}.information_schema.columns "
        "WHERE table_catalog = ? AND table_schema = ? AND table_name = ? "
        "ORDER BY ordinal_position"
    )
    return _fetch_dicts(sql, [catalog, schema, table])


def profile_table(catalog: str, schema: str, table: str) -> dict[str, Any]:
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    rows = _fetch_dicts(f"SELECT count(*) AS row_count FROM {safe_table}")
    return {"table": table, "row_count": rows[0]["row_count"] if rows else 0}


def profile_column(catalog: str, schema: str, table: str, column: str) -> dict[str, Any]:
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    safe_column = quote_identifier(column)
    sql = (
        f"SELECT count(*) AS row_count, count({safe_column}) AS non_null_count, "
        f"approx_distinct({safe_column}) AS approx_distinct_count "
        f"FROM {safe_table}"
    )
    rows = _fetch_dicts(sql)
    return rows[0] if rows else {"row_count": 0, "non_null_count": 0, "approx_distinct_count": 0}


def profile_table_safe(catalog: str, schema: str, table: str, max_top_values: int = 20) -> dict[str, Any]:
    """Build a safe Trino-derived profile using pushdown aggregates only."""
    check_allowlist(catalog=catalog, schema=schema)
    bounded_top_values = min(max(1, max_top_values), 50)
    table_profile = profile_table(catalog, schema, table)
    columns = [
        profile_column_safe(
            catalog,
            schema,
            table,
            column["column_name"],
            column.get("data_type", "varchar"),
            str(column.get("is_nullable", "")).upper() == "YES",
            bounded_top_values,
        )
        for column in describe_table(catalog, schema, table)
    ]
    return {
        "source_type": "trino",
        "table": table,
        "row_count": table_profile["row_count"],
        "columns": columns,
    }


def profile_column_safe(
    catalog: str,
    schema: str,
    table: str,
    column: str,
    data_type: str,
    nullable: bool,
    max_top_values: int,
) -> dict[str, Any]:
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    safe_column = quote_identifier(column)
    sensitive = infer_sensitive_from_name(column)
    aggregate_rows = _fetch_dicts(profile_column_sql(safe_table, safe_column, data_type))
    aggregates = aggregate_rows[0] if aggregate_rows else {}
    row_count = int(aggregates.get("row_count") or 0)
    non_null_count = int(aggregates.get("non_null_count") or 0)
    profile: dict[str, Any] = {
        "name": column,
        "data_type": data_type,
        "nullable": nullable,
        "row_count": row_count,
        "null_count": max(0, row_count - non_null_count),
        "null_ratio": round((row_count - non_null_count) / row_count, 6) if row_count else 0.0,
        "approx_distinct_count": aggregates.get("approx_distinct_count", 0),
        "sensitive": sensitive,
    }
    profile.update({key: value for key, value in aggregates.items() if key not in profile and value is not None})
    approx_distinct = int(profile.get("approx_distinct_count") or 0)
    if is_string_trino_type(data_type) and not sensitive and 0 < approx_distinct <= max_top_values:
        top_values = _fetch_dicts(
            f"SELECT {safe_column} AS value, count(*) AS count "
            f"FROM {safe_table} "
            f"WHERE {safe_column} IS NOT NULL "
            f"GROUP BY {safe_column} "
            f"ORDER BY count DESC "
            f"LIMIT {max_top_values}"
        )
        content_sensitive_type = infer_sensitive_type_from_values(row.get("value") for row in top_values)
        if content_sensitive_type is not None:
            profile["sensitive"] = True
            profile["semantic_type"] = content_sensitive_type
            pattern_counts: Counter[str] = Counter()
            for row in top_values:
                value = row.get("value")
                value_type = infer_sensitive_value_type(value) or content_sensitive_type
                pattern_counts[mask_pattern(str(value), value_type)] += int(row.get("count") or 0)
            profile["masked_patterns"] = [
                {"pattern": pattern, "count": count}
                for pattern, count in pattern_counts.most_common(10)
            ]
        else:
            profile["top_values"] = synthetic_category_distribution(
                int(row.get("count") or 0) for row in top_values
            )
    return profile


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
        metrics.extend([f"min({safe_column}) AS min_timestamp", f"max({safe_column}) AS max_timestamp"])
    elif is_date_trino_type(data_type):
        metrics.extend([f"min({safe_column}) AS min_date", f"max({safe_column}) AS max_date"])
    return f"SELECT {', '.join(metrics)} FROM {safe_table}"


def is_numeric_trino_type(data_type: str) -> bool:
    lowered = data_type.lower()
    return any(part in lowered for part in ("int", "decimal", "double", "float", "real"))


def is_timestamp_trino_type(data_type: str) -> bool:
    lowered = data_type.lower()
    return "timestamp" in lowered or "datetime" in lowered


def is_date_trino_type(data_type: str) -> bool:
    return "date" in data_type.lower() and not is_timestamp_trino_type(data_type)


def is_string_trino_type(data_type: str) -> bool:
    lowered = data_type.lower()
    return any(part in lowered for part in ("char", "varchar", "string"))


def profile_foreign_key(
    catalog: str,
    schema: str,
    parent_table: str,
    parent_field: str,
    child_table: str,
    child_field: str,
) -> dict[str, Any]:
    """Profile foreign-key coverage using counts only."""
    check_allowlist(catalog=catalog, schema=schema)
    parent = qualified_table(catalog, schema, parent_table)
    child = qualified_table(catalog, schema, child_table)
    parent_key = quote_identifier(parent_field)
    child_key = quote_identifier(child_field)
    sql = (
        "SELECT "
        "count(*) AS child_row_count, "
        f"count(c.{child_key}) AS checked_count, "
        "count_if(p.parent_key IS NOT NULL) AS matched_count, "
        f"count_if(c.{child_key} IS NOT NULL AND p.parent_key IS NULL) AS orphan_count "
        f"FROM {child} c "
        f"LEFT JOIN (SELECT DISTINCT {parent_key} AS parent_key FROM {parent} WHERE {parent_key} IS NOT NULL) p "
        f"ON c.{child_key} = p.parent_key"
    )
    row = first_row(_fetch_dicts(sql))
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
    catalog: str,
    schema: str,
    table: str,
    start_field: str,
    end_field: str,
    allow_equal: bool = True,
) -> dict[str, Any]:
    """Profile temporal ordering with pass/fail counts only."""
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    start = quote_identifier(start_field)
    end = quote_identifier(end_field)
    operator = "<=" if allow_equal else "<"
    fail_operator = ">" if allow_equal else ">="
    checked_condition = f"{start} IS NOT NULL AND {end} IS NOT NULL"
    sql = (
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({checked_condition}) AS checked_count, "
        f"count_if({checked_condition} AND {start} {operator} {end}) AS passed_count, "
        f"count_if({checked_condition} AND {start} {fail_operator} {end}) AS failed_count "
        f"FROM {safe_table}"
    )
    row = first_row(_fetch_dicts(sql))
    return rule_profile(
        "temporal",
        row,
        checked=int(row.get("checked_count") or 0),
        passed=int(row.get("passed_count") or 0),
        failed=int(row.get("failed_count") or 0),
        metadata={"table": table, "start_field": start_field, "end_field": end_field, "allow_equal": allow_equal},
    )


def profile_formula_rule(
    catalog: str,
    schema: str,
    table: str,
    target_field: str,
    expression: str,
    tolerance: float = 0.000001,
) -> dict[str, Any]:
    """Profile a numeric row formula without returning source values."""
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    safe_target = quote_identifier(target_field)
    formula = build_formula_sql(expression)
    safe_tolerance = require_non_negative_float(tolerance, "tolerance")
    checks = [f"{safe_target} IS NOT NULL"]
    checks.extend(f"{quote_identifier(column)} IS NOT NULL" for column in sorted(formula.columns))
    checks.extend(formula.extra_conditions)
    checked_condition = " AND ".join(checks)
    residual = f"abs(CAST({safe_target} AS double) - CAST(({formula.sql}) AS double))"
    sql = (
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({checked_condition}) AS checked_count, "
        f"count_if({checked_condition} AND {residual} <= {safe_tolerance}) AS passed_count, "
        f"count_if({checked_condition} AND {residual} > {safe_tolerance}) AS failed_count, "
        f"avg(CASE WHEN {checked_condition} THEN {residual} END) AS avg_abs_error, "
        f"max(CASE WHEN {checked_condition} THEN {residual} END) AS max_abs_error "
        f"FROM {safe_table}"
    )
    row = first_row(_fetch_dicts(sql))
    return rule_profile(
        "formula",
        row,
        checked=int(row.get("checked_count") or 0),
        passed=int(row.get("passed_count") or 0),
        failed=int(row.get("failed_count") or 0),
        metadata={"table": table, "target_field": target_field, "expression": expression, "tolerance": safe_tolerance},
    )


def profile_conditional_required(
    catalog: str,
    schema: str,
    table: str,
    condition_field: str,
    condition_equals: Any,
    required_field: str,
) -> dict[str, Any]:
    """Profile conditional requiredness without exposing condition values."""
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    condition_column = quote_identifier(condition_field)
    required_column = quote_identifier(required_field)
    present = present_sql(required_column)
    sql = (
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({condition_column} = ?) AS checked_count, "
        f"count_if({condition_column} = ? AND {present}) AS passed_count, "
        f"count_if({condition_column} = ? AND NOT ({present})) AS failed_count "
        f"FROM {safe_table}"
    )
    row = first_row(_fetch_dicts(sql, [condition_equals, condition_equals, condition_equals]))
    return rule_profile(
        "conditional_required",
        row,
        checked=int(row.get("checked_count") or 0),
        passed=int(row.get("passed_count") or 0),
        failed=int(row.get("failed_count") or 0),
        metadata={"table": table, "condition_field": condition_field, "required_field": required_field},
    )


def profile_conditional_allowed_values(
    catalog: str,
    schema: str,
    table: str,
    condition_field: str,
    condition_equals: Any,
    value_field: str,
    allowed_values: list[Any],
) -> dict[str, Any]:
    """Profile conditional allowed-values consistency with counts only."""
    check_allowlist(catalog=catalog, schema=schema)
    if not allowed_values:
        raise ValueError("allowed_values must not be empty")
    if len(allowed_values) > 50:
        raise ValueError("allowed_values is limited to 50 entries")
    safe_table = qualified_table(catalog, schema, table)
    condition_column = quote_identifier(condition_field)
    value_column = quote_identifier(value_field)
    placeholders = ", ".join("?" for _ in allowed_values)
    sql = (
        "SELECT "
        "count(*) AS row_count, "
        f"count_if({condition_column} = ?) AS checked_count, "
        f"count_if({condition_column} = ? AND {value_column} IN ({placeholders})) AS passed_count, "
        f"count_if({condition_column} = ? AND ({value_column} IS NULL OR {value_column} NOT IN ({placeholders}))) AS failed_count "
        f"FROM {safe_table}"
    )
    parameters = [condition_equals, condition_equals, *allowed_values, condition_equals, *allowed_values]
    row = first_row(_fetch_dicts(sql, parameters))
    return rule_profile(
        "conditional_allowed_values",
        row,
        checked=int(row.get("checked_count") or 0),
        passed=int(row.get("passed_count") or 0),
        failed=int(row.get("failed_count") or 0),
        metadata={"table": table, "condition_field": condition_field, "value_field": value_field},
    )


def profile_aggregate_mapping(
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
    """Profile whether parent aggregate fields match child aggregates."""
    check_allowlist(catalog=catalog, schema=schema)
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
    if aggregate == "count":
        child_aggregate_sql = "count(*)"
    else:
        child_aggregate_sql = (
            f"{aggregate}(CAST({child_value_sql} AS double))"
        )
    expected = "COALESCE(a.aggregate_value, 0.0)"
    residual = f"abs(CAST(p.{parent_value_sql} AS double) - {expected})"
    checked_condition = f"p.{parent_key_sql} IS NOT NULL AND p.{parent_value_sql} IS NOT NULL"
    sql = (
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
    row = first_row(_fetch_dicts(sql))
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


def present_sql(column: str) -> str:
    return f"{column} IS NOT NULL AND CAST({column} AS varchar) <> ''"


def require_non_negative_float(value: float, label: str) -> float:
    number = float(value)
    if number < 0:
        raise ValueError(f"{label} must be non-negative")
    return number


@dataclass(frozen=True)
class FormulaSql:
    sql: str
    columns: frozenset[str]
    extra_conditions: tuple[str, ...] = ()


def build_formula_sql(expression: str) -> FormulaSql:
    try:
        node = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise SqlSafetyError("formula expression is not valid arithmetic") from exc
    columns: set[str] = set()
    extra_conditions: list[str] = []
    sql = formula_node_to_sql(node.body, columns, extra_conditions)
    if not columns:
        raise SqlSafetyError("formula expression must reference at least one column")
    return FormulaSql(sql=sql, columns=frozenset(columns), extra_conditions=tuple(extra_conditions))


def formula_node_to_sql(node: ast.AST, columns: set[str], extra_conditions: list[str]) -> str:
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


def sample_rows_masked(catalog: str, schema: str, table: str, columns: list[str], limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    check_allowlist(catalog=catalog, schema=schema)
    if not columns:
        raise ValueError("at least one column is required")
    safe_limit = bounded_limit(limit)
    select_list = ", ".join(quote_identifier(column) for column in columns)
    rows = _fetch_dicts(f"SELECT {select_list} FROM {qualified_table(catalog, schema, table)} LIMIT {safe_limit}")
    return [mask_row(row) for row in rows]


def run_safe_select(sql: str) -> list[dict[str, Any]]:
    safe_sql = validate_safe_select(sql, require_limit=True)
    rows = _fetch_dicts(safe_sql)
    return [mask_row(row) for row in rows]


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


def trino_mcp_tools() -> list[Callable[..., Any]]:
    tools: list[Callable[..., Any]] = [
        list_catalogs,
        list_schemas,
        list_tables,
        describe_table,
        profile_table,
        profile_column,
        profile_table_safe,
        profile_foreign_key,
        profile_temporal_ordering,
        profile_formula_rule,
        profile_conditional_required,
        profile_conditional_allowed_values,
        profile_aggregate_mapping,
        sample_rows_masked,
    ]
    if parse_env_bool(ENABLE_SAFE_SELECT_ENV):
        tools.append(run_safe_select)
    return tools


mcp: Any = create_trino_mcp(trino_mcp_tools())


def main() -> None:
    missing = []
    if mcp is None:
        missing.append("mcp")
    if sqlglot is None:
        missing.append("sqlglot")
    if trino is None:
        missing.append("trino")
    if missing:
        raise RuntimeError(
            "Trino MCP support is not installed "
            f"(missing: {', '.join(missing)}); "
            "install agent-paranoid-android[mcp,trino]"
        )
    TrinoConfig.from_env()
    audit_logger_from_env("trino-mcp")
    mcp.run()


if __name__ == "__main__":
    main()
