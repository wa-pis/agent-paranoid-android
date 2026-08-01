import ast
from pathlib import Path
from types import ModuleType

import pytest
import test_data_agent.agent_approval as agent_approval_module
import test_data_agent.agent_recovery as agent_recovery_module
from test_data_agent.agent import (
    approve_agent_workspace,
    plan_agent_request,
    validate_agent_completion_checkpoint,
)
from test_data_agent.agent_contracts import AgentRequest, AgentSourceType
from test_data_agent.agent_recovery import AgentRecoveryService


FIXTURE_DATASET = Path("tests/fixtures/example_dataset")


def test_recovery_service_publishes_without_regenerating(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, reviewed_sha256 = _interrupt_approval(monkeypatch, tmp_path)
    generated_before = _bundle_bytes(workspace / "generated")

    result = AgentRecoveryService(
        validate_agent_completion_checkpoint
    ).recover_workspace(
        workspace,
        reviewed_spec_sha256=reviewed_sha256,
    )

    assert result.phase == "completed"
    assert _bundle_bytes(workspace / "generated") == generated_before
    assert (workspace / "approval_receipt.json").is_file()
    assert (workspace / "agent_result.json").is_file()


def test_recovery_service_rejects_tampered_rows_before_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace, reviewed_sha256 = _interrupt_approval(monkeypatch, tmp_path)
    customers_path = workspace / "generated" / "customers.csv"
    customers_path.write_text(customers_path.read_text() + "tampered,row\n")

    with pytest.raises(ValueError, match="inconsistent|validation report"):
        AgentRecoveryService(validate_agent_completion_checkpoint).recover_workspace(
            workspace,
            reviewed_spec_sha256=reviewed_sha256,
        )

    assert not (workspace / "approval_receipt.json").exists()
    assert not (workspace / "agent_result.json").exists()


def test_recovery_boundary_has_no_runtime_transport_or_compatibility_imports() -> None:
    forbidden = {
        "test_data_agent.agent",
        "test_data_agent.cli",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(agent_recovery_module).isdisjoint(forbidden)


def _interrupt_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[Path, str]:
    workspace = tmp_path / "agent"
    planned = plan_agent_request(
        AgentRequest(
            source_type=AgentSourceType.CSV_FOLDER,
            source_path=FIXTURE_DATASET,
            workspace=workspace,
            count=3,
            seed=91,
        )
    )
    assert planned.review is not None
    original_publish = agent_approval_module.publish_agent_completion

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
    monkeypatch.setattr(
        agent_approval_module,
        "publish_agent_completion",
        original_publish,
    )
    return workspace, planned.review.current_spec_sha256


def _bundle_bytes(folder: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(folder)): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
