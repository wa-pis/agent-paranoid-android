"""PostgreSQL metadata and aggregate queries constrained by source allowlists."""

from __future__ import annotations

from dataclasses import dataclass

from test_data_agent.core.privacy import LocalCategoryField, infer_sensitive_from_name
from test_data_agent.postgres_config import (
    PostgresConfig,
    parse_postgres_column_selector,
)


class PostgresScopeError(ValueError):
    """Raised when a metadata query would exceed the configured source scope."""


@dataclass(frozen=True)
class PostgresQuery:
    """A parameterized PostgreSQL query that has not been executed."""

    sql: str
    parameters: tuple[object, ...] = ()


def build_list_tables_query(config: PostgresConfig) -> PostgresQuery:
    tables = _allowed_tables(config)
    return PostgresQuery(
        "SELECT n.nspname AS table_schema, c.relname AS table_name "
        "FROM pg_catalog.pg_class AS c "
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
        "WHERE c.relkind IN ('r', 'p') "
        f"AND (n.nspname, c.relname) IN ({_tuple_placeholders(2, len(tables))}) "
        "ORDER BY n.nspname, c.relname",
        _flatten(tables),
    )


def build_columns_query(
    config: PostgresConfig,
    schema: str,
    table: str,
) -> PostgresQuery:
    columns = _allowed_columns_for_table(config, schema, table)
    return PostgresQuery(
        "SELECT a.attname AS column_name, "
        "pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type, "
        "NOT a.attnotnull AS is_nullable, a.attnum AS ordinal_position "
        "FROM pg_catalog.pg_attribute AS a "
        "JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid "
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relname = %s "
        "AND c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped "
        f"AND a.attname IN ({_scalar_placeholders(len(columns))}) "
        "ORDER BY a.attnum",
        (schema, table, *columns),
    )


def build_column_discovery_query(
    config: PostgresConfig,
    schema: str,
    table: str,
) -> PostgresQuery:
    """Discover names only for one explicitly wildcard-authorized table."""

    qualified_table = f"{schema}.{table}"
    if qualified_table not in config.allowed_tables:
        raise PostgresScopeError("PostgreSQL table is outside the allowlist")
    wildcard = f"{qualified_table}.*"
    if wildcard not in config.allowed_columns:
        raise PostgresScopeError(
            "PostgreSQL table does not have a qualified column wildcard"
        )
    return PostgresQuery(
        "SELECT a.attname AS column_name "
        "FROM pg_catalog.pg_attribute AS a "
        "JOIN pg_catalog.pg_class AS c ON c.oid = a.attrelid "
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relname = %s "
        "AND c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped "
        "ORDER BY a.attname LIMIT %s",
        (schema, table, config.limits.max_columns + 1),
    )


def build_primary_keys_query(
    config: PostgresConfig,
    schema: str,
    table: str,
) -> PostgresQuery:
    columns = _allowed_columns_for_table(config, schema, table)
    return PostgresQuery(
        "SELECT con.conname AS constraint_name, a.attname AS column_name, "
        "key.position AS ordinal_position "
        "FROM pg_catalog.pg_constraint AS con "
        "JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid "
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
        "JOIN LATERAL unnest(con.conkey) WITH ORDINALITY "
        "AS key(attnum, position) ON TRUE "
        "JOIN pg_catalog.pg_attribute AS a "
        "ON a.attrelid = c.oid AND a.attnum = key.attnum "
        "WHERE con.contype = 'p' AND n.nspname = %s AND c.relname = %s "
        f"AND a.attname IN ({_scalar_placeholders(len(columns))}) "
        "ORDER BY con.conname, key.position",
        (schema, table, *columns),
    )


def build_foreign_keys_query(config: PostgresConfig) -> PostgresQuery:
    columns = _allowed_columns(config)
    column_filter = _tuple_placeholders(3, len(columns))
    parameters = _flatten(columns)
    return PostgresQuery(
        "SELECT con.conname AS constraint_name, "
        "child_ns.nspname AS table_schema, child.relname AS table_name, "
        "child_att.attname AS column_name, "
        "parent_ns.nspname AS referenced_table_schema, "
        "parent.relname AS referenced_table_name, "
        "parent_att.attname AS referenced_column_name, "
        "key.position AS ordinal_position "
        "FROM pg_catalog.pg_constraint AS con "
        "JOIN pg_catalog.pg_class AS child ON child.oid = con.conrelid "
        "JOIN pg_catalog.pg_namespace AS child_ns "
        "ON child_ns.oid = child.relnamespace "
        "JOIN pg_catalog.pg_class AS parent ON parent.oid = con.confrelid "
        "JOIN pg_catalog.pg_namespace AS parent_ns "
        "ON parent_ns.oid = parent.relnamespace "
        "JOIN LATERAL unnest(con.conkey, con.confkey) WITH ORDINALITY "
        "AS key(child_attnum, parent_attnum, position) ON TRUE "
        "JOIN pg_catalog.pg_attribute AS child_att "
        "ON child_att.attrelid = child.oid "
        "AND child_att.attnum = key.child_attnum "
        "JOIN pg_catalog.pg_attribute AS parent_att "
        "ON parent_att.attrelid = parent.oid "
        "AND parent_att.attnum = key.parent_attnum "
        "WHERE con.contype = 'f' "
        f"AND (child_ns.nspname, child.relname, child_att.attname) IN ({column_filter}) "
        f"AND (parent_ns.nspname, parent.relname, parent_att.attname) IN ({column_filter}) "
        "ORDER BY child_ns.nspname, child.relname, con.conname, key.position",
        (*parameters, *parameters),
    )


def build_check_constraints_query(config: PostgresConfig) -> PostgresQuery:
    tables = _allowed_tables(config)
    return PostgresQuery(
        "SELECT n.nspname AS table_schema, c.relname AS table_name, "
        "con.conname AS constraint_name, "
        "pg_catalog.pg_get_expr(con.conbin, con.conrelid, TRUE) AS expression "
        "FROM pg_catalog.pg_constraint AS con "
        "JOIN pg_catalog.pg_class AS c ON c.oid = con.conrelid "
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace "
        "WHERE con.contype = 'c' "
        f"AND (n.nspname, c.relname) IN ({_tuple_placeholders(2, len(tables))}) "
        "ORDER BY n.nspname, c.relname, con.conname",
        _flatten(tables),
    )


def build_table_row_count_query(
    config: PostgresConfig,
    schema: str,
    table: str,
) -> PostgresQuery:
    safe_table = _qualified_table(config, schema, table)
    return PostgresQuery(f"SELECT count(*) AS row_count FROM {safe_table}")


def build_column_summary_query(
    config: PostgresConfig,
    schema: str,
    table: str,
    column: str,
) -> PostgresQuery:
    safe_table, safe_column = _qualified_column(config, schema, table, column)
    return PostgresQuery(
        f"SELECT count(*) AS row_count, count({safe_column}) AS non_null_count, "
        f"count(DISTINCT {safe_column}) AS distinct_count FROM {safe_table}"
    )


def build_numeric_shape_query(
    config: PostgresConfig,
    schema: str,
    table: str,
    column: str,
) -> PostgresQuery:
    safe_table, safe_column = _qualified_column(config, schema, table, column)
    magnitude = f"floor(log(10, abs(CAST({safe_column} AS numeric))))::integer"
    return PostgresQuery(
        f"SELECT count(*) AS row_count, count({safe_column}) AS non_null_count, "
        f"count(DISTINCT {safe_column}) AS distinct_count, "
        f"bool_or({safe_column} < 0) AS has_negative, "
        f"bool_or({safe_column} > 0) AS has_positive, "
        f"max(CASE WHEN {safe_column} = 0 THEN NULL ELSE {magnitude} END) "
        f"AS max_abs_magnitude FROM {safe_table}"
    )


def build_local_category_candidates_query(
    config: PostgresConfig,
    field: LocalCategoryField,
    *,
    max_categories: int = 20,
) -> PostgresQuery:
    matches = [
        (schema, table, column)
        for schema, table, column in _allowed_columns(config)
        if field.entity == f"{config.source_id}.{schema}.{table}"
        and field.field == column
    ]
    if len(matches) != 1:
        raise PostgresScopeError(
            "PostgreSQL local category field is outside the qualified allowlist"
        )
    schema, table, column = matches[0]
    if infer_sensitive_from_name(column):
        raise PostgresScopeError(
            "PostgreSQL local category field has a sensitive identifier"
        )
    if max_categories < 1:
        raise PostgresScopeError("PostgreSQL category limit must be positive")
    candidate_limit = max_categories + 1
    if candidate_limit > config.limits.max_result_rows:
        raise PostgresScopeError(
            "PostgreSQL category limit exceeds the result row budget"
        )
    safe_table, safe_column = _qualified_column(config, schema, table, column)
    return PostgresQuery(
        f"SELECT {safe_column} AS value, count(*) AS count FROM {safe_table} "
        f"WHERE {safe_column} IS NOT NULL GROUP BY {safe_column} "
        "ORDER BY count DESC, value ASC LIMIT %s",
        (candidate_limit,),
    )


def build_foreign_key_coverage_query(
    config: PostgresConfig,
    *,
    parent_schema: str,
    parent_table: str,
    parent_column: str,
    child_schema: str,
    child_table: str,
    child_column: str,
) -> PostgresQuery:
    parent, parent_key = _qualified_column(
        config, parent_schema, parent_table, parent_column
    )
    child, child_key = _qualified_column(
        config, child_schema, child_table, child_column
    )
    return PostgresQuery(
        "SELECT count(*) AS child_row_count, "
        f"count(c.{child_key}) AS checked_count, "
        "count(p.parent_key) AS matched_count, "
        f"count(*) FILTER (WHERE c.{child_key} IS NOT NULL "
        "AND p.parent_key IS NULL) AS orphan_count "
        f"FROM {child} AS c LEFT JOIN "
        f"(SELECT DISTINCT {parent_key} AS parent_key FROM {parent} "
        f"WHERE {parent_key} IS NOT NULL) AS p "
        f"ON c.{child_key} = p.parent_key"
    )


def _allowed_tables(config: PostgresConfig) -> tuple[tuple[str, str], ...]:
    config.validate()
    tables = tuple(
        (schema, table)
        for value in sorted(config.allowed_tables)
        for schema, table in (value.split(".", maxsplit=1),)
    )
    if len(tables) > config.limits.max_tables:
        raise PostgresScopeError("PostgreSQL table allowlist exceeds its budget")
    return tables


def _allowed_columns(
    config: PostgresConfig,
) -> tuple[tuple[str, str, str], ...]:
    _allowed_tables(config)
    configured_columns = (
        config.resolved_columns
        if config.resolved_columns is not None
        else config.allowed_columns
    )
    selectors = tuple(
        parse_postgres_column_selector(value) for value in sorted(configured_columns)
    )
    if any(selector.is_wildcard for selector in selectors):
        raise PostgresScopeError(
            "PostgreSQL column wildcard must be expanded before query construction"
        )
    columns = tuple(
        (selector.schema, selector.table, selector.column)
        for selector in selectors
        if selector.column is not None
    )
    if len(columns) > config.limits.max_columns:
        raise PostgresScopeError("PostgreSQL column allowlist exceeds its budget")
    return columns


def _allowed_columns_for_table(
    config: PostgresConfig,
    schema: str,
    table: str,
) -> tuple[str, ...]:
    qualified_table = f"{schema}.{table}"
    if qualified_table not in config.allowed_tables:
        raise PostgresScopeError("PostgreSQL table is outside the allowlist")
    columns = tuple(
        column
        for column_schema, column_table, column in _allowed_columns(config)
        if column_schema == schema and column_table == table
    )
    if not columns:
        raise PostgresScopeError("PostgreSQL table has no allowed columns")
    return columns


def _qualified_table(config: PostgresConfig, schema: str, table: str) -> str:
    _allowed_columns_for_table(config, schema, table)
    return f"{_quote_identifier(schema)}.{_quote_identifier(table)}"


def _qualified_column(
    config: PostgresConfig,
    schema: str,
    table: str,
    column: str,
) -> tuple[str, str]:
    if (schema, table, column) not in _allowed_columns(config):
        raise PostgresScopeError("PostgreSQL column is outside the allowlist")
    return _qualified_table(config, schema, table), _quote_identifier(column)


def _quote_identifier(value: str) -> str:
    return f'"{value}"'


def _tuple_placeholders(parts: int, count: int) -> str:
    item = f"({', '.join('%s' for _ in range(parts))})"
    return ", ".join(item for _ in range(count))


def _scalar_placeholders(count: int) -> str:
    return ", ".join("%s" for _ in range(count))


def _flatten(values: tuple[tuple[str, ...], ...]) -> tuple[object, ...]:
    return tuple(item for value in values for item in value)
