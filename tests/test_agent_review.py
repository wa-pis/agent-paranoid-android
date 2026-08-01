import ast
from pathlib import Path
from types import ModuleType
from typing import Callable

import pytest
import test_data_agent.agent_review as agent_review_module
from test_data_agent.agent import inspect_agent_workspace, plan_agent_request
from test_data_agent.agent_contracts import (
    AgentRequest,
    AgentSourceType,
    AgentWorkspaceStatus,
)
from test_data_agent.agent_review import AgentReviewService
from test_data_agent.io.artifacts import write_dataset_spec_artifact
from test_data_agent.io.readers import load_dataset_spec


FIXTURE_DATASET = Path("tests/fixtures/example_dataset")


def test_review_service_returns_metadata_without_mutating_workspace(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
            seed=42,
        )
    )
    before = {
        path.name: path.read_bytes() for path in workspace.iterdir() if path.is_file()
    }

    report = AgentReviewService(inspect_agent_workspace).review_workspace(workspace)

    after = {
        path.name: path.read_bytes() for path in workspace.iterdir() if path.is_file()
    }
    assert report.phase == "awaiting_approval"
    assert report.generation_performed is False
    assert report.safety.raw_sensitive_values_blocked is True
    assert "alice@example.com" not in report.model_dump_json()
    assert before == after
    assert not (workspace / "generated").exists()


def test_review_service_rejects_spec_changed_after_status_inspection(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    status = inspect_agent_workspace(workspace)
    changed = load_dataset_spec(status.artifacts.dataset_spec_path)
    changed.entities[0].row_count = 4
    write_dataset_spec_artifact(changed, status.artifacts.dataset_spec_path)

    service = AgentReviewService(_static_inspector(status))
    with pytest.raises(ValueError, match="changed during review"):
        service.review_workspace(workspace)

    assert not (workspace / "generated").exists()


def test_review_service_rejects_spec_symlink_after_status_inspection(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    status = inspect_agent_workspace(workspace)
    spec_path = status.artifacts.dataset_spec_path
    target = tmp_path / "dataset_spec.yaml"
    spec_path.replace(target)
    spec_path.symlink_to(target)

    service = AgentReviewService(_static_inspector(status))
    with pytest.raises(ValueError, match="regular file"):
        service.review_workspace(workspace)

    assert not (workspace / "generated").exists()


def test_review_boundary_has_no_runtime_transport_or_compatibility_imports() -> None:
    forbidden = {
        "test_data_agent.agent",
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(agent_review_module).isdisjoint(forbidden)


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def _static_inspector(
    status: AgentWorkspaceStatus,
) -> Callable[[Path], AgentWorkspaceStatus]:
    def inspect(_workspace: Path) -> AgentWorkspaceStatus:
        return status

    return inspect
