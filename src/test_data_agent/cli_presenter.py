"""Human and JSON presentation helpers for the public CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from test_data_agent.cli_contract import CliErrorCode
from test_data_agent.cli_parser import write_cli_error_response
from test_data_agent.validation import DatasetValidationReport


def friendly_error(exc: Exception) -> str:
    """Return a bounded, user-facing validation error."""
    if isinstance(exc, ValidationError):
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ()))
        message = first.get("msg", str(exc))
        return f"{location}: {message}" if location else message
    return str(exc)


def report_cli_error(
    args: argparse.Namespace,
    *,
    code: CliErrorCode,
    message: str,
    help_command: str | None = None,
    exit_code: int = 2,
) -> int:
    """Render a CLI failure in the requested human or JSON format."""
    if getattr(args, "json_output", False):
        write_cli_error_response(
            code=code,
            message=message,
            command=f"test-data-agent {args.command}",
            help_command=help_command,
            exit_code=exit_code,
        )
        return exit_code
    print(f"Error: {message}", file=sys.stderr)
    if help_command is not None:
        print(f"Run '{help_command}' for examples and options.", file=sys.stderr)
    return exit_code


def write_validation_result(
    report: DatasetValidationReport,
    output: Path | None,
) -> int:
    """Render validation output and return its public exit code."""
    failed = sum(section.failed for section in report.sections)
    passed = sum(section.passed for section in report.sections)
    status = "passed" if report.valid else "failed"
    destination = f" Report: {output}" if output is not None else ""
    print(
        f"Validation {status}: {passed} checks passed, {failed} failed."
        f"{destination}",
        file=sys.stderr,
    )
    if output is None:
        print(report.model_dump_json(indent=2))
    return 0 if report.valid else 1
