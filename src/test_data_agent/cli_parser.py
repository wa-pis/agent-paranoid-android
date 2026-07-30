"""Reusable parsing primitives for the public command-line interface."""

from __future__ import annotations

import argparse
import sys
from typing import Any, Never

from test_data_agent.cli_contract import (
    CliErrorCode,
    CliErrorDetail,
    CliErrorResponse,
)


class HelpfulArgumentParser(argparse.ArgumentParser):
    """Add a concrete recovery hint to argparse failures."""

    def __init__(
        self,
        *args: Any,
        json_errors: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.json_errors = json_errors

    def error(self, message: str) -> Never:
        if self.json_errors:
            write_cli_error_response(
                code=CliErrorCode.INVALID_ARGUMENTS,
                message=message,
                command=self.prog,
                help_command=f"{self.prog} --help",
            )
            raise SystemExit(2)
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        print(f"Try '{self.prog} --help' for examples and options.", file=sys.stderr)
        raise SystemExit(2)


class JsonHelpfulArgumentParser(HelpfulArgumentParser):
    """Render parser failures as the public JSON error contract."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, json_errors=True, **kwargs)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def ratio(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def write_cli_error_response(
    *,
    code: CliErrorCode,
    message: str,
    command: str,
    help_command: str | None = None,
    exit_code: int = 2,
) -> None:
    response = CliErrorResponse(
        error=CliErrorDetail(
            code=code,
            message=message,
            command=command,
            exit_code=exit_code,
            help=help_command,
        )
    )
    print(response.model_dump_json(indent=2))
