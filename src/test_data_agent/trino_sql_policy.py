"""Pure read-only SQL and allowlist policy for Trino operations."""

from __future__ import annotations

import re

try:  # pragma: no cover - optional Trino support.
    import sqlglot as sqlglot
    from sqlglot import exp as exp
except ImportError:  # pragma: no cover
    sqlglot = None  # type: ignore[assignment]
    exp = None  # type: ignore[assignment]

from test_data_agent.core.privacy import infer_sensitive_from_name
from test_data_agent.trino_config import TrinoConfig

FORBIDDEN_SQL_RE = re.compile(
    r"\b(insert|update|delete|merge|drop|truncate|alter|create|grant|revoke|call|execute)\b",
    re.IGNORECASE,
)
LIMIT_RE = re.compile(r"\blimit\s+\d+\b", re.IGNORECASE)
SELECT_STAR_RE = re.compile(
    r"\bselect\s+(?:distinct\s+)?(?:[a-zA-Z_][\w$]*\s*\.\s*)?\*",
    re.IGNORECASE,
)
TABLE_STAR_RE = re.compile(
    r"\bselect\b(?:(?!\bfrom\b).)*\b[a-zA-Z_][\w$]*\s*\.\s*\*",
    re.IGNORECASE | re.DOTALL,
)
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_LIMIT = 1000


class SqlSafetyError(ValueError):
    """Raised when SQL violates the read-only safety policy."""


class AllowlistError(ValueError):
    """Raised when a catalog or schema is outside configured allowlists."""


def require_identifier(value: str, label: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"invalid {label}: {value!r}")
    return value


def quote_identifier(value: str) -> str:
    return f'"{require_identifier(value, "identifier")}"'


def check_allowlist(
    catalog: str | None = None,
    schema: str | None = None,
    config: TrinoConfig | None = None,
) -> None:
    config = config or TrinoConfig.from_env()
    config.validate_security()
    if (
        catalog
        and config.allowed_catalogs is not None
        and catalog not in config.allowed_catalogs
    ):
        raise AllowlistError(f"catalog is not allowed: {catalog}")
    if schema and config.allowed_schemas is not None and schema not in config.allowed_schemas:
        raise AllowlistError(f"schema is not allowed: {schema}")


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)


def normalize_sql(sql: str) -> str:
    cleaned = strip_sql_comments(sql).strip()
    semicolon_positions = unquoted_char_positions(cleaned, ";")
    if len(semicolon_positions) > 1:
        raise SqlSafetyError("multiple SQL statements are not allowed")
    if semicolon_positions:
        semicolon = semicolon_positions[0]
        if cleaned[semicolon + 1 :].strip():
            raise SqlSafetyError("multiple SQL statements are not allowed")
        cleaned = cleaned[:semicolon].strip()
    if not cleaned:
        raise SqlSafetyError("empty SQL is not allowed")
    return cleaned


def validate_safe_select(
    sql: str,
    require_limit: bool = True,
    config: TrinoConfig | None = None,
) -> str:
    cleaned = normalize_sql(sql)
    if FORBIDDEN_SQL_RE.search(cleaned):
        raise SqlSafetyError("DDL, DML, and executable statements are not allowed")
    tree = parse_select_ast(cleaned)
    validate_safe_select_shape(tree)
    if has_unrestricted_projection_star(tree):
        raise SqlSafetyError("unrestricted SELECT * is not allowed")
    if selected_sensitive_identifier_names(tree):
        raise SqlSafetyError("SELECT queries must not project likely PII fields")
    if require_limit:
        limit = top_level_limit_value(tree)
        if limit is None:
            raise SqlSafetyError("row-returning SELECT queries must include LIMIT")
        if limit < 1 or limit > MAX_LIMIT:
            raise SqlSafetyError(
                f"row-returning SELECT queries must use LIMIT between 1 and {MAX_LIMIT}"
            )
    validate_table_references_allowed(tree, config=config)
    return cleaned


def validate_safe_select_shape(tree: exp.Expression) -> None:
    """Reject query shapes whose result LIMIT does not bound database work."""
    if tree.find(exp.Join) or tree.find(exp.CTE) or tree.find(exp.Subquery):
        raise SqlSafetyError("joins, CTEs, and subqueries are not allowed")
    if tree.find(exp.Order):
        raise SqlSafetyError("ORDER BY is not allowed in generic safe SELECT queries")
    if tree.find(exp.UDTF) or tree.find(exp.TableFromRows) or tree.find(exp.Unnest):
        raise SqlSafetyError("table functions and UNNEST are not allowed")


def parse_select_ast(sql: str) -> exp.Expression:
    if sqlglot is None or exp is None:
        raise RuntimeError(
            "Trino support is not installed; "
            "install agent-paranoid-android[trino]"
        )
    try:
        statements = sqlglot.parse(sql, read="trino")
    except sqlglot.errors.ParseError as exc:
        raise SqlSafetyError(f"invalid SQL: {exc}") from exc
    if len(statements) != 1:
        raise SqlSafetyError("exactly one SQL statement is allowed")
    tree = statements[0]
    if not isinstance(tree, exp.Select):
        raise SqlSafetyError("only SELECT queries are allowed")
    return tree


def unquoted_char_positions(sql: str, char: str) -> list[int]:
    positions: list[int] = []
    quote: str | None = None
    index = 0
    while index < len(sql):
        current = sql[index]
        if quote:
            if current == quote:
                if quote == "'" and index + 1 < len(sql) and sql[index + 1] == "'":
                    index += 2
                    continue
                quote = None
        elif current in {"'", '"'}:
            quote = current
        elif current == char:
            positions.append(index)
        index += 1
    return positions


def has_top_level_limit(sql_or_tree: str | exp.Expression) -> bool:
    return top_level_limit_value(sql_or_tree) is not None


def top_level_limit_value(sql_or_tree: str | exp.Expression) -> int | None:
    tree = (
        parse_select_ast(normalize_sql(sql_or_tree))
        if isinstance(sql_or_tree, str)
        else sql_or_tree
    )
    limit = tree.args.get("limit")
    if limit is None:
        return None
    expression = limit.expression
    if not isinstance(expression, exp.Literal) or not expression.is_int:
        return None
    return int(expression.this)


def validate_table_references_allowed(
    sql_or_tree: str | exp.Expression,
    config: TrinoConfig | None = None,
) -> None:
    config = config or TrinoConfig.from_env()
    config.validate_security()
    tree = (
        parse_select_ast(normalize_sql(sql_or_tree))
        if isinstance(sql_or_tree, str)
        else sql_or_tree
    )
    references = extract_table_references(tree)
    if not references:
        return
    for parts in references:
        if config.allowed_catalogs is not None or config.allowed_schemas is not None:
            if len(parts) != 3:
                raise AllowlistError(
                    "queries must use fully qualified catalog.schema.table references"
                )
        catalog = parts[0] if len(parts) == 3 else None
        schema = parts[1] if len(parts) == 3 else (parts[0] if len(parts) == 2 else None)
        check_allowlist(catalog=catalog, schema=schema, config=config)


def extract_table_references(tree: exp.Expression) -> list[tuple[str, ...]]:
    cte_aliases = {cte.alias for cte in tree.find_all(exp.CTE) if cte.alias}
    references: list[tuple[str, ...]] = []
    for table in tree.find_all(exp.Table):
        parts = tuple(part.name for part in table.parts)
        if not parts or parts[-1] in cte_aliases:
            continue
        references.append(parts)
    return references


def selected_sensitive_identifier_names(tree: exp.Expression) -> set[str]:
    sensitive: set[str] = set()
    for node in tree.walk():
        if not isinstance(node, exp.Select):
            continue
        for projection in node.expressions:
            alias = projection.alias
            if alias and infer_sensitive_from_name(alias):
                sensitive.add(alias)
            for column in projection.find_all(exp.Column):
                if is_star_column(column):
                    continue
                name = column.name
                if name and infer_sensitive_from_name(name):
                    sensitive.add(name)
    return sensitive


def has_unrestricted_projection_star(tree: exp.Expression) -> bool:
    return any(
        isinstance(projection, exp.Star) or is_star_column(projection)
        for projection in tree.expressions
    )


def is_star_column(expression: exp.Expression) -> bool:
    return isinstance(expression, exp.Column) and isinstance(expression.this, exp.Star)
