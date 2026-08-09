"""Reusable parsing primitives for the public command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Never

from test_data_agent.cli_contract import (
    CliErrorCode,
    CliErrorDetail,
    CliErrorResponse,
)
from test_data_agent.cli_text import bound_untrusted_text, display_untrusted_text
from test_data_agent.core.settings import (
    GenerationMode as CoreGenerationMode,
    OutputFormat as CoreOutputFormat,
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
        print(
            f"{self.prog}: error: {display_untrusted_text(message)}",
            file=sys.stderr,
        )
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
            message=bound_untrusted_text(message),
            command=bound_untrusted_text(command, limit=256),
            exit_code=exit_code,
            help=(
                bound_untrusted_text(help_command, limit=256)
                if help_command is not None
                else None
            ),
        )
    )
    print(response.model_dump_json(indent=2))


def register_dataset_commands(
    subparsers: argparse._SubParsersAction[HelpfulArgumentParser],
    *,
    generate_epilog: str,
) -> None:
    """Register dataset profiling, generation, and validation commands."""
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a dataset from a DatasetSpec, or from a safe profile with --profile.",
        description="Generate synthetic rows from a DatasetSpec file or safe profile metadata.",
        epilog=generate_epilog,
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
    generate_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing single-entity bundle.")

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
    generate_csv_parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing single-entity bundle.")

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


def register_utility_commands(
    subparsers: argparse._SubParsersAction[HelpfulArgumentParser],
) -> None:
    """Register environment and audit utility commands."""
    demo_parser = subparsers.add_parser(
        "demo",
        help="Generate a deterministic offline demo dataset.",
        description=(
            "Run the installed package against a bundled fictional fixture "
            "without network access or optional integrations."
        ),
    )
    demo_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="New folder for generated demo data and review artifacts.",
    )

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


def register_examples_command(
    subparsers: argparse._SubParsersAction[HelpfulArgumentParser],
    *,
    examples_text: str,
) -> None:
    """Register the copy-ready workflow examples command."""
    subparsers.add_parser(
        "examples",
        help="Show copy-ready examples for common workflows.",
        description=examples_text,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def register_agent_commands(
    subparsers: argparse._SubParsersAction[HelpfulArgumentParser],
) -> None:
    """Register review-gated agent workflow commands."""
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
    agent_plan_parser.add_argument(
        "source",
        type=Path,
        help="CSV file, CSV folder, or safe profile JSON.",
    )
    agent_plan_parser.add_argument(
        "--source-type",
        choices=["csv", "csv-folder", "profile"],
        help="Override automatic CSV, CSV-folder, or safe-profile detection.",
    )
    agent_plan_parser.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Empty folder for agent artifacts.",
    )
    agent_plan_parser.add_argument(
        "--count",
        type=positive_int,
        default=100,
        help="Synthetic row count per entity.",
    )
    agent_plan_parser.add_argument(
        "--seed",
        type=non_negative_int,
        default=12345,
        help="Deterministic generation seed.",
    )
    agent_plan_parser.add_argument(
        "--format",
        choices=[item.value for item in CoreOutputFormat],
        default="csv",
        dest="output_format",
    )
    agent_plan_parser.add_argument(
        "--mode",
        choices=[item.value for item in CoreGenerationMode],
        default="valid",
    )
    agent_plan_parser.add_argument(
        "--invalid-ratio",
        type=ratio,
        default=0.0,
    )
    agent_plan_parser.add_argument(
        "--table",
        type=str,
        help="Table/entity name for single CSV sources.",
    )
    agent_plan_parser.add_argument(
        "--rule-sample-rows",
        type=positive_int,
        default=50_000,
    )
    agent_plan_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force a fresh profile instead of reusing the metadata-only cache.",
    )
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
    agent_approve_parser.add_argument(
        "workspace",
        type=Path,
        help="Workspace created by agent-plan.",
    )
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
    agent_status_parser.add_argument(
        "workspace",
        type=Path,
        help="Workspace created by agent-plan.",
    )
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
