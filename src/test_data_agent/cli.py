"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from test_data_agent.agent import AgentRequest, AgentWorkspaceStatus
from test_data_agent.cli_agent import (
    advise_agent_workspace_with_provider as _advise_agent_workspace_with_provider,
    agent_request_from_args as _agent_request_from_args,
    run_agent_command as _run_agent_command,
)
from test_data_agent.cli_commands import (
    apply_business_rules_from_args as _apply_business_rules_from_args,
    run_dataset_command as _run_dataset_command,
    run_utility_command as _run_utility_command,
)
from test_data_agent.cli_contract import CliErrorCode, DoctorReport
from test_data_agent.cli_dependencies import CliDependencyResolver
from test_data_agent.cli_doctor import (
    CliDoctorService,
    run_mcp_doctor_smoke as _run_mcp_doctor_smoke,
    run_openai_doctor_smoke as _run_openai_doctor_smoke,
    run_parquet_doctor_smoke as _run_parquet_doctor_smoke,
    run_trino_doctor_smoke as _run_trino_doctor_smoke,
    write_doctor_fixture as _write_doctor_fixture,
)
from test_data_agent.cli_parser import (
    HelpfulArgumentParser,
    JsonHelpfulArgumentParser,
    register_agent_commands,
    register_dataset_commands,
    register_examples_command,
    register_utility_commands,
)
from test_data_agent.cli_presenter import friendly_error, report_cli_error
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.version import __version__

ROOT_EPILOG = """\
Quick start:
  Check the installation:
    test-data-agent doctor

  Generate from one CSV file:
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

1. Check the installation

   test-data-agent doctor

2. One CSV file: profile, infer, generate, and validate in one command

   test-data-agent generate-from-csv data/customers.csv \\
     --count 100 \\
     --seed 12345 \\
     --format csv \\
     --output out/customers.csv

3. Related CSV files: one file per table

   test-data-agent generate-from-example data/example_dataset \\
     --count 100 \\
     --seed 12345 \\
     --format csv \\
     --output out/generated

4. Reviewed DatasetSpec

   test-data-agent generate dataset_spec.yaml \\
     --seed 12345 \\
     --format csv \\
     --output out/generated

5. Safe profile metadata

   test-data-agent generate --profile profile.json \\
     --count 100 \\
     --seed 12345 \\
     --format csv \\
     --output out/customers.csv

6. Review-first agent workflow

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

7. Validate an existing generated dataset

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
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    register_examples_command(
        subparsers,
        examples_text=EXAMPLES_TEXT,
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser(arguments)
    args = parser.parse_args(arguments)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "generate" and args.spec is None and args.profile is None:
        print("Error: choose a DatasetSpec path or --profile.\n", file=sys.stderr)
        print(GENERATE_EPILOG, file=sys.stderr)
        print("Run 'test-data-agent generate --help' for all options.", file=sys.stderr)
        return 2

    if args.command == "generate" and args.spec is not None and args.profile is not None:
        print("Error: choose one input; a DatasetSpec path and --profile cannot be used together.", file=sys.stderr)
        print("Run 'test-data-agent generate --help' for examples.", file=sys.stderr)
        return 2

    try:
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
    except (ValidationError, ValueError) as exc:
        return report_cli_error(
            args,
            code=CliErrorCode.INVALID_INPUT,
            message=friendly_error(exc),
        )


def run_command(args: argparse.Namespace) -> int:
    utility_exit_code = _run_utility_command(
        args,
        examples_text=EXAMPLES_TEXT,
        doctor_inspector=inspect_doctor,
    )
    if utility_exit_code is not None:
        return utility_exit_code

    dataset_exit_code = _run_dataset_command(
        args,
        business_rules_applier=apply_business_rules_from_args,
    )
    if dataset_exit_code is not None:
        return dataset_exit_code

    agent_exit_code = _run_agent_command(
        args,
        request_builder=agent_request_from_args,
        advisor_runner=advise_agent_workspace_with_provider,
    )
    if agent_exit_code is not None:
        return agent_exit_code

    return 2


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
