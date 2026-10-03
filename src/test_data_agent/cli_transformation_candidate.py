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
    parser.add_argument("--max-total-input-bytes", type=int, metavar="BYTES")
    parser.add_argument("--max-output-bytes", type=int, metavar="BYTES",
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


def _write_common_result(result: dict[str, object], *, versioned_output: bool) -> None:
    if versioned_output:
        from test_data_agent.cli_contract import CliSuccessResponse
        result = CliSuccessResponse(command="test-data-agent transform-batch", exit_code=0,
            status="succeeded", result=result).model_dump(mode="json")
    print(json.dumps(result, sort_keys=True))


def _candidate_batch_main(argv: list[str], *, versioned_output: bool = False) -> int:
    """Isolated common-profile CLI composition; no production registration."""
    from test_data_agent.cli_contract import CliErrorCode
    from test_data_agent.cli_presenter import report_cli_error
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.io.transformation_batch_workflow import BatchWorkflowRequest, run_batch_workflow

    parser = _CandidateArgumentParser(prog="test-data-agent transform-batch" if versioned_output
        else "closed-common-transform", json_errors=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("operation", choices=("review", "validate", "execute"))
    parser.add_argument("root", type=Path)
    parser.add_argument("profile")
    parser.add_argument("--snapshot-sha256")
    parser.add_argument("--receipt")
    parser.add_argument("--destination")
    parser.add_argument("--max-total-input-bytes", type=int, required=True)
    parser.add_argument("--max-review-bytes", type=int, required=True)
    parser.add_argument("--max-output-bytes", type=int, required=True)
    args = parser.parse_args(argv)
    args.command, args.json_output = "transform-batch" if versioned_output else "closed-common-transform", True
    try:
        request = BatchWorkflowRequest(operation=args.operation, root=args.root.absolute(),
            profile=args.profile, snapshot_sha256=args.snapshot_sha256, receipt=args.receipt,
            destination=args.destination,
            max_total_bytes=args.max_total_input_bytes, max_review_bytes=args.max_review_bytes,
            max_output_bytes=args.max_output_bytes)
        result = run_batch_workflow(request, budget=GenerationBudget())
    except TransformationLimitError as error:
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT, message=str(error))
    except (ValueError, OSError):
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT,
            message="invalid common transformation request; no completion confirmed")
    _write_common_result(result.metadata(), versioned_output=versioned_output)
    return 0


def _candidate_batch_approve_main(argv: list[str], *, versioned_output: bool = False) -> int:
    """Unregistered local-only common approval CLI; controlling TTY required."""
    from test_data_agent.cli_contract import CliErrorCode
    from test_data_agent.cli_presenter import report_cli_error
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.io.transformation_batch_profile import load_batch_profile
    from test_data_agent.io.transformation_batch_receipt import issue_batch_receipt

    parser = _CandidateArgumentParser(prog="test-data-agent transform-batch" if versioned_output
        else "closed-common-approve", json_errors=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("root", type=Path)
    parser.add_argument("profile")
    parser.add_argument("receipt")
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--max-total-input-bytes", type=int, required=True)
    parser.add_argument("--max-review-bytes", type=int, required=True)
    args = parser.parse_args(argv)
    args.command, args.json_output = "transform-batch" if versioned_output else "closed-common-approve", True
    try:
        root, relative = args.root.absolute(), Path(args.receipt)
        if (len(relative.parts) != 1 or relative.is_absolute() or relative.name in {".", ".."}
                or args.max_total_input_bytes <= 0 or args.max_review_bytes <= 0):
            raise LocalReceiptError("local batch confirmation failed")
        receipt = root / relative
        if receipt.exists() or receipt.is_symlink():
            raise LocalReceiptError("local batch confirmation failed")
        budget = GenerationBudget()
        batch = load_batch_profile(root, args.profile, max_total_bytes=args.max_total_input_bytes,
            max_review_bytes=args.max_review_bytes, budget=budget)
        if batch.snapshot_sha256 != args.snapshot_sha256:
            raise LocalReceiptError("local batch confirmation failed")
        issue_batch_receipt(batch, receipt, max_total_bytes=args.max_total_input_bytes,
            max_review_bytes=args.max_review_bytes, budget=budget)
    except TransformationLimitError as error:
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT, message=str(error))
    except (ValueError, OSError):
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT,
            message="local batch confirmation failed; no approval confirmed")
    _write_common_result({"status": "local_batch_receipt_created",
        "snapshot_sha256": batch.snapshot_sha256}, versioned_output=versioned_output)
    return 0


def _candidate_common_main(argv: list[str], *, versioned_output: bool = False) -> int:
    """Single closed workflow entry; never registered by the production CLI."""
    if argv and argv[0] in {"review", "validate", "execute"}:
        return _candidate_batch_main(argv, versioned_output=versioned_output)
    if argv and argv[0] == "approve":
        return _candidate_batch_approve_main(argv[1:], versioned_output=versioned_output)
    if argv and argv[0] == "create":
        return _candidate_batch_create_main(argv[1:], versioned_output=versioned_output)
    _CandidateArgumentParser(prog="test-data-agent transform-batch" if versioned_output
        else "closed-common-transform", json_errors=True).error(
        "expected create, review, approve, validate or execute")


def _candidate_batch_create_main(argv: list[str], *, versioned_output: bool = False) -> int:
    """Materialize/save configuration only; optional local decision wizard."""
    import sys
    from test_data_agent.cli_contract import CliErrorCode
    from test_data_agent.cli_presenter import report_cli_error
    from test_data_agent.core.transformation_limits import TransformationLimitError
    from test_data_agent.core.transformation_yaml import _load_private_yaml
    from test_data_agent.io.transformation_batch_profile import (
        BatchProfile, temporary_batch_profile, temporary_batch_decisions, save_batch_profile,
        capture_batch_profile,
    )

    parser = _CandidateArgumentParser(prog="test-data-agent transform-batch" if versioned_output
        else "closed-common-create", json_errors=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("root", type=Path)
    parser.add_argument("profile")
    parser.add_argument("destination")
    parser.add_argument("--max-total-input-bytes", type=int, required=True)
    parser.add_argument("--max-review-bytes", type=int, required=True)
    parser.add_argument("--create-csv-policies", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--decide", action="store_true")
    parser.add_argument("--edit-actions", action="store_true")
    parser.add_argument("--edit-formats", action="store_true")
    args = parser.parse_args(argv)
    args.command, args.json_output = "transform-batch" if versioned_output else "closed-common-create", True
    try:
        root, budget = args.root.absolute(), GenerationBudget()
        if (args.max_total_input_bytes <= 0 or args.max_review_bytes <= 0
                or not args.decide and (args.edit_actions or args.edit_formats)):
            raise ValueError
        captured = capture_batch_profile(root, args.profile,
            max_total_bytes=args.max_total_input_bytes, budget=budget)
        profile = BatchProfile.model_validate(_load_private_yaml(captured, args.max_total_input_bytes))
        arguments = dict(max_total_bytes=args.max_total_input_bytes, max_review_bytes=args.max_review_bytes,
            budget=budget, create_csv_policies=args.create_csv_policies, seed=args.seed)
        context = (temporary_batch_decisions(root, profile, input_stream=sys.stdin,
            output_stream=sys.stdout, edit_actions=args.edit_actions, edit_formats=args.edit_formats,
            **arguments) if args.decide else temporary_batch_profile(root, profile, **arguments))
        with context as (_, batch):
            saved = save_batch_profile(root, args.destination, batch,
                max_total_bytes=args.max_total_input_bytes, max_review_bytes=args.max_review_bytes,
                budget=budget)
    except TransformationLimitError as error:
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT, message=str(error))
    except (ValueError, OSError):
        return report_cli_error(args, code=CliErrorCode.INVALID_INPUT,
            message="common configuration not saved or requires revalidation; no approval issued")
    _write_common_result({"status": "common_configuration_saved", "approved": False,
        "snapshot_sha256": saved.snapshot_sha256}, versioned_output=versioned_output)
    return 0
