import ast
import json
from pathlib import Path

import pytest
import test_data_agent.workspace_store as workspace_store_module
from test_data_agent.agent import (
    AgentArtifacts as CompatibilityAgentArtifacts,
    AgentRequest,
    AgentSourceType,
    plan_agent_request,
)
from test_data_agent.workspace_store import (
    AgentArtifacts,
    FilesystemAgentWorkspaceStore,
)


FIXTURE_CUSTOMERS = Path("tests/fixtures/customers.csv")


def test_agent_module_retains_workspace_artifact_compatibility() -> None:
    assert CompatibilityAgentArtifacts is AgentArtifacts


def test_workspace_store_rejects_nonempty_workspace_without_changes(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    workspace.mkdir()
    marker = workspace / "keep.txt"
    marker.write_text("keep")

    with pytest.raises(ValueError, match="must be empty"):
        FilesystemAgentWorkspaceStore().begin_plan(workspace)

    assert marker.read_text() == "keep"
    assert list(tmp_path.iterdir()) == [workspace]


def test_agent_plan_failure_rolls_back_staged_workspace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    workspace.mkdir()

    def interrupt_spec_write(*args: object, **kwargs: object) -> None:
        raise RuntimeError("interrupted plan publication")

    monkeypatch.setattr(
        workspace_store_module,
        "write_dataset_spec_artifact",
        interrupt_spec_write,
    )

    with pytest.raises(RuntimeError, match="interrupted plan publication"):
        plan_agent_request(
            AgentRequest(
                source_type=AgentSourceType.CSV,
                source_path=FIXTURE_CUSTOMERS,
                workspace=workspace,
                count=3,
            )
        )

    assert workspace.is_dir()
    assert not any(workspace.iterdir())
    assert not list(tmp_path.glob(".agent.plan.*"))


def test_agent_plan_commits_final_paths_with_staged_cache(tmp_path: Path) -> None:
    workspace = tmp_path / "agent"
    result = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=Path("tests/fixtures/example_dataset"),
            workspace=workspace,
            count=3,
            use_cache=True,
        )
    )

    persisted_request = json.loads((workspace / "agent_request.json").read_text())

    assert result.artifacts.workspace == workspace.resolve()
    assert persisted_request["workspace"] == str(workspace.resolve())
    assert (workspace / "profile_cache").is_dir()
    assert not list(tmp_path.glob(".agent.plan.*"))


def test_workspace_store_has_no_runtime_transport_or_agent_imports() -> None:
    source = Path(workspace_store_module.__file__).read_text()
    tree = ast.parse(source)
    top_level_imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "test_data_agent.agent" not in top_level_imports
    assert "test_data_agent.cli" not in top_level_imports
    assert "test_data_agent.mcp_generator_server" not in top_level_imports
