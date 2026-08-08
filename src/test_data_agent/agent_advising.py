"""Metadata-only advising lifecycle service for agent workspaces."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Protocol

from test_data_agent.advisor import (
    AdvisorExchange,
    AdvisorProposalPayload,
    AdvisorRequest,
    AdvisorReviewArtifact,
    DatasetAdvisor,
    build_advisor_exchange,
    build_advisor_request,
    build_advisor_review_artifact,
    _rebuild_advisor_request_for_profile_verification,
)
from test_data_agent.agent_contracts import (
    AgentPhase,
    AgentResult,
    AgentWorkspaceStatus,
)
from test_data_agent.agent_review import inspect_agent_review_context
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import read_limited_text
from test_data_agent.io.artifacts import (
    dataset_spec_fingerprint,
    write_dataset_spec_artifact_atomic,
    write_json_artifact_atomic,
)
from test_data_agent.workspace_store import (
    ADVISOR_REVIEW_FILE,
    AgentArtifacts,
    agent_artifacts,
)


class AgentWorkspaceInspector(Protocol):
    def __call__(self, workspace: Path, /) -> AgentWorkspaceStatus: ...


class AgentAdvisingService:
    """Build and apply fingerprint-bound advice without generating rows."""

    def __init__(self, inspect_workspace: AgentWorkspaceInspector) -> None:
        self._inspect_workspace = inspect_workspace

    def advise_workspace(
        self,
        workspace: Path,
        advisor: DatasetAdvisor,
    ) -> AgentWorkspaceStatus:
        resolved_workspace, artifacts, profile, spec = self._load_pending_context(
            workspace
        )
        review_path = resolved_workspace / ADVISOR_REVIEW_FILE
        if review_path.exists() or review_path.is_symlink():
            review_artifact = _load_advisor_review(review_path)
            return self._apply_persisted_review(
                resolved_workspace,
                artifacts,
                review_artifact,
            )

        advisor_request = build_advisor_request(
            profile,
            baseline_spec=spec,
        )
        payload = advisor.propose(advisor_request.model_copy(deep=True))
        review_artifact = build_advisor_review_artifact(advisor_request, payload)
        if review_path.exists() or review_path.is_symlink():
            raise ValueError("advisor_review.json was created concurrently")
        write_json_artifact_atomic(review_artifact, review_path)
        return self._apply_persisted_review(
            resolved_workspace,
            artifacts,
            review_artifact,
        )

    def build_request(self, workspace: Path) -> AdvisorRequest:
        """Build a read-only request for an awaiting-approval workspace."""

        resolved_workspace, _artifacts, profile, spec = self._load_pending_context(
            workspace
        )
        review_path = resolved_workspace / ADVISOR_REVIEW_FILE
        if review_path.exists() or review_path.is_symlink():
            if review_path.is_symlink() or not review_path.is_file():
                raise ValueError("advisor_review.json must be a regular file")
            raise ValueError("advisor review already exists for this workspace")
        return build_advisor_request(profile, baseline_spec=spec)

    def build_exchange(self, workspace: Path) -> AdvisorExchange:
        """Build a self-describing exchange for an external advisor client."""

        return build_advisor_exchange(self.build_request(workspace))

    def apply_proposal(
        self,
        workspace: Path,
        payload: AdvisorProposalPayload,
    ) -> AgentWorkspaceStatus:
        """Validate and persist an external proposal without generating data."""

        resolved_workspace, artifacts, profile, spec = self._load_pending_context(
            workspace
        )
        review_path = resolved_workspace / ADVISOR_REVIEW_FILE
        if review_path.exists() or review_path.is_symlink():
            review_artifact = _load_advisor_review(review_path)
            submitted_artifact = build_advisor_review_artifact(
                review_artifact.request,
                payload,
            )
            if submitted_artifact != review_artifact:
                raise ValueError(
                    "advisor_review.json contains a different advisor proposal"
                )
        else:
            advisor_request = build_advisor_request(profile, baseline_spec=spec)
            review_artifact = build_advisor_review_artifact(advisor_request, payload)
            if review_path.exists() or review_path.is_symlink():
                raise ValueError("advisor_review.json was created concurrently")
            write_json_artifact_atomic(review_artifact, review_path)

        return self._apply_persisted_review(
            resolved_workspace,
            artifacts,
            review_artifact,
        )

    def _load_pending_context(
        self,
        workspace: Path,
    ) -> tuple[Path, AgentArtifacts, DatasetProfile, DatasetSpec]:
        resolved_workspace = workspace.expanduser().resolve(strict=True)
        status = self._inspect_workspace(resolved_workspace)
        if status.phase != AgentPhase.AWAITING_APPROVAL:
            raise ValueError("advisor proposals require an awaiting-approval workspace")

        artifacts = agent_artifacts(resolved_workspace)
        plan = AgentResult.model_validate_json(read_limited_text(artifacts.plan_path))
        if plan.review is None:
            raise ValueError(
                "agent plan predates fingerprint-bound advisor review; create a new plan"
            )
        _request, profile, spec, _review = inspect_agent_review_context(
            artifacts,
            plan.review,
        )
        return resolved_workspace, artifacts, profile, spec

    def _apply_persisted_review(
        self,
        resolved_workspace: Path,
        artifacts: AgentArtifacts,
        review_artifact: AdvisorReviewArtifact,
    ) -> AgentWorkspaceStatus:
        current_plan = AgentResult.model_validate_json(
            read_limited_text(artifacts.plan_path)
        )
        if current_plan.review is None:
            raise ValueError(
                "agent plan predates fingerprint-bound advisor review; create a new plan"
            )
        _request, current_profile, current_spec, _review = inspect_agent_review_context(
            artifacts,
            current_plan.review,
        )
        profile_verification_request = _rebuild_advisor_request_for_profile_verification(
            current_profile,
            review_artifact.request,
        )
        profile_sha256 = profile_verification_request.profile_sha256
        if not hmac.compare_digest(
            review_artifact.request.profile_sha256,
            profile_sha256,
        ):
            raise ValueError("advisor review profile does not match workspace profile")
        current_spec_sha256 = dataset_spec_fingerprint(current_spec)
        if hmac.compare_digest(
            current_spec_sha256,
            review_artifact.proposed_spec_sha256,
        ):
            return self._inspect_workspace(resolved_workspace)
        current_advisor_request = build_advisor_request(
            current_profile,
            baseline_spec=current_spec,
        )
        if not hmac.compare_digest(
            current_advisor_request.baseline_spec_sha256,
            review_artifact.request.baseline_spec_sha256,
        ):
            raise ValueError(
                "dataset_spec.yaml changed after advisor review; create a new plan"
            )

        write_dataset_spec_artifact_atomic(
            review_artifact.proposal.dataset_spec,
            artifacts.dataset_spec_path,
        )
        return self._inspect_workspace(resolved_workspace)


def _load_advisor_review(review_path: Path) -> AdvisorReviewArtifact:
    if review_path.is_symlink() or not review_path.is_file():
        raise ValueError("advisor_review.json must be a regular file")
    return AdvisorReviewArtifact.model_validate_json(read_limited_text(review_path))
