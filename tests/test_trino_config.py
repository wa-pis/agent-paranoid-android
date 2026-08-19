from __future__ import annotations

from dataclasses import replace

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent.trino_config import (
    TrinoConfig,
    TrinoConfigurationError,
    TrinoDeploymentProfile,
    deployment_profile_from_env,
    parse_data_size_value,
    parse_duration_value,
    parse_trino_jdbc_url,
    parse_trino_port,
)


def test_trino_config_loads_explicit_allowlists_and_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_HOST", "trino.internal")
    monkeypatch.setenv("TRINO_PORT", "8443")
    monkeypatch.setenv("TRINO_USER", "synthetic-agent")
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "analytics, testing")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "safe, fixtures")
    monkeypatch.setenv(
        "TRINO_ALLOWED_TABLE_COLUMNS", "analytics.safe.customers.country_code"
    )
    monkeypatch.setenv("TRINO_MAX_RESULT_ROWS", "250")
    monkeypatch.setenv("TRINO_QUERY_MAX_EXECUTION_TIME", "20s")
    monkeypatch.setenv("TRINO_QUERY_MAX_RUN_TIME", "30s")
    monkeypatch.setenv("TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES", "512MB")

    config = TrinoConfig.from_env()

    assert config.host == "trino.internal"
    assert config.port == 8443
    assert config.user == "synthetic-agent"
    assert config.allowed_catalogs == frozenset({"analytics", "testing"})
    assert config.allowed_schemas == frozenset({"safe", "fixtures"})
    assert config.allowed_table_columns == frozenset(
        {"analytics.safe.customers.country_code"}
    )
    assert config.max_result_rows == 250
    assert config.query_max_execution_time == "20s"
    assert config.query_max_run_time == "30s"
    assert config.query_max_scan_physical_bytes == "512MB"
    assert config.deployment_profile is TrinoDeploymentProfile.TRUSTED_LOCAL


@pytest.mark.parametrize(
    "value",
    [
        "analytics",
        "analytics.safe.customers",
        "analytics.safe.customers.",
        ".analytics.safe.customers.country_code",
    ],
)
def test_trino_config_rejects_invalid_table_column_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "analytics")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "safe")
    monkeypatch.setenv("TRINO_ALLOWED_TABLE_COLUMNS", value)

    with pytest.raises(TrinoConfigurationError, match="catalog.schema.table.column"):
        TrinoConfig.from_env()


def test_trino_config_requires_a_known_deployment_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_DEPLOYMENT_PROFILE", "shared-hardened")
    assert deployment_profile_from_env() is TrinoDeploymentProfile.SHARED_HARDENED

    monkeypatch.setenv("TRINO_DEPLOYMENT_PROFILE", "unknown")
    with pytest.raises(TrinoConfigurationError, match="TRINO_DEPLOYMENT_PROFILE"):
        deployment_profile_from_env()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("host", "trino.internal\r\nX-Forged: yes", "TRINO_HOST"),
        ("user", "agent\nX-Forged: yes", "TRINO_USER"),
    ],
)
def test_trino_config_rejects_header_injection(
    field: str,
    value: str,
    message: str,
) -> None:
    config = TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe"}),
    )
    invalid = replace(config, **{field: value})

    with pytest.raises(TrinoConfigurationError, match=message):
        invalid.validate_security()


def test_trino_budget_parsers_fail_closed() -> None:
    assert parse_duration_value("30s", "duration", 30_000) == 30_000
    assert parse_data_size_value("1GB", "scan", 1_024**3) == 1_024**3

    with pytest.raises(TrinoConfigurationError, match="maximum allowed query budget"):
        parse_duration_value("31s", "duration", 30_000)
    with pytest.raises(TrinoConfigurationError, match="maximum allowed scan budget"):
        parse_data_size_value("2GB", "scan", 1_024**3)


def test_trino_server_keeps_config_compatibility_exports() -> None:
    assert mcp_trino_server.TrinoConfig is TrinoConfig
    assert mcp_trino_server.TrinoConfigurationError is TrinoConfigurationError
    assert mcp_trino_server.parse_trino_port is parse_trino_port


def test_trino_config_keeps_existing_optional_positional_order() -> None:
    config = TrinoConfig(
        "trino.internal",
        8443,
        "synthetic-agent",
        "https",
        frozenset({"analytics"}),
        frozenset({"safe"}),
        None,
        12.0,
    )

    assert config.request_timeout == 12.0
    assert config.default_catalog is None


def test_trino_jdbc_url_normalizes_allowlisted_request_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "TRINO_HOST",
        "TRINO_PORT",
        "TRINO_HTTP_SCHEME",
        "TRINO_CATALOG",
        "TRINO_SCHEMA",
    ):
        monkeypatch.delenv(name, raising=False)
    jdbc_url = "jdbc:trino://trino.example.test:8443/warehouse/analytics?SSL=true"
    monkeypatch.setenv("TRINO_JDBC_URL", jdbc_url)
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "warehouse")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "analytics")

    config = TrinoConfig.from_env()

    assert config.host == "trino.example.test"
    assert config.port == 8443
    assert config.http_scheme == "https"
    assert config.default_catalog == "warehouse"
    assert config.default_schema == "analytics"
    assert jdbc_url not in repr(config)


def test_trino_jdbc_url_rejects_component_conflicts_without_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_JDBC_URL", "jdbc:trino://private.example.test:8443")
    monkeypatch.setenv("TRINO_HOST", "trino.example.test")
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "warehouse")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "analytics")

    with pytest.raises(TrinoConfigurationError) as captured:
        TrinoConfig.from_env()

    assert str(captured.value) == (
        "TRINO_JDBC_URL conflicts with explicit component configuration"
    )
    assert "private.example.test" not in str(captured.value)


def test_trino_jdbc_url_allows_endpoint_without_request_defaults() -> None:
    endpoint = parse_trino_jdbc_url("jdbc:trino://trino.example.test")

    assert endpoint.port is None
    assert endpoint.catalog is None
    assert endpoint.schema is None
    assert endpoint.http_scheme is None


def test_trino_jdbc_url_detaches_invalid_explicit_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_JDBC_URL", "jdbc:trino://trino.example.test")
    monkeypatch.setenv("TRINO_PORT", "secret-port")
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "warehouse")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "analytics")

    with pytest.raises(TrinoConfigurationError) as captured:
        TrinoConfig.from_env()

    assert str(captured.value) == "TRINO_PORT must be an integer"
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True


def test_trino_jdbc_url_requires_allowlisted_path_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TRINO_JDBC_URL",
        "jdbc:trino://trino.example.test:8443/private/analytics?SSL=true",
    )
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "warehouse")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "analytics")

    with pytest.raises(TrinoConfigurationError, match="TRINO_ALLOWED_CATALOGS"):
        TrinoConfig.from_env()


@pytest.mark.parametrize(
    "jdbc_url",
    [
        "jdbc:trino://reader:secret@trino.test:8443/warehouse/analytics",
        "jdbc:trino://trino.test:8443/warehouse/analytics?password=secret",
        "jdbc:trino://trino.test:8443/warehouse/analytics?SSL=true&SSL=true",
        "jdbc:trino://trino.test:8443/warehouse/analytics?SSL=true%20",
        "jdbc:trino://trino.test:8443/warehouse/analytics?sessionProperties=x",
        "jdbc:trino://trino.test:8443/warehouse/analytics?SSL=false",
        "jdbc:trino://trino.test:8443/warehouse/analytics#secret",
        "jdbc:trino://trino.test:secret/warehouse/analytics",
        "jdbc:trino://trino%0Atest:8443/warehouse/analytics",
        "jdbc:trino://trino.test:8443/warehouse%ZZ/analytics",
        "jdbc:trino://trino.test:8443/warehouse/analytics/extra",
    ],
)
def test_trino_jdbc_url_fails_closed_without_echoing_input(jdbc_url: str) -> None:
    with pytest.raises(TrinoConfigurationError) as captured:
        parse_trino_jdbc_url(jdbc_url)

    assert str(captured.value) == (
        "TRINO_JDBC_URL must be a credential-free Trino JDBC endpoint"
    )
    assert "secret" not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True
