import ast
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import test_data_agent.agent_advising as agent_advising_module
from test_data_agent.advisor import AdvisorContractError, AdvisorRequest
from test_data_agent.agent import inspect_agent_workspace, plan_agent_request
from test_data_agent.agent_advising import AgentAdvisingService
from test_data_agent.agent_contracts import AgentRequest, AgentSourceType
from test_data_agent.io.readers import load_dataset_spec


FIXTURE_DATASET = Path("tests/fixtures/example_dataset")


class RowCountAdvisor:
    def __init__(self, row_count: int) -> None:
        self.row_count = row_count

    def propose(self, request: AdvisorRequest) -> dict[str, Any]:
        candidate = request.baseline_spec.model_copy(deep=True)
        candidate.entities[0].row_count = self.row_count
        return {
            "schema_version": "1.0",
            "profile_sha256": request.profile_sha256,
            "baseline_spec_sha256": request.baseline_spec_sha256,
            "approval_required": True,
            "generation_performed": False,
            "dataset_spec": candidate.model_dump(mode="json"),
        }


class SensitiveDowngradeAdvisor:
    def propose(self, request: AdvisorRequest) -> dict[str, Any]:
        request.baseline_spec.entity("customers").field("email").sensitive = False
        return {
            "schema_version": "1.0",
            "profile_sha256": request.profile_sha256,
            "baseline_spec_sha256": request.baseline_spec_sha256,
            "approval_required": True,
            "generation_performed": False,
            "dataset_spec": request.baseline_spec.model_dump(mode="json"),
        }


def test_advising_service_applies_metadata_only_proposal(tmp_path: Path) -> None:
    workspace = _planned_workspace(tmp_path)
    service = AgentAdvisingService(inspect_agent_workspace)

    request = service.build_request(workspace)
    status = service.advise_workspace(workspace, RowCountAdvisor(4))

    assert "alice@example.com" not in request.model_dump_json()
    assert status.phase == "awaiting_approval"
    assert status.review is not None
    assert load_dataset_spec(workspace / "dataset_spec.yaml").entities[0].row_count == 4
    assert (workspace / "advisor_review.json").is_file()
    assert not (workspace / "generated").exists()


def test_advising_service_rejects_unsafe_injected_provider_payload(
    tmp_path: Path,
) -> None:
    workspace = _planned_workspace(tmp_path)
    service = AgentAdvisingService(inspect_agent_workspace)
    spec_before = (workspace / "dataset_spec.yaml").read_bytes()

    with pytest.raises(AdvisorContractError, match="sensitive field"):
        service.advise_workspace(workspace, SensitiveDowngradeAdvisor())

    assert not (workspace / "advisor_review.json").exists()
    assert (workspace / "dataset_spec.yaml").read_bytes() == spec_before
    assert not (workspace / "generated").exists()


def test_advising_service_rejects_sensitive_field_downgrade(tmp_path: Path) -> None:
    workspace = _planned_workspace(tmp_path)
    service = AgentAdvisingService(inspect_agent_workspace)
    request = service.build_request(workspace)
    spec_before = (workspace / "dataset_spec.yaml").read_bytes()
    candidate = request.baseline_spec.model_copy(deep=True)
    candidate.entity("customers").field("email").sensitive = False
    payload = {
        "schema_version": "1.0",
        "profile_sha256": request.profile_sha256,
        "baseline_spec_sha256": request.baseline_spec_sha256,
        "approval_required": True,
        "generation_performed": False,
        "dataset_spec": candidate.model_dump(mode="json"),
    }

    with pytest.raises(AdvisorContractError, match="sensitive field"):
        service.apply_proposal(workspace, payload)

    assert not (workspace / "advisor_review.json").exists()
    assert (workspace / "dataset_spec.yaml").read_bytes() == spec_before
    assert not (workspace / "generated").exists()


def test_advising_boundary_has_no_runtime_transport_or_compatibility_imports() -> None:
    forbidden = {
        "test_data_agent.agent",
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(agent_advising_module).isdisjoint(forbidden)


def _planned_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "agent"
    plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
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
