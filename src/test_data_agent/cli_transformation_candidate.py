"""Unregistered CLI candidate, exercised only on fictional temporary fixtures.

Not imported by CLI composition, package facade or MCP. Activation requires
end-to-end evidence and independent review of the completed wiring.
"""

import argparse
from pathlib import Path

from test_data_agent.core.limits import (
    DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, DEFAULT_MAX_TOTAL_INPUT_BYTES, GenerationBudget,
)
from test_data_agent.io.transformation_publish import _execute_reviewed_test_from_paths
from test_data_agent.io.transformation_receipt import LocalReceiptError, issue_local_receipt
from test_data_agent.io.transformation_source import prepare_csv_review_from_paths


def _run_candidate_execution(argv: list[str]) -> dict[str, object]:
    """Parse a proposed execution request; never mint an approval receipt."""
    parser = argparse.ArgumentParser(prog="closed-transform-execute")
    parser.add_argument("source", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--table")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--max-output-bytes", type=int,
        help="Run output cap in bytes; defaults to effective session/profile ceiling.")
    args = parser.parse_args(argv)
    return _execute_reviewed_test_from_paths(args.source, args.table or args.source.stem,
        args.policy, args.destination, expected_snapshot_sha256=args.snapshot_sha256,
        max_total_bytes=DEFAULT_MAX_TOTAL_INPUT_BYTES,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES,
        max_output_bytes=args.max_output_bytes, budget=GenerationBudget(),
        receipt_path=args.receipt)


def _run_candidate_local_approval(argv: list[str]) -> dict[str, object]:
    """Local controlling-TTY confirmation only; never registered in MCP."""
    parser = argparse.ArgumentParser(prog="closed-transform-approve")
    parser.add_argument("source", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--table")
    args = parser.parse_args(argv)
    budget = GenerationBudget()
    request = prepare_csv_review_from_paths(args.source, args.table or args.source.stem,
        args.policy.parent.absolute(), args.policy.name, max_total_bytes=DEFAULT_MAX_TOTAL_INPUT_BYTES,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, budget=budget)
    if (request.snapshot_sha256 != args.snapshot_sha256
            or args.receipt.exists() or args.receipt.is_symlink()):
        raise LocalReceiptError("local transformation approval failed")
    issue_local_receipt(request, args.receipt, max_total_bytes=DEFAULT_MAX_TOTAL_INPUT_BYTES,
        max_review_bytes=DEFAULT_MAX_PROFILE_PAYLOAD_BYTES, budget=budget)
    return {"status": "local_receipt_created", "snapshot_sha256": request.snapshot_sha256}
