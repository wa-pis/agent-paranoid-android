from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import test_data_agent.cli_application as application_module
from test_data_agent.agent import AgentRequest, AgentWorkspaceStatus
from test_data_agent.cli_application import dispatch_command, run_cli_command
from test_data_agent.cli_contract import DoctorReport


def test_dispatch_stops_after_first_owned_command() -> None:
    calls: list[str] = []
    args = argparse.Namespace(command="profile-csv")

    def pass_handler(parsed: argparse.Namespace) -> int | None:
        calls.append(f"pass:{parsed.command}")
        return None

    def owned_handler(parsed: argparse.Namespace) -> int | None:
        calls.append(f"owned:{parsed.command}")
        return 0

    def late_handler(parsed: argparse.Namespace) -> int | None:
        calls.append(f"late:{parsed.command}")
        return 1

    assert dispatch_command(args, (pass_handler, owned_handler, late_handler)) == 0
    assert calls == ["pass:profile-csv", "owned:profile-csv"]


def test_dispatch_returns_usage_error_for_unknown_command() -> None:
    args = argparse.Namespace(command="unknown")

    assert dispatch_command(args, ()) == 2


def test_cli_application_composes_utility_before_dataset_and_agent(
    monkeypatch,
) -> None:
    calls: list[str] = []
    args = argparse.Namespace(command="generate")

    def utility_handler(
        parsed: argparse.Namespace,
        *,
        examples_text: str,
        doctor_inspector,
    ) -> int | None:
        calls.append(f"utility:{examples_text}:{parsed.command}")
        assert doctor_inspector() == DoctorReport(checks=(), failures=())
        return None

    def dataset_handler(
        parsed: argparse.Namespace,
        *,
        business_rules_applier,
    ) -> int | None:
        calls.append(f"dataset:{parsed.command}")
        assert business_rules_applier({}, parsed, 1, None) is None
        return 7

    def agent_handler(*args: Any, **kwargs: Any) -> int | None:
        calls.append("agent")
        return 8

    def unused_request_builder(parsed: argparse.Namespace) -> AgentRequest:
        raise AssertionError(f"agent handler should not run: {parsed.command}")

    def unused_advisor_runner(
        workspace: Path,
        *,
        provider: str,
        model: str | None,
    ) -> AgentWorkspaceStatus:
        raise AssertionError(
            f"advisor should not run: {workspace}, {provider}, {model}"
        )

    monkeypatch.setattr(application_module, "run_utility_command", utility_handler)
    monkeypatch.setattr(application_module, "run_dataset_command", dataset_handler)
    monkeypatch.setattr(application_module, "run_agent_command", agent_handler)

    exit_code = run_cli_command(
        args,
        examples_text="examples",
        doctor_inspector=lambda **kwargs: DoctorReport(checks=(), failures=()),
        business_rules_applier=lambda rows, parsed, seed, spec: None,
        request_builder=unused_request_builder,
        advisor_runner=unused_advisor_runner,
    )

    assert exit_code == 7
    assert calls == ["utility:examples:generate", "dataset:generate"]
