"""Validated PostgreSQL connection scope and profiling budgets."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


DEFAULT_POSTGRES_PORT = 5432
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresConfigurationError(ValueError):
    """Raised when PostgreSQL access is not explicitly bounded."""


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

    @classmethod
    def from_env(cls) -> PostgresConfig:
        config = cls(
            source_id=os.environ.get("POSTGRES_SOURCE_ID", "postgres"),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=_postgres_port_from_env(),
            database=os.environ.get("POSTGRES_DATABASE", "postgres"),
            user=os.environ.get("POSTGRES_USER", "test_data_agent"),
            password_env=_optional_env_name("POSTGRES_PASSWORD_ENV"),
            sslmode=os.environ.get("POSTGRES_SSLMODE", "require").strip().lower(),
            allow_insecure=_bool_env("POSTGRES_ALLOW_INSECURE"),
            allowed_schemas=_required_allowlist("POSTGRES_ALLOWED_SCHEMAS", 1),
            allowed_tables=_required_allowlist("POSTGRES_ALLOWED_TABLES", 2),
            allowed_columns=_required_allowlist("POSTGRES_ALLOWED_COLUMNS", 3),
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
        _validate_qualified_identifier(column, 3, "POSTGRES_ALLOWED_COLUMNS")
        schema, table, _ = column.split(".", maxsplit=2)
        if f"{schema}.{table}" not in tables:
            raise PostgresConfigurationError(
                "POSTGRES_ALLOWED_COLUMNS must stay within allowed tables"
            )


def _required_allowlist(name: str, parts: int) -> frozenset[str]:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise PostgresConfigurationError(f"{name} is required")
    entries = frozenset(item.strip() for item in value.split(",") if item.strip())
    for entry in entries:
        _validate_qualified_identifier(entry, parts, name)
    return entries


def _postgres_port_from_env() -> int:
    value = _positive_int_env("POSTGRES_PORT", DEFAULT_POSTGRES_PORT)
    if value > 65_535:
        raise PostgresConfigurationError("POSTGRES_PORT must be between 1 and 65535")
    return value


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
