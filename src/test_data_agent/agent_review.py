"""Metadata-only review lifecycle service for planned agent workspaces."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Protocol

from test_data_agent.agent_contracts import (
    AgentArtifacts,
    AgentPhase,
    AgentPlanSummary,
    AgentRequest,
    AgentReviewEntitySummary,
    AgentReviewFieldSummary,
    AgentReviewReport,
    AgentReviewSafetySummary,
    AgentReviewState,
    AgentWorkspaceStatus,
)
from test_data_agent.agent_planning import validate_spec_for_approval
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import read_limited_text
from test_data_agent.io.artifacts import (
    dataset_profile_fingerprint,
    dataset_spec_fingerprint,
)
from test_data_agent.io.readers import load_dataset_spec
from test_data_agent.safety import assert_profile_safe


class AgentWorkspaceInspector(Protocol):
    def __call__(self, workspace: Path, /) -> AgentWorkspaceStatus: ...


class AgentReviewService:
    """Render safe plan metadata without generating or mutating artifacts."""

    def __init__(self, inspect_workspace: AgentWorkspaceInspector) -> None:
        self._inspect_workspace = inspect_workspace

    def review_workspace(self, workspace: Path) -> AgentReviewReport:
        status = self._inspect_workspace(workspace)
        if status.phase != AgentPhase.AWAITING_APPROVAL:
            raise ValueError(
                "agent-review requires an awaiting-approval workspace; "
                "run agent-status for the current phase"
            )
        if not isinstance(status.summary, AgentPlanSummary) or status.review is None:
            raise ValueError(
                "agent plan predates fingerprint-bound review; create a new plan"
            )

        spec_path = status.artifacts.dataset_spec_path
        if spec_path.is_symlink() or not spec_path.is_file():
            raise ValueError("dataset_spec.yaml must be a regular file")
        spec = load_dataset_spec(spec_path)
        current_spec_sha256 = dataset_spec_fingerprint(spec)
        if not hmac.compare_digest(
            current_spec_sha256,
            status.review.current_spec_sha256,
        ):
            raise ValueError(
                "dataset_spec.yaml changed during review; run agent-review again"
            )

        entities = [
            AgentReviewEntitySummary(
                name=entity.name,
                row_count=entity.row_count,
                primary_key=entity.primary_key,
                fields=[
                    AgentReviewFieldSummary(
                        name=field.name,
                        data_type=field.data_type,
                        nullable=field.nullable,
                        null_ratio=field.null_ratio,
                        sensitive=field.sensitive,
                        semantic_type=field.semantic_type,
                        is_identifier=field.is_identifier,
                        distribution_kind=(
                            field.typed_distribution.kind
                            if field.typed_distribution is not None
                            else None
                        ),
                    )
                    for field in entity.fields
                ],
            )
            for entity in spec.entities
        ]
        sensitive_field_count = sum(
            field.sensitive for entity in spec.entities for field in entity.fields
        )
        return AgentReviewReport(
            workspace=status.artifacts.workspace,
            dataset_spec_path=spec_path,
            plan_id=status.review.plan_id,
            profile_sha256=status.review.profile_sha256,
            planned_spec_sha256=status.review.planned_spec_sha256,
            current_spec_sha256=current_spec_sha256,
            spec_changed_since_plan=status.review.spec_changed_since_plan,
            source_type=status.summary.source_type,
            seed=status.summary.seed,
            output_format=status.summary.output_format,
            entities=entities,
            relationships=status.summary.relationships,
            constraint_count=len(spec.constraints),
            safety=AgentReviewSafetySummary(
                raw_sensitive_values_blocked=(
                    not spec.privacy_settings.allow_raw_sensitive_values
                ),
                unknown_fields_treated_as_sensitive=(
                    spec.privacy_settings.treat_unknown_as_sensitive
                ),
                sensitive_field_count=sensitive_field_count,
                privacy_rule_count=len(spec.privacy_rules),
            ),
            assumptions=status.summary.assumptions,
            warnings=status.summary.warnings,
        )


def inspect_agent_review_state(
    artifacts: AgentArtifacts,
    planned_review: AgentReviewState,
) -> AgentReviewState:
    return inspect_agent_review_context(artifacts, planned_review)[3]


def inspect_agent_review_context(
    artifacts: AgentArtifacts,
    planned_review: AgentReviewState,
) -> tuple[AgentRequest, DatasetProfile, DatasetSpec, AgentReviewState]:
    request = AgentRequest.model_validate_json(
        read_limited_text(artifacts.request_path)
    )
    profile = DatasetProfile.model_validate_json(
        read_limited_text(artifacts.profile_path)
    )
    assert_profile_safe(profile)
    profile_sha256 = dataset_profile_fingerprint(profile)
    if not hmac.compare_digest(profile_sha256, planned_review.profile_sha256):
        raise ValueError("profile.json fingerprint does not match agent_plan.json")
    spec = load_dataset_spec(artifacts.dataset_spec_path)
    validate_spec_for_approval(spec, request)
    current_spec_sha256 = dataset_spec_fingerprint(spec)
    review = planned_review.model_copy(
        update={
            "profile_sha256": profile_sha256,
            "current_spec_sha256": current_spec_sha256,
            "spec_changed_since_plan": (
                current_spec_sha256 != planned_review.planned_spec_sha256
            ),
        }
    )
    return request, profile, spec, review
