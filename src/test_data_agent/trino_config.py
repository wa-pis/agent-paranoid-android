"""Validated Trino connection and resource-budget configuration."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qsl, unquote, urlsplit

DEFAULT_MAX_RESULT_ROWS = 10_000
ABSOLUTE_MAX_RESULT_ROWS = 100_000
DEFAULT_QUERY_MAX_EXECUTION_TIME = "30s"
DEFAULT_QUERY_MAX_RUN_TIME = "45s"
DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES = "1GB"
DURATION_RE = re.compile(r"^([1-9][0-9]*)(ms|s|m|h)$")
DATA_SIZE_RE = re.compile(r"^([1-9][0-9]*)(B|kB|MB|GB)$")
DURATION_MULTIPLIERS_MS = {"ms": 1, "s": 1_000, "m": 60_000, "h": 3_600_000}
DATA_SIZE_MULTIPLIERS = {"B": 1, "kB": 1_024, "MB": 1_024**2, "GB": 1_024**3}
MAX_QUERY_EXECUTION_TIME_MS = 3_600_000
MAX_QUERY_RUN_TIME_MS = 7_200_000
MAX_QUERY_SCAN_BYTES = 100 * 1_024**3
MAX_JDBC_URL_BYTES = 4_096
MAX_JDBC_HOST_CHARS = 253
MAX_TRINO_IDENTIFIER_CHARS = 255
TRINO_DEPLOYMENT_PROFILE_ENV = "TRINO_DEPLOYMENT_PROFILE"


class TrinoDeploymentProfile(StrEnum):
    TRUSTED_LOCAL = "trusted-local"
    SHARED_HARDENED = "shared-hardened"


class TrinoConfigurationError(ValueError):
    """Raised when Trino safety boundaries are not explicitly configured."""


@dataclass(frozen=True)
class TrinoJdbcEndpoint:
    host: str
    port: int | None
    catalog: str | None
    schema: str | None
    http_scheme: str | None


@dataclass(frozen=True, slots=True)
class TrinoColumnSelector:
    catalog: str
    schema: str
    table: str
    column: str | None

    @property
    def is_wildcard(self) -> bool:
        return self.column is None

    @property
    def table_name(self) -> str:
        return f"{self.catalog}.{self.schema}.{self.table}"

    @property
    def qualified_name(self) -> str:
        column = "*" if self.column is None else self.column
        return f"{self.table_name}.{column}"


@dataclass(frozen=True)
class TrinoConfig:
    host: str
    port: int
    user: str
    http_scheme: str
    allowed_catalogs: frozenset[str] | None
    allowed_schemas: frozenset[str] | None
    allowed_table_columns: frozenset[str] | None = None
    request_timeout: float = 30.0
    max_result_rows: int = DEFAULT_MAX_RESULT_ROWS
    query_max_execution_time: str = DEFAULT_QUERY_MAX_EXECUTION_TIME
    query_max_run_time: str = DEFAULT_QUERY_MAX_RUN_TIME
    query_max_scan_physical_bytes: str = DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES
    allow_unrestricted: bool = False
    allow_insecure_http: bool = False
    deployment_profile: TrinoDeploymentProfile = TrinoDeploymentProfile.TRUSTED_LOCAL
    default_catalog: str | None = None
    default_schema: str | None = None

    @classmethod
    def from_env(cls) -> TrinoConfig:
        endpoint = _trino_jdbc_endpoint_from_env()
        config = cls(
            host=_resolved_text_env(
                "TRINO_HOST",
                endpoint.host if endpoint is not None else None,
                "localhost",
                case_insensitive=True,
            ),
            port=parse_trino_port(endpoint.port if endpoint is not None else None),
            user=os.environ.get("TRINO_USER", "test_data_agent"),
            http_scheme=_resolved_text_env(
                "TRINO_HTTP_SCHEME",
                endpoint.http_scheme if endpoint is not None else None,
                "https",
                normalize=str.lower,
            ),
            allowed_catalogs=parse_allowlist(os.environ.get("TRINO_ALLOWED_CATALOGS")),
            allowed_schemas=parse_allowlist(os.environ.get("TRINO_ALLOWED_SCHEMAS")),
            allowed_table_columns=parse_allowlist(
                os.environ.get("TRINO_ALLOWED_TABLE_COLUMNS")
            ),
            default_catalog=_resolved_optional_text_env(
                "TRINO_CATALOG",
                endpoint.catalog if endpoint is not None else None,
            ),
            default_schema=_resolved_optional_text_env(
                "TRINO_SCHEMA",
                endpoint.schema if endpoint is not None else None,
            ),
            request_timeout=parse_request_timeout(),
            max_result_rows=parse_max_result_rows(),
            query_max_execution_time=parse_duration_env(
                "TRINO_QUERY_MAX_EXECUTION_TIME",
                DEFAULT_QUERY_MAX_EXECUTION_TIME,
                MAX_QUERY_EXECUTION_TIME_MS,
            ),
            query_max_run_time=parse_duration_env(
                "TRINO_QUERY_MAX_RUN_TIME",
                DEFAULT_QUERY_MAX_RUN_TIME,
                MAX_QUERY_RUN_TIME_MS,
            ),
            query_max_scan_physical_bytes=parse_data_size_env(
                "TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES",
                DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES,
                MAX_QUERY_SCAN_BYTES,
            ),
            allow_unrestricted=parse_env_bool("TRINO_ALLOW_UNRESTRICTED"),
            allow_insecure_http=parse_env_bool("TRINO_ALLOW_INSECURE_HTTP"),
            deployment_profile=deployment_profile_from_env(),
        )
        config.validate_security()
        return config

    def validate_security(self) -> None:
        scheme = self.http_scheme.lower()
        if not self.host.strip() or "\r" in self.host or "\n" in self.host:
            raise TrinoConfigurationError("TRINO_HOST must be a non-empty host name")
        if not self.user.strip() or "\r" in self.user or "\n" in self.user:
            raise TrinoConfigurationError("TRINO_USER must be a non-empty header-safe value")
        if not 1 <= self.port <= 65_535:
            raise TrinoConfigurationError("TRINO_PORT must be between 1 and 65535")
        if not 0.1 <= self.request_timeout <= 300:
            raise TrinoConfigurationError(
                "TRINO_REQUEST_TIMEOUT_SECONDS must be between 0.1 and 300"
            )
        if scheme not in {"http", "https"}:
            raise TrinoConfigurationError("TRINO_HTTP_SCHEME must be http or https")
        if scheme == "http" and not self.allow_insecure_http:
            raise TrinoConfigurationError(
                "plain HTTP is disabled; use https or explicitly set "
                "TRINO_ALLOW_INSECURE_HTTP=true"
            )
        if (
            self.allowed_catalogs is None or self.allowed_schemas is None
        ) and not self.allow_unrestricted:
            raise TrinoConfigurationError(
                "TRINO_ALLOWED_CATALOGS and TRINO_ALLOWED_SCHEMAS are required; "
                "set TRINO_ALLOW_UNRESTRICTED=true only for an intentionally "
                "unrestricted environment"
            )
        execution_ms = parse_duration_value(
            self.query_max_execution_time,
            "TRINO_QUERY_MAX_EXECUTION_TIME",
            MAX_QUERY_EXECUTION_TIME_MS,
        )
        run_ms = parse_duration_value(
            self.query_max_run_time,
            "TRINO_QUERY_MAX_RUN_TIME",
            MAX_QUERY_RUN_TIME_MS,
        )
        parse_data_size_value(
            self.query_max_scan_physical_bytes,
            "TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES",
            MAX_QUERY_SCAN_BYTES,
        )
        if self.allowed_table_columns is not None:
            for value in self.allowed_table_columns:
                selector = parse_trino_column_selector(value)
                if selector.is_wildcard and self.allow_unrestricted:
                    raise TrinoConfigurationError(
                        "TRINO_ALLOWED_TABLE_COLUMNS wildcards require restricted mode"
                    )
                if (
                    self.allowed_catalogs is None
                    or selector.catalog not in self.allowed_catalogs
                    or self.allowed_schemas is None
                    or selector.schema not in self.allowed_schemas
                ):
                    raise TrinoConfigurationError(
                        "TRINO_ALLOWED_TABLE_COLUMNS must stay within allowed "
                        "catalogs and schemas"
                    )
        if self.default_catalog is not None:
            _validate_database_identifier(self.default_catalog, "TRINO_CATALOG")
            if (
                self.allowed_catalogs is None
                or self.default_catalog not in self.allowed_catalogs
            ):
                raise TrinoConfigurationError(
                    "TRINO_CATALOG must be present in TRINO_ALLOWED_CATALOGS"
                )
        if self.default_schema is not None:
            _validate_database_identifier(self.default_schema, "TRINO_SCHEMA")
            if self.default_catalog is None:
                raise TrinoConfigurationError(
                    "TRINO_SCHEMA requires a validated TRINO_CATALOG"
                )
            if (
                self.allowed_schemas is None
                or self.default_schema not in self.allowed_schemas
            ):
                raise TrinoConfigurationError(
                    "TRINO_SCHEMA must be present in TRINO_ALLOWED_SCHEMAS"
                )
        if run_ms < execution_ms:
            raise TrinoConfigurationError(
                "TRINO_QUERY_MAX_RUN_TIME must be greater than or equal to "
                "TRINO_QUERY_MAX_EXECUTION_TIME"
            )


def deployment_profile_from_env() -> TrinoDeploymentProfile:
    raw_value = os.environ.get(
        TRINO_DEPLOYMENT_PROFILE_ENV,
        TrinoDeploymentProfile.TRUSTED_LOCAL.value,
    ).strip().lower()
    try:
        return TrinoDeploymentProfile(raw_value)
    except ValueError as exc:
        raise TrinoConfigurationError(
            f"{TRINO_DEPLOYMENT_PROFILE_ENV} must be trusted-local or shared-hardened"
        ) from exc


def parse_allowlist(value: str | None) -> frozenset[str] | None:
    if value is None or not value.strip():
        return None
    return frozenset(item.strip() for item in value.split(",") if item.strip())


def parse_trino_jdbc_url(value: str) -> TrinoJdbcEndpoint:
    """Parse a credential-free Trino JDBC-style endpoint."""

    try:
        _validate_jdbc_url_text(value)
        if not value.startswith("jdbc:trino://"):
            raise ValueError
        parsed = urlsplit(value.removeprefix("jdbc:"))
        if (
            parsed.scheme != "trino"
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
        catalog, schema = _trino_jdbc_path(parsed.path)
        properties = _unique_jdbc_properties(parsed.query)
        if set(properties) - {"SSL"}:
            raise ValueError
        ssl_value = properties.get("SSL")
        if ssl_value is not None and ssl_value.lower() != "true":
            raise ValueError
        http_scheme = "https" if ssl_value is not None else None
        if (
            not host.strip()
            or len(host) > MAX_JDBC_HOST_CHARS
            or any(character in host for character in "\r\n\t")
        ):
            raise ValueError
        if port is not None and not 1 <= port <= 65_535:
            raise ValueError
        if catalog is not None:
            _validate_database_identifier(catalog, "TRINO_CATALOG")
        if schema is not None:
            _validate_database_identifier(schema, "TRINO_SCHEMA")
    except (UnicodeError, ValueError):
        raise TrinoConfigurationError(
            "TRINO_JDBC_URL must be a credential-free Trino JDBC endpoint"
        ) from None
    return TrinoJdbcEndpoint(
        host=host,
        port=port,
        catalog=catalog,
        schema=schema,
        http_scheme=http_scheme,
    )


def _trino_jdbc_endpoint_from_env() -> TrinoJdbcEndpoint | None:
    value = os.environ.get("TRINO_JDBC_URL")
    if value is None:
        return None
    return parse_trino_jdbc_url(value)


def validate_fully_qualified_table_column(value: str) -> None:
    parse_trino_column_selector(value)


def parse_trino_column_selector(value: str) -> TrinoColumnSelector:
    """Parse one exact column or one table-qualified wildcard."""

    components = value.split(".")
    if len(components) != 4:
        raise TrinoConfigurationError(
            "TRINO_ALLOWED_TABLE_COLUMNS entries must be "
            "catalog.schema.table.column or catalog.schema.table.* values"
        )
    catalog, schema, table, column = components
    if any(
        not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", component)
        for component in (catalog, schema, table)
    ):
        raise TrinoConfigurationError(
            "TRINO_ALLOWED_TABLE_COLUMNS entries must be "
            "catalog.schema.table.column or catalog.schema.table.* values"
        )
    if column == "*":
        return TrinoColumnSelector(catalog, schema, table, None)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", column):
        raise TrinoConfigurationError(
            "TRINO_ALLOWED_TABLE_COLUMNS entries must be "
            "catalog.schema.table.column or catalog.schema.table.* values"
        )
    return TrinoColumnSelector(catalog, schema, table, column)


def parse_env_bool(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise TrinoConfigurationError(f"{name} must be a boolean")


def parse_trino_port(jdbc_port: int | None = None) -> int:
    raw_value = os.environ.get("TRINO_PORT")
    if raw_value is None:
        value = jdbc_port if jdbc_port is not None else 8080
    else:
        try:
            value = int(raw_value)
        except ValueError:
            raise TrinoConfigurationError("TRINO_PORT must be an integer") from None
        if jdbc_port is not None and value != jdbc_port:
            raise TrinoConfigurationError(
                "TRINO_JDBC_URL conflicts with explicit component configuration"
            )
    if not 1 <= value <= 65_535:
        raise TrinoConfigurationError("TRINO_PORT must be between 1 and 65535")
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
            raise TrinoConfigurationError(
                "TRINO_JDBC_URL conflicts with explicit component configuration"
            )
    return value


def _resolved_optional_text_env(name: str, jdbc_value: str | None) -> str | None:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return jdbc_value
    value = raw_value.strip()
    if jdbc_value is not None and value != jdbc_value:
        raise TrinoConfigurationError(
            "TRINO_JDBC_URL conflicts with explicit component configuration"
        )
    return value


def _validate_jdbc_url_text(value: str) -> None:
    if (
        not value
        or len(value.encode("utf-8")) > MAX_JDBC_URL_BYTES
        or value != value.strip()
        or any(character in value for character in "\r\n\t\\")
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


def _trino_jdbc_path(path: str) -> tuple[str | None, str | None]:
    if path in {"", "/"}:
        return None, None
    if not path.startswith("/"):
        raise ValueError
    parts = path[1:].split("/")
    if not 1 <= len(parts) <= 2 or any(not part for part in parts):
        raise ValueError
    decoded = [unquote(part, errors="strict") for part in parts]
    return decoded[0], decoded[1] if len(decoded) == 2 else None


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


_DATABASE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_database_identifier(value: str, name: str) -> None:
    if len(value) > MAX_TRINO_IDENTIFIER_CHARS or not _DATABASE_IDENTIFIER_RE.fullmatch(
        value
    ):
        raise TrinoConfigurationError(f"{name} must be a database identifier")


def parse_request_timeout() -> float:
    raw_value = os.environ.get("TRINO_REQUEST_TIMEOUT_SECONDS", "30")
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise TrinoConfigurationError(
            "TRINO_REQUEST_TIMEOUT_SECONDS must be a number"
        ) from exc
    if not 0.1 <= value <= 300:
        raise TrinoConfigurationError(
            "TRINO_REQUEST_TIMEOUT_SECONDS must be between 0.1 and 300"
        )
    return value


def parse_max_result_rows() -> int:
    raw_value = os.environ.get("TRINO_MAX_RESULT_ROWS", str(DEFAULT_MAX_RESULT_ROWS))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise TrinoConfigurationError("TRINO_MAX_RESULT_ROWS must be an integer") from exc
    if not 1 <= value <= ABSOLUTE_MAX_RESULT_ROWS:
        raise TrinoConfigurationError(
            f"TRINO_MAX_RESULT_ROWS must be between 1 and {ABSOLUTE_MAX_RESULT_ROWS}"
        )
    return value


def parse_duration_env(name: str, default: str, maximum_ms: int) -> str:
    value = os.environ.get(name, default)
    parse_duration_value(value, name, maximum_ms)
    return value


def parse_duration_value(value: str, name: str, maximum_ms: int) -> int:
    match = DURATION_RE.fullmatch(value)
    if match is None:
        raise TrinoConfigurationError(
            f"{name} must use an integer followed by ms, s, m, or h"
        )
    duration_ms = int(match.group(1)) * DURATION_MULTIPLIERS_MS[match.group(2)]
    if duration_ms > maximum_ms:
        raise TrinoConfigurationError(f"{name} exceeds the maximum allowed query budget")
    return duration_ms


def parse_data_size_env(name: str, default: str, maximum_bytes: int) -> str:
    value = os.environ.get(name, default)
    parse_data_size_value(value, name, maximum_bytes)
    return value


def parse_data_size_value(value: str, name: str, maximum_bytes: int) -> int:
    match = DATA_SIZE_RE.fullmatch(value)
    if match is None:
        raise TrinoConfigurationError(
            f"{name} must use an integer followed by B, kB, MB, or GB"
        )
    size_bytes = int(match.group(1)) * DATA_SIZE_MULTIPLIERS[match.group(2)]
    if size_bytes > maximum_bytes:
        raise TrinoConfigurationError(f"{name} exceeds the maximum allowed scan budget")
    return size_bytes
