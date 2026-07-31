from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

import test_data_agent.mcp_generator_transport as transport


class FakeMCP:
    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: list[Callable[..., Any]] = []

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def register(function: Callable[..., Any]) -> Callable[..., Any]:
            self.tools.append(function)
            return function

        return register


def test_generator_transport_registers_audited_services_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audited: list[tuple[str, str]] = []

    def profile_csv() -> str:
        return "profiled"

    def generate_dataset() -> str:
        return "generated"

    def record_audit(
        service: str,
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        audited.append((service, function.__name__))
        return function

    monkeypatch.setattr(transport, "FastMCP", FakeMCP)
    monkeypatch.setattr(transport, "audited_mcp_tool", record_audit)
    services = (profile_csv, generate_dataset)

    mcp = transport.create_generator_mcp(services)

    assert isinstance(mcp, FakeMCP)
    assert mcp.name == "test-data-agent-generator"
    assert [tool.__name__ for tool in mcp.tools] == [
        "profile_csv",
        "generate_dataset",
    ]
    assert audited == [
        ("generator-mcp", "profile_csv"),
        ("generator-mcp", "generate_dataset"),
    ]
    assert mcp.tools[0]() == "profiled"
    assert mcp.tools[1]() == "generated"


def test_generator_transport_is_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(transport, "FastMCP", None)

    assert transport.create_generator_mcp(()) is None
