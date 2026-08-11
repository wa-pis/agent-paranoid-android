"""Parameterized PostgreSQL metadata queries constrained by source allowlists."""

from __future__ import annotations

from dataclasses import dataclass

from test_data_agent.postgres_config import PostgresConfig


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
    columns = tuple(
        (schema, table, column)
        for value in sorted(config.allowed_columns)
        for schema, table, column in (value.split(".", maxsplit=2),)
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


def _tuple_placeholders(parts: int, count: int) -> str:
    item = f"({', '.join('%s' for _ in range(parts))})"
    return ", ".join(item for _ in range(count))


def _scalar_placeholders(count: int) -> str:
    return ", ".join("%s" for _ in range(count))


def _flatten(values: tuple[tuple[str, ...], ...]) -> tuple[object, ...]:
    return tuple(item for value in values for item in value)
