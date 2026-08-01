"""Read-only status lifecycle service for agent workspaces."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.agent_approval import ensure_agent_plan_files
from test_data_agent.agent_contracts import (
    AgentApprovalReceipt,
    AgentGenerationSummary,
    AgentNextAction,
    AgentPhase,
    AgentPlanSummary,
    AgentRecoverySummary,
    AgentResult,
    AgentWorkspaceStatus,
)
from test_data_agent.agent_planning import build_agent_plan_summary
from test_data_agent.agent_recovery import inspect_agent_recovery_state
from test_data_agent.agent_review import inspect_agent_review_context
from test_data_agent.core.limits import read_limited_text
from test_data_agent.workspace_store import (
    AGENT_RESULT_FILE,
    GENERATED_FOLDER,
    agent_artifacts,
)


class AgentStatusService:
    """Reconstruct lifecycle status from bounded workspace artifacts."""

    def inspect_workspace(self, workspace: Path) -> AgentWorkspaceStatus:
        resolved_workspace = workspace.expanduser().resolve(strict=True)
        if not resolved_workspace.is_dir():
            raise ValueError("agent workspace must be a folder")

        artifacts = agent_artifacts(resolved_workspace)
        ensure_agent_plan_files(artifacts)

        plan = AgentResult.model_validate_json(read_limited_text(artifacts.plan_path))
        if plan.phase != AgentPhase.AWAITING_APPROVAL:
            raise ValueError("agent_plan.json must describe an awaiting-approval plan")

        result_path = resolved_workspace / AGENT_RESULT_FILE
        generated_folder = resolved_workspace / GENERATED_FOLDER
        if result_path.is_symlink():
            raise ValueError("agent_result.json must be a regular file")
        if not result_path.exists():
            if generated_folder.exists() or generated_folder.is_symlink():
                recovery_artifacts = agent_artifacts(
                    resolved_workspace,
                    generated_folder=generated_folder,
                )
                review, checkpoint = inspect_agent_recovery_state(
                    recovery_artifacts,
                    plan,
                )
                return AgentWorkspaceStatus(
                    phase=AgentPhase.RECOVERY_REQUIRED,
                    approval_required=False,
                    next_action=AgentNextAction.RECOVER,
                    artifacts=recovery_artifacts,
                    summary=AgentRecoverySummary(
                        reason="completion_metadata_missing",
                        plan_id=checkpoint.plan_id,
                        reviewed_spec_sha256=checkpoint.reviewed_spec_sha256,
                    ),
                    review=review,
                )
            if not isinstance(plan.summary, AgentPlanSummary):
                raise ValueError("agent plan is missing its plan summary")
            if plan.review is None:
                planned_review = None
                summary = plan.summary
            else:
                request, profile, spec, planned_review = inspect_agent_review_context(
                    artifacts,
                    plan.review,
                )
                summary = build_agent_plan_summary(profile, spec, request)
            return AgentWorkspaceStatus(
                phase=AgentPhase.AWAITING_APPROVAL,
                approval_required=True,
                next_action=AgentNextAction.REVIEW_AND_APPROVE,
                artifacts=artifacts,
                summary=summary,
                review=planned_review,
            )

        if not result_path.is_file():
            raise ValueError("agent_result.json must be a file")
        result = AgentResult.model_validate_json(read_limited_text(result_path))
        if result.phase != AgentPhase.COMPLETED:
            raise ValueError("agent_result.json must describe a completed run")
        if not generated_folder.is_dir():
            raise ValueError("completed agent workspace is missing generated output")

        completed_artifacts = agent_artifacts(
            resolved_workspace,
            generated_folder=generated_folder,
        )
        completed_files = (
            completed_artifacts.validation_report_path,
            completed_artifacts.manifest_path,
        )
        if any(path is None or not path.is_file() for path in completed_files):
            raise ValueError(
                "completed agent workspace is missing validation or manifest artifacts"
            )
        if result.approval_receipt is not None:
            receipt_path = completed_artifacts.approval_receipt_path
            if receipt_path is None:
                raise RuntimeError(
                    "completed agent artifacts require an approval receipt path"
                )
            if not receipt_path.exists():
                review, checkpoint = inspect_agent_recovery_state(
                    completed_artifacts,
                    plan,
                )
                if (
                    result.approval_receipt.reviewed_spec_sha256
                    != checkpoint.reviewed_spec_sha256
                ):
                    raise ValueError(
                        "agent_result.json does not match agent_completion.json"
                    )
                return AgentWorkspaceStatus(
                    phase=AgentPhase.RECOVERY_REQUIRED,
                    approval_required=False,
                    next_action=AgentNextAction.RECOVER,
                    artifacts=completed_artifacts,
                    summary=AgentRecoverySummary(
                        reason="approval_receipt_missing",
                        plan_id=checkpoint.plan_id,
                        reviewed_spec_sha256=checkpoint.reviewed_spec_sha256,
                    ),
                    review=review,
                    approval_receipt=result.approval_receipt,
                )
            if receipt_path.is_symlink() or not receipt_path.is_file():
                raise ValueError("approval_receipt.json must be a regular file")
            persisted_receipt = AgentApprovalReceipt.model_validate_json(
                read_limited_text(receipt_path)
            )
            if persisted_receipt != result.approval_receipt:
                raise ValueError(
                    "approval_receipt.json does not match agent_result.json"
                )
        if not isinstance(result.summary, AgentGenerationSummary):
            raise ValueError("completed agent result is missing its generation summary")
        return AgentWorkspaceStatus(
            phase=AgentPhase.COMPLETED,
            approval_required=False,
            next_action=AgentNextAction.NONE,
            artifacts=completed_artifacts,
            summary=result.summary,
            review=result.review,
            approval_receipt=result.approval_receipt,
        )
