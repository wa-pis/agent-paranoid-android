"""Validated Trino connection and resource-budget configuration."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import StrEnum

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
TRINO_DEPLOYMENT_PROFILE_ENV = "TRINO_DEPLOYMENT_PROFILE"


class TrinoDeploymentProfile(StrEnum):
    TRUSTED_LOCAL = "trusted-local"
    SHARED_HARDENED = "shared-hardened"


class TrinoConfigurationError(ValueError):
    """Raised when Trino safety boundaries are not explicitly configured."""


@dataclass(frozen=True)
class TrinoConfig:
    host: str
    port: int
    user: str
    http_scheme: str
    allowed_catalogs: frozenset[str] | None
    allowed_schemas: frozenset[str] | None
    request_timeout: float = 30.0
    max_result_rows: int = DEFAULT_MAX_RESULT_ROWS
    query_max_execution_time: str = DEFAULT_QUERY_MAX_EXECUTION_TIME
    query_max_run_time: str = DEFAULT_QUERY_MAX_RUN_TIME
    query_max_scan_physical_bytes: str = DEFAULT_QUERY_MAX_SCAN_PHYSICAL_BYTES
    allow_unrestricted: bool = False
    allow_insecure_http: bool = False
    deployment_profile: TrinoDeploymentProfile = TrinoDeploymentProfile.TRUSTED_LOCAL

    @classmethod
    def from_env(cls) -> TrinoConfig:
        config = cls(
            host=os.environ.get("TRINO_HOST", "localhost"),
            port=parse_trino_port(),
            user=os.environ.get("TRINO_USER", "test_data_agent"),
            http_scheme=os.environ.get("TRINO_HTTP_SCHEME", "https"),
            allowed_catalogs=parse_allowlist(os.environ.get("TRINO_ALLOWED_CATALOGS")),
            allowed_schemas=parse_allowlist(os.environ.get("TRINO_ALLOWED_SCHEMAS")),
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


def parse_trino_port() -> int:
    raw_value = os.environ.get("TRINO_PORT", "8080")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise TrinoConfigurationError("TRINO_PORT must be an integer") from exc
    if not 1 <= value <= 65_535:
        raise TrinoConfigurationError("TRINO_PORT must be between 1 and 65535")
    return value


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
