import pytest

from test_data_agent.mcp_trino_server import (
    AllowlistError,
    SqlSafetyError,
    TrinoConfig,
    check_allowlist,
    has_top_level_limit,
    mask_row,
    profile_aggregate_mapping,
    profile_conditional_allowed_values,
    profile_conditional_required,
    profile_foreign_key,
    profile_formula_rule,
    profile_table_safe,
    profile_temporal_ordering,
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


def test_profile_table_safe_uses_aggregates_without_sensitive_top_values(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        if "information_schema.columns" in sql:
            return [
                {"column_name": "customer_email", "data_type": "varchar", "is_nullable": "NO"},
                {"column_name": "status", "data_type": "varchar", "is_nullable": "YES"},
                {"column_name": "amount", "data_type": "double", "is_nullable": "NO"},
            ]
        if sql.startswith("SELECT count(*) AS row_count FROM"):
            return [{"row_count": 1000}]
        if 'approx_distinct("customer_email")' in sql:
            return [{"row_count": 1000, "non_null_count": 1000, "approx_distinct_count": 1000}]
        if 'approx_distinct("status")' in sql:
            return [{"row_count": 1000, "non_null_count": 990, "approx_distinct_count": 2}]
        if 'GROUP BY "status"' in sql:
            return [{"value": "paid", "count": 700}, {"value": "cancelled", "count": 290}]
        if 'approx_distinct("amount")' in sql:
            return [
                {
                    "row_count": 1000,
                    "non_null_count": 1000,
                    "approx_distinct_count": 800,
                    "min_value": 1.0,
                    "max_value": 999.0,
                    "p05": 10.0,
                    "p95": 900.0,
                }
            ]
        raise AssertionError(sql)

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    profile = profile_table_safe("analytics", "safe_schema", "orders")

    email = next(column for column in profile["columns"] if column["name"] == "customer_email")
    status = next(column for column in profile["columns"] if column["name"] == "status")
    amount = next(column for column in profile["columns"] if column["name"] == "amount")

    assert profile["row_count"] == 1000
    assert email["sensitive"] is True
    assert "top_values" not in email
    assert status["top_values"] == [{"value": "paid", "count": 700}, {"value": "cancelled", "count": 290}]
    assert amount["p05"] == 10.0
    assert not any('GROUP BY "customer_email"' in sql for sql in executed_sql)


def test_profile_foreign_key_uses_join_counts_only(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        return [{"child_row_count": 100, "checked_count": 98, "matched_count": 97, "orphan_count": 1}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    profile = profile_foreign_key("analytics", "safe_schema", "customers", "customer_id", "orders", "customer_id")

    assert profile["type"] == "foreign_key"
    assert profile["confidence"] == 0.989796
    assert profile["status"] == "inferred"
    assert profile["failed_count"] == 1
    assert "LEFT JOIN" in executed_sql[0]
    assert "SELECT DISTINCT" in executed_sql[0]
    assert "SELECT *" not in executed_sql[0]


def test_profile_temporal_ordering_uses_count_if(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        return [{"row_count": 10, "checked_count": 10, "passed_count": 9, "failed_count": 1}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    profile = profile_temporal_ordering("analytics", "safe_schema", "orders", "created_at", "paid_at")

    assert profile["type"] == "temporal"
    assert profile["confidence"] == 0.9
    assert profile["status"] == "inferred"
    assert 'count_if("created_at" IS NOT NULL AND "paid_at" IS NOT NULL' in executed_sql[0]


def test_profile_formula_rule_uses_safe_arithmetic_residual(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        return [
            {
                "row_count": 100,
                "checked_count": 100,
                "passed_count": 99,
                "failed_count": 1,
                "avg_abs_error": 0.01,
                "max_abs_error": 1.0,
            }
        ]

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    profile = profile_formula_rule("analytics", "safe_schema", "orders", "amount", "quantity * unit_price")

    assert profile["type"] == "formula"
    assert profile["confidence"] == 0.99
    assert profile["status"] == "inferred"
    assert 'CAST("quantity" AS double) * CAST("unit_price" AS double)' in executed_sql[0]
    assert "avg_abs_error" in executed_sql[0]


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('whoami')",
        "quantity * unit_price; DROP TABLE orders",
        "orders.quantity * unit_price",
    ],
)
def test_profile_formula_rule_rejects_unsafe_expression(expression: str) -> None:
    with pytest.raises(SqlSafetyError):
        profile_formula_rule("analytics", "safe_schema", "orders", "amount", expression)


def test_profile_conditional_rules_use_parameters_without_echoing_values(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        calls.append((sql, list(parameters or [])))
        return [{"row_count": 20, "checked_count": 5, "passed_count": 4, "failed_count": 1}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    required = profile_conditional_required(
        "analytics",
        "safe_schema",
        "orders",
        "status",
        "cancelled",
        "cancel_reason",
    )
    allowed = profile_conditional_allowed_values(
        "analytics",
        "safe_schema",
        "orders",
        "status",
        "paid",
        "payment_state",
        ["captured", "refunded"],
    )

    assert required["type"] == "conditional_required"
    assert allowed["type"] == "conditional_allowed_values"
    assert required["confidence"] == 0.8
    assert required["status"] == "rejected"
    assert required.get("condition_equals") is None
    assert allowed.get("allowed_values") is None
    assert calls[0][1] == ["cancelled", "cancelled", "cancelled"]
    assert calls[1][1] == ["paid", "paid", "captured", "refunded", "paid", "captured", "refunded"]


def test_profile_aggregate_mapping_uses_child_aggregate_cte(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        return [
            {
                "parent_row_count": 10,
                "checked_count": 10,
                "passed_count": 10,
                "failed_count": 0,
                "avg_abs_error": 0.0,
                "max_abs_error": 0.0,
            }
        ]

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    profile = profile_aggregate_mapping(
        "analytics",
        "safe_schema",
        "customers",
        "customer_id",
        "orders_amount_total",
        "orders",
        "customer_id",
        "amount",
    )

    assert profile["type"] == "aggregate_mapping"
    assert profile["confidence"] == 1.0
    assert profile["status"] == "inferred"
    assert "WITH child_agg AS" in executed_sql[0]
    assert 'sum(CAST("amount" AS double))' in executed_sql[0]
