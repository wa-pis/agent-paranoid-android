from __future__ import annotations

from dataclasses import replace

import pytest

from test_data_agent.postgres_config import (
    PostgresConfig,
    PostgresConfigurationError,
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
