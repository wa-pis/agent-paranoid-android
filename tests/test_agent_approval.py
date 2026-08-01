import ast
import json
from pathlib import Path
from types import ModuleType

import pytest
import test_data_agent.agent_approval as agent_approval_module
from test_data_agent.agent import (
    generate_agent_dataset,
    inspect_agent_workspace,
    plan_agent_request,
)
from test_data_agent.agent_approval import AgentApprovalService
from test_data_agent.agent_contracts import (
    AgentCompletionCheckpoint,
    AgentRequest,
    AgentReviewState,
    AgentSourceType,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.io.artifacts import write_dataset_spec_artifact
from test_data_agent.io.readers import load_dataset_spec


FIXTURE_DATASET = Path("tests/fixtures/example_dataset")


def test_approval_service_generates_and_publishes_synthetic_bundle(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
            seed=42,
        )
    )
    assert planned.review is not None

    result = AgentApprovalService(
        inspect_agent_workspace,
        generate_agent_dataset,
    ).approve_workspace(
        workspace,
        reviewed_spec_sha256=planned.review.current_spec_sha256,
    )

    manifest = json.loads(
        (workspace / "generated" / "generation_manifest.json").read_text()
    )
    assert result.phase == "completed"
    assert result.approval_receipt is not None
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert (workspace / "approval_receipt.json").is_file()
    assert (workspace / "agent_result.json").is_file()


def test_approval_service_rejects_changed_spec_before_generation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    spec_path = workspace / "dataset_spec.yaml"
    spec = load_dataset_spec(spec_path)
    spec.entities[0].row_count = 4
    write_dataset_spec_artifact(spec, spec_path)

    service = AgentApprovalService(inspect_agent_workspace, _forbidden_generation)
    with pytest.raises(ValueError, match="reviewed DatasetSpec fingerprint mismatch"):
        service.approve_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )

    assert not (workspace / "generated").exists()
    assert not (workspace / "approval_receipt.json").exists()


def test_approval_service_rejects_receipt_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
        )
    )
    assert planned.review is not None
    target = tmp_path / "outside.json"
    target.write_text("unchanged")
    (workspace / "approval_receipt.json").symlink_to(target)

    service = AgentApprovalService(inspect_agent_workspace, _forbidden_generation)
    with pytest.raises(ValueError, match="approval output already exists"):
        service.approve_workspace(
            workspace,
            reviewed_spec_sha256=planned.review.current_spec_sha256,
        )

    assert target.read_text() == "unchanged"
    assert not (workspace / "generated").exists()


def test_approval_boundary_has_no_runtime_transport_or_compatibility_imports() -> None:
    forbidden = {
        "test_data_agent.agent",
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(agent_approval_module).isdisjoint(forbidden)


def _forbidden_generation(
    request: AgentRequest,
    profile: DatasetProfile,
    spec: DatasetSpec,
    *,
    review: AgentReviewState,
    output_folder: Path,
) -> AgentCompletionCheckpoint:
    del request, profile, spec, review, output_folder
    raise AssertionError("generation must not run before the approval gate passes")


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
