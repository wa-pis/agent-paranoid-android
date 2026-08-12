"""Versioned machine-readable CLI contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class CliExternalServiceError(RuntimeError):
    """A bounded remote-service failure suitable for CLI classification."""


class CliErrorCode(StrEnum):
    INVALID_ARGUMENTS = "invalid_arguments"
    INPUT_NOT_FOUND = "input_not_found"
    INVALID_PATH = "invalid_path"
    INVALID_INPUT = "invalid_input"
    CONFIGURATION = "configuration"
    MISSING_DEPENDENCY = "missing_dependency"
    EXTERNAL_SERVICE = "external_service"
    IO_FAILURE = "io_failure"
    INTERNAL_ERROR = "internal_error"
    CANCELLED = "cancelled"


class CliErrorDetail(BaseModel):
    code: CliErrorCode
    message: str
    command: str
    exit_code: int = Field(ge=1, le=255)
    retryable: bool = False
    help: str | None = None


class CliErrorResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    ok: Literal[False] = False
    error: CliErrorDetail


class CliSuccessResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    ok: Literal[True] = True
    command: str
    exit_code: Literal[0, 1]
    status: Literal["succeeded", "validation_failed"]
    artifacts: list[str] = Field(default_factory=list)
    result: Any | None = None


class DoctorStatus(StrEnum):
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    NOT_CONFIGURED = "not_configured"
    CONFIGURED_NOT_TESTED = "configured_not_tested"
    REACHABLE = "reachable"
    FAILED = "failed"
    SKIPPED = "skipped"


class DoctorCheck(BaseModel):
    name: str
    status: DoctorStatus
    detail: str
    remediation: str | None = None


class DoctorResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    ok: bool
    command: Literal["test-data-agent doctor"] = "test-data-agent doctor"
    exit_code: Literal[0, 1]
    checks: list[DoctorCheck]


@dataclass(frozen=True)
class DoctorReport:
    """Typed result passed from installation checks to CLI presentation."""

    checks: tuple[str, ...]
    failures: tuple[str, ...]
    states: tuple[DoctorCheck, ...] = ()
