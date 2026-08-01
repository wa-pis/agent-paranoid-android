"""Stable typed contracts shared by agent lifecycle services."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from test_data_agent.core.field import FieldType
from test_data_agent.core.relationship import RelationshipType
from test_data_agent.core.settings import GenerationMode, OutputFormat


class AgentSourceType(StrEnum):
    CSV = "csv"
    CSV_FOLDER = "csv_folder"
    PROFILE = "profile"


class AgentPhase(StrEnum):
    AWAITING_APPROVAL = "awaiting_approval"
    RECOVERY_REQUIRED = "recovery_required"
    COMPLETED = "completed"


class AgentNextAction(StrEnum):
    REVIEW_AND_APPROVE = "review_and_approve"
    RECOVER = "recover"
    NONE = "none"


class AgentArtifacts(BaseModel):
    workspace: Path
    request_path: Path
    profile_path: Path
    dataset_spec_path: Path
    plan_path: Path
    generated_folder: Path | None = None
    validation_report_path: Path | None = None
    manifest_path: Path | None = None
    approval_receipt_path: Path | None = None
    completion_checkpoint_path: Path | None = None


class AgentRequest(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    source_type: AgentSourceType
    source_path: Path
    workspace: Path
    count: int = Field(default=100, ge=1)
    seed: int = Field(default=12345, ge=0)
    output_format: OutputFormat = OutputFormat.CSV
    mode: GenerationMode = GenerationMode.VALID
    invalid_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    table_name: str | None = None
    rule_sample_rows: int = Field(default=50_000, ge=1)
    use_cache: bool = False


class AgentStep(BaseModel):
    name: str
    status: Literal["completed", "pending", "skipped"]
    summary: str


class AgentFieldSummary(BaseModel):
    name: str
    data_type: FieldType
    sensitive: bool
    semantic_type: str | None = None
    is_identifier: bool = False


class AgentEntitySummary(BaseModel):
    name: str
    row_count: int
    field_count: int
    fields: list[AgentFieldSummary] = Field(default_factory=list)


class AgentFieldReference(BaseModel):
    entity: str
    field: str


class AgentRelationshipSummary(BaseModel):
    parent_entity: str
    parent_field: str
    child_entity: str
    child_field: str
    relationship_type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0)
    status: str


class AgentSummary(BaseModel):
    """Typed summary with temporary dict-style access for compatibility."""

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key) from None

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class AgentPlanSummary(AgentSummary):
    metadata_trust: Literal["untrusted"] = "untrusted"
    source_type: str
    entities: list[AgentEntitySummary]
    relationship_count: int
    constraint_count: int
    seed: int
    output_format: OutputFormat
    sensitive_fields: list[AgentFieldReference] = Field(default_factory=list)
    relationships: list[AgentRelationshipSummary] = Field(default_factory=list)
    minimum_inference_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentReviewFieldSummary(BaseModel):
    name: str
    data_type: FieldType
    nullable: bool
    null_ratio: float = Field(ge=0.0, le=1.0)
    sensitive: bool
    semantic_type: str | None = None
    is_identifier: bool
    distribution_kind: str | None = None


class AgentReviewEntitySummary(BaseModel):
    name: str
    row_count: int = Field(ge=1)
    primary_key: str | None = None
    fields: list[AgentReviewFieldSummary]


class AgentReviewSafetySummary(BaseModel):
    raw_sensitive_values_blocked: bool
    unknown_fields_treated_as_sensitive: bool
    sensitive_field_count: int = Field(ge=0)
    privacy_rule_count: int = Field(ge=0)


class AgentReviewReport(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    phase: Literal["awaiting_approval"] = "awaiting_approval"
    approval_required: Literal[True] = True
    generation_performed: Literal[False] = False
    workspace: Path
    dataset_spec_path: Path
    plan_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    planned_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    spec_changed_since_plan: bool
    source_type: str
    seed: int = Field(ge=0)
    output_format: OutputFormat
    entities: list[AgentReviewEntitySummary]
    relationships: list[AgentRelationshipSummary]
    constraint_count: int = Field(ge=0)
    safety: AgentReviewSafetySummary
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentGenerationSummary(AgentSummary):
    source_type: str
    row_counts: dict[str, int]
    seed: int
    output_format: OutputFormat
    validation_valid: bool
    synthetic: Literal[True] = True
    source_rows_copied: Literal[False] = False


class AgentReviewState(BaseModel):
    plan_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    planned_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    spec_changed_since_plan: bool


class AgentApprovalReceipt(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    approval_method: Literal["sha256_confirmation"] = "sha256_confirmation"
    plan_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class AgentCompletionCheckpoint(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    plan_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_type: str
    row_counts: dict[str, int]
    seed: int = Field(ge=0)
    output_format: OutputFormat
    validation_valid: bool
    synthetic: Literal[True] = True
    source_rows_copied: Literal[False] = False


class AgentRecoverySummary(AgentSummary):
    reason: Literal["completion_metadata_missing", "approval_receipt_missing"]
    plan_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    reviewed_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    checkpoint_present: Literal[True] = True
    generated_artifacts_present: Literal[True] = True


class AgentResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    phase: AgentPhase
    approval_required: bool
    steps: list[AgentStep]
    artifacts: AgentArtifacts
    summary: AgentPlanSummary | AgentGenerationSummary
    review: AgentReviewState | None = None
    approval_receipt: AgentApprovalReceipt | None = None

    @model_validator(mode="after")
    def validate_phase_summary(self) -> AgentResult:
        if self.phase == AgentPhase.RECOVERY_REQUIRED:
            raise ValueError(
                "recovery-required is a workspace status, not an agent result"
            )
        if self.phase == AgentPhase.AWAITING_APPROVAL and not isinstance(
            self.summary, AgentPlanSummary
        ):
            raise ValueError("awaiting-approval results require an agent plan summary")
        if self.phase == AgentPhase.COMPLETED and not isinstance(
            self.summary, AgentGenerationSummary
        ):
            raise ValueError("completed results require an agent generation summary")
        if (
            self.phase == AgentPhase.AWAITING_APPROVAL
            and self.approval_receipt is not None
        ):
            raise ValueError(
                "awaiting-approval results cannot contain an approval receipt"
            )
        if self.approval_receipt is not None:
            if self.review is None:
                raise ValueError("approval receipts require agent review state")
            if (
                self.approval_receipt.plan_id != self.review.plan_id
                or self.approval_receipt.profile_sha256 != self.review.profile_sha256
                or self.approval_receipt.reviewed_spec_sha256
                != self.review.current_spec_sha256
            ):
                raise ValueError("approval receipt does not match agent review state")
        return self


class AgentWorkspaceStatus(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    phase: AgentPhase
    approval_required: bool
    next_action: AgentNextAction
    artifacts: AgentArtifacts
    summary: AgentPlanSummary | AgentGenerationSummary | AgentRecoverySummary
    review: AgentReviewState | None = None
    approval_receipt: AgentApprovalReceipt | None = None

    @model_validator(mode="after")
    def validate_phase_summary(self) -> AgentWorkspaceStatus:
        if self.phase == AgentPhase.AWAITING_APPROVAL:
            if not isinstance(self.summary, AgentPlanSummary):
                raise ValueError(
                    "awaiting-approval status requires an agent plan summary"
                )
            if (
                not self.approval_required
                or self.next_action != AgentNextAction.REVIEW_AND_APPROVE
            ):
                raise ValueError(
                    "awaiting-approval status requires review and approval"
                )
        elif self.phase == AgentPhase.RECOVERY_REQUIRED:
            if not isinstance(self.summary, AgentRecoverySummary):
                raise ValueError(
                    "recovery-required status requires an agent recovery summary"
                )
            if self.approval_required or self.next_action != AgentNextAction.RECOVER:
                raise ValueError("recovery-required status requires recovery")
        elif not isinstance(self.summary, AgentGenerationSummary):
            raise ValueError("completed status requires an agent generation summary")
        elif self.approval_required or self.next_action != AgentNextAction.NONE:
            raise ValueError("completed status cannot require another approval")
        return self
