import base64
import json
from pathlib import Path

import pytest

from test_data_agent.audit import (
    AUDIT_HMAC_KEY_ENV,
    AUDIT_LOG_ENV,
    AuditConfigurationError,
    AuditVerificationError,
    audited_mcp_tool,
    decode_audit_key,
    verify_audit_log,
)
from test_data_agent.cli import main


AUDIT_KEY_BYTES = b"k" * 32
AUDIT_KEY = base64.b64encode(AUDIT_KEY_BYTES).decode("ascii")


def configure_audit(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setenv(AUDIT_LOG_ENV, str(path))
    monkeypatch.setenv(AUDIT_HMAC_KEY_ENV, AUDIT_KEY)


def test_audited_tool_writes_authenticated_records_without_arguments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "audit.jsonl"
    configure_audit(monkeypatch, log_path)

    def profile_secret(value: str) -> str:
        return f"processed:{value}"

    wrapped = audited_mcp_tool("generator-mcp", profile_secret)

    assert wrapped("victim@example.test") == "processed:victim@example.test"

    records = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    verification = verify_audit_log(log_path, AUDIT_KEY_BYTES)

    assert verification.record_count == 2
    assert [record["status"] for record in records] == ["started", "succeeded"]
    assert records[0]["invocation_id"] == records[1]["invocation_id"]
    assert "victim@example.test" not in log_path.read_text(encoding="utf-8")


def test_audited_tool_records_failure_type(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "audit.jsonl"
    configure_audit(monkeypatch, log_path)

    def fail() -> None:
        raise ValueError("raw sensitive detail")

    with pytest.raises(ValueError, match="raw sensitive detail"):
        audited_mcp_tool("trino-mcp", fail)()

    records = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
    ]
    assert records[-1]["status"] == "failed"
    assert records[-1]["error_type"] == "ValueError"
    assert "raw sensitive detail" not in log_path.read_text(encoding="utf-8")
    assert verify_audit_log(log_path, AUDIT_KEY_BYTES).record_count == 2


def test_audit_verification_detects_tampering(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "audit.jsonl"
    configure_audit(monkeypatch, log_path)
    audited_mcp_tool("generator-mcp", lambda: None)()
    contents = log_path.read_text(encoding="utf-8")
    log_path.write_text(contents.replace('"succeeded"', '"failed"', 1), encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="HMAC verification"):
        verify_audit_log(log_path, AUDIT_KEY_BYTES)


def test_incomplete_audit_configuration_fails_before_tool_runs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(AUDIT_LOG_ENV, str(tmp_path / "audit.jsonl"))
    called = False

    def operation() -> None:
        nonlocal called
        called = True

    with pytest.raises(AuditConfigurationError, match="configured together"):
        audited_mcp_tool("generator-mcp", operation)()

    assert called is False


def test_audit_log_rejects_symlink_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = tmp_path / "target.jsonl"
    target.touch()
    link = tmp_path / "audit.jsonl"
    link.symlink_to(target)
    configure_audit(monkeypatch, link)

    with pytest.raises(AuditConfigurationError, match="symbolic link"):
        audited_mcp_tool("generator-mcp", lambda: None)()


def test_audit_key_requires_32_decoded_bytes() -> None:
    with pytest.raises(AuditConfigurationError, match="at least 32 bytes"):
        decode_audit_key(base64.b64encode(b"short").decode("ascii"))


def test_cli_verifies_audit_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    log_path = tmp_path / "audit.jsonl"
    configure_audit(monkeypatch, log_path)
    audited_mcp_tool("generator-mcp", lambda: None)()

    assert main(["audit-verify", str(log_path)]) == 0
    assert "Audit log verified: 2 records" in capsys.readouterr().err
