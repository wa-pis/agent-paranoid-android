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
        "--use-cache",
        action="store_true",
        help="Use a safe profile cache inside the agent workspace.",
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
