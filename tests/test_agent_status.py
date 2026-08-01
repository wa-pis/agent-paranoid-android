import ast
from pathlib import Path
from types import ModuleType

import pytest
import test_data_agent.agent_approval as agent_approval_module
import test_data_agent.agent_status as agent_status_module
from test_data_agent.agent import approve_agent_workspace, plan_agent_request
from test_data_agent.agent_contracts import (
    AgentGenerationSummary,
    AgentPlanSummary,
    AgentRecoverySummary,
    AgentRequest,
    AgentSourceType,
)
from test_data_agent.agent_status import AgentStatusService


FIXTURE_DATASET = Path("tests/fixtures/example_dataset")


def test_status_service_tracks_plan_and_completion(tmp_path: Path) -> None:
    workspace = _planned_workspace(tmp_path)
    service = AgentStatusService()

    planned = service.inspect_workspace(workspace)

    assert planned.phase == "awaiting_approval"
    assert planned.next_action == "review_and_approve"
    assert isinstance(planned.summary, AgentPlanSummary)
    assert planned.review is not None

    approve_agent_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )
    completed = service.inspect_workspace(workspace)

    assert completed.phase == "completed"
    assert completed.next_action == "none"
    assert isinstance(completed.summary, AgentGenerationSummary)
    assert completed.approval_receipt is not None


def test_status_service_reports_interrupted_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = _planned_workspace(tmp_path)
    planned = AgentStatusService().inspect_workspace(workspace)
    assert planned.review is not None

    def interrupt_publication(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise RuntimeError("interrupted")

    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        interrupt_publication,
    )
    with pytest.raises(RuntimeError, match="interrupted"):
        approve_agent_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )

    status = AgentStatusService().inspect_workspace(workspace)

    assert status.phase == "recovery_required"
    assert status.next_action == "recover"
    assert isinstance(status.summary, AgentRecoverySummary)
    assert status.summary.reason == "completion_metadata_missing"


def test_status_boundary_has_no_runtime_transport_or_compatibility_imports() -> None:
    forbidden = {
        "test_data_agent.agent",
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(agent_status_module).isdisjoint(forbidden)


def _planned_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
            seed=51,
        )
    )
    return workspace


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
