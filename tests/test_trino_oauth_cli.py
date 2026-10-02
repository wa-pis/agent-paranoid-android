from types import SimpleNamespace
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_data_agent.io import commands
from test_data_agent.trino_auth import TrinoAuthConfig
from test_data_agent.trino_config import TrinoConfigurationError


def config():
    return SimpleNamespace(host="fictional.test", port=443, authentication=TrinoAuthConfig(method="oauth2"))


@pytest.mark.parametrize("input_tty,output_tty", [(False, False), (True, False), (False, True)])
def test_oauth_browser_rejects_noninteractive_cli(monkeypatch, input_tty, output_tty):
    monkeypatch.setattr(commands.sys, "stdin", SimpleNamespace(isatty=lambda: input_tty))
    monkeypatch.setattr(commands.sys, "stdout", SimpleNamespace(isatty=lambda: output_tty))
    with pytest.raises(TrinoConfigurationError, match="interactive terminal"):
        commands._cli_trino_oauth_redirect(config())


def test_oauth_browser_uses_explicit_safe_redirect_without_console_output(monkeypatch, capsys):
    monkeypatch.setattr(commands.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(commands.sys.stdout, "isatty", lambda: True)
    opened = []
    monkeypatch.setattr(commands.webbrowser, "open", lambda url, **kwargs: opened.append(url) or True)
    redirect = commands._cli_trino_oauth_redirect(config())
    redirect("https://fictional.test/oauth?state=fictional-state")
    assert len(opened) == 1
    assert capsys.readouterr() == ("", "")
    for url in ("http://fictional.test/oauth", "https://elsewhere.test/oauth", "https://fictional.test:bad/oauth"):
        with pytest.raises(TrinoConfigurationError) as caught:
            redirect(url)
        assert url not in str(caught.value)
        assert caught.value.__context__ is None
    assert len(opened) == 1


def test_oauth_browser_failure_does_not_expose_url(monkeypatch):
    monkeypatch.setattr(commands.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(commands.sys.stdout, "isatty", lambda: True)
    def fail(url, **kwargs):
        raise RuntimeError(url)
    monkeypatch.setattr(commands.webbrowser, "open", fail)
    redirect = commands._cli_trino_oauth_redirect(config())
    with pytest.raises(TrinoConfigurationError) as caught:
        redirect("https://fictional.test/oauth?state=fictional-state")
    assert "fictional-state" not in str(caught.value)
    assert caught.value.__context__ is None


def test_installed_oauth_opt_in_rejects_pipe_before_driver_or_artifact(tmp_path: Path):
    root = os.environ.get("TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT")
    if root is None:
        pytest.skip("requires the isolated registration candidate")
    env = {key: value for key, value in os.environ.items() if not key.startswith("TRINO_")}
    env.update(
        PYTHONPATH=root, TRINO_HOST="fictional.test", TRINO_PORT="443",
        TRINO_USER="fictional", TRINO_HTTP_SCHEME="https", TRINO_AUTH_METHOD="oauth2",
        TRINO_ALLOWED_CATALOGS="lake", TRINO_ALLOWED_SCHEMAS="safe",
        TRINO_ALLOWED_TABLE_COLUMNS="lake.safe.orders.order_id",
    )
    probe = subprocess.run([sys.executable, "-c", "import test_data_agent; print(test_data_agent.__file__)"],
                           env=env, cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert probe.returncode == 0
    assert Path(probe.stdout.strip()).resolve().is_relative_to(Path(root).resolve())
    query = tmp_path / "fictional.sql"
    query.write_text("SELECT order_id FROM lake.safe.orders", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "test_data_agent.cli", "profile-query", str(query),
         "--adapter", "trino", "--source-id", "fictional", "--entity", "orders",
         "--output", str(tmp_path / "profile.json"), "--trino-oauth-browser"],
        env=env, cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 2
    assert "requires a local interactive terminal" in completed.stderr
    assert "fictional.test" not in completed.stdout + completed.stderr
    assert not (tmp_path / "profile.json").exists()
