"""Runnable review-first agent integration using the public Python API."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from test_data_agent import (
    AgentRequest,
    AdvisorExchange,
    AdvisorExchangeClient,
    AdvisorProposal,
    ExchangeDatasetAdvisor,
    advise_agent_workspace,
    approve_agent_workspace,
    detect_agent_source_type,
    inspect_agent_workspace,
    plan_agent_request,
)
from test_data_agent.core.settings import OutputFormat


class BaselineAdvisorClient:
    """Safe stand-in for a provider-specific structured-output client."""

    def complete(self, exchange: AdvisorExchange) -> dict[str, Any]:
        request = exchange.request
        return AdvisorProposal(
            profile_sha256=request.profile_sha256,
            baseline_spec_sha256=request.baseline_spec_sha256,
            dataset_spec=request.baseline_spec.model_copy(deep=True),
        ).model_dump(mode="json")


def build_advisor_client(
    provider: str,
    *,
    model: str | None = None,
) -> AdvisorExchangeClient:
    if provider == "baseline":
        return BaselineAdvisorClient()
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
    return OpenAIAdvisorClient(model=model or DEFAULT_OPENAI_MODEL)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the review-first agent flow with the local baseline or an "
            "optional structured-output provider."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser(
        "plan",
        help="Profile input, obtain a safe advisor proposal, and stop for review.",
    )
    plan_parser.add_argument("source", type=Path)
    plan_parser.add_argument("--workspace", type=Path, required=True)
    plan_parser.add_argument("--count", type=int, default=100)
    plan_parser.add_argument("--seed", type=int, default=12345)
    plan_parser.add_argument(
        "--advisor",
        choices=["baseline", "openai"],
        default="baseline",
        help="Advisor implementation. OpenAI requires the optional openai extra.",
    )
    plan_parser.add_argument(
        "--model",
        help="OpenAI model override. Ignored by the baseline advisor.",
    )
    plan_parser.add_argument(
        "--format",
        choices=[output_format.value for output_format in OutputFormat],
        default=OutputFormat.CSV.value,
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Inspect a workspace without modifying it.",
    )
    status_parser.add_argument("workspace", type=Path)

    approve_parser = subparsers.add_parser(
        "approve",
        help="Generate only from the exact human-reviewed DatasetSpec.",
    )
    approve_parser.add_argument("workspace", type=Path)
    approve_parser.add_argument(
        "--reviewed-spec-sha256",
        required=True,
        help="Exact review.current_spec_sha256 shown after human review.",
    )
    return parser


def run(args: argparse.Namespace) -> str:
    if args.command == "plan":
        plan_agent_request(
            AgentRequest(
                source_type=detect_agent_source_type(args.source),
                source_path=args.source,
                workspace=args.workspace,
                count=args.count,
                seed=args.seed,
                output_format=OutputFormat(args.format),
            )
        )
        result = advise_agent_workspace(
            args.workspace,
            ExchangeDatasetAdvisor(
                build_advisor_client(args.advisor, model=args.model)
            ),
        )
    elif args.command == "status":
        result = inspect_agent_workspace(args.workspace)
    else:
        result = approve_agent_workspace(
            args.workspace,
            reviewed_spec_sha256=args.reviewed_spec_sha256,
        )
    return result.model_dump_json(indent=2)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = run(args)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"reference-agent: {exc}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
