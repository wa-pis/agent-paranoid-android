"""Recovery lifecycle service for interrupted agent publication."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Protocol

from test_data_agent.agent_approval import (
    build_completed_agent_result,
    ensure_agent_plan_files,
    load_agent_approval_context,
    normalize_sha256_digest,
    publish_agent_completion,
)
from test_data_agent.agent_contracts import (
    AgentCompletionCheckpoint,
    AgentRequest,
    AgentResult,
    AgentReviewState,
)
from test_data_agent.agent_review import inspect_agent_review_state
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import enforce_output_folder_size, read_limited_text
from test_data_agent.workspace_store import (
    GENERATED_FOLDER,
    AgentArtifacts,
    agent_artifacts,
)


class AgentCompletionValidator(Protocol):
    def __call__(
        self,
        request: AgentRequest,
        profile: DatasetProfile,
        spec: DatasetSpec,
        review: AgentReviewState,
        artifacts: AgentArtifacts,
    ) -> AgentCompletionCheckpoint: ...


class AgentRecoveryService:
    """Validate and publish an interrupted synthetic generation bundle."""

    def __init__(self, validate_completion: AgentCompletionValidator) -> None:
        self._validate_completion = validate_completion

    def recover_workspace(
        self,
        workspace: Path,
        *,
        reviewed_spec_sha256: str,
    ) -> AgentResult:
        expected_spec_sha256 = normalize_sha256_digest(reviewed_spec_sha256)
        resolved_workspace = workspace.expanduser().resolve(strict=True)
        artifacts = agent_artifacts(resolved_workspace)
        ensure_agent_plan_files(artifacts)
        request, profile, spec, review = load_agent_approval_context(
            resolved_workspace,
            artifacts,
        )
        if not hmac.compare_digest(
            review.current_spec_sha256,
            expected_spec_sha256,
        ):
            raise ValueError(
                "reviewed DatasetSpec fingerprint mismatch; run agent-status and "
                "review dataset_spec.yaml again"
            )

        generated_folder = resolved_workspace / GENERATED_FOLDER
        if generated_folder.is_symlink() or not generated_folder.is_dir():
            raise ValueError(
                "agent recovery requires a regular generated output folder"
            )
        completed_artifacts = agent_artifacts(
            resolved_workspace,
            generated_folder=generated_folder,
        )
        checkpoint = self._validate_completion(
            request,
            profile,
            spec,
            review,
            completed_artifacts,
        )
        receipt, result = build_completed_agent_result(
            review,
            checkpoint,
            completed_artifacts,
        )
        publish_agent_completion(receipt, result, completed_artifacts)
        return result


def inspect_agent_recovery_state(
    artifacts: AgentArtifacts,
    plan: AgentResult,
) -> tuple[AgentReviewState, AgentCompletionCheckpoint]:
    if plan.review is None:
        raise ValueError(
            "agent plan predates fingerprint-bound approval; create a new plan"
        )
    if artifacts.generated_folder is None or artifacts.generated_folder.is_symlink():
        raise ValueError("agent generated output must be a regular folder")
    if not artifacts.generated_folder.is_dir():
        raise ValueError("agent workspace is missing generated output")
    enforce_output_folder_size(artifacts.generated_folder)
    checkpoint_path = artifacts.completion_checkpoint_path
    if (
        checkpoint_path is None
        or not checkpoint_path.is_file()
        or checkpoint_path.is_symlink()
    ):
        raise ValueError("agent recovery requires generated/agent_completion.json")
    checkpoint = AgentCompletionCheckpoint.model_validate_json(
        read_limited_text(checkpoint_path)
    )
    review = inspect_agent_review_state(artifacts, plan.review)
    if (
        checkpoint.plan_id != review.plan_id
        or not hmac.compare_digest(checkpoint.profile_sha256, review.profile_sha256)
        or not hmac.compare_digest(
            checkpoint.reviewed_spec_sha256,
            review.current_spec_sha256,
        )
    ):
        raise ValueError(
            "agent_completion.json does not match the current reviewed plan"
        )
    return review, checkpoint
