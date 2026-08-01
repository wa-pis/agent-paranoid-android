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
    DatasetAdvisor,
)
from test_data_agent.agent_advising import AgentAdvisingService
from test_data_agent.agent_approval import (
    AgentApprovalService,
    build_completed_agent_result as build_completed_agent_result,
    ensure_agent_plan_files as ensure_agent_plan_files,
    load_agent_approval_context as load_agent_approval_context,
    normalize_sha256_digest as normalize_sha256_digest,
    publish_agent_completion as publish_agent_completion,
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
from test_data_agent.agent_recovery import (
    AgentRecoveryService,
    inspect_agent_recovery_state as inspect_agent_recovery_state,
)
from test_data_agent.agent_review import (
    AgentReviewService,
    inspect_agent_review_context as inspect_agent_review_context,
    inspect_agent_review_state as inspect_agent_review_state,
)
from test_data_agent.agent_status import AgentStatusService
from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.limits import enforce_output_folder_size, read_limited_text
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.artifacts import (
    GenerationManifest,
    dataset_profile_fingerprint,
    dataset_spec_fingerprint,
    write_dataset_review_artifacts,
    write_generation_manifest,
    write_json_artifact,
)
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import (
    commit_temp_output_folder,
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
    AGENT_PLAN_FILE as AGENT_PLAN_FILE,
    AGENT_REQUEST_FILE as AGENT_REQUEST_FILE,
    COMPLETION_CHECKPOINT_FILE,
    DATASET_SPEC_FILE,
    DEFAULT_AGENT_WORKSPACE_STORE,
    PROFILE_FILE,
    AgentArtifacts,
)


def detect_agent_source_type(source: Path) -> AgentSourceType:
    return _detect_agent_source_type(source)


def plan_agent_request(request: AgentRequest) -> AgentResult:
    """Compatibility wrapper for the extracted planning service."""

    return DEFAULT_AGENT_PLANNING_SERVICE.plan_request(request)


def plan_agent_profile(request: AgentRequest, profile: DatasetProfile) -> AgentResult:
    """Compatibility wrapper for metadata-only planning."""

    return DEFAULT_AGENT_PLANNING_SERVICE.plan_profile(request, profile)


DEFAULT_AGENT_STATUS_SERVICE = AgentStatusService()


def inspect_agent_workspace(workspace: Path) -> AgentWorkspaceStatus:
    """Compatibility wrapper for the extracted status service."""

    return DEFAULT_AGENT_STATUS_SERVICE.inspect_workspace(workspace)


DEFAULT_AGENT_ADVISING_SERVICE = AgentAdvisingService(inspect_agent_workspace)


def advise_agent_workspace(
    workspace: Path,
    advisor: DatasetAdvisor,
) -> AgentWorkspaceStatus:
    """Compatibility wrapper for the extracted advising service."""

    return DEFAULT_AGENT_ADVISING_SERVICE.advise_workspace(workspace, advisor)


def build_agent_advisor_request(workspace: Path) -> AdvisorRequest:
    """Compatibility wrapper for a safe advisor request."""

    return DEFAULT_AGENT_ADVISING_SERVICE.build_request(workspace)


def build_agent_advisor_exchange(workspace: Path) -> AdvisorExchange:
    """Compatibility wrapper for a self-describing advisor exchange."""

    return DEFAULT_AGENT_ADVISING_SERVICE.build_exchange(workspace)


def apply_agent_advisor_proposal(
    workspace: Path,
    payload: AdvisorProposalPayload,
) -> AgentWorkspaceStatus:
    """Compatibility wrapper for applying one advisor proposal."""

    return DEFAULT_AGENT_ADVISING_SERVICE.apply_proposal(workspace, payload)


DEFAULT_AGENT_REVIEW_SERVICE = AgentReviewService(inspect_agent_workspace)


def review_agent_workspace(workspace: Path) -> AgentReviewReport:
    """Compatibility wrapper for the extracted review service."""

    return DEFAULT_AGENT_REVIEW_SERVICE.review_workspace(workspace)


def ensure_agent_workspace_for_plan(request: AgentRequest) -> None:
    """Compatibility helper retained while planning moves behind its service."""

    DEFAULT_AGENT_WORKSPACE_STORE.ensure_new(request.workspace, create=True)


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


DEFAULT_AGENT_APPROVAL_SERVICE = AgentApprovalService(
    inspect_agent_workspace,
    generate_agent_dataset,
)


def approve_agent_workspace(
    workspace: Path,
    *,
    reviewed_spec_sha256: str,
) -> AgentResult:
    """Compatibility wrapper for the extracted approval service."""

    return DEFAULT_AGENT_APPROVAL_SERVICE.approve_workspace(
        workspace,
        reviewed_spec_sha256=reviewed_spec_sha256,
    )


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


DEFAULT_AGENT_RECOVERY_SERVICE = AgentRecoveryService(
    validate_agent_completion_checkpoint,
)


def recover_agent_workspace(
    workspace: Path,
    *,
    reviewed_spec_sha256: str,
) -> AgentResult:
    """Compatibility wrapper for the extracted recovery service."""

    return DEFAULT_AGENT_RECOVERY_SERVICE.recover_workspace(
        workspace,
        reviewed_spec_sha256=reviewed_spec_sha256,
    )


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
