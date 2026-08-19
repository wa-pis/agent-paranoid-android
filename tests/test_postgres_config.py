from __future__ import annotations

from dataclasses import replace

import pytest

from test_data_agent.postgres_config import (
    PostgresConfig,
    PostgresConfigurationError,
    parse_postgres_column_selector,
    parse_postgres_jdbc_url,
    with_resolved_postgres_columns,
)


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_SOURCE_ID", "hr")
    monkeypatch.setenv("POSTGRES_HOST", "postgres.internal")
    monkeypatch.setenv("POSTGRES_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DATABASE", "analytics")
    monkeypatch.setenv("POSTGRES_USER", "synthetic_agent")
    monkeypatch.setenv("POSTGRES_PASSWORD_ENV", "POSTGRES_TEST_PASSWORD")
    monkeypatch.setenv("POSTGRES_ALLOWED_SCHEMAS", "public")
    monkeypatch.setenv("POSTGRES_ALLOWED_TABLES", "public.employees")
    monkeypatch.setenv(
        "POSTGRES_ALLOWED_COLUMNS",
        "public.employees.employee_id,public.employees.status",
    )


def test_postgres_config_loads_explicit_scope_and_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_STATEMENT_TIMEOUT_MS", "20000")
    monkeypatch.setenv("POSTGRES_LOCK_TIMEOUT_MS", "2000")
    monkeypatch.setenv("POSTGRES_MAX_TABLES", "5")
    monkeypatch.setenv("POSTGRES_MAX_COLUMNS", "20")
    monkeypatch.setenv("POSTGRES_MAX_STATEMENTS", "30")
    monkeypatch.setenv("POSTGRES_MAX_RESULT_ROWS", "40")
    monkeypatch.setenv("POSTGRES_MAX_RESULT_CELLS", "200")
    monkeypatch.setenv("POSTGRES_MAX_SECONDS", "15")

    config = PostgresConfig.from_env()

    assert config.source_id == "hr"
    assert config.port == 5433
    assert config.allowed_schemas == frozenset({"public"})
    assert config.allowed_tables == frozenset({"public.employees"})
    assert config.allowed_columns == frozenset(
        {"public.employees.employee_id", "public.employees.status"}
    )
    assert config.statement_timeout_ms == 20_000
    assert config.lock_timeout_ms == 2_000
    assert config.limits.max_result_cells == 200
    assert config.limits.max_seconds == 15


@pytest.mark.parametrize(
    "name",
    [
        "POSTGRES_ALLOWED_SCHEMAS",
        "POSTGRES_ALLOWED_TABLES",
        "POSTGRES_ALLOWED_COLUMNS",
    ],
)
def test_postgres_config_requires_every_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.delenv(name)

    with pytest.raises(PostgresConfigurationError, match=f"{name} is required"):
        PostgresConfig.from_env()


@pytest.mark.parametrize(
    ("name", "value", "expected"),
    [
        ("POSTGRES_ALLOWED_SCHEMAS", "pub*", "schema identifiers"),
        ("POSTGRES_ALLOWED_TABLES", "public", "schema.table identifiers"),
        (
            "POSTGRES_ALLOWED_COLUMNS",
            "public.employees",
            "schema.table.column identifiers",
        ),
    ],
)
def test_postgres_config_rejects_malformed_scope(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
    expected: str,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv(name, value)

    with pytest.raises(PostgresConfigurationError, match=expected):
        PostgresConfig.from_env()


def test_postgres_config_rejects_scope_escalation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_ALLOWED_COLUMNS", "private.payroll.salary")

    with pytest.raises(PostgresConfigurationError, match="within allowed tables"):
        PostgresConfig.from_env()


def test_postgres_config_accepts_only_table_qualified_column_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_ALLOWED_COLUMNS", "public.employees.*")

    config = PostgresConfig.from_env()
    selector = parse_postgres_column_selector(next(iter(config.allowed_columns)))

    assert selector.is_wildcard is True
    assert selector.table_name == "public.employees"


@pytest.mark.parametrize(
    "value",
    ["*", "public.*", "*.employees.*", "public.*.*", "public.employees.sta*"],
)
def test_postgres_config_rejects_unqualified_or_pattern_wildcards(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_ALLOWED_COLUMNS", value)

    with pytest.raises(PostgresConfigurationError, match="schema.table.column"):
        PostgresConfig.from_env()


def test_internal_resolved_snapshot_cannot_broaden_exact_selectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    config = PostgresConfig.from_env()

    with pytest.raises(PostgresConfigurationError, match="exact allowed columns"):
        with_resolved_postgres_columns(
            config,
            frozenset(
                {
                    "public.employees.employee_id",
                    "public.employees.private_note",
                }
            ),
        )


def test_postgres_config_validates_direct_scope_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    config = PostgresConfig.from_env()

    with pytest.raises(PostgresConfigurationError, match="schema.table identifiers"):
        replace(config, allowed_tables=frozenset({"public"})).validate()


def test_postgres_config_keeps_secret_value_outside_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("POSTGRES_TEST_PASSWORD", "do-not-store-this")

    config = PostgresConfig.from_env()

    assert config.password_env == "POSTGRES_TEST_PASSWORD"
    assert "do-not-store-this" not in repr(config)


def test_postgres_config_rejects_unbounded_or_insecure_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    config = PostgresConfig.from_env()

    with pytest.raises(PostgresConfigurationError, match="POSTGRES_MAX_TABLES"):
        replace(config, limits=replace(config.limits, max_tables=1_001)).validate()

    with pytest.raises(PostgresConfigurationError, match="ALLOW_INSECURE"):
        replace(config, sslmode="disable").validate()


def test_postgres_jdbc_url_normalizes_into_existing_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    for name in (
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DATABASE",
        "POSTGRES_SSLMODE",
    ):
        monkeypatch.delenv(name, raising=False)
    jdbc_url = (
        "jdbc:postgresql://postgres.example.test:5444/analytics?sslmode=verify-full"
    )
    monkeypatch.setenv("POSTGRES_JDBC_URL", jdbc_url)

    config = PostgresConfig.from_env()

    assert config.host == "postgres.example.test"
    assert config.port == 5444
    assert config.database == "analytics"
    assert config.sslmode == "verify-full"
    assert jdbc_url not in repr(config)


def test_postgres_jdbc_url_accepts_equal_explicit_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv(
        "POSTGRES_JDBC_URL",
        "jdbc:postgresql://postgres.internal:5433/analytics?sslmode=require",
    )

    config = PostgresConfig.from_env()

    assert config.host == "postgres.internal"
    assert config.port == 5433


def test_postgres_jdbc_url_uses_existing_default_port() -> None:
    endpoint = parse_postgres_jdbc_url(
        "jdbc:postgresql://postgres.example.test/analytics"
    )

    assert endpoint.port is None
    assert endpoint.database == "analytics"


def test_postgres_jdbc_url_rejects_component_conflicts_without_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    jdbc_url = "jdbc:postgresql://private.example.test:5433/analytics"
    monkeypatch.setenv("POSTGRES_JDBC_URL", jdbc_url)

    with pytest.raises(PostgresConfigurationError) as captured:
        PostgresConfig.from_env()

    assert str(captured.value) == (
        "POSTGRES_JDBC_URL conflicts with explicit component configuration"
    )
    assert "private.example.test" not in str(captured.value)


def test_postgres_jdbc_url_detaches_invalid_explicit_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv(
        "POSTGRES_JDBC_URL",
        "jdbc:postgresql://postgres.internal/analytics",
    )
    monkeypatch.setenv("POSTGRES_PORT", "secret-port")

    with pytest.raises(PostgresConfigurationError) as captured:
        PostgresConfig.from_env()

    assert str(captured.value) == "POSTGRES_PORT must be an integer"
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True


@pytest.mark.parametrize(
    "jdbc_url",
    [
        "jdbc:postgresql://reader:secret@postgres.test:5432/app",
        "jdbc:postgresql://postgres.test:5432/app?password=secret",
        "jdbc:postgresql://postgres.test:5432/app?sslmode=require&sslmode=verify-full",
        "jdbc:postgresql://postgres.test:5432/app?sslmode=require%20",
        "jdbc:postgresql://postgres.test:5432/app?options=-csearch_path%3Dprivate",
        "jdbc:postgresql://postgres.test:5432/app#secret",
        "jdbc:postgresql://postgres.test:secret/app",
        "jdbc:postgresql://postgres%0Atest:5432/app",
        "jdbc:postgresql://postgres.test:5432/app%ZZ",
        "jdbc:postgresql://postgres.test:5432/app/extra",
    ],
)
def test_postgres_jdbc_url_fails_closed_without_echoing_input(
    jdbc_url: str,
) -> None:
    with pytest.raises(PostgresConfigurationError) as captured:
        parse_postgres_jdbc_url(jdbc_url)

    assert str(captured.value) == (
        "POSTGRES_JDBC_URL must be a credential-free PostgreSQL JDBC endpoint"
    )
    assert "secret" not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__suppress_context__ is True
