"""Unregistered CLI candidate, exercised only on fictional temporary fixtures.

Not imported by CLI composition, package facade or MCP. Activation requires
end-to-end evidence and independent review of the completed wiring.
"""

from pathlib import Path
from typing import Never
import argparse
import json

from test_data_agent.cli_parser import HelpfulArgumentParser

from test_data_agent.core.limits import (
    DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, GenerationBudget,
)
from test_data_agent.core.transformation_limits import InputDimension, resolve_input_limit
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.core.transformation_policy import validate_execution_actions
import os
from test_data_agent.io.transformation_publish import _execute_reviewed_test_from_paths
from test_data_agent.io.transformation_receipt import LocalReceiptError, issue_local_receipt
from test_data_agent.io.transformation_source import prepare_csv_review_from_paths


class _CandidateArgumentParser(HelpfulArgumentParser):
    """Keep rejected caller values out of CLI diagnostics."""

    def error(self, message: str) -> Never:
        super().error("invalid transformation arguments")


def _add_execution_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--table")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--max-total-input-bytes", type=int)
    parser.add_argument("--max-output-bytes", type=int,
        help="Run output cap in bytes; defaults to effective session/profile ceiling.")


def _create_test_execution_parser(*, json_errors: bool = False) -> argparse.ArgumentParser:
    """Prospective command composition, only constructed by fictional tests."""
    from test_data_agent.cli_parser import add_common_runtime_options

    parser = _CandidateArgumentParser(prog="test-data-agent", json_errors=json_errors)
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_CandidateArgumentParser)
    execution = commands.add_parser("transform-execute", json_errors=json_errors,
        help="Execute a separately reviewed local mixed-origin transformation.")
    _add_execution_arguments(execution)
    add_common_runtime_options(parser)
    add_common_runtime_options(execution)
    return parser


def _run_candidate_execution(argv: list[str], *, json_errors: bool = False) -> dict[str, object]:
    """Parse a proposed execution request; never mint an approval receipt."""
    parser = _CandidateArgumentParser(prog="closed-transform-execute", json_errors=json_errors)
    _add_execution_arguments(parser)
    args = parser.parse_args(argv)
    return _execute_candidate_namespace(args)


def _execute_candidate_namespace(args: argparse.Namespace) -> dict[str, object]:
    return _execute_reviewed_test_from_paths(args.source, args.table or args.source.stem,
        args.policy, args.destination, expected_snapshot_sha256=args.snapshot_sha256,
        max_total_bytes=args.max_total_input_bytes,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES,
        max_output_bytes=args.max_output_bytes, budget=GenerationBudget(),
        receipt_path=args.receipt)


def _candidate_execution_main(argv: list[str], *, json_output: bool = False,
                              prospective: bool = False) -> int:
    """Closed test entrypoint; not connected to production command composition."""
    from test_data_agent.cli_contract import CliErrorCode
    from test_data_agent.cli_presenter import report_cli_error
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.io.transformation_publish import TransformationCleanupError

    args = argparse.Namespace(command="closed-transform-execute", json_output=json_output)
    try:
        if prospective:
            args = _create_test_execution_parser(json_errors=json_output or "--json" in argv).parse_args(argv)
            args.json_output = args.json_output or json_output
            result = _execute_candidate_namespace(args)
        else:
            result = _run_candidate_execution(argv, json_errors=json_output)
    except (TransformationLimitError, TransformationCleanupError) as error:
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT, message=str(error))
    except (ValueError, OSError):
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT,
            message="invalid transformation request; no successful publication confirmed")
    print(json.dumps(result))
    return 0


def _run_candidate_local_approval(argv: list[str]) -> dict[str, object]:
    """Local controlling-TTY confirmation only; never registered in MCP."""
    parser = _CandidateArgumentParser(prog="closed-transform-approve")
    parser.add_argument("source", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--table")
    parser.add_argument("--max-total-input-bytes", type=int)
    args = parser.parse_args(argv)
    return _approve_candidate_namespace(args)


def _approve_candidate_namespace(args: argparse.Namespace) -> dict[str, object]:
    """Shared local-only approval dispatch; controlling-TTY enforcement unchanged."""
    budget = GenerationBudget()
    request = prepare_csv_review_from_paths(args.source, args.table or args.source.stem,
        args.policy.parent.absolute(), args.policy.name, max_total_bytes=args.max_total_input_bytes,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, budget=budget)
    if (request.snapshot_sha256 != args.snapshot_sha256
            or args.receipt.exists() or args.receipt.is_symlink()):
        raise LocalReceiptError("local transformation approval failed")
    policy_bytes = next(part.payload for part in request.parts if part.kind == "policy")
    policy = load_behavior_policy_yaml(policy_bytes, max_bytes=len(policy_bytes), budget=budget)
    validate_execution_actions(policy)
    total = resolve_input_limit(InputDimension.TOTAL_BYTES, policy.resource_limits, os.environ).value
    issue_local_receipt(request, args.receipt,
        max_total_bytes=total if args.max_total_input_bytes is None else args.max_total_input_bytes,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, budget=budget)
    return {"status": "local_receipt_created", "snapshot_sha256": request.snapshot_sha256}
