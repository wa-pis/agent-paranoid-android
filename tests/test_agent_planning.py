import ast
from pathlib import Path
from types import ModuleType

import pytest
import test_data_agent.agent as agent_module
import test_data_agent.agent_contracts as agent_contracts_module
import test_data_agent.agent_planning as agent_planning_module
import test_data_agent.workspace_store as workspace_store_module
from test_data_agent.agent_contracts import (
    AgentArtifacts,
    AgentPhase,
    AgentRequest,
    AgentSourceType,
)
from test_data_agent.agent_planning import AgentPlanningService
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.safety import ProfileSafetyError
from test_data_agent.workspace_store import FilesystemAgentWorkspaceStore


FIXTURE_CUSTOMERS = Path("tests/fixtures/customers.csv")


def test_planning_service_persists_review_only_plan(tmp_path: Path) -> None:
    workspace = tmp_path / "agent"
    service = AgentPlanningService(FilesystemAgentWorkspaceStore())

    result = service.plan_request(
        AgentRequest(
            source_type=AgentSourceType.CSV,
            source_path=FIXTURE_CUSTOMERS,
            workspace=workspace,
            count=3,
            seed=17,
        )
    )

    assert result.phase == AgentPhase.AWAITING_APPROVAL
    assert result.approval_required is True
    assert result.artifacts.workspace == workspace.resolve()
    assert (workspace / "agent_plan.json").is_file()
    assert (workspace / "dataset_spec.yaml").is_file()
    assert not (workspace / "generated").exists()


def test_planning_service_rejects_workspace_inside_csv_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "customers.csv").write_text("customer_id\n1\n")
    workspace = source / "agent"
    service = AgentPlanningService(FilesystemAgentWorkspaceStore())

    with pytest.raises(ValueError, match="must not be inside"):
        service.plan_request(
            AgentRequest(
                source_type=AgentSourceType.CSV_FOLDER,
                source_path=source,
                workspace=workspace,
            )
        )

    assert not workspace.exists()


def test_planning_service_rejects_unsafe_profile_without_artifacts(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    profile = DatasetProfile.model_validate(
        {
            "source_type": "manual",
            "entities": [
                {
                    "name": "customers",
                    "row_count": 1,
                    "fields": [
                        {
                            "name": "customer_email",
                            "data_type": "string",
                            "sensitive": True,
                            "distribution": {
                                "kind": "categorical",
                                "categories": [
                                    {"value": "private@example.com", "count": 1}
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    )
    service = AgentPlanningService(FilesystemAgentWorkspaceStore())

    with pytest.raises(ProfileSafetyError, match="unsafe distribution"):
        service.plan_profile(
            AgentRequest(
                source_type=AgentSourceType.PROFILE,
                source_path=tmp_path / "unused.json",
                workspace=workspace,
            ),
            profile,
        )

    assert not workspace.exists()
    assert not list(tmp_path.glob(".agent.plan.*"))


def test_agent_compatibility_modules_reexport_contract_models() -> None:
    assert agent_module.AgentRequest is AgentRequest
    assert agent_module.AgentArtifacts is AgentArtifacts
    assert workspace_store_module.AgentArtifacts is AgentArtifacts


def test_planning_boundary_has_no_runtime_transport_or_compatibility_imports() -> None:
    forbidden = {
        "test_data_agent.agent",
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(agent_planning_module).isdisjoint(forbidden)
    assert _top_level_imports(agent_contracts_module).isdisjoint(
        forbidden | {"test_data_agent.workspace_store"}
    )


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
