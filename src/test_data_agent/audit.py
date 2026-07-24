"""Tamper-evident audit records for shared MCP deployments."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import stat
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import ParamSpec, TypeVar

try:  # pragma: no cover - available on supported MCP deployment platforms.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]


AUDIT_LOG_ENV = "TEST_DATA_AGENT_AUDIT_LOG"
AUDIT_HMAC_KEY_ENV = "TEST_DATA_AGENT_AUDIT_HMAC_KEY"
AUDIT_ACTOR_ENV = "TEST_DATA_AGENT_AUDIT_ACTOR"
AUDIT_MAX_BYTES_ENV = "TEST_DATA_AGENT_AUDIT_MAX_BYTES"
AUDIT_SCHEMA_VERSION = "1.0"
DEFAULT_AUDIT_MAX_BYTES = 64 * 1024 * 1024
MAX_AUDIT_MAX_BYTES = 1024 * 1024 * 1024
MAX_AUDIT_RECORD_BYTES = 4096
INITIAL_MAC = "0" * 64

P = ParamSpec("P")
R = TypeVar("R")


class AuditConfigurationError(ValueError):
    """Raised when audit logging is enabled with unsafe configuration."""


class AuditVerificationError(ValueError):
    """Raised when an audit log is malformed or fails authentication."""


@dataclass(frozen=True)
class AuditSettings:
    path: Path
    key: bytes
    actor: str | None
    max_bytes: int


@dataclass(frozen=True)
class AuditVerificationResult:
    record_count: int
    last_mac: str


class AuditLogger:
    def __init__(self, service: str, settings: AuditSettings) -> None:
        self._service = _validate_label(service, "audit service")
        self._settings = settings

    def record(
        self,
        operation: str,
        status_value: str,
        invocation_id: str,
        *,
        error_type: str | None = None,
    ) -> None:
        _append_record(
            self._settings,
            service=self._service,
            operation=_validate_label(operation, "audit operation"),
            status_value=status_value,
            invocation_id=invocation_id,
            error_type=error_type,
        )


def audit_logger_from_env(service: str) -> AuditLogger | None:
    path_value = os.environ.get(AUDIT_LOG_ENV)
    key_value = os.environ.get(AUDIT_HMAC_KEY_ENV)
    if path_value is None and key_value is None:
        return None
    if not path_value or not key_value:
        raise AuditConfigurationError(
            f"{AUDIT_LOG_ENV} and {AUDIT_HMAC_KEY_ENV} must be configured together"
        )
    if fcntl is None or not hasattr(os, "O_NOFOLLOW"):
        raise AuditConfigurationError(
            "signed audit logging requires a POSIX platform with secure file locking"
        )

    raw_path = Path(path_value).expanduser()
    if raw_path.is_symlink():
        raise AuditConfigurationError("audit log path must not be a symbolic link")
    parent = raw_path.parent.resolve(strict=True)
    if not parent.is_dir():
        raise AuditConfigurationError("audit log parent must be a directory")
    path = parent / raw_path.name

    actor_value = os.environ.get(AUDIT_ACTOR_ENV)
    actor = _validate_label(actor_value, "audit actor") if actor_value else None
    return AuditLogger(
        service,
        AuditSettings(
            path=path,
            key=decode_audit_key(key_value),
            actor=actor,
            max_bytes=parse_audit_max_bytes(os.environ.get(AUDIT_MAX_BYTES_ENV)),
        ),
    )


def audited_mcp_tool(
    service: str,
    function: Callable[P, R],
) -> Callable[P, R]:
    """Wrap an MCP tool without recording its arguments or return value."""

    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger = audit_logger_from_env(service)
        if logger is None:
            return function(*args, **kwargs)

        invocation_id = uuid.uuid4().hex
        logger.record(function.__name__, "started", invocation_id)
        try:
            result = function(*args, **kwargs)
        except Exception as exc:
            logger.record(
                function.__name__,
                "failed",
                invocation_id,
                error_type=type(exc).__name__,
            )
            raise
        logger.record(function.__name__, "succeeded", invocation_id)
        return result

    return wrapper


def verify_audit_log(path: Path, key: bytes) -> AuditVerificationResult:
    resolved = _resolve_existing_regular_file(path)
    previous_mac = INITIAL_MAC
    expected_sequence = 1
    record_count = 0

    with resolved.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if len(raw_line) > MAX_AUDIT_RECORD_BYTES:
                raise AuditVerificationError(
                    f"audit record {line_number} exceeds {MAX_AUDIT_RECORD_BYTES} bytes"
                )
            try:
                record = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise AuditVerificationError(
                    f"audit record {line_number} is not valid JSON"
                ) from exc
            if not isinstance(record, dict):
                raise AuditVerificationError(
                    f"audit record {line_number} must be an object"
                )
            supplied_mac = record.pop("mac", None)
            if not isinstance(supplied_mac, str):
                raise AuditVerificationError(
                    f"audit record {line_number} has no valid MAC"
                )
            if record.get("schema_version") != AUDIT_SCHEMA_VERSION:
                raise AuditVerificationError(
                    f"audit record {line_number} has an unsupported schema version"
                )
            if record.get("sequence") != expected_sequence:
                raise AuditVerificationError(
                    f"audit record {line_number} has an invalid sequence"
                )
            if record.get("previous_mac") != previous_mac:
                raise AuditVerificationError(
                    f"audit record {line_number} breaks the hash chain"
                )
            expected_mac = _record_mac(record, key)
            if not hmac.compare_digest(supplied_mac, expected_mac):
                raise AuditVerificationError(
                    f"audit record {line_number} failed HMAC verification"
                )
            previous_mac = supplied_mac
            expected_sequence += 1
            record_count += 1

    return AuditVerificationResult(
        record_count=record_count,
        last_mac=previous_mac,
    )


def verify_audit_log_from_env(path: Path) -> AuditVerificationResult:
    key_value = os.environ.get(AUDIT_HMAC_KEY_ENV)
    if not key_value:
        raise AuditConfigurationError(
            f"{AUDIT_HMAC_KEY_ENV} is required to verify an audit log"
        )
    return verify_audit_log(path, decode_audit_key(key_value))


def decode_audit_key(value: str) -> bytes:
    try:
        key = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AuditConfigurationError(
            f"{AUDIT_HMAC_KEY_ENV} must be valid base64"
        ) from exc
    if len(key) < 32:
        raise AuditConfigurationError(
            f"{AUDIT_HMAC_KEY_ENV} must decode to at least 32 bytes"
        )
    return key


def parse_audit_max_bytes(value: str | None) -> int:
    if value is None:
        return DEFAULT_AUDIT_MAX_BYTES
    try:
        parsed = int(value)
    except ValueError as exc:
        raise AuditConfigurationError(
            f"{AUDIT_MAX_BYTES_ENV} must be an integer"
        ) from exc
    if not MAX_AUDIT_RECORD_BYTES <= parsed <= MAX_AUDIT_MAX_BYTES:
        raise AuditConfigurationError(
            f"{AUDIT_MAX_BYTES_ENV} must be between "
            f"{MAX_AUDIT_RECORD_BYTES} and {MAX_AUDIT_MAX_BYTES}"
        )
    return parsed


def _append_record(
    settings: AuditSettings,
    *,
    service: str,
    operation: str,
    status_value: str,
    invocation_id: str,
    error_type: str | None,
) -> None:
    if status_value not in {"started", "succeeded", "failed"}:
        raise AuditConfigurationError("invalid audit status")
    flags = os.O_CREAT | os.O_RDWR | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        descriptor = os.open(settings.path, flags, 0o600)
    except OSError as exc:
        raise AuditConfigurationError(f"cannot open audit log: {exc}") from exc

    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise AuditConfigurationError("audit log must be a regular file")
        if file_stat.st_nlink != 1:
            raise AuditConfigurationError("audit log must not have hard links")
        if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise AuditConfigurationError(
                "audit log must not be group- or world-writable"
            )
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        file_stat = os.fstat(descriptor)
        sequence, previous_mac = _last_record_state(descriptor, settings.key)
        record: dict[str, object] = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "sequence": sequence,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "event_id": uuid.uuid4().hex,
            "invocation_id": invocation_id,
            "service": service,
            "operation": operation,
            "status": status_value,
            "previous_mac": previous_mac,
        }
        if settings.actor is not None:
            record["actor"] = settings.actor
        if error_type is not None:
            record["error_type"] = _validate_label(error_type, "audit error type")
        record["mac"] = _record_mac(record, settings.key)
        encoded = _canonical_json(record) + b"\n"
        if len(encoded) > MAX_AUDIT_RECORD_BYTES:
            raise AuditConfigurationError("audit record is too large")
        if file_stat.st_size + len(encoded) > settings.max_bytes:
            raise AuditConfigurationError(
                f"audit log reached {AUDIT_MAX_BYTES_ENV}; rotate it before retrying"
            )
        _write_all(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _last_record_state(descriptor: int, key: bytes) -> tuple[int, str]:
    size = os.fstat(descriptor).st_size
    if size == 0:
        return 1, INITIAL_MAC
    read_size = min(size, MAX_AUDIT_RECORD_BYTES)
    os.lseek(descriptor, size - read_size, os.SEEK_SET)
    tail = os.read(descriptor, read_size)
    if not tail.endswith(b"\n"):
        raise AuditVerificationError("audit log has a partial final record")
    lines = tail.rstrip(b"\n").split(b"\n")
    if not lines or (size > read_size and len(lines) == 1):
        raise AuditVerificationError("audit log final record is too large")
    try:
        record = json.loads(lines[-1])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditVerificationError("audit log final record is invalid") from exc
    if not isinstance(record, dict):
        raise AuditVerificationError("audit log final record must be an object")
    supplied_mac = record.pop("mac", None)
    if not isinstance(supplied_mac, str):
        raise AuditVerificationError("audit log final record has no valid MAC")
    if not hmac.compare_digest(supplied_mac, _record_mac(record, key)):
        raise AuditVerificationError("audit log final record failed HMAC verification")
    sequence = record.get("sequence")
    if not isinstance(sequence, int) or sequence < 1:
        raise AuditVerificationError("audit log final record has an invalid sequence")
    return sequence + 1, supplied_mac


def _record_mac(record: dict[str, object], key: bytes) -> str:
    authenticated = {name: value for name, value in record.items() if name != "mac"}
    return hmac.new(key, _canonical_json(authenticated), hashlib.sha256).hexdigest()


def _write_all(descriptor: int, value: bytes) -> None:
    remaining = memoryview(value)
    while remaining:
        written = os.write(descriptor, remaining)
        if written < 1:
            raise AuditConfigurationError("audit log write did not complete")
        remaining = remaining[written:]


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _resolve_existing_regular_file(path: Path) -> Path:
    candidate = path.expanduser()
    if candidate.is_symlink():
        raise AuditVerificationError("audit log path must not be a symbolic link")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise AuditVerificationError("audit log does not exist") from exc
    file_stat = resolved.stat()
    if not stat.S_ISREG(file_stat.st_mode):
        raise AuditVerificationError("audit log must be a regular file")
    if file_stat.st_nlink != 1:
        raise AuditVerificationError("audit log must not have hard links")
    return resolved


def _validate_label(value: str, label: str) -> str:
    if not value or len(value) > 128:
        raise AuditConfigurationError(f"{label} must contain 1 to 128 characters")
    if any(character in "\r\n\x00" for character in value):
        raise AuditConfigurationError(f"{label} must not contain control characters")
    return value
