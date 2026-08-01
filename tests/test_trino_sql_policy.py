from __future__ import annotations

import pytest

from test_data_agent import mcp_trino_server
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_sql_policy import (
    AllowlistError,
    SqlSafetyError,
    check_allowlist,
    quote_identifier,
    validate_safe_select,
)


def policy_config() -> TrinoConfig:
    return TrinoConfig(
        host="trino.internal",
        port=8443,
        user="synthetic-agent",
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe"}),
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM analytics.safe.records",
        "SELECT * FROM analytics.safe.records LIMIT 1",
        "SELECT customer_email AS value FROM analytics.safe.records LIMIT 1",
        "SELECT id FROM analytics.safe.records",
        "SELECT id FROM analytics.safe.records ORDER BY rand() LIMIT 1",
        "SELECT id FROM analytics.safe.records LIMIT 1; DROP TABLE records",
    ],
)
def test_direct_sql_policy_rejects_unsafe_queries(sql: str) -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select(sql, config=policy_config())


def test_direct_sql_policy_accepts_bounded_allowlisted_select() -> None:
    sql = "SELECT synthetic_id FROM analytics.safe.records LIMIT 10"

    assert validate_safe_select(sql, config=policy_config()) == sql


def test_direct_allowlist_policy_fails_closed() -> None:
    config = policy_config()

    check_allowlist(catalog="analytics", schema="safe", config=config)
    with pytest.raises(AllowlistError, match="catalog is not allowed"):
        check_allowlist(catalog="raw", schema="safe", config=config)
    with pytest.raises(AllowlistError, match="fully qualified"):
        validate_safe_select("SELECT id FROM records LIMIT 1", config=config)


def test_identifier_policy_rejects_sql_fragments() -> None:
    assert quote_identifier("safe_name") == '"safe_name"'

    with pytest.raises(ValueError, match="invalid identifier"):
        quote_identifier('records"; DROP TABLE records; --')


def test_trino_server_keeps_sql_policy_compatibility_exports() -> None:
    assert mcp_trino_server.SqlSafetyError is SqlSafetyError
    assert mcp_trino_server.AllowlistError is AllowlistError
    assert mcp_trino_server.validate_safe_select is validate_safe_select
