"""CLI application composition and command dispatch."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence

from test_data_agent.cli_agent import (
    AgentAdvisorRunner,
    AgentRequestBuilder,
    run_agent_command,
)
from test_data_agent.cli_commands import (
    BusinessRulesApplier,
    DoctorInspector,
    run_dataset_command,
    run_utility_command,
)

CommandHandler = Callable[[argparse.Namespace], int | None]


def dispatch_command(
    args: argparse.Namespace,
    handlers: Sequence[CommandHandler],
) -> int:
    """Dispatch to the first handler that owns the parsed command."""

    for handler in handlers:
        exit_code = handler(args)
        if exit_code is not None:
            return exit_code
    return 2


def run_cli_command(
    args: argparse.Namespace,
    *,
    examples_text: str,
    doctor_inspector: DoctorInspector,
    business_rules_applier: BusinessRulesApplier,
    request_builder: AgentRequestBuilder,
    advisor_runner: AgentAdvisorRunner,
) -> int:
    """Compose the CLI handlers and dispatch one parsed command."""

    def run_utility(parsed: argparse.Namespace) -> int | None:
        return run_utility_command(
            parsed,
            examples_text=examples_text,
            doctor_inspector=doctor_inspector,
        )

    def run_dataset(parsed: argparse.Namespace) -> int | None:
        return run_dataset_command(
            parsed,
            business_rules_applier=business_rules_applier,
        )

    def run_agent(parsed: argparse.Namespace) -> int | None:
        return run_agent_command(
            parsed,
            request_builder=request_builder,
            advisor_runner=advisor_runner,
        )

    return dispatch_command(args, (run_utility, run_dataset, run_agent))
