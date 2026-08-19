"""Strict local SQL-query source parsing and authorization."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional database extra.
    import sqlglot
    from sqlglot import exp
except ImportError:  # pragma: no cover
    sqlglot = None  # type: ignore[assignment]
    exp = None  # type: ignore[assignment]


QUERY_SOURCE_POLICY_VERSION = "1.0"
DEFAULT_MAX_QUERY_BYTES = 64 * 1024
DEFAULT_MAX_AST_NODES = 500
DEFAULT_MAX_AST_DEPTH = 32
DEFAULT_MAX_PROJECTED_COLUMNS = 100
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SqlQuerySourceError(ValueError):
    """A source-free query policy rejection."""


class SqlQueryAdapter(StrEnum):
    POSTGRES = "postgres"
    TRINO = "trino"


@dataclass(frozen=True, slots=True)
class SqlQueryProfileLimits:
    max_query_bytes: int = DEFAULT_MAX_QUERY_BYTES
    max_ast_nodes: int = DEFAULT_MAX_AST_NODES
    max_ast_depth: int = DEFAULT_MAX_AST_DEPTH
    max_projected_columns: int = DEFAULT_MAX_PROJECTED_COLUMNS

    @classmethod
    def from_env(cls) -> SqlQueryProfileLimits:
        limits = cls(
            max_query_bytes=_positive_int_env(
                "SQL_QUERY_MAX_BYTES", DEFAULT_MAX_QUERY_BYTES
            ),
            max_ast_nodes=_positive_int_env(
                "SQL_QUERY_MAX_AST_NODES", DEFAULT_MAX_AST_NODES
            ),
            max_ast_depth=_positive_int_env(
                "SQL_QUERY_MAX_AST_DEPTH", DEFAULT_MAX_AST_DEPTH
            ),
            max_projected_columns=_positive_int_env(
                "SQL_QUERY_MAX_PROJECTED_COLUMNS",
                DEFAULT_MAX_PROJECTED_COLUMNS,
            ),
        )
        limits.validate()
        return limits

    def validate(self) -> None:
        for name, value, maximum in (
            ("query bytes", self.max_query_bytes, 1024 * 1024),
            ("AST nodes", self.max_ast_nodes, 10_000),
            ("AST depth", self.max_ast_depth, 100),
            ("projected columns", self.max_projected_columns, 1_000),
        ):
            if not 1 <= value <= maximum:
                raise SqlQuerySourceError(f"SQL query {name} budget is invalid")


@dataclass(frozen=True, slots=True)
class SqlQueryProfileRequest:
    adapter: SqlQueryAdapter
    source_id: str
    entity: str
    query_file: Path = field(repr=False)
    limits: SqlQueryProfileLimits = field(default_factory=SqlQueryProfileLimits)

    @property
    def entity_name(self) -> str:
        return f"{self.source_id}.{self.entity}"

    def validate(self) -> None:
        if not _IDENTIFIER_RE.fullmatch(self.source_id):
            raise SqlQuerySourceError("SQL query source id is invalid")
        if not _IDENTIFIER_RE.fullmatch(self.entity):
            raise SqlQuerySourceError("SQL query entity is invalid")
        self.limits.validate()


@dataclass(frozen=True, slots=True)
class QuerySourceDraft:
    request: SqlQueryProfileRequest
    table_parts: tuple[str, ...]
    table_alias: str
    statement: Any = field(repr=False, compare=False)

    @property
    def table_name(self) -> str:
        return ".".join(self.table_parts)


@dataclass(frozen=True, slots=True)
class QuerySourceColumn:
    name: str
    data_type: str
    nullable: bool


@dataclass(frozen=True, slots=True)
class ValidatedSqlQuery:
    adapter: SqlQueryAdapter
    source_id: str
    entity_name: str
    table_parts: tuple[str, ...]
    output_fields: tuple[str, ...]
    fingerprint: str
    sql: str = field(repr=False, compare=False)


_ALLOWED_NODE_NAMES = frozenset(
    {
        "Abs",
        "Add",
        "Alias",
        "And",
        "Between",
        "Boolean",
        "Cast",
        "Coalesce",
        "Column",
        "DataType",
        "DataTypeParam",
        "Div",
        "EQ",
        "From",
        "GT",
        "GTE",
        "ILike",
        "Identifier",
        "In",
        "Is",
        "LE",
        "LT",
        "Like",
        "Literal",
        "Lower",
        "Mod",
        "Mul",
        "NEQ",
        "Neg",
        "Not",
        "Null",
        "Or",
        "Paren",
        "Round",
        "Select",
        "Star",
        "Sub",
        "Table",
        "TableAlias",
        "Trim",
        "Upper",
        "Where",
    }
)
_ALLOWED_FUNCTIONS = frozenset(
    {"ABS", "CAST", "COALESCE", "LOWER", "ROUND", "TRIM", "UPPER"}
)


def inspect_query_source(request: SqlQueryProfileRequest) -> QuerySourceDraft:
    """Read and structurally validate one local query before database access."""

    request.validate()
    query_text = _read_stable_query_file(
        request.query_file,
        max_bytes=request.limits.max_query_bytes,
    )
    if sqlglot is None or exp is None:
        raise SqlQuerySourceError("SQL query parser is unavailable")
    dialect = "postgres" if request.adapter is SqlQueryAdapter.POSTGRES else "trino"
    try:
        statements = sqlglot.parse(query_text, read=dialect)
    except Exception:
        raise SqlQuerySourceError("SQL query syntax is invalid") from None
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise SqlQuerySourceError("SQL query must contain exactly one SELECT")
    statement = statements[0]
    nodes = tuple(statement.walk())
    if len(nodes) > request.limits.max_ast_nodes:
        raise SqlQuerySourceError("SQL query AST node budget exceeded")
    if _ast_depth(statement) > request.limits.max_ast_depth:
        raise SqlQuerySourceError("SQL query AST depth budget exceeded")
    if any(getattr(node, "comments", None) for node in nodes):
        raise SqlQuerySourceError("SQL query comments are not allowed")
    if any(type(node).__name__ not in _ALLOWED_NODE_NAMES for node in nodes):
        raise SqlQuerySourceError("SQL query contains a forbidden operation")
    for node in nodes:
        if isinstance(node, exp.Func) and node.sql_name().upper() not in _ALLOWED_FUNCTIONS:
            raise SqlQuerySourceError("SQL query contains a forbidden function")
    tables = tuple(statement.find_all(exp.Table))
    if len(tables) != 1:
        raise SqlQuerySourceError("SQL query must reference exactly one table")
    table = tables[0]
    table_parts = _table_parts(table, request.adapter)
    alias = table.alias_or_name
    if not _IDENTIFIER_RE.fullmatch(alias):
        raise SqlQuerySourceError("SQL query table alias is invalid")
    if len(statement.expressions) > request.limits.max_projected_columns:
        raise SqlQuerySourceError("SQL query projected-column budget exceeded")
    if not statement.expressions:
        raise SqlQuerySourceError("SQL query must project at least one field")
    return QuerySourceDraft(
        request=request,
        table_parts=table_parts,
        table_alias=alias,
        statement=statement,
    )


def authorize_query_source(
    draft: QuerySourceDraft,
    columns: tuple[QuerySourceColumn, ...],
) -> ValidatedSqlQuery:
    """Authorize every source column and expand stars to explicit projections."""

    if exp is None:
        raise SqlQuerySourceError("SQL query parser is unavailable")
    metadata = {column.name: column for column in columns}
    if not metadata or len(metadata) != len(columns):
        raise SqlQuerySourceError("SQL query source metadata is invalid")
    for column in columns:
        if not _IDENTIFIER_RE.fullmatch(column.name) or not column.data_type.strip():
            raise SqlQuerySourceError("SQL query source metadata is invalid")

    statement = draft.statement.copy()
    projections: list[Any] = []
    for projection in statement.expressions:
        if _is_star_projection(projection):
            if (
                isinstance(projection, exp.Column)
                and projection.table != draft.table_alias
            ):
                raise SqlQuerySourceError(
                    "SQL query wildcard qualification is invalid"
                )
            for name in sorted(metadata):
                projections.append(exp.column(name, table=draft.table_alias))
            continue
        projections.append(projection)
    if len(projections) > draft.request.limits.max_projected_columns:
        raise SqlQuerySourceError("SQL query projected-column budget exceeded")
    statement.set("expressions", projections)

    for column in statement.find_all(exp.Column):
        if isinstance(column.this, exp.Star):
            raise SqlQuerySourceError("SQL query wildcard expansion failed")
        if column.db or column.catalog:
            raise SqlQuerySourceError("SQL query column qualification is invalid")
        if column.table and column.table != draft.table_alias:
            raise SqlQuerySourceError("SQL query column qualification is invalid")
        if column.name not in metadata:
            raise SqlQuerySourceError("SQL query references an unauthorized column")

    output_fields = tuple(_projection_name(item) for item in statement.expressions)
    if len(output_fields) != len(set(output_fields)):
        raise SqlQuerySourceError("SQL query output field names must be unique")
    dialect = "postgres" if draft.request.adapter is SqlQueryAdapter.POSTGRES else "trino"
    canonical_sql = statement.sql(dialect=dialect, pretty=False)
    fingerprint = hashlib.sha256(
        (
            f"{QUERY_SOURCE_POLICY_VERSION}\n{draft.request.adapter.value}\n"
            f"{canonical_sql}"
        ).encode("utf-8")
    ).hexdigest()
    return ValidatedSqlQuery(
        adapter=draft.request.adapter,
        source_id=draft.request.source_id,
        entity_name=draft.request.entity_name,
        table_parts=draft.table_parts,
        output_fields=output_fields,
        fingerprint=fingerprint,
        sql=canonical_sql,
    )


def _read_stable_query_file(path: Path, *, max_bytes: int) -> str:
    try:
        with path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise SqlQuerySourceError("SQL query input must be a regular file")
            payload = handle.read(max_bytes + 1)
            after = os.fstat(handle.fileno())
    except SqlQuerySourceError:
        raise
    except OSError:
        raise SqlQuerySourceError("SQL query file could not be read") from None
    if len(payload) > max_bytes or before.st_size > max_bytes:
        raise SqlQuerySourceError("SQL query file exceeds its byte budget")
    if (
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise SqlQuerySourceError("SQL query file changed while being read")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        raise SqlQuerySourceError("SQL query file must be UTF-8") from None
    if not text.strip():
        raise SqlQuerySourceError("SQL query file is empty")
    return text


def _table_parts(table: Any, adapter: SqlQueryAdapter) -> tuple[str, ...]:
    raw = (table.catalog, table.db, table.name)
    parts = tuple(part for part in raw if part)
    expected = 2 if adapter is SqlQueryAdapter.POSTGRES else 3
    if len(parts) != expected or any(not _IDENTIFIER_RE.fullmatch(part) for part in parts):
        raise SqlQuerySourceError("SQL query table must be fully qualified")
    return parts


def _projection_name(projection: Any) -> str:
    if isinstance(projection, exp.Column):
        name = projection.name
    elif isinstance(projection, exp.Alias):
        name = projection.alias
    else:
        raise SqlQuerySourceError("SQL query expressions require explicit aliases")
    if not _IDENTIFIER_RE.fullmatch(name):
        raise SqlQuerySourceError("SQL query output field name is invalid")
    return name


def _is_star_projection(projection: Any) -> bool:
    return isinstance(projection, exp.Star) or (
        isinstance(projection, exp.Column) and isinstance(projection.this, exp.Star)
    )


def _ast_depth(root: Any) -> int:
    maximum = 0
    pending = [(root, 1)]
    while pending:
        node, depth = pending.pop()
        maximum = max(maximum, depth)
        pending.extend((child, depth + 1) for child in node.iter_expressions())
    return maximum


def _positive_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise SqlQuerySourceError(f"{name} must be an integer") from None
    if value <= 0:
        raise SqlQuerySourceError(f"{name} must be positive")
    return value


__all__ = [
    "QUERY_SOURCE_POLICY_VERSION",
    "QuerySourceColumn",
    "QuerySourceDraft",
    "SqlQueryAdapter",
    "SqlQueryProfileLimits",
    "SqlQueryProfileRequest",
    "SqlQuerySourceError",
    "ValidatedSqlQuery",
    "authorize_query_source",
    "inspect_query_source",
]
