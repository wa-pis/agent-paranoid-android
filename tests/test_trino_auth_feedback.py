"""Fictional authentication failures exercise actual service boundaries offline."""
import base64
import json
import os
import traceback
from types import SimpleNamespace

import pytest
import requests

from test_data_agent import cli_commands, mcp_trino_server
from test_data_agent.audit import audited_mcp_tool
from test_data_agent.cli import main
from test_data_agent.sql_query_adapters import profile_trino_query_source
from test_data_agent.sql_query_profiling import SqlQueryProfileError
from test_data_agent.sql_query_source import SqlQueryAdapter, SqlQueryProfileRequest
from test_data_agent.trino_auth import TrinoAuthConfig
from test_data_agent.trino_client import TrinoClient
from test_data_agent.trino_config import TrinoConfig, TrinoConfigurationError

CANARY = "fictional-auth-canary-never-a-real-credential"


def configure(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("TRINO_", "TEST_DATA_AGENT_AUDIT_")):
            monkeypatch.delenv(key)
    for key, value in {
        "TRINO_HOST": "fictional.test", "TRINO_PORT": "8443",
        "TRINO_USER": "fictional", "TRINO_HTTP_SCHEME": "https",
        "TRINO_ALLOWED_CATALOGS": "lake", "TRINO_ALLOWED_SCHEMAS": "safe",
        "TRINO_ALLOWED_TABLE_COLUMNS": "lake.safe.orders.amount",
        "TRINO_AUTH_METHOD": "basic", "TRINO_AUTH_SECRET_ENV": "FICTIONAL_AUTH_SECRET",
        "FICTIONAL_AUTH_SECRET": CANARY,
    }.items():
        monkeypatch.setenv(key, value)


def failing_driver(error, stage, seen):
    def execute(*args):
        seen.append("execute")
        if stage == "execute":
            raise error
    def fetchmany(*args):
        seen.append("fetch")
        raise error
    cursor = SimpleNamespace(execute=execute, fetchmany=fetchmany,
        description=[("Column",), ("Type",), ("Extra",), ("Comment",)],
        close=lambda: seen.append("cursor_closed"))
    connection = SimpleNamespace(cursor=lambda: cursor, close=lambda: seen.append("connection_closed"))
    def connect(**kwargs):
        assert kwargs["http_scheme"] == "https" and kwargs["verify"] is True
        seen.append("connect")
        if stage == "connect":
            raise error
        return connection
    return SimpleNamespace(dbapi=SimpleNamespace(connect=connect),
        auth=SimpleNamespace(BasicAuthentication=lambda user, password: object()))


@pytest.mark.parametrize("kind", ["401", "403", "tls"])
@pytest.mark.parametrize("stage", ["connect", "execute", "fetch"])
def test_auth_failure_canaries_do_not_cross_profile_cli_mcp_or_audit(
    tmp_path, monkeypatch, capsys, caplog, kind, stage,
):
    configure(monkeypatch)
    error = (requests.exceptions.SSLError(CANARY) if kind == "tls" else
             requests.HTTPError(CANARY, response=SimpleNamespace(status_code=int(kind))))
    seen = []
    driver = failing_driver(error, stage, seen)
    query = tmp_path / "query.sql"
    query.write_text("SELECT amount FROM lake.safe.orders")
    config = TrinoConfig.from_env()
    assert CANARY not in repr(config)
    assert CANARY not in repr(config.authentication)
    request = SqlQueryProfileRequest(SqlQueryAdapter.TRINO, "fictional", "summary", query)
    with pytest.raises(SqlQueryProfileError, match="^SQL query source profiling failed$") as caught:
        profile_trino_query_source(request, config=config, driver=driver)
    assert CANARY not in ''.join(traceback.format_exception(caught.value))
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None

    audit = tmp_path / "audit.jsonl"
    monkeypatch.setenv("TEST_DATA_AGENT_AUDIT_LOG", str(audit))
    monkeypatch.setenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY", base64.b64encode(b"f" * 32).decode())
    monkeypatch.setattr(mcp_trino_server, "trino", driver)
    tool = audited_mcp_tool("trino-mcp", mcp_trino_server.profile_column_safe)
    with pytest.raises(RuntimeError, match="Trino request failed") as mcp_error:
        tool("lake", "safe", "orders", "amount", "bigint", True, 5)
    assert CANARY not in ''.join(traceback.format_exception(mcp_error.value))
    assert mcp_error.value.__cause__ is None
    assert mcp_error.value.__context__ is None
    assert CANARY not in audit.read_text()
    assert CANARY not in caplog.text

    real = cli_commands.DEFAULT_CLI_DEPENDENCY_RESOLVER
    monkeypatch.setattr(cli_commands, "DEFAULT_CLI_DEPENDENCY_RESOLVER", SimpleNamespace(
        require_module=lambda name, **kwargs: driver if name == "trino" else
                       real.require_module(name, **kwargs)))
    output = tmp_path / "profile.json"
    output.write_text('{"previous":"fictional"}')
    before = output.read_bytes()
    assert main(["--json", "profile-query", str(query), "--adapter", "trino",
                 "--source-id", "fictional", "--entity", "summary", "--output", str(output),
                 "--overwrite"]) == 69
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "external_service"
    assert CANARY not in captured.out + captured.err + caplog.text
    assert output.read_bytes() == before
    assert "connect" in seen
    if stage != "connect":
        assert "cursor_closed" in seen and "connection_closed" in seen


@pytest.mark.parametrize("method", ["basic", "jwt", "kerberos", "gssapi", "oauth2", "certificate"])
def test_every_auth_method_rejects_http_even_with_insecure_override(monkeypatch, method):
    configure(monkeypatch)
    monkeypatch.setenv("TRINO_AUTH_METHOD", method)
    monkeypatch.setenv("TRINO_HTTP_SCHEME", "http")
    monkeypatch.setenv("TRINO_ALLOW_INSECURE_HTTP", "true")
    auth = TrinoAuthConfig.from_env(os.environ)
    with pytest.raises(TrinoConfigurationError, match="verified HTTPS") as caught:
        auth.build(driver_auth=None, environ={}, username="fictional", http_scheme="http")
    assert CANARY not in str(caught.value)


@pytest.mark.parametrize("method", ["basic", "jwt"])
@pytest.mark.parametrize("secret", [None, "", "fictional\nsecret", "f" * 65537])
def test_incomplete_or_invalid_credentials_reject_before_connection(monkeypatch, method, secret):
    configure(monkeypatch)
    monkeypatch.setenv("TRINO_AUTH_METHOD", method)
    if secret is None:
        monkeypatch.delenv("FICTIONAL_AUTH_SECRET")
    else:
        monkeypatch.setenv("FICTIONAL_AUTH_SECRET", secret)
    calls = []
    driver = SimpleNamespace(
        auth=SimpleNamespace(BasicAuthentication=lambda *args: calls.append("auth"),
                             JWTAuthentication=lambda *args: calls.append("auth")),
        dbapi=SimpleNamespace(connect=lambda **kwargs: calls.append("connect")),
    )
    with pytest.raises(TrinoConfigurationError, match="missing or invalid") as caught:
        TrinoClient(config=TrinoConfig.from_env(), driver=driver).fetch_dicts(
            "SELECT amount FROM lake.safe.orders")
    assert calls == []
    assert CANARY not in str(caught.value)
    assert caught.value.__context__ is None


def test_credential_bearing_endpoint_rejects_without_reflecting_secret(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv("TRINO_JDBC_URL", f"jdbc:trino://fictional:{CANARY}@fictional.test:8443/lake/safe")
    with pytest.raises(TrinoConfigurationError) as caught:
        TrinoConfig.from_env()
    assert CANARY not in ''.join(traceback.format_exception(caught.value))


def test_missing_certificate_paths_are_runtime_only_and_value_free(tmp_path):
    config = TrinoAuthConfig(method="certificate", certificate_env="FICTIONAL_CERT", key_env="FICTIONAL_KEY")
    with pytest.raises(TrinoConfigurationError, match="missing or unreadable") as caught:
        config.build(driver_auth=SimpleNamespace(CertificateAuthentication=lambda *args: None),
            environ={"FICTIONAL_CERT": str(tmp_path / CANARY), "FICTIONAL_KEY": str(tmp_path / "key")},
            username="fictional", http_scheme="https")
    assert CANARY not in str(caught.value)
    assert caught.value.__context__ is None
