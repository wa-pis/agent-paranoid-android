"""Safe agent orchestration over deterministic dataset workflows."""

from __future__ import annotations

import hmac
import shutil
from pathlib import Path
from typing import Any

from test_data_agent.advisor import (
    AdvisorExchange,
    AdvisorProposalPayload,
    AdvisorRequest,
    AdvisorReviewArtifact,
    DatasetAdvisor,
    build_advisor_exchange,
    build_advisor_request,
    build_advisor_review_artifact,
)
from test_data_agent.agent_contracts import (
    AgentApprovalReceipt as AgentApprovalReceipt,
    AgentCompletionCheckpoint as AgentCompletionCheckpoint,
    AgentEntitySummary as AgentEntitySummary,
    AgentFieldReference as AgentFieldReference,
    AgentFieldSummary as AgentFieldSummary,
    AgentGenerationSummary as AgentGenerationSummary,
    AgentNextAction as AgentNextAction,
    AgentPhase as AgentPhase,
    AgentPlanSummary as AgentPlanSummary,
    AgentRecoverySummary as AgentRecoverySummary,
    AgentRelationshipSummary as AgentRelationshipSummary,
    AgentRequest as AgentRequest,
    AgentResult as AgentResult,
    AgentReviewEntitySummary as AgentReviewEntitySummary,
    AgentReviewFieldSummary as AgentReviewFieldSummary,
    AgentReviewReport as AgentReviewReport,
    AgentReviewSafetySummary as AgentReviewSafetySummary,
    AgentReviewState as AgentReviewState,
    AgentSourceType as AgentSourceType,
    AgentStep as AgentStep,
    AgentSummary as AgentSummary,
    AgentWorkspaceStatus as AgentWorkspaceStatus,
)
from test_data_agent.agent_planning import (
    DEFAULT_AGENT_PLANNING_SERVICE,
    agent_source_label as agent_source_label,
    build_agent_plan_summary as build_agent_plan_summary,
    build_agent_profile as build_agent_profile,
    build_agent_spec as build_agent_spec,
    detect_agent_source_type as _detect_agent_source_type,
    entity_summary as entity_summary,
    minimum_inference_confidence as minimum_inference_confidence,
    normalize_agent_request as normalize_agent_request,
    plan_assumptions as plan_assumptions,
    plan_warnings as plan_warnings,
    prepare_spec_for_approval as prepare_spec_for_approval,
    relationship_summary as relationship_summary,
    sensitive_field_summary as sensitive_field_summary,
    validate_spec_for_approval as validate_spec_for_approval,
)
from test_data_agent.agent_review import (
    AgentReviewService,
    inspect_agent_review_context as inspect_agent_review_context,
    inspect_agent_review_state as inspect_agent_review_state,
)
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import enforce_output_folder_size, read_limited_text
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.artifacts import (
    GenerationManifest,
    dataset_profile_fingerprint,
    dataset_spec_fingerprint,
    write_dataset_review_artifacts,
    write_dataset_spec_artifact_atomic,
    write_generation_manifest,
    write_json_artifact,
    write_json_artifact_atomic,
)
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import (
    commit_temp_output_folder,
    ensure_empty_output_folder,
    make_temp_output_folder,
    prepare_generation_budget,
)
from test_data_agent.io.writers import write_dataset_rows
from test_data_agent.safety import (
    assert_no_csv_folder_source_rows,
    assert_no_csv_source_rows,
    assert_profile_safe,
)
from test_data_agent.validation import DatasetValidationReport, validate_dataset
from test_data_agent.workspace_store import (
    ADVISOR_REVIEW_FILE,
    AGENT_PLAN_FILE as AGENT_PLAN_FILE,
    AGENT_REQUEST_FILE as AGENT_REQUEST_FILE,
    AGENT_RESULT_FILE,
    APPROVAL_RECEIPT_FILE,
    COMPLETION_CHECKPOINT_FILE,
    DATASET_SPEC_FILE,
    DEFAULT_AGENT_WORKSPACE_STORE,
    GENERATED_FOLDER,
    PROFILE_FILE,
    AgentArtifacts,
    agent_artifacts,
)


def detect_agent_source_type(source: Path) -> AgentSourceType:
    return _detect_agent_source_type(source)


def plan_agent_request(request: AgentRequest) -> AgentResult:
    """Compatibility wrapper for the extracted planning service."""

    return DEFAULT_AGENT_PLANNING_SERVICE.plan_request(request)


def plan_agent_profile(request: AgentRequest, profile: DatasetProfile) -> AgentResult:
    """Compatibility wrapper for metadata-only planning."""

    return DEFAULT_AGENT_PLANNING_SERVICE.plan_profile(request, profile)


def advise_agent_workspace(
    workspace: Path,
    advisor: DatasetAdvisor,
) -> AgentWorkspaceStatus:
    """Persist one validated advisor proposal without generating data."""

    resolved_workspace, artifacts, profile, spec = _load_pending_advisor_context(
        workspace
    )
    review_path = resolved_workspace / ADVISOR_REVIEW_FILE
    if review_path.exists() or review_path.is_symlink():
        review_artifact = _load_advisor_review(review_path)
        return _apply_persisted_advisor_review(
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
    return _apply_persisted_advisor_review(
        resolved_workspace,
        artifacts,
        review_artifact,
    )


def build_agent_advisor_request(workspace: Path) -> AdvisorRequest:
    """Build a read-only advisor request for an awaiting-approval workspace."""

    resolved_workspace, _artifacts, profile, spec = _load_pending_advisor_context(
        workspace
    )
    review_path = resolved_workspace / ADVISOR_REVIEW_FILE
    if review_path.exists() or review_path.is_symlink():
        if review_path.is_symlink() or not review_path.is_file():
            raise ValueError("advisor_review.json must be a regular file")
        raise ValueError("advisor review already exists for this workspace")
    return build_advisor_request(profile, baseline_spec=spec)


def build_agent_advisor_exchange(workspace: Path) -> AdvisorExchange:
    """Build a self-describing exchange for an external advisor client."""

    return build_advisor_exchange(build_agent_advisor_request(workspace))


def apply_agent_advisor_proposal(
    workspace: Path,
    payload: AdvisorProposalPayload,
) -> AgentWorkspaceStatus:
    """Validate and persist an external proposal without generating data."""

    resolved_workspace, artifacts, profile, spec = _load_pending_advisor_context(
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

    return _apply_persisted_advisor_review(
        resolved_workspace,
        artifacts,
        review_artifact,
    )


def _load_pending_advisor_context(
    workspace: Path,
) -> tuple[Path, AgentArtifacts, DatasetProfile, DatasetSpec]:
    resolved_workspace = workspace.expanduser().resolve(strict=True)
    status = inspect_agent_workspace(resolved_workspace)
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


def _load_advisor_review(review_path: Path) -> AdvisorReviewArtifact:
    if review_path.is_symlink() or not review_path.is_file():
        raise ValueError("advisor_review.json must be a regular file")
    return AdvisorReviewArtifact.model_validate_json(read_limited_text(review_path))


def _apply_persisted_advisor_review(
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
    current_advisor_request = build_advisor_request(
        current_profile,
        baseline_spec=current_spec,
    )
    profile_sha256 = current_advisor_request.profile_sha256
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
        return inspect_agent_workspace(resolved_workspace)
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
    return inspect_agent_workspace(resolved_workspace)


def approve_agent_workspace(
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
        status = inspect_agent_workspace(resolved_workspace)
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
        raise ValueError(f"agent approval output already exists: {receipt_path.name}")

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
    checkpoint = generate_agent_dataset(
        request,
        profile,
        spec,
        review=review,
        output_folder=generated_folder,
    )

    completed_artifacts = agent_artifacts(resolved_workspace, generated_folder=generated_folder)
    receipt, result = build_completed_agent_result(
        review,
        checkpoint,
        completed_artifacts,
    )
    publish_agent_completion(receipt, result, completed_artifacts)
    return result


def recover_agent_workspace(
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
    if not hmac.compare_digest(review.current_spec_sha256, expected_spec_sha256):
        raise ValueError(
            "reviewed DatasetSpec fingerprint mismatch; run agent-status and "
            "review dataset_spec.yaml again"
        )

    generated_folder = resolved_workspace / GENERATED_FOLDER
    if generated_folder.is_symlink() or not generated_folder.is_dir():
        raise ValueError("agent recovery requires a regular generated output folder")
    completed_artifacts = agent_artifacts(
        resolved_workspace,
        generated_folder=generated_folder,
    )
    checkpoint = validate_agent_completion_checkpoint(
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
            AgentStep(name="profile", status="completed", summary="Safe profile metadata loaded."),
            AgentStep(name="infer_spec", status="completed", summary="Reviewed DatasetSpec loaded."),
            AgentStep(name="approval", status="completed", summary="Approval gate passed."),
            AgentStep(name="generate", status="completed", summary="Synthetic dataset bundle written."),
            AgentStep(name="validate", status="completed", summary="Validation report written."),
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


def inspect_agent_workspace(workspace: Path) -> AgentWorkspaceStatus:
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
        raise ValueError("completed agent workspace is missing validation or manifest artifacts")
    if result.approval_receipt is not None:
        receipt_path = completed_artifacts.approval_receipt_path
        if receipt_path is None:
            raise RuntimeError("completed agent artifacts require an approval receipt path")
        if not receipt_path.exists():
            review, checkpoint = inspect_agent_recovery_state(
                completed_artifacts,
                plan,
            )
            if result.approval_receipt.reviewed_spec_sha256 != checkpoint.reviewed_spec_sha256:
                raise ValueError("agent_result.json does not match agent_completion.json")
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
            raise ValueError("approval_receipt.json does not match agent_result.json")
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


DEFAULT_AGENT_REVIEW_SERVICE = AgentReviewService(inspect_agent_workspace)


def review_agent_workspace(workspace: Path) -> AgentReviewReport:
    """Compatibility wrapper for the extracted review service."""

    return DEFAULT_AGENT_REVIEW_SERVICE.review_workspace(workspace)


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
        raise ValueError(f"agent workspace is incomplete; missing: {', '.join(missing)}")


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
    if checkpoint_path is None or not checkpoint_path.is_file() or checkpoint_path.is_symlink():
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
        raise ValueError("agent_completion.json does not match the current reviewed plan")
    return review, checkpoint


def ensure_agent_workspace_for_plan(request: AgentRequest) -> None:
    """Compatibility helper retained while planning moves behind its service."""

    DEFAULT_AGENT_WORKSPACE_STORE.ensure_new(request.workspace, create=True)


def normalize_sha256_digest(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError("reviewed spec fingerprint must be a 64-character SHA-256 hex digest")
    return normalized


def generate_agent_dataset(
    request: AgentRequest,
    profile: DatasetProfile,
    spec: DatasetSpec,
    *,
    review: AgentReviewState,
    output_folder: Path,
) -> AgentCompletionCheckpoint:
    budget = prepare_generation_budget(spec, output_folder)
    temp_folder = make_temp_output_folder(output_folder)
    try:
        rows_by_entity = generate_dataset(spec, seed=request.seed, budget=budget)
        budget.check("dataset generation")
        assert_agent_source_not_copied(request, spec, rows_by_entity)
        write_dataset_rows(rows_by_entity, request.output_format, temp_folder)
        budget.check("dataset export")
        report = validate_dataset(rows_by_entity, spec)
        budget.check("dataset validation")
        write_dataset_review_artifacts(profile, spec, report, temp_folder)
        row_counts = {name: len(rows) for name, rows in rows_by_entity.items()}
        write_generation_manifest(
            spec,
            seed=request.seed,
            output_format=request.output_format,
            row_counts=row_counts,
            validation_valid=report.valid,
            output_folder=temp_folder,
        )
        checkpoint = AgentCompletionCheckpoint(
            plan_id=review.plan_id,
            profile_sha256=review.profile_sha256,
            reviewed_spec_sha256=review.current_spec_sha256,
            source_type=agent_source_label(request, profile),
            row_counts=row_counts,
            seed=request.seed,
            output_format=request.output_format,
            validation_valid=report.valid,
        )
        write_json_artifact(checkpoint, temp_folder / COMPLETION_CHECKPOINT_FILE)
        enforce_output_folder_size(temp_folder)
        budget.check("artifact publication")
        commit_temp_output_folder(temp_folder, output_folder)
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise
    return checkpoint


def validate_agent_completion_checkpoint(
    request: AgentRequest,
    profile: DatasetProfile,
    spec: DatasetSpec,
    review: AgentReviewState,
    artifacts: AgentArtifacts,
) -> AgentCompletionCheckpoint:
    generated_folder = artifacts.generated_folder
    if generated_folder is None:
        raise RuntimeError("agent recovery requires generated artifacts")
    enforce_output_folder_size(generated_folder)
    checkpoint_path = artifacts.completion_checkpoint_path
    profile_path = generated_folder / PROFILE_FILE
    spec_path = generated_folder / DATASET_SPEC_FILE
    report_path = artifacts.validation_report_path
    manifest_path = artifacts.manifest_path
    required = (checkpoint_path, profile_path, spec_path, report_path, manifest_path)
    if any(
        path is None or not path.is_file() or path.is_symlink()
        for path in required
    ):
        raise ValueError("generated output is missing a regular recovery artifact")

    assert checkpoint_path is not None
    assert report_path is not None
    assert manifest_path is not None
    checkpoint = AgentCompletionCheckpoint.model_validate_json(
        read_limited_text(checkpoint_path)
    )
    expected_source_type = agent_source_label(request, profile)
    if (
        checkpoint.plan_id != review.plan_id
        or not hmac.compare_digest(checkpoint.profile_sha256, review.profile_sha256)
        or not hmac.compare_digest(
            checkpoint.reviewed_spec_sha256,
            review.current_spec_sha256,
        )
        or checkpoint.source_type != expected_source_type
        or checkpoint.seed != request.seed
        or checkpoint.output_format != request.output_format
    ):
        raise ValueError("agent_completion.json does not match the reviewed plan")

    generated_profile = DatasetProfile.model_validate_json(read_limited_text(profile_path))
    assert_profile_safe(generated_profile)
    if not hmac.compare_digest(
        dataset_profile_fingerprint(generated_profile),
        review.profile_sha256,
    ):
        raise ValueError("generated profile.json does not match the reviewed profile")
    generated_spec = load_dataset_spec(spec_path)
    if not hmac.compare_digest(
        dataset_spec_fingerprint(generated_spec),
        review.current_spec_sha256,
    ):
        raise ValueError("generated dataset_spec.yaml does not match the reviewed DatasetSpec")

    manifest = GenerationManifest.model_validate_json(read_limited_text(manifest_path))
    report = DatasetValidationReport.model_validate_json(read_limited_text(report_path))
    rows_by_entity = load_dataset_rows(generated_folder)
    row_counts = {name: len(rows) for name, rows in rows_by_entity.items()}
    if (
        manifest.spec_sha256 != review.current_spec_sha256
        or manifest.seed != request.seed
        or manifest.output_format != request.output_format
        or manifest.row_counts != row_counts
        or checkpoint.row_counts != row_counts
        or manifest.validation_valid != report.valid
        or checkpoint.validation_valid != report.valid
    ):
        raise ValueError("generated manifest, checkpoint, or validation report is inconsistent")

    assert_agent_source_not_copied(request, spec, rows_by_entity)
    recovered_report = validate_dataset(rows_by_entity, spec)
    if recovered_report != report:
        raise ValueError("generated rows do not match the persisted validation report")
    enforce_output_folder_size(generated_folder)
    return checkpoint


def assert_agent_source_not_copied(
    request: AgentRequest,
    spec: DatasetSpec,
    rows_by_entity: dict[str, list[dict[str, Any]]],
) -> None:
    if request.source_type == AgentSourceType.CSV:
        if len(spec.entities) != 1:
            raise ValueError("csv agent source expects exactly one generated entity")
        entity_name = spec.entities[0].name
        assert_no_csv_source_rows(request.source_path, rows_by_entity[entity_name])
    elif request.source_type == AgentSourceType.CSV_FOLDER:
        assert_no_csv_folder_source_rows(request.source_path, rows_by_entity)
