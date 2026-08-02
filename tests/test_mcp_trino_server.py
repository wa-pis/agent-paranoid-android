from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from test_data_agent import mcp_trino_server, trino_masking, trino_query_builders
from test_data_agent.mcp_trino_server import (
    AllowlistError,
    SqlSafetyError,
    TrinoConfig,
    TrinoConfigurationError,
    TrinoResultLimitError,
    check_allowlist,
    describe_table,
    has_top_level_limit,
    list_catalogs,
    list_schemas,
    list_tables,
    mask_row,
    profile_aggregate_mapping,
    profile_column_safe,
    profile_conditional_allowed_values,
    profile_conditional_required,
    profile_foreign_key,
    profile_formula_rule,
    profile_column,
    profile_table,
    profile_table_safe,
    profile_temporal_ordering,
    run_safe_select,
    trino_mcp_services,
    trino_mcp_tools,
    validate_table_references_allowed,
    validate_safe_select,
)
from test_data_agent.trino_work_budget import (
    DEFAULT_QUERY_WORK_LIMITS,
    QueryWorkBudgetExceeded,
)
from tests.trino_source_literals import (
    SOURCE_ROWS,
    assert_source_literals_absent,
)


DEFAULT_TOOL_ARGUMENTS: dict[str, dict[str, Any]] = {
    "list_catalogs": {},
    "list_schemas": {"catalog": "analytics"},
    "list_tables": {"catalog": "analytics", "schema": "safe_schema"},
    "describe_table": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
    },
    "profile_table": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
    },
    "profile_column": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
        "column": "amount",
    },
    "profile_table_safe": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
    },
    "profile_foreign_key": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "parent_table": "synthetic_customers",
        "parent_field": "customer_id",
        "child_table": "synthetic_orders",
        "child_field": "customer_id",
    },
    "profile_temporal_ordering": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
        "start_field": "created_at",
        "end_field": "fulfilled_at",
    },
    "profile_formula_rule": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
        "target_field": "total",
        "expression": "subtotal + tax",
    },
    "profile_conditional_required": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
        "condition_field": "status",
        "condition_equals": "source-literal-condition",
        "required_field": "fulfilled_at",
    },
    "profile_conditional_allowed_values": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "table": "synthetic_orders",
        "condition_field": "kind",
        "condition_equals": "source-literal-kind",
        "value_field": "status",
        "allowed_values": ["source-literal-allowed"],
    },
    "profile_aggregate_mapping": {
        "catalog": "analytics",
        "schema": "safe_schema",
        "parent_table": "synthetic_customers",
        "parent_key": "customer_id",
        "parent_value_field": "lifetime_value",
        "child_table": "synthetic_orders",
        "child_key": "customer_id",
        "child_value_field": "amount",
    },
}


class RecordingProfiler:
    def __init__(
        self,
        failure_message: str | None = None,
        failure_type: type[Exception] = ValueError,
        nested: bool = False,
        source_rows: tuple[dict[str, object], ...] = SOURCE_ROWS,
    ) -> None:
        self.calls: list[str] = []
        self.failure_message = failure_message
        self.failure_type = failure_type
        self.nested = nested
        self.source_count = len(source_rows)

    def __getattr__(self, name: str) -> Any:
        def invoke(*args: Any, **kwargs: Any) -> Any:
            self.calls.append(name)
            if self.failure_message is not None:
                raise self.failure_type(self.failure_message)
            if name == "list_catalogs":
                return ["analytics"]
            if name == "list_schemas":
                return ["safe_schema"]
            if name == "list_tables":
                return ["synthetic_orders"]
            if name == "describe_table":
                if self.nested:
                    return [
                        {
                            "name": "amount",
                            "data_type": "double",
                            "metadata": {"nullable": True},
                        }
                    ]
                return [{"name": "amount", "data_type": "double"}]
            if self.nested:
                return {
                    "tool": name,
                    "summary": {
                        "counts": {
                            "checked": self.source_count,
                            "failed": 0,
                        },
                        "columns": [
                            {
                                "name": "synthetic_metric",
                                "metrics": {"null_ratio": 0.0},
                            }
                        ],
                    },
                }
            return {
                "tool": name,
                "counts": {"checked": self.source_count, "failed": 0},
            }

        return invoke


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


def test_safe_select_accepts_explicit_doctor_config() -> None:
    config = TrinoConfig(
        host="doctor.invalid",
        port=443,
        user="doctor",
        http_scheme="https",
        allowed_catalogs=frozenset({"doctor"}),
        allowed_schemas=frozenset({"safe"}),
    )

    assert validate_safe_select(
        "SELECT synthetic_id FROM doctor.safe.synthetic_table LIMIT 1",
        config=config,
    ) == "SELECT synthetic_id FROM doctor.safe.synthetic_table LIMIT 1"


def test_raw_sql_tool_is_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    assert "run_safe_select" not in {tool.__name__ for tool in trino_mcp_tools()}

    monkeypatch.setenv("TRINO_ENABLE_SAFE_SELECT", "true")
    assert "run_safe_select" in {tool.__name__ for tool in trino_mcp_tools()}


def test_safe_select_shares_preflight_budget_without_opening_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sql = (
        "SELECT synthetic_id FROM analytics.safe_schema.customers "
        "LIMIT 1"
    )

    class RejectingDbApi:
        def __init__(self) -> None:
            self.connect_calls = 0

        def connect(self, **_: object) -> None:
            self.connect_calls += 1
            raise AssertionError("budget failure must precede Trino connection")

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = RejectingDbApi()

    fake_trino = FakeTrino()
    limits = replace(
        DEFAULT_QUERY_WORK_LIMITS,
        sql_formula_chars=2 * len(sql),
    )
    monkeypatch.setenv("TRINO_ENABLE_SAFE_SELECT", "true")
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)
    service = next(
        tool
        for tool in trino_mcp_services(work_limits=limits)
        if tool.__name__ == "run_safe_select"
    )

    with pytest.raises(QueryWorkBudgetExceeded, match="SQL/formula characters"):
        service(sql)

    assert fake_trino.dbapi.connect_calls == 0


def test_nested_profile_budget_stops_before_later_column_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed_sql: list[str] = []

    class FakeCursor:
        def __init__(self) -> None:
            self.description: list[tuple[str]] = []
            self.rows: list[tuple[object, ...]] = []
            self.closed = False

        def execute(self, sql: str, parameters: list[object]) -> None:
            executed_sql.append(sql)
            if "information_schema.columns" in sql:
                self.description = [
                    ("column_name",),
                    ("data_type",),
                    ("is_nullable",),
                ]
                self.rows = [
                    ("customer_email", "varchar", "NO"),
                    ("amount", "double", "NO"),
                ]
            elif sql.startswith("SELECT count(*) AS row_count FROM"):
                self.description = [("row_count",)]
                self.rows = [(12,)]
            elif 'approx_distinct("customer_email")' in sql:
                self.description = [
                    ("row_count",),
                    ("non_null_count",),
                    ("approx_distinct_count",),
                ]
                self.rows = [(12, 12, 12)]
            else:
                raise AssertionError(f"unexpected query: {sql}")

        def fetchmany(self, size: int) -> list[tuple[object, ...]]:
            assert size == 1
            batch = self.rows[:size]
            self.rows = self.rows[size:]
            return batch

        def close(self) -> None:
            self.closed = True

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()
            self.closed = False

        def cursor(self) -> FakeCursor:
            return self.cursor_instance

        def close(self) -> None:
            self.closed = True

    class FakeDbApi:
        def __init__(self) -> None:
            self.connections: list[FakeConnection] = []

        def connect(self, **_: object) -> FakeConnection:
            connection = FakeConnection()
            self.connections.append(connection)
            return connection

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = FakeDbApi()

    fake_trino = FakeTrino()
    limits = replace(DEFAULT_QUERY_WORK_LIMITS, statements=3)
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)
    service = next(
        tool
        for tool in trino_mcp_services(work_limits=limits)
        if tool.__name__ == "profile_table_safe"
    )

    with pytest.raises(QueryWorkBudgetExceeded, match="statements"):
        service("analytics", "safe_schema", "orders")

    assert len(fake_trino.dbapi.connections) == 3
    assert len(executed_sql) == 3
    assert any('approx_distinct("customer_email")' in sql for sql in executed_sql)
    assert all('"amount"' not in sql for sql in executed_sql)
    assert all(
        connection.closed and connection.cursor_instance.closed
        for connection in fake_trino.dbapi.connections
    )


def test_row_sampling_surface_is_removed() -> None:
    assert "sample_rows_masked" not in {
        tool.__name__ for tool in trino_mcp_tools()
    }
    assert not hasattr(mcp_trino_server, "sample_rows_masked")
    assert not hasattr(trino_masking.TrinoMasker, "sample_rows_masked")
    assert not hasattr(trino_query_builders, "build_masked_sample_query")


def test_default_tools_complete_direct_service_success_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler()
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr(mcp_trino_server, "_trino_profiler", lambda: profiler)
    tools = trino_mcp_tools()

    outputs = {
        tool.__name__: tool(**DEFAULT_TOOL_ARGUMENTS[tool.__name__])
        for tool in tools
    }

    assert tuple(outputs) == tuple(DEFAULT_TOOL_ARGUMENTS)
    assert profiler.calls == list(DEFAULT_TOOL_ARGUMENTS)
    serialized = json.dumps(outputs, sort_keys=True)
    assert_source_literals_absent(json.loads(serialized))
    for source_literal in (
        "source-literal-condition",
        "source-literal-kind",
        "source-literal-allowed",
    ):
        assert source_literal not in serialized


def test_default_tools_direct_validation_errors_are_source_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler(failure_message="request failed validation")
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr(mcp_trino_server, "_trino_profiler", lambda: profiler)
    errors: dict[str, dict[str, str]] = {}

    for tool in trino_mcp_tools():
        with pytest.raises(ValueError) as error_info:
            tool(**DEFAULT_TOOL_ARGUMENTS[tool.__name__])
        errors[tool.__name__] = {
            "type": type(error_info.value).__name__,
            "message": str(error_info.value),
        }

    assert tuple(errors) == tuple(DEFAULT_TOOL_ARGUMENTS)
    assert profiler.calls == list(DEFAULT_TOOL_ARGUMENTS)
    serialized = json.dumps(errors, sort_keys=True)
    assert_source_literals_absent(json.loads(serialized))
    for source_literal in (
        "source-literal-condition",
        "source-literal-kind",
        "source-literal-allowed",
    ):
        assert source_literal not in serialized


def test_default_tools_direct_database_errors_are_source_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler(
        failure_message="database request failed",
        failure_type=ConnectionError,
    )
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr(mcp_trino_server, "_trino_profiler", lambda: profiler)
    errors: dict[str, dict[str, str]] = {}

    for tool in trino_mcp_tools():
        with pytest.raises(ConnectionError) as error_info:
            tool(**DEFAULT_TOOL_ARGUMENTS[tool.__name__])
        errors[tool.__name__] = {
            "type": type(error_info.value).__name__,
            "message": str(error_info.value),
        }

    assert tuple(errors) == tuple(DEFAULT_TOOL_ARGUMENTS)
    assert profiler.calls == list(DEFAULT_TOOL_ARGUMENTS)
    serialized = json.dumps(errors, sort_keys=True)
    assert_source_literals_absent(json.loads(serialized))
    for source_literal in (
        "source-literal-condition",
        "source-literal-kind",
        "source-literal-allowed",
    ):
        assert source_literal not in serialized


def test_default_tools_direct_nested_responses_round_trip_source_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profiler = RecordingProfiler(nested=True)
    monkeypatch.delenv("TRINO_ENABLE_SAFE_SELECT", raising=False)
    monkeypatch.setattr(mcp_trino_server, "_trino_profiler", lambda: profiler)

    outputs = {
        tool.__name__: tool(**DEFAULT_TOOL_ARGUMENTS[tool.__name__])
        for tool in trino_mcp_tools()
    }
    serialized = json.dumps(outputs, sort_keys=True)

    assert json.loads(serialized) == outputs
    assert_source_literals_absent(json.loads(serialized))
    assert outputs["describe_table"][0]["metadata"] == {"nullable": True}
    for name, output in outputs.items():
        if name.startswith("profile_"):
            assert output["summary"]["columns"][0]["metrics"] == {
                "null_ratio": 0.0
            }
    for source_literal in (
        "source-literal-condition",
        "source-literal-kind",
        "source-literal-allowed",
    ):
        assert source_literal not in serialized


def test_unrestricted_execution_helpers_are_private() -> None:
    assert not hasattr(mcp_trino_server, "execute_query")
    assert not hasattr(mcp_trino_server, "fetch_dicts")


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


@pytest.mark.parametrize(
    ("sql", "error_type"),
    [
        ("DELETE FROM analytics.safe_schema.users", SqlSafetyError),
        (
            "SELECT id FROM raw.safe_schema.users LIMIT 10",
            AllowlistError,
        ),
    ],
)
def test_safe_select_service_rejects_before_cursor_execution(
    monkeypatch: pytest.MonkeyPatch,
    sql: str,
    error_type: type[Exception],
) -> None:
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "analytics")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "safe_schema")

    class FakeCursor:
        def __init__(self) -> None:
            self.executed: list[tuple[str, list[object]]] = []

        def execute(self, query: str, parameters: list[object]) -> None:
            self.executed.append((query, parameters))

    cursor = FakeCursor()

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return cursor

    class FakeDbApi:
        def __init__(self) -> None:
            self.connect_calls = 0

        def connect(self, **_: object) -> FakeConnection:
            self.connect_calls += 1
            return FakeConnection()

    class FakeTrino:
        def __init__(self) -> None:
            self.dbapi = FakeDbApi()

    fake_trino = FakeTrino()
    monkeypatch.setattr("test_data_agent.mcp_trino_server.trino", fake_trino)

    with pytest.raises(error_type):
        run_safe_select(sql)

    assert fake_trino.dbapi.connect_calls == 0
    assert cursor.executed == []


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
        "customer_email": "[MASKED]",
        "api_token": "[MASKED]",
        "order_id": 123,
    }


def test_sensitive_values_are_masked_even_with_neutral_column_names() -> None:
    row = {
        "value": "alice@example.com",
        "note": "sk_live_51ABCDEF",
        "status": "paid",
    }

    masked = mask_row(row)

    assert masked["value"] == "[MASKED]"
    assert masked["note"] == "[MASKED]"
    assert masked["status"] == "paid"


def test_profile_column_safe_suppresses_secret_top_values(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch_dicts(sql: str, parameters=None):
        if "GROUP BY" in sql:
            return [{"value": "sk_live_51ABCDEF", "count": 2}]
        return [{"row_count": 2, "non_null_count": 2, "approx_distinct_count": 1}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

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


def test_profile_column_safe_suppresses_quasi_identifier_categories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_values = ["district-7-house-41", "district-7-house-99"]

    def fake_fetch_dicts(sql: str, parameters=None):
        if "GROUP BY" in sql:
            return [
                {"value": source_values[0], "count": 2},
                {"value": source_values[1], "count": 1},
            ]
        return [{"row_count": 3, "non_null_count": 3, "approx_distinct_count": 2}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

    profile = profile_column_safe(
        "analytics",
        "safe_schema",
        "customers",
        "location_code",
        "varchar",
        False,
        20,
    )

    assert profile["top_values"] == [
        {"value": "category_1", "count": 2},
        {"value": "category_2", "count": 1},
    ]
    assert all(value not in str(profile) for value in source_values)


def test_execute_query_closes_cursor_and_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCursor:
        description = [("id",)]

        def __init__(self) -> None:
            self.closed = False
            self.rows = iter([(1,)])

        def execute(self, sql, parameters):
            assert sql == "SELECT id FROM users LIMIT 1"
            assert parameters == []

        def fetchmany(self, size):
            assert size == 1
            row = next(self.rows, None)
            return [row] if row is not None else []

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

    rows, description = mcp_trino_server._execute_query("SELECT id FROM users LIMIT 1")

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
        mcp_trino_server._execute_query("SELECT id FROM users LIMIT 1")

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
        mcp_trino_server._execute_query("SELECT id FROM users LIMIT 1")

    assert fake_trino.dbapi.connection.closed is True


def test_execute_query_rejects_oversized_result_and_closes_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCursor:
        description = [("id",)]

        def __init__(self) -> None:
            self.closed = False
            self.rows = iter([(1,), (2,), (3,)])

        def execute(self, sql, parameters):
            pass

        def fetchmany(self, size):
            assert size == 1
            row = next(self.rows, None)
            return [row] if row is not None else []

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
        mcp_trino_server._execute_query("SELECT id FROM users LIMIT 3")

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

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

    profile = profile_table_safe("analytics", "safe_schema", "orders")

    email = next(column for column in profile["columns"] if column["name"] == "customer_email")
    status = next(column for column in profile["columns"] if column["name"] == "status")
    amount = next(column for column in profile["columns"] if column["name"] == "amount")

    assert profile["row_count"] == 1000
    assert email["sensitive"] is True
    assert "top_values" not in email
    assert status["top_values"] == [
        {"value": "category_1", "count": 700},
        {"value": "category_2", "count": 290},
    ]
    assert "paid" not in str(status)
    assert "cancelled" not in str(status)
    assert amount["p05"] == 10.0
    assert not any('GROUP BY "customer_email"' in sql for sql in executed_sql)


def test_describe_table_qualifies_information_schema_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_fetch_dicts(sql: str, parameters=None):
        captured["sql"] = sql
        captured["parameters"] = parameters
        return []

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

    assert describe_table("analytics", "safe_schema", "orders") == []
    assert 'FROM "analytics".information_schema.columns' in str(captured["sql"])
    assert captured["parameters"] == ["analytics", "safe_schema", "orders"]


def test_metadata_and_basic_profilers_use_bounded_query_builders(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRINO_ALLOWED_CATALOGS", "analytics")
    monkeypatch.setenv("TRINO_ALLOWED_SCHEMAS", "safe_schema")
    calls: list[tuple[str, list[object]]] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        calls.append((sql, list(parameters or [])))
        if sql == "SHOW CATALOGS":
            return [{"Catalog": "analytics"}, {"Catalog": "raw"}]
        if sql == 'SHOW SCHEMAS FROM "analytics"':
            return [{"Schema": "safe_schema"}, {"Schema": "private"}]
        if sql == 'SHOW TABLES FROM "analytics"."safe_schema"':
            return [{"Table": "orders"}]
        if "information_schema.columns" in sql:
            return [{"column_name": "amount", "data_type": "double", "is_nullable": "NO"}]
        if sql == 'SELECT count(*) AS row_count FROM "analytics"."safe_schema"."orders"':
            return [{"row_count": 12}]
        if 'approx_distinct("amount")' in sql:
            return [{"row_count": 12, "non_null_count": 11, "approx_distinct_count": 9}]
        raise AssertionError(sql)

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

    assert list_catalogs() == ["analytics"]
    assert list_schemas("analytics") == ["safe_schema"]
    assert list_tables("analytics", "safe_schema") == ["orders"]
    assert describe_table("analytics", "safe_schema", "orders")[0]["column_name"] == "amount"
    assert profile_table("analytics", "safe_schema", "orders")["row_count"] == 12
    assert profile_column("analytics", "safe_schema", "orders", "amount")["approx_distinct_count"] == 9

    assert all("SELECT *" not in sql.upper() for sql, _ in calls)
    assert calls[3][1] == ["analytics", "safe_schema", "orders"]


def test_profile_foreign_key_uses_join_counts_only(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        return [{"child_row_count": 100, "checked_count": 98, "matched_count": 97, "orphan_count": 1}]

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

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

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

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

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

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

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

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

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

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


def test_profile_aggregate_mapping_supports_average(monkeypatch: pytest.MonkeyPatch) -> None:
    executed_sql: list[str] = []

    def fake_fetch_dicts(sql: str, parameters=None):
        executed_sql.append(sql)
        return [
            {
                "parent_row_count": 1,
                "checked_count": 1,
                "passed_count": 1,
                "failed_count": 0,
            }
        ]

    monkeypatch.setattr("test_data_agent.mcp_trino_server._fetch_dicts", fake_fetch_dicts)

    profile = profile_aggregate_mapping(
        "analytics",
        "safe_schema",
        "customers",
        "customer_id",
        "orders_amount_average",
        "orders",
        "customer_id",
        "amount",
        aggregate="avg",
    )

    assert profile["aggregate"] == "avg"
    assert 'avg(CAST("amount" AS double))' in executed_sql[0]
