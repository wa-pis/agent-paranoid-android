from __future__ import annotations

from dataclasses import replace

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent.trino_config import (
    TrinoConfig,
    TrinoConfigurationError,
    parse_data_size_value,
    parse_duration_value,
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
    assert config.max_result_rows == 250
    assert config.query_max_execution_time == "20s"
    assert config.query_max_run_time == "30s"
    assert config.query_max_scan_physical_bytes == "512MB"


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
