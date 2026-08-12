"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import importlib
import io
import json
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from test_data_agent.agent import AgentRequest, AgentWorkspaceStatus
from test_data_agent.audit import AuditConfigurationError
from test_data_agent.cli_agent import (
    advise_agent_workspace_with_provider as _advise_agent_workspace_with_provider,
    agent_request_from_args as _agent_request_from_args,
)
from test_data_agent.cli_application import run_cli_command as _run_cli_command
from test_data_agent.cli_commands import apply_business_rules_from_args as _apply_business_rules_from_args
from test_data_agent.cli_contract import (
    CliErrorCode,
    CliExternalServiceError,
    CliSuccessResponse,
    DoctorReport,
)
from test_data_agent.cli_dependencies import CliDependencyError, CliDependencyResolver
from test_data_agent.cli_doctor import (
    CliDoctorService,
    run_gigachat_doctor_smoke as _run_gigachat_doctor_smoke,
    run_mcp_doctor_smoke as _run_mcp_doctor_smoke,
    run_openai_doctor_smoke as _run_openai_doctor_smoke,
    run_parquet_doctor_smoke as _run_parquet_doctor_smoke,
    run_trino_doctor_smoke as _run_trino_doctor_smoke,
    write_doctor_fixture as _write_doctor_fixture,
)
from test_data_agent.cli_parser import (
    HelpfulArgumentParser,
    JsonHelpfulArgumentParser,
    PublicHelpFormatter,
    add_common_runtime_options,
    configure_completion_inventory,
    register_agent_commands,
    register_dataset_commands,
    register_examples_command,
    register_completion_command,
    register_utility_commands,
)
from test_data_agent.cli_presenter import friendly_error, report_cli_error
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.postgres_config import PostgresConfigurationError
from test_data_agent.version import __version__

ROOT_EPILOG = """\
Quick start:
  Generate the bundled offline demo:
    test-data-agent demo --output out/demo

  Then check the installation:
    test-data-agent doctor

  Generate from your own CSV file:
    test-data-agent generate-from-csv data/customers.csv \\
      --count 100 --seed 12345 --format csv \\
      --output out/customers.csv

  Generate related tables from a CSV folder:
    test-data-agent generate-from-example data/example_dataset \\
      --count 100 --seed 12345 --format csv \\
      --output out/generated

  Generate from a reviewed DatasetSpec:
    test-data-agent generate dataset_spec.yaml \\
      --seed 12345 --format csv --output out/generated

Learn more:
  test-data-agent examples
  test-data-agent COMMAND --help
  Documentation: https://wa-pis.github.io/agent-paranoid-android/

Generated rows are synthetic. Review generation_manifest.json for the seed,
row counts, validation result, and safety flags.
"""

EXAMPLES_TEXT = """\
Common workflows
================

1. Bundled offline demo: no checkout, network, or optional extra required

   test-data-agent demo --output out/demo

2. Check the installation

   test-data-agent doctor

3. One CSV file: profile, infer, generate, and validate in one command

   test-data-agent generate-from-csv data/customers.csv \\
     --count 100 \\
     --seed 12345 \\
     --format csv \\
     --output out/customers.csv

4. Related CSV files: one file per table

   test-data-agent generate-from-example data/example_dataset \\
     --count 100 \\
     --seed 12345 \\
     --format csv \\
     --output out/generated

5. Reviewed DatasetSpec

   test-data-agent generate dataset_spec.yaml \\
     --seed 12345 \\
     --format csv \\
     --output out/generated

6. Safe profile metadata

   test-data-agent generate --profile profile.json \\
     --count 100 \\
     --seed 12345 \\
     --format csv \\
     --output out/customers.csv

7. Review-first agent workflow

   test-data-agent agent-plan data/example_dataset \\
     --workspace out/agent

   # Review out/agent/dataset_spec.yaml and its metadata checklist.
   test-data-agent agent-review out/agent
   # Optional: ask the installed OpenAI adapter for a structured proposal.
   test-data-agent agent-advise out/agent --provider openai
   # Advice changes the spec, so review it again and use the new fingerprint.
   test-data-agent agent-review out/agent
   test-data-agent agent-approve out/agent \\
     --reviewed-spec-sha256 SHA256_FROM_STATUS

   # If status reports recovery_required after an interrupted approval:
   test-data-agent agent-recover out/agent \\
     --reviewed-spec-sha256 SHA256_FROM_STATUS

8. Validate an existing generated dataset

   test-data-agent validate dataset_spec.yaml out/generated \\
     --output out/generated/validation_report.json

Use "test-data-agent COMMAND --help" for every option.
Documentation: https://wa-pis.github.io/agent-paranoid-android/
"""

GENERATE_EPILOG = """\
Choose exactly one input:

  Reviewed DatasetSpec:
    test-data-agent generate dataset_spec.yaml \\
      --seed 12345 --format csv --output out/generated

  Safe profile:
    test-data-agent generate --profile profile.json \\
      --count 100 --seed 12345 --format csv \\
      --output out/customers.csv

A DatasetSpec produces a dataset folder. A safe single-table profile produces
one output file and requires --count and --seed.
"""


def build_parser(argv: list[str] | None = None) -> HelpfulArgumentParser:
    """Build the public CLI parser for the requested output mode."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_errors = "--json" in arguments or arguments[:1] == ["agent-advisor-request"]
    parser = HelpfulArgumentParser(
        prog="test-data-agent",
        description=(
            "Agent Paranoid Android: safe deterministic synthetic data generation "
            "from CSV files, CSV folders, safe profiles, or dataset specs."
        ),
        epilog=ROOT_EPILOG,
        formatter_class=PublicHelpFormatter,
        json_errors=json_errors,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="COMMAND",
        parser_class=JsonHelpfulArgumentParser if json_errors else HelpfulArgumentParser,
    )

    register_dataset_commands(
        subparsers,
        generate_epilog=GENERATE_EPILOG,
    )

    register_utility_commands(subparsers)
    register_agent_commands(subparsers)
    register_completion_command(subparsers)
    register_examples_command(
        subparsers,
        examples_text=EXAMPLES_TEXT,
    )

    add_common_runtime_options(parser)
    seen: set[int] = set()
    for command_parser in subparsers.choices.values():
        if id(command_parser) in seen:
            continue
        seen.add(id(command_parser))
        add_common_runtime_options(command_parser)
    configure_completion_inventory(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser(arguments)
    args = parser.parse_args(arguments)
    args.json_output = "--json" in arguments or getattr(args, "json_output", False)
    args.debug = "--debug" in arguments or getattr(args, "debug", False)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "generate" and args.spec is None and args.profile is None:
        if args.json_output:
            return report_cli_error(
                args,
                code=CliErrorCode.INVALID_ARGUMENTS,
                message="choose a DatasetSpec path or --profile",
                help_command="test-data-agent generate --help",
            )
        print("Error: choose a DatasetSpec path or --profile.\n", file=sys.stderr)
        print(GENERATE_EPILOG, file=sys.stderr)
        print("Run 'test-data-agent generate --help' for all options.", file=sys.stderr)
        return 2

    if args.command == "generate" and args.spec is not None and args.profile is not None:
        if args.json_output:
            return report_cli_error(
                args,
                code=CliErrorCode.INVALID_ARGUMENTS,
                message=(
                    "choose one input; a DatasetSpec path and --profile "
                    "cannot be used together"
                ),
                help_command="test-data-agent generate --help",
            )
        print("Error: choose one input; a DatasetSpec path and --profile cannot be used together.", file=sys.stderr)
        print("Run 'test-data-agent generate --help' for examples.", file=sys.stderr)
        return 2

    if (
        args.command == "generate"
        and args.json_output
        and args.profile is not None
        and args.output is None
    ):
        return report_cli_error(
            args,
            code=CliErrorCode.INVALID_ARGUMENTS,
            message="--json with --profile requires --output to keep rows in an artifact",
            help_command="test-data-agent generate --help",
        )

    try:
        if args.json_output and args.command not in _NATIVE_JSON_COMMANDS:
            return run_json_command(args)
        return run_command(args)
    except SystemExit as exc:
        if isinstance(exc.code, str):
            return report_cli_error(
                args,
                code=CliErrorCode.INVALID_INPUT,
                message=exc.code,
                help_command=f"test-data-agent {args.command} --help",
            )
        raise
    except FileNotFoundError as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.INPUT_NOT_FOUND,
            message=f"file not found: {exc.filename}",
        )
    except (IsADirectoryError, NotADirectoryError, PermissionError) as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.INVALID_PATH,
            message=f"{exc.strerror}: {exc.filename}",
        )
    except CliDependencyError as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.MISSING_DEPENDENCY,
            message=friendly_error(exc),
            exit_code=69,
        )
    except CliExternalServiceError as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.EXTERNAL_SERVICE,
            message=friendly_error(exc),
            exit_code=69,
        )
    except (AuditConfigurationError, PostgresConfigurationError) as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.CONFIGURATION,
            message=friendly_error(exc),
        )
    except (ValidationError, ValueError, yaml.YAMLError) as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.INVALID_INPUT,
            message=friendly_error(exc),
        )
    except OSError:
        return report_cli_error(
            args,
            code=CliErrorCode.IO_FAILURE,
            message="the operating system could not complete the file operation",
            exit_code=74,
        )
    except KeyboardInterrupt:
        return report_cli_error(
            args,
            code=CliErrorCode.CANCELLED,
            message="operation cancelled; no incomplete final artifact was published",
            exit_code=130,
        )
    except Exception:
        if args.debug:
            traceback.print_exc()
        return report_cli_error(
            args,
            code=CliErrorCode.INTERNAL_ERROR,
            message="unexpected internal error; retry with --debug for technical details",
            exit_code=70,
        )


_NATIVE_JSON_COMMANDS = {
    "agent-plan",
    "agent-approve",
    "agent-recover",
    "agent-advise",
    "agent-advisor-request",
    "agent-advisor-apply",
    "agent-status",
    "agent-review",
    "doctor",
}


def run_json_command(args: argparse.Namespace) -> int:
    """Run a human presenter behind one stable machine-readable envelope."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = run_command(args)
    if exit_code not in {0, 1}:
        return exit_code
    response_exit_code: Literal[0, 1] = 0 if exit_code == 0 else 1
    raw_result = stdout.getvalue().strip()
    result: Any | None = None
    if raw_result:
        try:
            result = json.loads(raw_result)
        except json.JSONDecodeError:
            result = raw_result
    response = CliSuccessResponse(
        command=f"test-data-agent {args.command}",
        exit_code=response_exit_code,
        status="succeeded" if exit_code == 0 else "validation_failed",
        artifacts=_json_artifacts(args),
        result=result,
    )
    print(response.model_dump_json(indent=2))
    return exit_code


def _json_artifacts(args: argparse.Namespace) -> list[str]:
    artifacts: list[str] = []
    for name in ("output", "workspace"):
        value = getattr(args, name, None)
        if isinstance(value, Path) and (value.exists() or value.is_symlink()):
            artifacts.append(str(value))
    return artifacts


def run_command(args: argparse.Namespace) -> int:
    """Compatibility wrapper for extracted CLI composition and dispatch."""

    return _run_cli_command(
        args,
        examples_text=EXAMPLES_TEXT,
        doctor_inspector=inspect_doctor,
        business_rules_applier=apply_business_rules_from_args,
        request_builder=agent_request_from_args,
        advisor_runner=advise_agent_workspace_with_provider,
    )


def inspect_doctor(
    *,
    skip_smoke: bool = False,
    required_extras: set[str] | None = None,
) -> DoctorReport:
    return CliDoctorService(
        import_module=importlib.import_module,
        parquet_smoke=run_parquet_doctor_smoke,
        mcp_smoke=run_mcp_doctor_smoke,
        trino_smoke=run_trino_doctor_smoke,
        openai_smoke=run_openai_doctor_smoke,
        gigachat_smoke=_run_gigachat_doctor_smoke,
    ).inspect(
        skip_smoke=skip_smoke,
        required_extras=required_extras,
    )


def run_parquet_doctor_smoke(fixture: Path, output: Path) -> None:
    """Compatibility wrapper for the extracted doctor capability smoke."""

    _run_parquet_doctor_smoke(fixture, output)


def run_mcp_doctor_smoke() -> None:
    """Compatibility wrapper for the extracted MCP capability smoke."""

    _run_mcp_doctor_smoke()


def run_trino_doctor_smoke() -> None:
    """Compatibility wrapper for the extracted Trino capability smoke."""

    _run_trino_doctor_smoke()


def run_openai_doctor_smoke() -> None:
    """Compatibility wrapper for the extracted OpenAI capability smoke."""

    _run_openai_doctor_smoke()


def write_doctor_fixture(directory: Path) -> None:
    """Compatibility wrapper for the synthetic doctor fixture."""

    _write_doctor_fixture(directory)


def agent_request_from_args(args: argparse.Namespace) -> AgentRequest:
    """Compatibility wrapper for agent request translation."""

    return _agent_request_from_args(args)


def advise_agent_workspace_with_provider(
    workspace: Path,
    *,
    provider: str,
    model: str | None,
) -> AgentWorkspaceStatus:
    """Compatibility wrapper for optional provider-backed advice."""

    return _advise_agent_workspace_with_provider(
        workspace,
        provider=provider,
        model=model,
        dependencies=CliDependencyResolver(importlib.import_module),
    )


def apply_business_rules_from_args(
    rows_by_table: dict[str, list[dict[str, Any]]],
    args: argparse.Namespace,
    seed: int,
    spec: DatasetSpec | None = None,
) -> Any | None:
    """Compatibility wrapper for extracted dataset command rule handling."""

    return _apply_business_rules_from_args(
        rows_by_table,
        args,
        seed,
        spec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
