"""CLI handlers for review-first agent lifecycle commands."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

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
from test_data_agent.advisor import (
    AdvisorContractError,
    AdvisorProposal,
    ExchangeDatasetAdvisor,
)
from test_data_agent.cli_dependencies import (
    DEFAULT_CLI_DEPENDENCY_RESOLVER,
    CliDependencyResolver,
)
from test_data_agent.cli_contract import CliExternalServiceError
from test_data_agent.cli_presenter import (
    write_agent_command_result,
    write_agent_review_result,
    write_agent_status_result,
    write_json_document,
)
from test_data_agent.core.limits import read_limited_text
from test_data_agent.core.settings import GenerationMode, OutputFormat

AgentRequestBuilder = Callable[[argparse.Namespace], AgentRequest]


class AgentAdvisorRunner(Protocol):
    def __call__(
        self,
        workspace: Path,
        *,
        provider: str,
        model: str | None,
    ) -> AgentWorkspaceStatus: ...


def run_agent_command(
    args: argparse.Namespace,
    *,
    request_builder: AgentRequestBuilder | None = None,
    advisor_runner: AgentAdvisorRunner | None = None,
) -> int | None:
    """Run one agent command, or return ``None`` when it is not agent-owned."""

    request_builder = request_builder or agent_request_from_args
    advisor_runner = advisor_runner or advise_agent_workspace_with_provider

    if args.command == "agent-plan":
        agent_result = plan_agent_request(request_builder(args))
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
        status = advisor_runner(
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
        proposal = AdvisorProposal.model_validate_json(read_limited_text(args.proposal))
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

    return None


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
        output_format=OutputFormat(args.output_format),
        mode=GenerationMode(args.mode),
        invalid_ratio=args.invalid_ratio,
        table_name=args.table,
        rule_sample_rows=args.rule_sample_rows,
        use_cache=not args.no_cache,
        local_category_fields=getattr(args, "local_category_fields", []),
    )


def advise_agent_workspace_with_provider(
    workspace: Path,
    *,
    provider: str,
    model: str | None,
    dependencies: CliDependencyResolver = DEFAULT_CLI_DEPENDENCY_RESOLVER,
) -> AgentWorkspaceStatus:
    if provider == "openai":

        def load_provider() -> tuple[str, Any]:
            from test_data_agent.providers.openai import (
                DEFAULT_OPENAI_MODEL,
                OpenAIAdvisorClient,
            )

            return DEFAULT_OPENAI_MODEL, OpenAIAdvisorClient

        purpose = "OpenAI advice"
    elif provider == "gigachat":

        def load_provider() -> tuple[str, Any]:
            from test_data_agent.providers.gigachat import (
                DEFAULT_GIGACHAT_MODEL,
                GigaChatAdvisorClient,
            )

            return DEFAULT_GIGACHAT_MODEL, GigaChatAdvisorClient

        purpose = "GigaChat advice"
    else:
        raise ValueError(f"unsupported advisor provider: {provider}")

    default_model, advisor_client = dependencies.load(
        extra=provider,
        purpose=purpose,
        loader=load_provider,
    )
    client = advisor_client(model=model or default_model)
    try:
        try:
            return advise_agent_workspace(
                workspace,
                ExchangeDatasetAdvisor(client),
            )
        except AdvisorContractError as exc:
            raise CliExternalServiceError(str(exc)) from None
    finally:
        if provider == "gigachat":
            client.close()
