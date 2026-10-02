"""Separate execution registration never exposes a receipt issuer to agents."""

import argparse
import pytest

import test_data_agent
from test_data_agent.cli import build_parser
from test_data_agent.mcp_generator_server import _GENERATOR_MCP_TOOLS


@pytest.mark.parametrize("command", ["transform-execute", "transform-approve"])
def test_execution_and_receipt_cli_explicitly_registered(command):
    parser = build_parser([command])
    choices = next(action.choices for action in parser._actions
                   if isinstance(action, argparse._SubParsersAction))
    assert command in choices


def test_agent_surfaces_expose_consumers_not_receipt_issuers():
    names = {tool.__name__ for tool in _GENERATOR_MCP_TOOLS}
    assert {name for name in names if "transform" in name} == {
        "review_transformation", "execute_transformation"}
    assert not {name for name in test_data_agent.__all__ if "transform" in name.lower()}
    assert "issue_local_receipt" not in names
    assert "verify_local_receipt" not in names
