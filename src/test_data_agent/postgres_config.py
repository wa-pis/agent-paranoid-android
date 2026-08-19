"""Validated PostgreSQL connection scope and profiling budgets."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from urllib.parse import parse_qsl, unquote, urlsplit


DEFAULT_POSTGRES_PORT = 5432
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresConfigurationError(ValueError):
    """Raised when PostgreSQL access is not explicitly bounded."""


@dataclass(frozen=True)
class PostgresJdbcEndpoint:
    host: str
    port: int | None
    database: str
    sslmode: str | None


@dataclass(frozen=True, slots=True)
class PostgresColumnSelector:
    schema: str
    table: str
    column: str | None

    @property
    def is_wildcard(self) -> bool:
        return self.column is None

    @property
    def table_name(self) -> str:
        return f"{self.schema}.{self.table}"

    @property
    def qualified_name(self) -> str:
        column = "*" if self.column is None else self.column
        return f"{self.table_name}.{column}"


@dataclass(frozen=True)
class PostgresProfileLimits:
    max_tables: int = 100
    max_columns: int = 1_000
    max_statements: int = 1_500
    max_result_rows: int = 10_000
    max_result_cells: int = 100_000
    max_seconds: float = 120.0

    @classmethod
    def from_env(cls) -> PostgresProfileLimits:
        limits = cls(
            max_tables=_positive_int_env("POSTGRES_MAX_TABLES", 100),
            max_columns=_positive_int_env("POSTGRES_MAX_COLUMNS", 1_000),
            max_statements=_positive_int_env("POSTGRES_MAX_STATEMENTS", 1_500),
            max_result_rows=_positive_int_env("POSTGRES_MAX_RESULT_ROWS", 10_000),
            max_result_cells=_positive_int_env("POSTGRES_MAX_RESULT_CELLS", 100_000),
            max_seconds=_positive_float_env("POSTGRES_MAX_SECONDS", 120.0),
        )
        limits.validate()
        return limits

    def validate(self) -> None:
        _bounded_positive("POSTGRES_MAX_TABLES", self.max_tables, 1_000)
        _bounded_positive("POSTGRES_MAX_COLUMNS", self.max_columns, 10_000)
        _bounded_positive("POSTGRES_MAX_STATEMENTS", self.max_statements, 100_000)
        _bounded_positive("POSTGRES_MAX_RESULT_ROWS", self.max_result_rows, 100_000)
        _bounded_positive("POSTGRES_MAX_RESULT_CELLS", self.max_result_cells, 1_000_000)
        if not 0.1 <= self.max_seconds <= 3_600:
            raise PostgresConfigurationError(
                "POSTGRES_MAX_SECONDS must be between 0.1 and 3600"
            )


@dataclass(frozen=True)
class PostgresConfig:
    source_id: str
    host: str
    port: int
    database: str
    user: str
    allowed_schemas: frozenset[str]
    allowed_tables: frozenset[str]
    allowed_columns: frozenset[str]
    password_env: str | None = None
    sslmode: str = "require"
    allow_insecure: bool = False
    statement_timeout_ms: int = 30_000
    lock_timeout_ms: int = 5_000
    limits: PostgresProfileLimits = field(default_factory=PostgresProfileLimits)
    resolved_columns: frozenset[str] | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    @classmethod
    def from_env(cls) -> PostgresConfig:
        endpoint = _postgres_jdbc_endpoint_from_env()
        config = cls(
            source_id=os.environ.get("POSTGRES_SOURCE_ID", "postgres"),
            host=_resolved_text_env(
                "POSTGRES_HOST",
                endpoint.host if endpoint is not None else None,
                "localhost",
                case_insensitive=True,
            ),
            port=_postgres_port_from_env(
                endpoint.port if endpoint is not None else None
            ),
            database=_resolved_text_env(
                "POSTGRES_DATABASE",
                endpoint.database if endpoint is not None else None,
                "postgres",
            ),
            user=os.environ.get("POSTGRES_USER", "test_data_agent"),
            password_env=_optional_env_name("POSTGRES_PASSWORD_ENV"),
            sslmode=_resolved_text_env(
                "POSTGRES_SSLMODE",
                endpoint.sslmode if endpoint is not None else None,
                "require",
                normalize=str.lower,
            ),
            allow_insecure=_bool_env("POSTGRES_ALLOW_INSECURE"),
            allowed_schemas=_required_allowlist("POSTGRES_ALLOWED_SCHEMAS", 1),
            allowed_tables=_required_allowlist("POSTGRES_ALLOWED_TABLES", 2),
            allowed_columns=_required_column_allowlist(),
            statement_timeout_ms=_positive_int_env(
                "POSTGRES_STATEMENT_TIMEOUT_MS", 30_000
            ),
            lock_timeout_ms=_positive_int_env("POSTGRES_LOCK_TIMEOUT_MS", 5_000),
            limits=PostgresProfileLimits.from_env(),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _validate_identifier(self.source_id, "POSTGRES_SOURCE_ID")
        _validate_text(self.host, "POSTGRES_HOST")
        _validate_identifier(self.database, "POSTGRES_DATABASE")
        _validate_text(self.user, "POSTGRES_USER")
        if not 1 <= self.port <= 65_535:
            raise PostgresConfigurationError(
                "POSTGRES_PORT must be between 1 and 65535"
            )
        if self.password_env is not None and not _ENV_NAME_RE.fullmatch(
            self.password_env
        ):
            raise PostgresConfigurationError(
                "POSTGRES_PASSWORD_ENV must name an environment variable"
            )
        if self.sslmode not in {"require", "verify-ca", "verify-full", "disable"}:
            raise PostgresConfigurationError(
                "POSTGRES_SSLMODE must be require, verify-ca, verify-full, or disable"
            )
        if self.sslmode == "disable" and not self.allow_insecure:
            raise PostgresConfigurationError(
                "POSTGRES_SSLMODE=disable requires POSTGRES_ALLOW_INSECURE=true"
            )
        _bounded_positive(
            "POSTGRES_STATEMENT_TIMEOUT_MS", self.statement_timeout_ms, 3_600_000
        )
        _bounded_positive("POSTGRES_LOCK_TIMEOUT_MS", self.lock_timeout_ms, 300_000)
        self.limits.validate()
        _validate_scope(
            self.allowed_schemas,
            self.allowed_tables,
            self.allowed_columns,
        )
        if self.resolved_columns is not None:
            _validate_resolved_columns(
                self.allowed_tables,
                self.allowed_columns,
                self.resolved_columns,
                self.limits.max_columns,
            )


def parse_postgres_jdbc_url(value: str) -> PostgresJdbcEndpoint:
    """Parse a credential-free PostgreSQL JDBC-style endpoint."""

    try:
        _validate_jdbc_url_text(value)
        if not value.startswith("jdbc:postgresql://"):
            raise ValueError
        parsed = urlsplit(value.removeprefix("jdbc:"))
        if (
            parsed.scheme != "postgresql"
            or parsed.hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or "@" in parsed.netloc
            or "%" in parsed.netloc
            or parsed.fragment
        ):
            raise ValueError
        host = parsed.hostname
        port = parsed.port
        database = _single_jdbc_path_component(parsed.path)
        properties = _unique_jdbc_properties(parsed.query)
        if set(properties) - {"sslmode"}:
            raise ValueError
        sslmode = properties.get("sslmode")
        if sslmode is not None:
            sslmode = sslmode.lower()
            if sslmode not in {"require", "verify-ca", "verify-full", "disable"}:
                raise ValueError
        _validate_text(host, "POSTGRES_HOST")
        _validate_identifier(database, "POSTGRES_DATABASE")
        if port is not None and not 1 <= port <= 65_535:
            raise ValueError
    except (UnicodeError, ValueError):
        raise PostgresConfigurationError(
            "POSTGRES_JDBC_URL must be a credential-free PostgreSQL JDBC endpoint"
        ) from None
    return PostgresJdbcEndpoint(
        host=host,
        port=port,
        database=database,
        sslmode=sslmode,
    )


def parse_postgres_column_selector(value: str) -> PostgresColumnSelector:
    """Parse one exact column or one table-qualified wildcard."""

    components = value.split(".")
    if len(components) != 3:
        raise PostgresConfigurationError(
            "POSTGRES_ALLOWED_COLUMNS entries must be "
            "schema.table.column identifiers or a schema.table.* wildcard"
        )
    schema, table, column = components
    if not _IDENTIFIER_RE.fullmatch(schema) or not _IDENTIFIER_RE.fullmatch(table):
        raise PostgresConfigurationError(
            "POSTGRES_ALLOWED_COLUMNS entries must be "
            "schema.table.column identifiers or a schema.table.* wildcard"
        )
    if column == "*":
        return PostgresColumnSelector(schema=schema, table=table, column=None)
    if not _IDENTIFIER_RE.fullmatch(column):
        raise PostgresConfigurationError(
            "POSTGRES_ALLOWED_COLUMNS entries must be "
            "schema.table.column identifiers or a schema.table.* wildcard"
        )
    return PostgresColumnSelector(schema=schema, table=table, column=column)


def with_resolved_postgres_columns(
    config: PostgresConfig,
    columns: frozenset[str],
) -> PostgresConfig:
    """Return an internal immutable config snapshot for trusted query builders."""

    resolved = replace(config)
    object.__setattr__(resolved, "resolved_columns", columns)
    resolved.validate()
    return resolved


def _postgres_jdbc_endpoint_from_env() -> PostgresJdbcEndpoint | None:
    value = os.environ.get("POSTGRES_JDBC_URL")
    if value is None:
        return None
    return parse_postgres_jdbc_url(value)


def _validate_scope(
    schemas: frozenset[str],
    tables: frozenset[str],
    columns: frozenset[str],
) -> None:
    if not schemas or not tables or not columns:
        raise PostgresConfigurationError(
            "PostgreSQL schema, table, and column allowlists are required"
        )
    for schema in schemas:
        _validate_identifier(schema, "POSTGRES_ALLOWED_SCHEMAS")
    for table in tables:
        _validate_qualified_identifier(table, 2, "POSTGRES_ALLOWED_TABLES")
        schema, _ = table.split(".", maxsplit=1)
        if schema not in schemas:
            raise PostgresConfigurationError(
                "POSTGRES_ALLOWED_TABLES must stay within allowed schemas"
            )
    for column in columns:
        selector = parse_postgres_column_selector(column)
        if selector.table_name not in tables:
            raise PostgresConfigurationError(
                "POSTGRES_ALLOWED_COLUMNS must stay within allowed tables"
            )


def _validate_resolved_columns(
    tables: frozenset[str],
    configured_columns: frozenset[str],
    columns: frozenset[str],
    max_columns: int,
) -> None:
    if not columns:
        raise PostgresConfigurationError(
            "PostgreSQL resolved column snapshot must not be empty"
        )
    if len(columns) > max_columns:
        raise PostgresConfigurationError(
            "PostgreSQL resolved column snapshot exceeds its budget"
        )
    for column in columns:
        selector = parse_postgres_column_selector(column)
        if (
            selector.is_wildcard
            or selector.table_name not in tables
            or (
                selector.qualified_name not in configured_columns
                and f"{selector.table_name}.*" not in configured_columns
            )
        ):
            raise PostgresConfigurationError(
                "PostgreSQL resolved column snapshot must contain exact allowed columns"
            )


def _required_allowlist(name: str, parts: int) -> frozenset[str]:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise PostgresConfigurationError(f"{name} is required")
    entries = frozenset(item.strip() for item in value.split(",") if item.strip())
    for entry in entries:
        _validate_qualified_identifier(entry, parts, name)
    return entries


def _required_column_allowlist() -> frozenset[str]:
    name = "POSTGRES_ALLOWED_COLUMNS"
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise PostgresConfigurationError(f"{name} is required")
    entries = frozenset(item.strip() for item in value.split(",") if item.strip())
    for entry in entries:
        parse_postgres_column_selector(entry)
    return entries


def _postgres_port_from_env(jdbc_port: int | None = None) -> int:
    raw_value = os.environ.get("POSTGRES_PORT")
    if raw_value is None:
        value = jdbc_port if jdbc_port is not None else DEFAULT_POSTGRES_PORT
    else:
        try:
            value = int(raw_value)
        except ValueError:
            raise PostgresConfigurationError(
                "POSTGRES_PORT must be an integer"
            ) from None
        if jdbc_port is not None and value != jdbc_port:
            raise PostgresConfigurationError(
                "POSTGRES_JDBC_URL conflicts with explicit component configuration"
            )
    if value > 65_535:
        raise PostgresConfigurationError("POSTGRES_PORT must be between 1 and 65535")
    if value < 1:
        raise PostgresConfigurationError("POSTGRES_PORT must be positive")
    return value


def _resolved_text_env(
    name: str,
    jdbc_value: str | None,
    default: str,
    *,
    normalize: Callable[[str], str] | None = None,
    case_insensitive: bool = False,
) -> str:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return jdbc_value if jdbc_value is not None else default
    value = raw_value.strip()
    if normalize is not None:
        value = normalize(value)
    if jdbc_value is not None:
        left = value.casefold() if case_insensitive else value
        right = jdbc_value.casefold() if case_insensitive else jdbc_value
        if left != right:
            raise PostgresConfigurationError(
                "POSTGRES_JDBC_URL conflicts with explicit component configuration"
            )
    return value


def _validate_jdbc_url_text(value: str) -> None:
    if not value or value != value.strip() or any(
        character in value for character in "\r\n\t\\"
    ):
        raise ValueError
    index = 0
    while index < len(value):
        if value[index] == "%":
            if index + 2 >= len(value) or not re.fullmatch(
                r"[0-9A-Fa-f]{2}", value[index + 1 : index + 3]
            ):
                raise ValueError
            index += 3
            continue
        index += 1


def _single_jdbc_path_component(path: str) -> str:
    if not path.startswith("/") or path.count("/") != 1 or len(path) == 1:
        raise ValueError
    return unquote(path[1:], errors="strict")


def _unique_jdbc_properties(query: str) -> dict[str, str]:
    if not query:
        return {}
    pairs = parse_qsl(
        query,
        keep_blank_values=True,
        strict_parsing=True,
        encoding="utf-8",
        errors="strict",
    )
    properties: dict[str, str] = {}
    for name, value in pairs:
        if name in properties:
            raise ValueError
        properties[name] = value
    return properties


def _optional_env_name(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _bool_env(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise PostgresConfigurationError(f"{name} must be a boolean")


def _positive_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise PostgresConfigurationError(f"{name} must be an integer") from exc
    if value < 1:
        raise PostgresConfigurationError(f"{name} must be positive")
    return value


def _positive_float_env(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise PostgresConfigurationError(f"{name} must be a number") from exc
    if not value > 0 or value == float("inf"):
        raise PostgresConfigurationError(f"{name} must be a finite positive number")
    return value


def _bounded_positive(name: str, value: int, maximum: int) -> None:
    if not 1 <= value <= maximum:
        raise PostgresConfigurationError(f"{name} must be between 1 and {maximum}")


def _validate_identifier(value: str, name: str) -> None:
    if not _IDENTIFIER_RE.fullmatch(value):
        raise PostgresConfigurationError(f"{name} must be a PostgreSQL identifier")


def _validate_qualified_identifier(value: str, parts: int, name: str) -> None:
    components = value.split(".")
    if len(components) != parts or any(
        not _IDENTIFIER_RE.fullmatch(component) for component in components
    ):
        expected = ".".join(("schema", "table", "column")[:parts])
        raise PostgresConfigurationError(
            f"{name} entries must be {expected} identifiers"
        )


def _validate_text(value: str, name: str) -> None:
    if not value.strip() or "\r" in value or "\n" in value:
        raise PostgresConfigurationError(f"{name} must be a non-empty safe value")
