"""Typed filesystem persistence for review-first agent workspaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Protocol, Self

from pydantic import BaseModel

from test_data_agent.agent_contracts import AgentArtifacts as AgentArtifacts
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import read_limited_text
from test_data_agent.io.artifacts import (
    write_dataset_profile_artifact,
    write_dataset_spec_artifact,
    write_json_artifact,
    write_json_artifact_atomic,
)
from test_data_agent.io.path_policy import (
    PathIdentity,
    ensure_directory,
    make_staging_directory,
    path_identity,
    publish_directory,
    remove_tree_if_identity,
)

if TYPE_CHECKING:
    from test_data_agent.agent_contracts import AgentApprovalReceipt, AgentRequest, AgentResult


AGENT_REQUEST_FILE = "agent_request.json"
AGENT_PLAN_FILE = "agent_plan.json"
AGENT_RESULT_FILE = "agent_result.json"
ADVISOR_REVIEW_FILE = "advisor_review.json"
APPROVAL_RECEIPT_FILE = "approval_receipt.json"
COMPLETION_CHECKPOINT_FILE = "agent_completion.json"
PROFILE_FILE = "profile.json"
DATASET_SPEC_FILE = "dataset_spec.yaml"
GENERATED_FOLDER = "generated"


class WorkspacePlanTransition(Protocol):
    """Staging area whose commit atomically publishes a planned workspace."""

    workspace: Path
    staging_workspace: Path

    @property
    def committed(self) -> bool: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


class AgentWorkspaceStore(Protocol):
    """Persistence port used by agent lifecycle services."""

    def ensure_new(self, workspace: Path, *, create: bool = False) -> None: ...

    def begin_plan(self, workspace: Path) -> WorkspacePlanTransition: ...

    def persist_plan(
        self,
        transition: WorkspacePlanTransition,
        *,
        request: AgentRequest,
        profile: DatasetProfile,
        spec: DatasetSpec,
        plan: AgentResult,
    ) -> None: ...

    def publish_completion(
        self,
        receipt: AgentApprovalReceipt,
        result: AgentResult,
        artifacts: AgentArtifacts,
    ) -> None: ...


@dataclass(slots=True)
class _FilesystemWorkspacePlanTransition:
    workspace: Path
    staging_workspace: Path
    staging_identity: PathIdentity
    _committed: bool = False

    @property
    def committed(self) -> bool:
        return self._committed

    def commit(self) -> None:
        if self._committed:
            raise RuntimeError("workspace plan transition is already committed")
        _validate_new_workspace(self.workspace)
        publish_directory(self.staging_workspace, self.workspace)
        self._committed = True

    def rollback(self) -> None:
        if not self._committed:
            remove_tree_if_identity(self.staging_workspace, self.staging_identity)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollback()


class FilesystemAgentWorkspaceStore:
    """Filesystem adapter with atomic plan and completion state markers."""

    def ensure_new(self, workspace: Path, *, create: bool = False) -> None:
        _validate_new_workspace(workspace)
        if create:
            ensure_directory(workspace)

    def begin_plan(self, workspace: Path) -> WorkspacePlanTransition:
        self.ensure_new(workspace)
        staging_workspace = make_staging_directory(workspace)
        return _FilesystemWorkspacePlanTransition(
            workspace,
            staging_workspace,
            path_identity(staging_workspace),
        )

    def persist_plan(
        self,
        transition: WorkspacePlanTransition,
        *,
        request: AgentRequest,
        profile: DatasetProfile,
        spec: DatasetSpec,
        plan: AgentResult,
    ) -> None:
        staged = agent_artifacts(transition.staging_workspace)
        write_json_artifact(request, staged.request_path)
        write_dataset_profile_artifact(profile, staged.profile_path)
        write_dataset_spec_artifact(spec, staged.dataset_spec_path)
        write_json_artifact(plan, staged.plan_path)
        transition.commit()

    def publish_completion(
        self,
        receipt: AgentApprovalReceipt,
        result: AgentResult,
        artifacts: AgentArtifacts,
    ) -> None:
        receipt_path = artifacts.approval_receipt_path
        if receipt_path is None:
            raise RuntimeError(
                "completed agent artifacts require an approval receipt path"
            )
        result_path = artifacts.workspace / AGENT_RESULT_FILE
        receipt_missing = _validate_matching_json(receipt, receipt_path)
        result_missing = _validate_matching_json(result, result_path)
        if receipt_missing:
            write_json_artifact_atomic(receipt, receipt_path)
        if result_missing:
            write_json_artifact_atomic(result, result_path)


def _validate_new_workspace(workspace: Path) -> None:
    if workspace.is_symlink():
        raise ValueError("agent workspace must not be a symbolic link")
    if workspace.exists() and not workspace.is_dir():
        raise ValueError("agent workspace must be a folder")
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("agent workspace must be empty for planning")


def _validate_matching_json(payload: BaseModel, path: Path) -> bool:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                f"agent completion output must be a regular file: {path.name}"
            )
        existing = type(payload).model_validate_json(read_limited_text(path))
        if existing != payload:
            raise ValueError(
                f"existing {path.name} does not match recovered completion"
            )
        return False
    return True


def agent_artifacts(
    workspace: Path,
    *,
    generated_folder: Path | None = None,
) -> AgentArtifacts:
    return AgentArtifacts(
        workspace=workspace,
        request_path=workspace / AGENT_REQUEST_FILE,
        profile_path=workspace / PROFILE_FILE,
        dataset_spec_path=workspace / DATASET_SPEC_FILE,
        plan_path=workspace / AGENT_PLAN_FILE,
        generated_folder=generated_folder,
        validation_report_path=(
            generated_folder / "validation_report.json" if generated_folder else None
        ),
        manifest_path=(
            generated_folder / "generation_manifest.json" if generated_folder else None
        ),
        approval_receipt_path=(
            workspace / APPROVAL_RECEIPT_FILE if generated_folder else None
        ),
        completion_checkpoint_path=(
            generated_folder / COMPLETION_CHECKPOINT_FILE if generated_folder else None
        ),
    )


DEFAULT_AGENT_WORKSPACE_STORE: AgentWorkspaceStore = FilesystemAgentWorkspaceStore()
