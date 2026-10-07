"""Synthetic cross-request owned SQL session and local receipt lifecycle."""
import json
import os
from pathlib import Path
import time

import pytest
import yaml

from test_data_agent.io.transformation_query_sessions import _ConfiguredQuerySessions
from test_data_agent.mcp_transformation_candidate import _configured_query_session_tool, _approve_configured_query_session_locally
from test_data_agent.io.transformation_batch import TransformationBatchError
from test_data_agent.core.transformation_errors import TransformationCleanupError
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.sql_query_source import SqlQueryAdapter
from tests.test_transformation_query_workflow import fixture


def prepare(tmp_path, monkeypatch, *, preserve=False):
    profile, bindings, captures = fixture(tmp_path, SqlQueryAdapter.POSTGRES)
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setattr(PostgresConfig, "from_env", classmethod(lambda cls: next(iter(bindings.values())).config))
    (tmp_path / "input.sql").write_text("SELECT status FROM public.orders")
    (tmp_path / "profile.yaml").write_text(yaml.safe_dump(profile.model_dump(mode="json", exclude_unset=True)))
    (tmp_path / "references.yaml").write_text(yaml.safe_dump({"schema_version": "0.1", "queries": {
        key: {"adapter": "postgres", "source_id": "warehouse", "entity": item.request.entity,
            "query_file": "input.sql", "max_rows": 3, "max_bytes": 16384, "max_seconds": 10.0}
        for key, item in bindings.items()}}))
    if preserve:
        policy_path = tmp_path / profile.inputs[0].policy
        policy = yaml.safe_load(policy_path.read_text())
        policy["fields"][0]["behavior"] = {"action": "preserve", "authorization_ref": "local",
            "comment": "Synthetic controlling-TTY review"}
        policy_path.write_text(yaml.safe_dump(policy))
    calls = []
    def capture(binding, *, max_seconds):
        calls.append(binding.request.query_file)
        return captures[binding.request.entity_name]
    monkeypatch.setattr("test_data_agent.io.transformation_postgres_capture._capture_configured_postgres", capture)
    return calls


def open_session(tool):
    return tool("open", profile="profile.yaml", references="references.yaml",
        max_total_bytes=65536, max_review_bytes=32768, max_output_bytes=65536)


def test_cross_request_review_validate_execute_retains_parent_output(tmp_path, monkeypatch):
    calls = prepare(tmp_path, monkeypatch)
    sessions = _ConfiguredQuerySessions(tmp_path, max_active=2, max_cumulative_bytes=131072, max_seconds=10)
    tool = _configured_query_session_tool(sessions)
    try:
        opened = open_session(tool)
        handle = opened["handle"]
        digest = opened["snapshot_sha256"]
        owned = Path(opened["local_approval"]["root"])
        assert owned.exists() and handle not in str(owned)
        assert "alpha" not in json.dumps(opened)
        assert tool("review", handle=handle)["snapshot_sha256"] == digest
        assert tool("validate", handle=handle, snapshot_sha256=digest)["status"] == "closed_validation_completed"
        result = tool("execute", handle=handle, snapshot_sha256=digest, destination="selected")
        assert result["status"] == "closed_publication_completed"
        assert "gamma" in (tmp_path / "selected" / "input-0.csv").read_text()
        assert not owned.exists() and len(calls) == 2
        with pytest.raises(TransformationBatchError):
            tool("review", handle=handle)
        assert len(calls) == 2
    finally:
        sessions.close()


def test_local_cli_receipt_is_consumed_without_mcp_issuer(tmp_path, monkeypatch):
    calls = prepare(tmp_path, monkeypatch, preserve=True)
    sessions = _ConfiguredQuerySessions(tmp_path, max_active=1, max_cumulative_bytes=65536, max_seconds=10)
    tool = _configured_query_session_tool(sessions)
    try:
        opened = open_session(tool)
        handle = opened["handle"]
        digest = opened["snapshot_sha256"]
        owned = Path(opened["local_approval"]["root"])
        tty = tmp_path / "synthetic-tty"
        tty.write_bytes(b"")
        original = os.open
        def open_tty(path, flags, *args, **kwargs):
            return original(tty if path == "/dev/tty" else path, flags, *args, **kwargs)
        confirmations = []
        monkeypatch.setattr(os, "open", open_tty)
        monkeypatch.setattr("test_data_agent.io.transformation_batch_receipt._confirm_tty_fd",
            lambda fd, review, sha: confirmations.append(sha))
        assert _approve_configured_query_session_locally(sessions, handle) == 0
        assert confirmations == [digest]
        assert tool("validate", handle=handle, snapshot_sha256=digest)["status"] == "closed_validation_completed"
        assert tool("execute", handle=handle, snapshot_sha256=digest, destination="selected")["status"] == "closed_publication_completed"
        assert "alpha" in (tmp_path / "selected" / "input-0.csv").read_text()
        assert not owned.exists() and len(calls) == 2
    finally:
        sessions.close()


@pytest.mark.parametrize("fault", ["digest", "destination", "missing_receipt"])
def test_session_refusal_closes_owned_context_without_reconnect(tmp_path, monkeypatch, fault):
    calls = prepare(tmp_path, monkeypatch, preserve=fault == "missing_receipt")
    sessions = _ConfiguredQuerySessions(tmp_path, max_active=1, max_cumulative_bytes=65536, max_seconds=10)
    tool = _configured_query_session_tool(sessions)
    try:
        opened = open_session(tool)
        owned = Path(opened["local_approval"]["root"])
        with pytest.raises(TransformationBatchError):
            tool("execute", handle=opened["handle"],
                snapshot_sha256="0" * 64 if fault == "digest" else opened["snapshot_sha256"],
                destination="../escape" if fault == "destination" else "selected")
        assert not owned.exists() and not (tmp_path / "selected").exists()
        with pytest.raises(TransformationBatchError):
            tool("review", handle=opened["handle"])
        assert len(calls) == 2
    finally:
        sessions.close()


def test_active_and_lifetime_byte_admission_is_not_reset_by_close(tmp_path, monkeypatch):
    calls = prepare(tmp_path, monkeypatch)
    sessions = _ConfiguredQuerySessions(tmp_path, max_active=1, max_cumulative_bytes=65536, max_seconds=10)
    tool = _configured_query_session_tool(sessions)
    try:
        opened = open_session(tool)
        with pytest.raises(TransformationBatchError):
            open_session(tool)
        assert tool("close", handle=opened["handle"])["status"] == "closed"
        with pytest.raises(TransformationBatchError):
            open_session(tool)
        assert len(calls) == 2
    finally:
        sessions.close()


def test_expiry_timer_removes_owned_files_without_polling(tmp_path, monkeypatch):
    calls = prepare(tmp_path, monkeypatch)
    sessions = _ConfiguredQuerySessions(tmp_path, max_active=1, max_cumulative_bytes=65536, max_seconds=0.2)
    tool = _configured_query_session_tool(sessions)
    try:
        opened = open_session(tool)
        owned = Path(opened["local_approval"]["root"])
        end = time.monotonic() + 2
        while owned.exists() and time.monotonic() < end:
            time.sleep(0.02)
        assert not owned.exists()
        with pytest.raises(TransformationBatchError):
            tool("review", handle=opened["handle"])
        assert len(calls) == 2
    finally:
        sessions.close()



@pytest.mark.parametrize("timer", [False, True])
def test_cleanup_failure_latches_safe_error_and_attempts_other_shutdowns(tmp_path, monkeypatch, timer):
    calls = prepare(tmp_path, monkeypatch)
    sessions = _ConfiguredQuerySessions(tmp_path, max_active=2, max_cumulative_bytes=131072, max_seconds=10)
    tool = _configured_query_session_tool(sessions)
    first, second = open_session(tool), open_session(tool)
    owner = sessions._sessions[first["handle"]].owner
    close = owner.close
    canary = "fictional-backend-cleanup-secret"
    def fail():
        raise OSError(canary)
    monkeypatch.setattr(owner, "close", fail)
    try:
        if timer:
            sessions._expire(first["handle"])
            with pytest.raises(TransformationCleanupError) as error:
                tool("review", handle=second["handle"])
        else:
            with pytest.raises(TransformationCleanupError) as error:
                sessions.close()
            assert not Path(second["local_approval"]["root"]).exists()
        assert canary not in str(error.value)
        with pytest.raises(TransformationCleanupError):
            open_session(tool)
        assert len(calls) == 4
    finally:
        monkeypatch.setattr(owner, "close", close)
        close()
        with pytest.raises(TransformationCleanupError):
            sessions.close()
        assert not Path(second["local_approval"]["root"]).exists()



def test_closed_server_composition_owns_shutdown_cleanup(tmp_path, monkeypatch):
    from test_data_agent.mcp_transformation_candidate import _configured_query_session_server
    calls = prepare(tmp_path, monkeypatch)
    def server(tools, *, strict_arguments):
        assert strict_arguments is True and len(tools) == 1
        return tools[0]
    monkeypatch.setattr("test_data_agent.mcp_generator_transport.create_generator_mcp", server)
    with _configured_query_session_server(tmp_path, max_active=1,
            max_cumulative_bytes=65536, max_seconds=10) as tool:
        opened = open_session(tool)
        owned = Path(opened["local_approval"]["root"])
        assert owned.exists()
    assert not owned.exists()
    with pytest.raises(TransformationBatchError):
        tool("review", handle=opened["handle"])
    assert len(calls) == 2
