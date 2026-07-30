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
    non_negative_int,
    positive_int,
    ratio,
    write_cli_error_response,
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

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a dataset from a DatasetSpec, or from a safe profile with --profile.",
        description="Generate synthetic rows from a DatasetSpec file or safe profile metadata.",
        epilog=GENERATE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    generate_parser.add_argument("spec", nargs="?", type=Path, help="Reviewed DatasetSpec YAML/JSON.")
    generate_parser.add_argument("--profile", type=Path, help="Safe profile JSON to generate from instead of a spec file.")
    generate_parser.add_argument("--count", type=positive_int, help="Override generated row count per entity.")
    generate_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid", help="Generation mode: valid rows by default, or controlled invalid/edge data.")
    generate_parser.add_argument("--invalid-ratio", type=ratio, default=0.0, help="Share of invalid values for mixed/negative modes, between 0 and 1.")
    generate_parser.add_argument("--seed", type=non_negative_int, help="Deterministic seed. Reuse it to reproduce the same output.")
    generate_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], dest="output_format", help="Output format for generated rows.")
    generate_parser.add_argument("--output", "-o", type=Path, help="Output folder for DatasetSpec generation, or output file for --profile.")
    generate_parser.add_argument("--business-rules", type=Path, help="Optional YAML/JSON business rules to enforce and validate.")
    generate_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing single-file output.")

    profile_example_parser = subparsers.add_parser(
        "profile-example",
        aliases=["profile-csv-folder"],
        help="Create a safe profile from a folder of related CSV files.",
        description="Profile a CSV folder without writing source rows or raw PII to the profile.",
        epilog=(
            "Example:\n"
            "  test-data-agent profile-example data/example_dataset "
            "--output out/profile.json\n\n"
            "Then review the profile and run:\n"
            "  test-data-agent infer-spec out/profile.json --output out/dataset_spec.yaml"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    profile_example_parser.add_argument("input_folder", type=Path, help="Folder containing one CSV file per table.")
    profile_example_parser.add_argument("--output", "-o", type=Path, required=True, help="Profile JSON to write.")
    profile_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"), help="Safe profile cache directory.")
    profile_example_parser.add_argument("--no-cache", action="store_true", help="Force a fresh profile instead of reusing the cache.")
    profile_example_parser.add_argument("--rule-sample-rows", type=positive_int, default=50_000, help="Rows sampled for relationship and rule mining.")
    profile_example_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing profile JSON.")

    infer_spec_parser = subparsers.add_parser(
        "infer-spec",
        help="Infer a reusable DatasetSpec YAML from a safe profile.",
        description="Turn a safe profile JSON into a DatasetSpec YAML recipe for generation.",
        epilog=(
            "Example:\n"
            "  test-data-agent infer-spec out/profile.json "
            "--count 100 --output out/dataset_spec.yaml\n\n"
            "Review the spec before passing it to the generate command."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    infer_spec_parser.add_argument("profile", type=Path, help="Safe profile JSON.")
    infer_spec_parser.add_argument("--output", "-o", type=Path, required=True, help="DatasetSpec YAML/JSON to write.")
    infer_spec_parser.add_argument("--count", type=positive_int, help="Override row count per entity in the inferred spec.")
    infer_spec_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing spec file.")

    profile_csv_parser = subparsers.add_parser(
        "profile-csv",
        help="Create a safe profile from one CSV file.",
        description="Profile one CSV file into safe metadata: schema, distributions, ranges, and masked sensitive patterns.",
        epilog=(
            "Example:\n"
            "  test-data-agent profile-csv data/customers.csv "
            "--output out/customers_profile.json\n\n"
            "For the complete one-command workflow, use generate-from-csv."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    profile_csv_parser.add_argument("input", type=Path, help="Source CSV file. Source rows are not copied to the profile.")
    profile_csv_parser.add_argument("--table", type=str, help="Table/entity name to use in the profile.")
    profile_csv_parser.add_argument("--output", "-o", type=Path, required=True, help="Profile JSON to write.")
    profile_csv_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing profile JSON.")

    generate_csv_parser = subparsers.add_parser(
        "generate-from-csv",
        help="Generate a synthetic single-table dataset directly from one CSV file.",
        description="Profile one CSV file, infer a DatasetSpec, generate synthetic rows, and validate the result.",
        epilog=(
            "Example:\n"
            "  test-data-agent generate-from-csv tests/fixtures/customers.csv "
            "--count 25 --seed 12345 --format csv --output out/customers.csv\n\n"
            "Writes csv_profile.json, dataset_spec.json, validation_report.json, "
            "and generation_manifest.json next to the output file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    generate_csv_parser.add_argument("input", type=Path, help="Source CSV file used only for safe metadata.")
    generate_csv_parser.add_argument("--count", type=positive_int, required=True, help="Number of synthetic rows to generate.")
    generate_csv_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid", help="Generation mode: valid rows by default, or controlled invalid/edge data.")
    generate_csv_parser.add_argument("--invalid-ratio", type=ratio, default=0.0, help="Share of invalid values for mixed/negative modes, between 0 and 1.")
    generate_csv_parser.add_argument("--seed", type=non_negative_int, required=True, help="Deterministic seed. Reuse it to reproduce the same output.")
    generate_csv_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], required=True, dest="output_format", help="Output format for generated rows.")
    generate_csv_parser.add_argument("--output", "-o", type=Path, required=True, help="Generated output file.")
    generate_csv_parser.add_argument("--table", type=str, help="Table/entity name to use for the generated dataset.")
    generate_csv_parser.add_argument("--business-rules", type=Path, help="Optional YAML/JSON business rules to enforce and validate.")
    generate_csv_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing generated file.")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate generated rows against a DatasetSpec.",
        description="Validate generated files and optionally write a validation_report.json.",
        epilog=(
            "Example:\n"
            "  test-data-agent validate dataset_spec.yaml out/generated "
            "--output out/generated/validation_report.json\n\n"
            "The rows argument must be the generated dataset folder, not one data file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    validate_parser.add_argument("spec", type=Path, help="DatasetSpec YAML/JSON.")
    validate_parser.add_argument("rows", type=Path, help="Generated output folder.")
    validate_parser.add_argument("--output", "-o", type=Path, help="Validation report JSON to write.")
    validate_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing validation report.")

    generate_example_parser = subparsers.add_parser(
        "generate-from-example",
        aliases=["generate-from-csv-folder"],
        help="Generate a related multi-table dataset from a folder of CSV examples.",
        description="Profile a CSV folder, infer a DatasetSpec, generate synthetic related tables, and validate them.",
        epilog=(
            "Example:\n"
            "  test-data-agent generate-from-example tests/fixtures/example_dataset "
            "--count 25 --seed 12345 --format csv --output out/example_dataset\n\n"
            "Writes profile.json, dataset_spec.yaml, validation_report.json, "
            "generation_manifest.json, and one synthetic data file per entity."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    generate_example_parser.add_argument("input_folder", type=Path, help="Folder containing one CSV file per table.")
    generate_example_parser.add_argument("--output", "-o", type=Path, required=True, help="Output folder for generated tables and review artifacts.")
    generate_example_parser.add_argument("--seed", type=non_negative_int, required=True, help="Deterministic seed. Reuse it to reproduce the same output.")
    generate_example_parser.add_argument("--count", type=positive_int, help="Override generated row count per entity.")
    generate_example_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], required=True, dest="output_format", help="Output format for generated rows.")
    generate_example_parser.add_argument("--cache-dir", type=Path, default=Path(".test_data_agent_cache/profiles"), help="Safe profile cache directory.")
    generate_example_parser.add_argument("--no-cache", action="store_true", help="Force a fresh profile instead of reusing the cache.")
    generate_example_parser.add_argument("--rule-sample-rows", type=positive_int, default=50_000, help="Rows sampled for relationship and rule mining.")

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Run local environment and fixture smoke checks.",
        description="Check Python, installed features, and a small synthetic generation smoke test.",
        epilog=(
            "Examples:\n"
            "  test-data-agent doctor\n"
            "  test-data-agent doctor --require-extra openai"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    doctor_parser.add_argument("--skip-smoke", action="store_true", help="Only check Python and importable dependencies.")
    doctor_parser.add_argument(
        "--require-extra",
        action="append",
        choices=["parquet", "mcp", "trino", "openai", "all"],
        default=[],
        help="Fail when an optional feature is unavailable. Repeat to require multiple extras.",
    )

    audit_verify_parser = subparsers.add_parser(
        "audit-verify",
        help="Verify an HMAC-authenticated MCP audit log.",
        description="Verify the complete HMAC chain of a metadata-only MCP audit JSONL file.",
        epilog=(
            "Example:\n"
            "  TEST_DATA_AGENT_AUDIT_KEY_FILE=/run/secrets/audit.key "
            "test-data-agent audit-verify logs/mcp-audit.jsonl"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    audit_verify_parser.add_argument("log", type=Path, help="Audit JSONL file to verify.")

    agent_plan_parser = subparsers.add_parser(
        "agent-plan",
        help="Plan a safe agent workflow and stop before generation.",
        description="Profile input data, infer a reviewable DatasetSpec, and require approval before generation.",
        epilog=(
            "Example:\n"
            "  test-data-agent agent-plan tests/fixtures/example_dataset "
            "--workspace out/agent --count 25 --seed 12345 --format csv\n"
            "  test-data-agent agent-review out/agent\n"
            "  test-data-agent agent-approve out/agent "
            "--reviewed-spec-sha256 SHA256_FROM_STATUS"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_plan_parser.add_argument("source", type=Path, help="CSV file, CSV folder, or safe profile JSON.")
    agent_plan_parser.add_argument(
        "--source-type",
        choices=["csv", "csv-folder", "profile"],
        help="Override automatic CSV, CSV-folder, or safe-profile detection.",
    )
    agent_plan_parser.add_argument("--workspace", type=Path, required=True, help="Empty folder for agent artifacts.")
    agent_plan_parser.add_argument("--count", type=positive_int, default=100, help="Synthetic row count per entity.")
    agent_plan_parser.add_argument("--seed", type=non_negative_int, default=12345, help="Deterministic generation seed.")
    agent_plan_parser.add_argument("--format", choices=[item.value for item in CoreOutputFormat], default="csv", dest="output_format")
    agent_plan_parser.add_argument("--mode", choices=[item.value for item in CoreGenerationMode], default="valid")
    agent_plan_parser.add_argument("--invalid-ratio", type=ratio, default=0.0)
    agent_plan_parser.add_argument("--table", type=str, help="Table/entity name for single CSV sources.")
    agent_plan_parser.add_argument("--rule-sample-rows", type=positive_int, default=50_000)
    agent_plan_parser.add_argument("--use-cache", action="store_true", help="Use a safe profile cache inside the agent workspace.")
    agent_plan_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned agent result as JSON.",
    )

    agent_approve_parser = subparsers.add_parser(
        "agent-approve",
        help="Approve a planned agent workflow and generate synthetic data.",
        description="Load a prepared agent workspace, use the reviewed DatasetSpec, generate data, and validate it.",
        epilog=(
            "Example:\n"
            "  test-data-agent agent-review out/agent\n"
            "  test-data-agent agent-approve out/agent "
            "--reviewed-spec-sha256 SHA256_FROM_STATUS\n\n"
            "Run this only after reviewing out/agent/dataset_spec.yaml and "
            "recording the fingerprint reported by agent-review."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_approve_parser.add_argument("workspace", type=Path, help="Workspace created by agent-plan.")
    agent_approve_parser.add_argument(
        "--reviewed-spec-sha256",
        required=True,
        help="SHA-256 reported by agent-review for the exact reviewed DatasetSpec.",
    )
    agent_approve_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned agent result as JSON.",
    )

    agent_recover_parser = subparsers.add_parser(
        "agent-recover",
        help="Finish publishing an interrupted approved agent run.",
        description=(
            "Revalidate an existing generated bundle and publish missing completion "
            "metadata without regenerating rows."
        ),
        epilog=(
            "Example:\n"
            "  test-data-agent agent-status out/agent\n"
            "  test-data-agent agent-recover out/agent "
            "--reviewed-spec-sha256 SHA256_FROM_STATUS\n\n"
            "Use this only when agent-status reports recovery_required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_recover_parser.add_argument(
        "workspace",
        type=Path,
        help="Workspace whose approval was interrupted.",
    )
    agent_recover_parser.add_argument(
        "--reviewed-spec-sha256",
        required=True,
        help="SHA-256 reported by agent-status for the reviewed DatasetSpec.",
    )
    agent_recover_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned agent result as JSON.",
    )

    agent_advise_parser = subparsers.add_parser(
        "agent-advise",
        help="Ask an optional AI provider to propose safe DatasetSpec changes.",
        description=(
            "Send safe profile metadata to a configured provider, validate its "
            "structured proposal, and stop for another human review."
        ),
        epilog=(
            "Example:\n"
            "  python3 -m pip install \"agent-paranoid-android[openai]\"\n"
            "  test-data-agent agent-advise out/agent --provider openai\n"
            "  test-data-agent agent-review out/agent\n\n"
            "The provider receives metadata, not source rows. This command never "
            "approves a spec or generates data."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_advise_parser.add_argument(
        "workspace",
        type=Path,
        help="Awaiting-approval workspace created by agent-plan.",
    )
    agent_advise_parser.add_argument(
        "--provider",
        choices=["openai"],
        default="openai",
        help="Structured-output provider. Currently supported: openai.",
    )
    agent_advise_parser.add_argument(
        "--model",
        help="Provider model override. Uses the adapter default when omitted.",
    )
    agent_advise_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned pending workspace status as JSON.",
    )

    agent_advisor_request_parser = subparsers.add_parser(
        "agent-advisor-request",
        help="Export safe metadata for an external AI advisor.",
        description=(
            "Write one fingerprint-bound advisor request JSON document to stdout "
            "without changing the workspace."
        ),
        epilog=(
            "Recommended external AI exchange:\n"
            "  test-data-agent agent-advisor-request out/agent "
            "--exchange > advisor_exchange.json\n\n"
            "Raw request for custom adapters:\n"
            "  test-data-agent agent-advisor-request out/agent "
            "> advisor_request.json\n\n"
            "Exchange mode separates trusted instructions, untrusted request "
            "metadata, and the AdvisorProposal JSON Schema."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_advisor_request_parser.add_argument(
        "workspace",
        type=Path,
        help="Awaiting-approval workspace created by agent-plan.",
    )
    agent_advisor_request_parser.add_argument(
        "--exchange",
        action="store_true",
        help=(
            "Include trusted instructions and the AdvisorProposal JSON Schema "
            "around the request."
        ),
    )
    agent_advisor_request_parser.set_defaults(json_output=True)

    agent_advisor_apply_parser = subparsers.add_parser(
        "agent-advisor-apply",
        help="Validate and apply an external AI proposal for review.",
        description=(
            "Read a bounded proposal JSON file, validate it against the workspace "
            "request, and update the pending DatasetSpec without generating data."
        ),
        epilog=(
            "Example:\n"
            "  test-data-agent agent-advisor-apply "
            "out/agent advisor_proposal.json\n\n"
            "Review dataset_spec.yaml after this command, then use agent-review "
            "and agent-approve with the exact reviewed fingerprint."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_advisor_apply_parser.add_argument(
        "workspace",
        type=Path,
        help="Awaiting-approval workspace used to create the advisor request.",
    )
    agent_advisor_apply_parser.add_argument(
        "proposal",
        type=Path,
        help="Bounded regular JSON file containing an AdvisorProposal.",
    )
    agent_advisor_apply_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned pending workspace status as JSON.",
    )

    agent_status_parser = subparsers.add_parser(
        "agent-status",
        help="Inspect a planned or completed agent workspace.",
        description="Read an agent workspace and report its phase, next action, and artifact summary.",
        epilog=(
            "Examples:\n"
            "  test-data-agent agent-status out/agent\n"
            "  test-data-agent agent-status out/agent --json\n\n"
            "Status inspection never generates data or changes the workspace."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_status_parser.add_argument("workspace", type=Path, help="Workspace created by agent-plan.")
    agent_status_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned status contract as JSON.",
    )

    agent_review_parser = subparsers.add_parser(
        "agent-review",
        help="Review the current DatasetSpec before approval.",
        description=(
            "Show a metadata-only field, relationship, privacy, and fingerprint "
            "checklist without changing the workspace."
        ),
        epilog=(
            "Examples:\n"
            "  test-data-agent agent-review out/agent\n"
            "  test-data-agent agent-review out/agent --json\n\n"
            "Review dataset_spec.yaml, then pass the reported current SHA-256 "
            "unchanged to agent-approve."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_review_parser.add_argument(
        "workspace",
        type=Path,
        help="Awaiting-approval workspace created by agent-plan.",
    )
    agent_review_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Write the versioned metadata-only review report as JSON.",
    )

    subparsers.add_parser(
        "examples",
        help="Show copy-ready examples for common workflows.",
        description=EXAMPLES_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        write_validation_summary(report, args.output)
        text = report.model_dump_json(indent=2)
        if args.output is None:
            print(text)
        return 0 if report.valid else 1

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


def friendly_error(exc: Exception) -> str:
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


def write_validation_summary(report: Any, output: Path | None) -> None:
    failed = sum(section.failed for section in report.sections)
    passed = sum(section.passed for section in report.sections)
    status = "passed" if report.valid else "failed"
    destination = f" Report: {output}" if output is not None else ""
    print(f"Validation {status}: {passed} checks passed, {failed} failed.{destination}", file=sys.stderr)


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
