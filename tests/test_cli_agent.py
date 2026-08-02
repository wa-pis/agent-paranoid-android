import argparse
import ast
import json
from pathlib import Path
from types import ModuleType

import pytest
import test_data_agent.cli_agent as cli_agent_module
from test_data_agent.cli_agent import (
    advise_agent_workspace_with_provider,
    run_agent_command,
)


FIXTURE_DATASET = Path("tests/fixtures/example_dataset")


def test_agent_handler_plans_without_generating_rows(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "agent"
    args = argparse.Namespace(
        command="agent-plan",
        source=FIXTURE_DATASET,
        source_type=None,
        workspace=workspace,
        count=3,
        seed=42,
        output_format="csv",
        mode="valid",
        invalid_ratio=0.0,
        table=None,
        rule_sample_rows=50_000,
        no_cache=True,
        json_output=True,
    )

    assert run_agent_command(args) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["phase"] == "awaiting_approval"
    assert payload["summary"]["metadata_trust"] == "untrusted"
    assert "alice@example.com" not in captured.out
    assert not (workspace / "generated").exists()


def test_agent_handler_ignores_non_agent_command() -> None:
    assert run_agent_command(argparse.Namespace(command="doctor")) is None


def test_agent_provider_rejects_unknown_provider_before_workspace_access() -> None:
    with pytest.raises(ValueError, match="unsupported advisor provider"):
        advise_agent_workspace_with_provider(
            Path("missing-workspace"),
            provider="unknown",
            model=None,
        )


def test_agent_handler_boundary_has_no_composition_or_mcp_imports() -> None:
    forbidden = {
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(cli_agent_module).isdisjoint(forbidden)


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
