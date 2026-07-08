"""Safe Trino MCP tools for schema inspection and profiling.

The public helpers in this module are intentionally small and conservative so
they can be tested without a live Trino cluster.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from test_data_agent.spec import infer_sensitive_from_name

try:  # pragma: no cover - exercised when the MCP dependency is installed.
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None  # type: ignore[assignment]

try:  # pragma: no cover - live Trino is not used in unit tests.
    import trino
except ImportError:  # pragma: no cover
    trino = None  # type: ignore[assignment]


FORBIDDEN_SQL_RE = re.compile(
    r"\b(insert|update|delete|merge|drop|truncate|alter|create|grant|revoke|call|execute)\b",
    re.IGNORECASE,
)
LIMIT_RE = re.compile(r"\blimit\s+\d+\b", re.IGNORECASE)
SELECT_STAR_RE = re.compile(r"\bselect\s+(?:distinct\s+)?(?:[a-zA-Z_][\w$]*\s*\.\s*)?\*", re.IGNORECASE)
TABLE_STAR_RE = re.compile(r"\bselect\b(?:(?!\bfrom\b).)*\b[a-zA-Z_][\w$]*\s*\.\s*\*", re.IGNORECASE | re.DOTALL)
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


class SqlSafetyError(ValueError):
    """Raised when SQL violates the read-only safety policy."""


class AllowlistError(ValueError):
    """Raised when a catalog or schema is outside configured allowlists."""


@dataclass(frozen=True)
class TrinoConfig:
    host: str
    port: int
    user: str
    http_scheme: str
    allowed_catalogs: frozenset[str] | None
    allowed_schemas: frozenset[str] | None

    @classmethod
    def from_env(cls) -> TrinoConfig:
        return cls(
            host=os.environ.get("TRINO_HOST", "localhost"),
            port=int(os.environ.get("TRINO_PORT", "8080")),
            user=os.environ.get("TRINO_USER", "test_data_agent"),
            http_scheme=os.environ.get("TRINO_HTTP_SCHEME", "http"),
            allowed_catalogs=parse_allowlist(os.environ.get("TRINO_ALLOWED_CATALOGS")),
            allowed_schemas=parse_allowlist(os.environ.get("TRINO_ALLOWED_SCHEMAS")),
        )


def parse_allowlist(value: str | None) -> frozenset[str] | None:
    if value is None or not value.strip():
        return None
    return frozenset(item.strip() for item in value.split(",") if item.strip())


def require_identifier(value: str, label: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"invalid {label}: {value!r}")
    return value


def quote_identifier(value: str) -> str:
    return f'"{require_identifier(value, "identifier")}"'


def check_allowlist(catalog: str | None = None, schema: str | None = None, config: TrinoConfig | None = None) -> None:
    config = config or TrinoConfig.from_env()
    if catalog and config.allowed_catalogs is not None and catalog not in config.allowed_catalogs:
        raise AllowlistError(f"catalog is not allowed: {catalog}")
    if schema and config.allowed_schemas is not None and schema not in config.allowed_schemas:
        raise AllowlistError(f"schema is not allowed: {schema}")


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)


def normalize_sql(sql: str) -> str:
    cleaned = strip_sql_comments(sql).strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    if ";" in cleaned:
        raise SqlSafetyError("multiple SQL statements are not allowed")
    return cleaned


def validate_safe_select(sql: str, require_limit: bool = True) -> str:
    cleaned = normalize_sql(sql)
    lowered = cleaned.lower()

    if not (lowered.startswith("select ") or lowered.startswith("with ")):
        raise SqlSafetyError("only SELECT queries are allowed")
    if FORBIDDEN_SQL_RE.search(cleaned):
        raise SqlSafetyError("DDL, DML, and executable statements are not allowed")
    if SELECT_STAR_RE.search(cleaned) or TABLE_STAR_RE.search(cleaned):
        raise SqlSafetyError("unrestricted SELECT * is not allowed")
    if require_limit and not LIMIT_RE.search(cleaned):
        raise SqlSafetyError("row-returning SELECT queries must include LIMIT")
    return cleaned


def mask_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= 2:
        return "*" * len(text)
    return f"{text[0]}***{text[-1]}"


def mask_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: mask_value(value) if infer_sensitive_from_name(key) else value
        for key, value in row.items()
    }


def rows_to_dicts(description: Sequence[Any], rows: Iterable[Sequence[Any]]) -> list[dict[str, Any]]:
    names = [column[0] for column in description]
    return [dict(zip(names, row, strict=True)) for row in rows]


def execute_query(sql: str, parameters: Sequence[Any] | None = None) -> tuple[list[tuple[Any, ...]], list[Any]]:
    if trino is None:
        raise RuntimeError("trino package is not installed")

    config = TrinoConfig.from_env()
    connection = trino.dbapi.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        http_scheme=config.http_scheme,
    )
    cursor = connection.cursor()
    cursor.execute(sql, parameters or [])
    rows = cursor.fetchall()
    return rows, cursor.description or []


def fetch_dicts(sql: str, parameters: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    rows, description = execute_query(sql, parameters)
    return rows_to_dicts(description, rows)


def list_catalogs() -> list[str]:
    rows = fetch_dicts("SHOW CATALOGS")
    allowed = TrinoConfig.from_env().allowed_catalogs
    return [row["Catalog"] for row in rows if allowed is None or row["Catalog"] in allowed]


def list_schemas(catalog: str) -> list[str]:
    check_allowlist(catalog=catalog)
    rows = fetch_dicts(f"SHOW SCHEMAS FROM {quote_identifier(catalog)}")
    allowed = TrinoConfig.from_env().allowed_schemas
    return [row["Schema"] for row in rows if allowed is None or row["Schema"] in allowed]


def list_tables(catalog: str, schema: str) -> list[str]:
    check_allowlist(catalog=catalog, schema=schema)
    rows = fetch_dicts(f"SHOW TABLES FROM {quote_identifier(catalog)}.{quote_identifier(schema)}")
    return [next(iter(row.values())) for row in rows]


def describe_table(catalog: str, schema: str, table: str) -> list[dict[str, Any]]:
    check_allowlist(catalog=catalog, schema=schema)
    sql = (
        "SELECT column_name, data_type, is_nullable "
        "FROM information_schema.columns "
        "WHERE table_catalog = ? AND table_schema = ? AND table_name = ? "
        "ORDER BY ordinal_position"
    )
    return fetch_dicts(sql, [catalog, schema, table])


def profile_table(catalog: str, schema: str, table: str) -> dict[str, Any]:
    check_allowlist(catalog=catalog, schema=schema)
    safe_table = qualified_table(catalog, schema, table)
    rows = fetch_dicts(f"SELECT count(*) AS row_count FROM {safe_table}")
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
    rows = fetch_dicts(sql)
    return rows[0] if rows else {"row_count": 0, "non_null_count": 0, "approx_distinct_count": 0}


def sample_rows_masked(catalog: str, schema: str, table: str, columns: list[str], limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    check_allowlist(catalog=catalog, schema=schema)
    if not columns:
        raise ValueError("at least one column is required")
    safe_limit = bounded_limit(limit)
    select_list = ", ".join(quote_identifier(column) for column in columns)
    rows = fetch_dicts(f"SELECT {select_list} FROM {qualified_table(catalog, schema, table)} LIMIT {safe_limit}")
    return [mask_row(row) for row in rows]


def run_safe_select(sql: str) -> list[dict[str, Any]]:
    safe_sql = validate_safe_select(sql, require_limit=True)
    rows = fetch_dicts(safe_sql)
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


if FastMCP is not None:
    mcp = FastMCP("test-data-agent-trino")
    mcp.tool()(list_catalogs)
    mcp.tool()(list_schemas)
    mcp.tool()(list_tables)
    mcp.tool()(describe_table)
    mcp.tool()(profile_table)
    mcp.tool()(profile_column)
    mcp.tool()(sample_rows_masked)
    mcp.tool()(run_safe_select)
else:  # pragma: no cover
    mcp = None


def main() -> None:
    if mcp is None:
        raise RuntimeError("mcp package is not installed")
    mcp.run()


if __name__ == "__main__":
    main()
