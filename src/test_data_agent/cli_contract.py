"""Versioned machine-readable CLI contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class CliErrorCode(StrEnum):
    INVALID_ARGUMENTS = "invalid_arguments"
    INPUT_NOT_FOUND = "input_not_found"
    INVALID_PATH = "invalid_path"
    INVALID_INPUT = "invalid_input"


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


@dataclass(frozen=True)
class DoctorReport:
    """Typed result passed from installation checks to CLI presentation."""

    checks: tuple[str, ...]
    failures: tuple[str, ...]
