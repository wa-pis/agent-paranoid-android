"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from test_data_agent.agent import (
    AgentRequest,
    AgentSourceType,
    AgentWorkspaceStatus,
    apply_agent_advisor_proposal,
    advise_agent_workspace,
    approve_agent_workspace,
    build_agent_advisor_exchange,
    build_agent_advisor_request,
    detect_agent_source_type,
    inspect_agent_workspace,
    plan_agent_request,
    recover_agent_workspace,
    review_agent_workspace,
)
from test_data_agent.advisor import AdvisorProposal, ExchangeDatasetAdvisor
from test_data_agent.audit import verify_audit_log_from_env
from test_data_agent.cli_contract import CliErrorCode
from test_data_agent.cli_parser import (
    HelpfulArgumentParser,
    JsonHelpfulArgumentParser,
    register_agent_commands,
    register_dataset_commands,
    register_examples_command,
    register_utility_commands,
)
from test_data_agent.cli_presenter import (
    friendly_error,
    report_cli_error,
    write_agent_command_result,
    write_agent_review_result,
    write_agent_status_result,
    write_json_document,
    write_validation_result,
)
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import read_limited_text
from test_data_agent.core.settings import GenerationMode as CoreGenerationMode, OutputFormat as CoreOutputFormat
from test_data_agent.generation.constraint_solver import default_value_for_field
from test_data_agent.io import (
    generate_dataset_from_csv_command,
    generate_dataset_from_example_artifacts,
    generate_dataset_from_example_command,
    generate_dataset_from_profile_command,
    generate_dataset_command,
    infer_dataset_spec_command,
    profile_csv_command,
    profile_example_command,
    validate_dataset_artifacts,
)
from test_data_agent.rules.business_config import apply_and_validate_business_rules_from_path
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
    if args.command == "examples":
        print(EXAMPLES_TEXT)
        return 0

    if args.command == "generate":
        if args.profile is not None:
            return generate_dataset_from_profile_command(
                args,
                business_rules_applier=lambda rows_by_entity, seed, spec: apply_business_rules_from_args(
                    rows_by_entity,
                    args,
                    seed,
                    spec,
                ),
            )
        return generate_dataset_command(
            args,
            business_rules_applier=lambda rows_by_entity, seed, spec: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
                spec,
            ),
        )

    if args.command in {"profile-example", "profile-csv-folder"}:
        return profile_example_command(args)

    if args.command == "infer-spec":
        return infer_dataset_spec_command(args)

    if args.command == "profile-csv":
        return profile_csv_command(args)

    if args.command == "generate-from-csv":
        return generate_dataset_from_csv_command(
            args,
            business_rules_applier=lambda rows_by_entity, seed, spec: apply_business_rules_from_args(
                rows_by_entity,
                args,
                seed,
                spec,
            ),
        )

    if args.command == "validate":
        report = validate_dataset_artifacts(
            args.spec,
            args.rows,
            output_path=args.output,
            overwrite=args.overwrite,
        )
        return write_validation_result(report, args.output)

    if args.command in {"generate-from-example", "generate-from-csv-folder"}:
        return generate_dataset_from_example_command(args)

    if args.command == "doctor":
        return run_doctor(
            skip_smoke=args.skip_smoke,
            required_extras=set(args.require_extra),
        )

    if args.command == "audit-verify":
        audit_result = verify_audit_log_from_env(args.log)
        print(
            f"Audit log verified: {audit_result.record_count} records, "
            f"last MAC {audit_result.last_mac}",
            file=sys.stderr,
        )
        return 0

    if args.command == "agent-plan":
        agent_result = plan_agent_request(agent_request_from_args(args))
        write_agent_command_result(agent_result, json_output=args.json_output)
        return 0

    if args.command == "agent-approve":
        agent_result = approve_agent_workspace(
            args.workspace,
            reviewed_spec_sha256=args.reviewed_spec_sha256,
        )
        write_agent_command_result(agent_result, json_output=args.json_output)
        return 0 if agent_result.summary.get("validation_valid", False) else 1

    if args.command == "agent-recover":
        agent_result = recover_agent_workspace(
            args.workspace,
            reviewed_spec_sha256=args.reviewed_spec_sha256,
        )
        write_agent_command_result(agent_result, json_output=args.json_output)
        return 0 if agent_result.summary.get("validation_valid", False) else 1

    if args.command == "agent-advise":
        status = advise_agent_workspace_with_provider(
            args.workspace,
            provider=args.provider,
            model=args.model,
        )
        write_agent_status_result(
            status,
            json_output=args.json_output,
            pending_heading="AI proposal ready; review required",
        )
        return 0

    if args.command == "agent-advisor-request":
        payload = (
            build_agent_advisor_exchange(args.workspace)
            if args.exchange
            else build_agent_advisor_request(args.workspace)
        )
        write_json_document(payload)
        return 0

    if args.command == "agent-advisor-apply":
        proposal = AdvisorProposal.model_validate_json(
            read_limited_text(args.proposal)
        )
        status = apply_agent_advisor_proposal(args.workspace, proposal)
        write_agent_status_result(status, json_output=args.json_output)
        return 0

    if args.command == "agent-status":
        status = inspect_agent_workspace(args.workspace)
        write_agent_status_result(status, json_output=args.json_output)
        return 0

    if args.command == "agent-review":
        review_report = review_agent_workspace(args.workspace)
        write_agent_review_result(review_report, json_output=args.json_output)
        return 0

    return 2


def run_doctor(
    *,
    skip_smoke: bool = False,
    required_extras: set[str] | None = None,
) -> int:
    checks: list[str] = []
    failures: list[str] = []
    required = set(required_extras or ())
    if "all" in required:
        required.update({"parquet", "mcp", "trino", "openai"})

    if sys.version_info >= (3, 11):
        checks.append(f"python: ok ({sys.version_info.major}.{sys.version_info.minor})")
    else:
        failures.append("python: Python 3.11 or newer is required")

    for module_name in ("faker", "pydantic", "yaml"):
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            failures.append(f"dependency {module_name}: missing ({exc})")
        else:
            checks.append(f"dependency {module_name}: ok")

    optional_modules = {
        "parquet": ("pyarrow",),
        "mcp": ("mcp",),
        "trino": ("sqlglot", "trino"),
        "openai": ("openai",),
    }
    for extra, module_names in optional_modules.items():
        missing = []
        for module_name in module_names:
            try:
                importlib.import_module(module_name)
            except ImportError:
                missing.append(module_name)
        if missing and extra in required:
            failures.append(
                f"extra {extra}: missing {', '.join(missing)} "
                f"(install agent-paranoid-android[{extra}])"
            )
        elif missing:
            checks.append(f"extra {extra}: not installed (optional)")
        else:
            checks.append(f"extra {extra}: ok")

    if not skip_smoke and not failures:
        with tempfile.TemporaryDirectory(prefix="test-data-agent-doctor-") as tmp:
            root = Path(tmp)
            fixture = root / "example_dataset"
            output = root / "generated"
            cache_dir = root / "cache"
            write_doctor_fixture(fixture)
            generate_dataset_from_example_artifacts(
                fixture,
                output_folder=output,
                seed=12345,
                count=3,
                output_format=CoreOutputFormat.CSV,
                cache_dir=cache_dir,
                use_cache=False,
            )
            manifest = json.loads((output / "generation_manifest.json").read_text())
            if (
                manifest.get("synthetic") is True
                and manifest.get("source_rows_copied") is False
                and manifest.get("validation_valid") is True
            ):
                checks.append("quickstart smoke: ok")
            else:
                failures.append("quickstart smoke: manifest safety flags are not valid")

    for check in checks:
        print(check, file=sys.stderr)
    for failure in failures:
        print(f"doctor failed: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("doctor passed", file=sys.stderr)
    return 0


def write_doctor_fixture(directory: Path) -> None:
    directory.mkdir()
    (directory / "customers.csv").write_text(
        "customer_id,email,segment\n"
        "C1,alice@example.test,retail\n"
        "C2,bob@example.test,business\n",
        encoding="utf-8",
    )
    (directory / "orders.csv").write_text(
        "order_id,customer_id,status,amount\n"
        "O1,C1,paid,20\n"
        "O2,C2,cancelled,30\n",
        encoding="utf-8",
    )


def agent_request_from_args(args: argparse.Namespace) -> AgentRequest:
    source_type = (
        AgentSourceType(args.source_type.replace("-", "_"))
        if args.source_type is not None
        else detect_agent_source_type(args.source)
    )
    return AgentRequest(
        source_type=source_type,
        source_path=args.source,
        workspace=args.workspace,
        count=args.count,
        seed=args.seed,
        output_format=CoreOutputFormat(args.output_format),
        mode=CoreGenerationMode(args.mode),
        invalid_ratio=args.invalid_ratio,
        table_name=args.table,
        rule_sample_rows=args.rule_sample_rows,
        use_cache=args.use_cache,
    )


def advise_agent_workspace_with_provider(
    workspace: Path,
    *,
    provider: str,
    model: str | None,
) -> AgentWorkspaceStatus:
    if provider != "openai":
        raise ValueError(f"unsupported advisor provider: {provider}")
    try:
        from test_data_agent.providers.openai import (
            DEFAULT_OPENAI_MODEL,
            OpenAIAdvisorClient,
        )
    except ImportError as exc:
        raise ValueError(
            "OpenAI advice requires agent-paranoid-android[openai]"
        ) from exc
    client = OpenAIAdvisorClient(model=model or DEFAULT_OPENAI_MODEL)
    return advise_agent_workspace(
        workspace,
        ExchangeDatasetAdvisor(client),
    )


def apply_business_rules_from_args(
    rows_by_table: dict[str, list[dict[str, Any]]],
    args: argparse.Namespace,
    seed: int,
    spec: DatasetSpec | None = None,
) -> Any | None:
    field_defaults = None
    if spec is not None:
        field_defaults = {
            entity.name: {
                field.name: default_value_for_field(field)
                for field in entity.fields
            }
            for entity in spec.entities
        }
    return apply_and_validate_business_rules_from_path(
        rows_by_table,
        getattr(args, "business_rules", None),
        seed=seed,
        mode=args.mode,
        invalid_ratio=args.invalid_ratio,
        field_defaults=field_defaults,
        spec=spec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
