"""Command-line interface for local synthetic data generation."""

from __future__ import annotations

import argparse
import importlib
import json
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from test_data_agent.agent import (
    AgentGenerationSummary,
    AgentPlanSummary,
    AgentRecoverySummary,
    AgentRequest,
    AgentReviewReport,
    AgentResult,
    AgentReviewState,
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
        if args.json_output:
            print(status.model_dump_json(indent=2))
        else:
            write_agent_status_summary(
                status,
                pending_heading="AI proposal ready; review required",
            )
        return 0

    if args.command == "agent-advisor-request":
        payload = (
            build_agent_advisor_exchange(args.workspace)
            if args.exchange
            else build_agent_advisor_request(args.workspace)
        )
        print(payload.model_dump_json(indent=2))
        return 0

    if args.command == "agent-advisor-apply":
        proposal = AdvisorProposal.model_validate_json(
            read_limited_text(args.proposal)
        )
        status = apply_agent_advisor_proposal(args.workspace, proposal)
        if args.json_output:
            print(status.model_dump_json(indent=2))
        else:
            write_agent_status_summary(status)
        return 0

    if args.command == "agent-status":
        status = inspect_agent_workspace(args.workspace)
        if args.json_output:
            print(status.model_dump_json(indent=2))
        else:
            write_agent_status_summary(status)
        return 0

    if args.command == "agent-review":
        review_report = review_agent_workspace(args.workspace)
        if args.json_output:
            print(review_report.model_dump_json(indent=2))
        else:
            write_agent_review_report(review_report)
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


def write_agent_result_summary(result: AgentResult) -> None:
    if result.phase.value == "awaiting_approval":
        if not isinstance(result.summary, AgentPlanSummary):
            raise ValueError("awaiting-approval result is missing its plan summary")
        write_agent_plan_review(
            heading="Agent plan ready",
            summary=result.summary,
            workspace=result.artifacts.workspace,
            spec_path=result.artifacts.dataset_spec_path,
            review=result.review,
        )
        return
    if not isinstance(result.summary, AgentGenerationSummary):
        raise ValueError("completed agent result is missing its generation summary")
    row_counts = result.summary.row_counts
    rows_text = ", ".join(f"{name}={count}" for name, count in row_counts.items()) or "no rows"
    validation = "passed" if result.summary.validation_valid else "failed"
    print(
        "Agent generation completed: "
        f"{result.artifacts.generated_folder} | rows: {rows_text} | "
        f"seed: {result.summary.seed} | validation: {validation} | "
        "source rows copied: no | "
        f"approval receipt: {result.artifacts.approval_receipt_path}",
        file=sys.stderr,
    )


def write_agent_command_result(result: AgentResult, *, json_output: bool) -> None:
    if json_output:
        print(result.model_dump_json(indent=2))
    else:
        write_agent_result_summary(result)


def write_agent_status_summary(
    status: AgentWorkspaceStatus,
    *,
    pending_heading: str = "Agent status: awaiting approval",
) -> None:
    if status.phase.value == "awaiting_approval":
        if not isinstance(status.summary, AgentPlanSummary):
            raise ValueError("awaiting-approval status is missing its plan summary")
        write_agent_plan_review(
            heading=pending_heading,
            summary=status.summary,
            workspace=status.artifacts.workspace,
            spec_path=status.artifacts.dataset_spec_path,
            review=status.review,
        )
        return
    if status.phase.value == "recovery_required":
        if not isinstance(status.summary, AgentRecoverySummary):
            raise ValueError("recovery-required status is missing its recovery summary")
        workspace_command = display_untrusted_name(
            shlex.quote(str(status.artifacts.workspace)),
            limit=260,
        )
        print(
            "Agent status: recovery required | generated rows will not be regenerated",
            file=sys.stderr,
        )
        print(
            f"Recover: test-data-agent agent-recover {workspace_command} "
            f"--reviewed-spec-sha256 {status.summary.reviewed_spec_sha256}",
            file=sys.stderr,
        )
        return
    if not isinstance(status.summary, AgentGenerationSummary):
        raise ValueError("completed agent status is missing its generation summary")
    validation = "passed" if status.summary.validation_valid else "failed"
    print(
        "Agent status: completed | "
        f"output: {status.artifacts.generated_folder} | "
        f"validation: {validation} | source rows copied: no",
        file=sys.stderr,
    )


def write_agent_review_report(report: AgentReviewReport) -> None:
    workspace_text = display_untrusted_name(str(report.workspace), limit=240)
    workspace_command = display_untrusted_name(
        shlex.quote(str(report.workspace)),
        limit=260,
    )
    spec_path_text = display_untrusted_name(
        str(report.dataset_spec_path),
        limit=240,
    )
    print(f"DatasetSpec review: {workspace_text}", file=sys.stderr)
    print(
        f"Spec: {spec_path_text} | source: "
        f"{display_untrusted_name(report.source_type)} | seed: {report.seed} | "
        f"format: {report.output_format.value}",
        file=sys.stderr,
    )
    changed = "yes" if report.spec_changed_since_plan else "no"
    print(
        f"Plan ID: {report.plan_id} | changed since plan: {changed}",
        file=sys.stderr,
    )
    print(
        f"Current spec SHA-256: {report.current_spec_sha256}",
        file=sys.stderr,
    )
    raw_values = (
        "blocked"
        if report.safety.raw_sensitive_values_blocked
        else "ALLOWED - do not approve"
    )
    unknown_fields = (
        "sensitive"
        if report.safety.unknown_fields_treated_as_sensitive
        else "not sensitive - review required"
    )
    print(
        f"Privacy: raw sensitive values {raw_values} | unknown fields "
        f"{unknown_fields} | sensitive fields: "
        f"{report.safety.sensitive_field_count} | privacy rules: "
        f"{report.safety.privacy_rule_count}",
        file=sys.stderr,
    )
    print("Entities:", file=sys.stderr)
    for entity in report.entities:
        primary_key = (
            display_untrusted_name(entity.primary_key)
            if entity.primary_key is not None
            else "none"
        )
        print(
            f"  {display_untrusted_name(entity.name)}: {entity.row_count} rows | "
            f"primary key: {primary_key}",
            file=sys.stderr,
        )
        for field in entity.fields[:20]:
            flags = [
                (
                    f"nullable {field.null_ratio:.2f}"
                    if field.nullable
                    else "required"
                )
            ]
            if field.sensitive:
                flags.append("sensitive")
            if field.is_identifier:
                flags.append("identifier")
            if field.semantic_type is not None:
                flags.append(
                    f"semantic={display_untrusted_name(field.semantic_type)}"
                )
            if field.distribution_kind is not None:
                flags.append(
                    "distribution="
                    f"{display_untrusted_name(field.distribution_kind)}"
                )
            print(
                f"    {display_untrusted_name(field.name)}: "
                f"{field.data_type.value} | {' | '.join(flags)}",
                file=sys.stderr,
            )
        omitted = len(entity.fields) - 20
        if omitted > 0:
            print(
                f"    +{omitted} more fields; inspect dataset_spec.yaml",
                file=sys.stderr,
            )
    if report.relationships:
        print("Relationships:", file=sys.stderr)
        for relationship in report.relationships:
            child = (
                f"{display_untrusted_name(relationship.child_entity)}."
                f"{display_untrusted_name(relationship.child_field)}"
            )
            parent = (
                f"{display_untrusted_name(relationship.parent_entity)}."
                f"{display_untrusted_name(relationship.parent_field)}"
            )
            print(
                f"  {child} -> {parent} | "
                f"{relationship.relationship_type.value} | "
                f"confidence: {relationship.confidence:.2f}",
                file=sys.stderr,
            )
    print(f"Constraints: {report.constraint_count}", file=sys.stderr)
    for assumption in report.assumptions:
        print(f"Assumption: {assumption}", file=sys.stderr)
    for warning in report.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print("Approve only after reviewing the complete DatasetSpec:", file=sys.stderr)
    print(
        f"  test-data-agent agent-approve {workspace_command} "
        f"--reviewed-spec-sha256 {report.current_spec_sha256}",
        file=sys.stderr,
    )
    print(
        "Optional AI advice (review the changed spec again before approval):",
        file=sys.stderr,
    )
    print(
        f"  test-data-agent agent-advise {workspace_command} --provider openai",
        file=sys.stderr,
    )


def write_agent_plan_review(
    *,
    heading: str,
    summary: AgentPlanSummary,
    workspace: Path,
    spec_path: Path,
    review: AgentReviewState | None,
) -> None:
    workspace_text = display_untrusted_name(str(workspace), limit=240)
    workspace_command = display_untrusted_name(shlex.quote(str(workspace)), limit=260)
    spec_path_text = display_untrusted_name(str(spec_path), limit=240)
    print(f"{heading}: {workspace_text}", file=sys.stderr)
    print(
        f"Source: {display_untrusted_name(summary.source_type)} | seed: {summary.seed} | "
        f"format: {summary.output_format.value}",
        file=sys.stderr,
    )
    print("Entities:", file=sys.stderr)
    for entity in summary.entities:
        fields = [
            f"{display_untrusted_name(field.name)}:{field.data_type.value}"
            for field in entity.fields
        ]
        print(
            f"  {display_untrusted_name(entity.name)}: {entity.row_count} rows | "
            f"fields ({entity.field_count}): {format_review_items(fields)}",
            file=sys.stderr,
        )
    sensitive = [
        f"{display_untrusted_name(field.entity)}.{display_untrusted_name(field.field)}"
        for field in summary.sensitive_fields
    ]
    print(
        f"Sensitive fields: {format_review_items(sensitive) if sensitive else 'none detected'}",
        file=sys.stderr,
    )
    if summary.relationships:
        print("Relationships:", file=sys.stderr)
        for relationship in summary.relationships:
            child = (
                f"{display_untrusted_name(relationship.child_entity)}."
                f"{display_untrusted_name(relationship.child_field)}"
            )
            parent = (
                f"{display_untrusted_name(relationship.parent_entity)}."
                f"{display_untrusted_name(relationship.parent_field)}"
            )
            print(
                f"  {child} -> {parent} | {relationship.relationship_type.value} | "
                f"confidence: {relationship.confidence:.2f}",
                file=sys.stderr,
            )
    for assumption in summary.assumptions:
        print(f"Assumption: {assumption}", file=sys.stderr)
    for warning in summary.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(f"Review: {spec_path_text}", file=sys.stderr)
    if review is None:
        print(
            "Approve unavailable: create a new plan with fingerprint-bound approval.",
            file=sys.stderr,
        )
        return
    print(
        f"Plan ID: {review.plan_id} | current spec SHA-256: "
        f"{review.current_spec_sha256}",
        file=sys.stderr,
    )
    if review.spec_changed_since_plan:
        print("Notice: DatasetSpec changed since the initial plan.", file=sys.stderr)
    print(
        f"Next: test-data-agent agent-review {workspace_command}",
        file=sys.stderr,
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


def display_untrusted_name(value: str, *, limit: int = 80) -> str:
    truncated = value[:limit]
    escaped = json.dumps(truncated, ensure_ascii=False)[1:-1]
    return f"{escaped}..." if len(value) > limit else escaped


def format_review_items(items: list[str], *, limit: int = 8) -> str:
    if not items:
        return "none"
    visible = items[:limit]
    suffix = f", +{len(items) - limit} more" if len(items) > limit else ""
    return ", ".join(visible) + suffix


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
