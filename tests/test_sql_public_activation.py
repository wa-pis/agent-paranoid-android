"""Prospective public SQL registration; all sources and backend fixtures fictional."""
import json
from pathlib import Path

import pytest

from test_data_agent import cli, mcp_generator_server as server
from tests.test_transformation_query_sessions import prepare


def test_registered_cli_query_execute_is_one_versioned_json_result(tmp_path, monkeypatch, capsys):
    calls = prepare(tmp_path, monkeypatch)
    assert cli.main(["transform-batch", "query-execute", str(tmp_path), "profile.yaml", "references.yaml",
        "selected", "--max-total-input-bytes", "65536", "--max-review-bytes", "32768",
        "--max-output-bytes", "65536", "--json"]) == 0
    streams = capsys.readouterr()
    result = json.loads(streams.out)
    assert result["result"]["status"] == "closed_publication_completed"
    assert result["command"] == "test-data-agent transform-batch"
    assert "review_only" in streams.err
    assert "alpha" not in streams.out + streams.err
    assert len(calls) == 2 and all(not path.exists() for path in calls)
    assert (tmp_path / "selected" / "manifest.json").exists()


@pytest.mark.parametrize("transport_failure", [False, True])
def test_runtime_mcp_registers_session_tool_and_closes_on_transport_shutdown(tmp_path, monkeypatch, transport_failure):
    calls = prepare(tmp_path, monkeypatch)
    opened = []
    class Runtime:
        def __init__(self, tools):
            self.tools = tools
        def get_context(self):
            raise LookupError
    monkeypatch.setattr(server, "mcp", Runtime([]))
    monkeypatch.setattr(server, "audit_logger_from_env", lambda *a: None)
    def create(tools, *, strict_arguments):
        assert strict_arguments is True
        return Runtime(tools)
    monkeypatch.setattr(server, "create_generator_mcp", create)
    def run(runtime, **kwargs):
        tool = next(item for item in runtime.tools if item.__name__ == "configured_query_session")
        assert "approve_configured_query_session" not in {item.__name__ for item in runtime.tools}
        opened.append(tool("open", profile="profile.yaml", references="references.yaml",
            max_total_bytes=65536, max_review_bytes=32768, max_output_bytes=65536))
        assert Path(opened[0]["local_approval"]["root"]).exists()
        if transport_failure:
            raise RuntimeError("synthetic transport stop")
    monkeypatch.setattr(server, "run_bounded_generator_mcp", run)
    if transport_failure:
        with pytest.raises(RuntimeError, match="synthetic transport stop"):
            server.main()
    else:
        assert server.main() == 0
    assert len(calls) == 2
    assert not Path(opened[0]["local_approval"]["root"]).exists()


def test_runtime_session_config_error_never_reflects_value(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    canary = "synthetic-secret-config-canary"
    monkeypatch.setenv("TEST_DATA_AGENT_QUERY_SESSION_MAX_ACTIVE", canary)
    monkeypatch.setattr(server, "mcp", object())
    monkeypatch.setattr(server, "audit_logger_from_env", lambda *a: None)
    assert server.main() == 78
    output = capsys.readouterr()
    assert canary not in output.out + output.err



@pytest.mark.parametrize("root_kind", ["missing", "file"])
def test_invalid_workspace_import_is_safe_and_startup_returns_generic_78(tmp_path, root_kind):
    import os
    import subprocess
    import sys
    canary = "synthetic-private-workspace-canary"
    root = tmp_path / canary
    if root_kind == "file":
        root.write_bytes(b"synthetic")
    env = dict(os.environ, TEST_DATA_AGENT_WORKSPACE_ROOT=str(root),
        PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    result = subprocess.run([sys.executable, "-c",
        "from test_data_agent import mcp_generator_server as s; s.mcp=object(); raise SystemExit(s.main())"],
        env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 78
    assert canary not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert "Invalid bounded SQL session configuration" in result.stderr


def test_runtime_permission_failure_is_fixed_startup_error(monkeypatch, capsys):
    monkeypatch.setattr(server, "mcp", object())
    monkeypatch.setattr(server, "audit_logger_from_env", lambda *a: None)
    canary = "synthetic-private-permission-canary"
    def denied():
        raise PermissionError(canary)
    monkeypatch.setattr(server, "workspace_root", denied)
    assert server.main() == 78
    output = capsys.readouterr()
    assert canary not in output.out + output.err
