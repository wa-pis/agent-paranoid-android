"""Public activation remains closed while private fictional evidence is assembled."""

import pytest

import test_data_agent
from test_data_agent.cli import build_parser
from test_data_agent.mcp_generator_server import _GENERATOR_MCP_TOOLS


@pytest.mark.parametrize("command", ["transform-execute", "transform-approve"])
def test_execution_and_receipt_cli_not_registered(command, capsys):
    with pytest.raises(SystemExit) as caught:
        build_parser([command]).parse_args([command])
    assert caught.value.code == 2
    capsys.readouterr()


def test_agent_surfaces_expose_review_only_for_transformation():
    names = {tool.__name__ for tool in _GENERATOR_MCP_TOOLS}
    assert {name for name in names if "transform" in name} == {"review_transformation"}
    assert not {name for name in test_data_agent.__all__ if "transform" in name.lower()}
    assert "issue_local_receipt" not in names
    assert "verify_local_receipt" not in names
