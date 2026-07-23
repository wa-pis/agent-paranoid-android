import pytest

from test_data_agent.mcp_trino_server import (
    AllowlistError,
    SqlSafetyError,
    TrinoConfig,
    TrinoConfigurationError,
    TrinoResultLimitError,
    check_allowlist,
    execute_query,
    has_top_level_limit,
    mask_row,
    profile_aggregate_mapping,
    profile_column_safe,
    profile_conditional_allowed_values,
    profile_conditional_required,
    profile_foreign_key,
    profile_formula_rule,
    profile_table_safe,
    profile_temporal_ordering,
    validate_table_references_allowed,
    validate_safe_select,
)


@pytest.fixture(autouse=True)
def allow_unrestricted_unit_test_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRINO_ALLOW_UNRESTRICTED", "true")


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


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT id FROM users LIMIT 0",
        "SELECT id FROM users LIMIT 1001",
        "SELECT id FROM users LIMIT 10 + 1",
    ],
)
def test_safe_select_rejects_unbounded_or_nonliteral_limit(sql: str) -> None:
    with pytest.raises(SqlSafetyError, match="LIMIT"):
        validate_safe_select(sql)


def test_safe_select_rejects_likely_pii_even_with_safe_alias() -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select("SELECT customer_email AS value FROM analytics.safe_schema.users LIMIT 10")


def test_safe_select_rejects_pii_hidden_behind_cte_alias() -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select(
            "WITH source AS (SELECT customer_email AS value FROM analytics.safe_schema.users) "
            "SELECT value FROM source LIMIT 1"
        )


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a.id FROM analytics.safe_schema.users a CROSS JOIN analytics.safe_schema.users b LIMIT 10",
        "SELECT id FROM analytics.safe_schema.users ORDER BY rand() LIMIT 10",
    ],
)
def test_safe_select_rejects_work_expanding_query_shapes(sql: str) -> None:
    with pytest.raises(SqlSafetyError):
        validate_safe_select(sql)


def test_safe_select_enforces_allowlist_for_table_references() -> None:
    config = TrinoConfig(
        host="localhost",
        port=8080,
        user="agent",
        http_scheme="https",
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
        http_scheme="https",
        allowed_catalogs=frozenset({"analytics"}),
        allowed_schemas=frozenset({"safe_schema"}),
    )

    check_allowlist(catalog="analytics", schema="safe_schema", config=config)
    with pytest.raises(AllowlistError):
        check_allowlist(catalog="raw", schema="safe_schema", config=config)
    with pytest.raises(AllowlistError):
        check_allowlist(catalog="analytics", schema="pii", config=config)


def test_trino_config_requires_catalog_and_schema_allowlists_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TRINO_ALLOW_UNRESTRICTED")
    monkeypatch.delenv("TRINO_ALLOWED_CATALOGS", raising=False)
    monkeypatch.delenv("TRINO_ALLOWED_SCHEMAS", raising=False)

    with pytest.raises(TrinoConfigurationError, match="are required"):
        TrinoConfig.from_env()


def test_trino_config_rejects_plain_http_without_explicit_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "analytics")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "safe_schema")
    monkeypatch.setenv("TRINO_HTTP_SCHEME", "http")

    with pytest.raises(TrinoConfigurationError, match="plain HTTP is disabled"):
        TrinoConfig.from_env()

    monkeypatch.setenv("TRINO_ALLOW_INSECURE_HTTP", "true")
    assert TrinoConfig.from_env().http_scheme == "http"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("TRINO_QUERY_MAX_EXECUTION_TIME", "0s"),
        ("TRINO_QUERY_MAX_EXECUTION_TIME", "30 seconds"),
        ("TRINO_QUERY_MAX_EXECUTION_TIME", "2h"),
        ("TRINO_QUERY_MAX_RUN_TIME", "3h"),
        ("TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES", "101GB"),
        ("TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES", "1TB"),
        ("TRINO_REQUEST_TIMEOUT_SECONDS", "nan"),
        ("TRINO_REQUEST_TIMEOUT_SECONDS", "301"),
        ("TRINO_PORT", "0"),
    ],
)
def test_trino_config_rejects_invalid_resource_budgets(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(TrinoConfigurationError):
        TrinoConfig.from_env()


def test_trino_config_requires_run_budget_to_cover_execution_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_QUERY_MAX_EXECUTION_TIME", "30s")
    monkeypatch.setenv("TRINO_QUERY_MAX_RUN_TIME", "20s")

    with pytest.raises(TrinoConfigurationError, match="greater than or equal"):
        TrinoConfig.from_env()


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


def test_sensitive_values_are_masked_even_with_neutral_column_names() -> None:
    row = {
        "value": "alice@example.com",
        "note": "sk_live_51ABCDEF",
        "status": "paid",
    }

    masked = mask_row(row)

    assert masked["value"] != row["value"]
    assert masked["note"] != row["note"]
    assert masked["status"] == "paid"


def test_profile_column_safe_suppresses_secret_top_values(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch_dicts(sql: str, parameters=None):
        if "GROUP BY" in sql:
            return [{"value": "sk_live_51ABCDEF", "count": 2}]
        return [{"row_count": 2, "non_null_count": 2, "approx_distinct_count": 1}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server.fetch_dicts", fake_fetch_dicts)

    profile = profile_column_safe(
        "analytics",
        "safe_schema",
        "settings",
        "value",
        "varchar",
        False,
        20,
    )

    assert profile["sensitive"] is True
    assert profile["semantic_type"] == "secret"
    assert profile["masked_patterns"] == [{"pattern": "secret", "count": 2}]
    assert "top_values" not in profile
    assert "sk_live_51ABCDEF" not in str(profile)


def test_execute_query_closes_cursor_and_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCursor:
        description = [("id",)]

        def __init__(self) -> None:
            self.closed = False

        def execute(self, sql, parameters):
            assert sql == "SELECT id FROM users LIMIT 1"
            assert parameters == []

        def fetchmany(self, size):
            assert size == 10_001
            return [(1,)]

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def close(self):
            self.closed = True

    class FakeDbapi:
        def __init__(self) -> None:
            self.connection = FakeConnection()
            self.connect_kwargs = None

        def connect(self, **kwargs):
            self.connect_kwargs = kwargs
            return self.connection

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = FakeDbapi()

    fake_trino = FakeTrino()
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)

    rows, description = execute_query("SELECT id FROM users LIMIT 1")

    assert rows == [(1,)]
    assert description == [("id",)]
    assert fake_trino.dbapi.connection.cursor_instance.closed is True
    assert fake_trino.dbapi.connection.closed is True
    assert fake_trino.dbapi.connect_kwargs["session_properties"] == {
        "query_max_execution_time": "30s",
        "query_max_run_time": "45s",
        "query_max_scan_physical_bytes": "1GB",
    }


def test_execute_query_closes_resources_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCursor:
        description = None

        def __init__(self) -> None:
            self.closed = False

        def execute(self, sql, parameters):
            raise RuntimeError("boom")

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def close(self):
            self.closed = True

    class FakeDbapi:
        def __init__(self) -> None:
            self.connection = FakeConnection()

        def connect(self, **kwargs):
            return self.connection

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = FakeDbapi()

    fake_trino = FakeTrino()
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)

    with pytest.raises(RuntimeError, match="boom"):
        execute_query("SELECT id FROM users LIMIT 1")

    assert fake_trino.dbapi.connection.cursor_instance.closed is True
    assert fake_trino.dbapi.connection.closed is True


def test_execute_query_closes_connection_when_cursor_close_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCursor:
        description = [("id",)]

        def execute(self, sql, parameters):
            pass

        def fetchmany(self, size):
            assert size == 10_001
            return [(1,)]

        def close(self):
            raise RuntimeError("cursor close failed")

    class FakeConnection:
        def __init__(self) -> None:
            self.closed = False

        def cursor(self):
            return FakeCursor()

        def close(self):
            self.closed = True

    class FakeDbapi:
        def __init__(self) -> None:
            self.connection = FakeConnection()

        def connect(self, **kwargs):
            return self.connection

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = FakeDbapi()

    fake_trino = FakeTrino()
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)

    with pytest.raises(RuntimeError, match="cursor close failed"):
        execute_query("SELECT id FROM users LIMIT 1")

    assert fake_trino.dbapi.connection.closed is True


def test_execute_query_rejects_oversized_result_and_closes_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCursor:
        description = [("id",)]

        def __init__(self) -> None:
            self.closed = False

        def execute(self, sql, parameters):
            pass

        def fetchmany(self, size):
            assert size == 3
            return [(1,), (2,), (3,)]

        def close(self):
            self.closed = True

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()
            self.closed = False

        def cursor(self):
            return self.cursor_instance

        def close(self):
            self.closed = True

    class FakeDbapi:
        def __init__(self) -> None:
            self.connection = FakeConnection()

        def connect(self, **kwargs):
            return self.connection

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = FakeDbapi()

    fake_trino = FakeTrino()
    monkeypatch.setenv("TRINO_MAX_RESULT_ROWS", "2")
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)

    with pytest.raises(TrinoResultLimitError, match="limit of 2 rows"):
        execute_query("SELECT id FROM users LIMIT 3")

    assert fake_trino.dbapi.connection.cursor_instance.closed is True
    assert fake_trino.dbapi.connection.closed is True


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
