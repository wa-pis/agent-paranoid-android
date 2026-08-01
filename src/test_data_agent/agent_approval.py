"""Approval lifecycle service for reviewed agent workspaces."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Protocol

from test_data_agent.agent_contracts import (
    AgentApprovalReceipt,
    AgentCompletionCheckpoint,
    AgentGenerationSummary,
    AgentPhase,
    AgentRequest,
    AgentResult,
    AgentReviewState,
    AgentStep,
    AgentWorkspaceStatus,
)
from test_data_agent.agent_planning import normalize_agent_request
from test_data_agent.agent_review import inspect_agent_review_context
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import read_limited_text
from test_data_agent.io.workflows import ensure_empty_output_folder
from test_data_agent.workspace_store import (
    AGENT_RESULT_FILE,
    APPROVAL_RECEIPT_FILE,
    GENERATED_FOLDER,
    DEFAULT_AGENT_WORKSPACE_STORE,
    AgentArtifacts,
    agent_artifacts,
)


class AgentWorkspaceInspector(Protocol):
    def __call__(self, workspace: Path, /) -> AgentWorkspaceStatus: ...


class AgentDatasetGenerator(Protocol):
    def __call__(
        self,
        request: AgentRequest,
        profile: DatasetProfile,
        spec: DatasetSpec,
        *,
        review: AgentReviewState,
        output_folder: Path,
    ) -> AgentCompletionCheckpoint: ...


class AgentApprovalService:
    """Approve one reviewed plan and publish its synthetic result."""

    def __init__(
        self,
        inspect_workspace: AgentWorkspaceInspector,
        generate_dataset: AgentDatasetGenerator,
    ) -> None:
        self._inspect_workspace = inspect_workspace
        self._generate_dataset = generate_dataset

    def approve_workspace(
        self,
        workspace: Path,
        *,
        reviewed_spec_sha256: str,
    ) -> AgentResult:
        expected_spec_sha256 = normalize_sha256_digest(reviewed_spec_sha256)
        resolved_workspace = workspace.expanduser().resolve(strict=True)
        artifacts = agent_artifacts(resolved_workspace)
        ensure_agent_plan_files(artifacts)
        result_path = resolved_workspace / AGENT_RESULT_FILE
        receipt_path = resolved_workspace / APPROVAL_RECEIPT_FILE

        if result_path.exists() or result_path.is_symlink():
            status = self._inspect_workspace(resolved_workspace)
            if status.phase == AgentPhase.RECOVERY_REQUIRED:
                raise ValueError(
                    "agent workspace requires agent-recover before approval can continue"
                )
            result = AgentResult.model_validate_json(read_limited_text(result_path))
            receipt = result.approval_receipt
            if receipt is None or not hmac.compare_digest(
                receipt.reviewed_spec_sha256,
                expected_spec_sha256,
            ):
                raise ValueError(
                    "completed agent result does not match reviewed DatasetSpec fingerprint"
                )
            return result

        generated_folder = resolved_workspace / GENERATED_FOLDER
        if generated_folder.exists() or generated_folder.is_symlink():
            raise ValueError(
                "agent workspace has generated output awaiting publication; "
                "run agent-recover with the reviewed DatasetSpec fingerprint"
            )
        if receipt_path.exists() or receipt_path.is_symlink():
            raise ValueError(
                f"agent approval output already exists: {receipt_path.name}"
            )

        request, profile, spec, review = load_agent_approval_context(
            resolved_workspace,
            artifacts,
        )
        current_spec_sha256 = review.current_spec_sha256
        if not hmac.compare_digest(current_spec_sha256, expected_spec_sha256):
            raise ValueError(
                "reviewed DatasetSpec fingerprint mismatch; run agent-status and "
                "review dataset_spec.yaml again"
            )

        ensure_empty_output_folder(generated_folder)
        checkpoint = self._generate_dataset(
            request,
            profile,
            spec,
            review=review,
            output_folder=generated_folder,
        )

        completed_artifacts = agent_artifacts(
            resolved_workspace,
            generated_folder=generated_folder,
        )
        receipt, result = build_completed_agent_result(
            review,
            checkpoint,
            completed_artifacts,
        )
        publish_agent_completion(receipt, result, completed_artifacts)
        return result


def ensure_agent_plan_files(artifacts: AgentArtifacts) -> None:
    required_plan_files = (
        artifacts.request_path,
        artifacts.profile_path,
        artifacts.dataset_spec_path,
        artifacts.plan_path,
    )
    missing = [
        path.name
        for path in required_plan_files
        if not path.is_file() or path.is_symlink()
    ]
    if missing:
        raise ValueError(
            f"agent workspace is incomplete; missing: {', '.join(missing)}"
        )


def load_agent_approval_context(
    workspace: Path,
    artifacts: AgentArtifacts,
) -> tuple[AgentRequest, DatasetProfile, DatasetSpec, AgentReviewState]:
    plan = AgentResult.model_validate_json(read_limited_text(artifacts.plan_path))
    if plan.phase != AgentPhase.AWAITING_APPROVAL:
        raise ValueError("agent_plan.json must describe an awaiting-approval plan")
    if plan.review is None:
        raise ValueError(
            "agent plan predates fingerprint-bound approval; create a new plan"
        )
    request, profile, spec, review = inspect_agent_review_context(
        artifacts,
        plan.review,
    )
    request = normalize_agent_request(
        request.model_copy(update={"workspace": workspace})
    )
    return request, profile, spec, review


def build_completed_agent_result(
    review: AgentReviewState,
    checkpoint: AgentCompletionCheckpoint,
    artifacts: AgentArtifacts,
) -> tuple[AgentApprovalReceipt, AgentResult]:
    receipt = AgentApprovalReceipt(
        plan_id=review.plan_id,
        profile_sha256=review.profile_sha256,
        reviewed_spec_sha256=review.current_spec_sha256,
    )
    result = AgentResult(
        phase=AgentPhase.COMPLETED,
        approval_required=False,
        steps=[
            AgentStep(
                name="profile",
                status="completed",
                summary="Safe profile metadata loaded.",
            ),
            AgentStep(
                name="infer_spec",
                status="completed",
                summary="Reviewed DatasetSpec loaded.",
            ),
            AgentStep(
                name="approval",
                status="completed",
                summary="Approval gate passed.",
            ),
            AgentStep(
                name="generate",
                status="completed",
                summary="Synthetic dataset bundle written.",
            ),
            AgentStep(
                name="validate",
                status="completed",
                summary="Validation report written.",
            ),
        ],
        artifacts=artifacts,
        review=review,
        approval_receipt=receipt,
        summary=AgentGenerationSummary(
            source_type=checkpoint.source_type,
            row_counts=checkpoint.row_counts,
            seed=checkpoint.seed,
            output_format=checkpoint.output_format,
            validation_valid=checkpoint.validation_valid,
        ),
    )
    return receipt, result


def publish_agent_completion(
    receipt: AgentApprovalReceipt,
    result: AgentResult,
    artifacts: AgentArtifacts,
) -> None:
    DEFAULT_AGENT_WORKSPACE_STORE.publish_completion(receipt, result, artifacts)


def normalize_sha256_digest(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(
            "reviewed spec fingerprint must be a 64-character SHA-256 hex digest"
        )
    return normalized
