import pytest

from test_data_agent.mcp_trino_server import (
    AllowlistError,
    SqlSafetyError,
    TrinoConfig,
    check_allowlist,
    has_top_level_limit,
    mask_row,
    validate_table_references_allowed,
    validate_safe_select,
)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO users VALUES (1)",
        "UPDATE users SET name = 'x'",
        "DELETE FROM users",
        "MERGE INTO users USING other ON users.id = other.id WHEN MATCHED THEN UPDATE SET id = other.id",
        "DROP TABLE users",
        "TRUNCATE TABLE users",
        "ALTER TABLE users ADD COLUMN x integer",
        "CREATE TABLE users (id integer)",
        "GRANT SELECT ON TABLE users TO someone",
        "REVOKE SELECT ON TABLE users FROM someone",
        "CALL system.flush_metadata_cache()",
    ],
)
def test_unsafe_sql_is_rejected(sql: str) -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM users LIMIT 10",
        "SELECT u.* FROM users u LIMIT 10",
        "SELECT id FROM users",
        "SELECT id FROM users LIMIT 10; DROP TABLE users",
    ],
)
def test_unrestricted_or_unbounded_select_is_rejected(sql: str) -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select(sql)


def test_safe_select_with_limit_is_allowed() -> None:
    assert validate_safe_select("SELECT id, count(*) AS n FROM users GROUP BY id LIMIT 10") == (
        "SELECT id, count(*) AS n FROM users GROUP BY id LIMIT 10"
    )


def test_limit_must_be_top_level_not_inside_literal() -> None:
    assert has_top_level_limit("SELECT id FROM users WHERE note = 'limit 1'") is False
    with pytest.raises(SqlSafetyError):
        validate_safe_select("SELECT id FROM users WHERE note = 'limit 1'")


def test_safe_select_rejects_likely_pii_even_with_safe_alias() -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select("SELECT customer_email AS value FROM analytics.safe_schema.users LIMIT 10")


def test_safe_select_enforces_allowlist_for_table_references() -> None:
    config = TrinoConfig(
        host="localhost",
        port=8080,
        user="agent",
        http_scheme="http",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe_schema"}),
    )

    validate_table_references_allowed("SELECT id FROM analytics.safe_schema.users LIMIT 10", config=config)
    with pytest.raises(AllowlistError):
        validate_table_references_allowed("SELECT id FROM raw.safe_schema.users LIMIT 10", config=config)
    with pytest.raises(AllowlistError):
        validate_table_references_allowed("SELECT id FROM users LIMIT 10", config=config)


def test_safe_select_uses_env_allowlists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "analytics")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "safe_schema")

    validate_safe_select("SELECT id FROM analytics.safe_schema.users LIMIT 10")
    with pytest.raises(AllowlistError):
        validate_safe_select("SELECT id FROM raw.safe_schema.users LIMIT 10")
    with pytest.raises(AllowlistError):
        validate_safe_select("SELECT id FROM users LIMIT 10")


def test_allowlist_rejects_catalog_and_schema() -> None:
    config = TrinoConfig(
        host="localhost",
        port=8080,
        user="agent",
        http_scheme="http",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe_schema"}),
    )

    check_allowlist(catalog="analytics", schema="safe_schema", config=config)
    with pytest.raises(AllowlistError):
        check_allowlist(catalog="raw", schema="safe_schema", config=config)
    with pytest.raises(AllowlistError):
        check_allowlist(catalog="analytics", schema="pii", config=config)


def test_likely_pii_fields_are_masked() -> None:
    row = {
        "customer_email": "person@example.com",
        "api_token": "secret-token",
        "order_id": 123,
    }

    assert mask_row(row) == {
        "customer_email": "p***m",
        "api_token": "s***n",
        "order_id": 123,
    }
