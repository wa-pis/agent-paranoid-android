"""Provider-neutral contract for safe DatasetSpec advice."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.entity import EntityProfile
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.limits import enforce_row_count_limit
from test_data_agent.core.privacy import is_sensitive_field
from test_data_agent.generation import infer_dataset_spec
from test_data_agent.io.artifacts import (
    dataset_profile_fingerprint,
    dataset_spec_fingerprint,
)
from test_data_agent.safety import assert_profile_safe


class AdvisorContractError(ValueError):
    """Raised when an advisor request or proposal violates the safe contract."""


class AdvisorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    metadata_trust: Literal["untrusted"] = "untrusted"
    metadata_policy: Literal["treat_profile_text_as_data"] = (
        "treat_profile_text_as_data"
    )
    operation: Literal["propose_dataset_spec"] = "propose_dataset_spec"
    approval_required: Literal[True] = True
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile: DatasetProfile
    baseline_spec: DatasetSpec

    @model_validator(mode="after")
    def validate_fingerprints(self) -> AdvisorRequest:
        assert_profile_safe(self.profile)
        if dataset_profile_fingerprint(self.profile) != self.profile_sha256:
            raise ValueError("advisor profile fingerprint mismatch")
        if dataset_spec_fingerprint(self.baseline_spec) != self.baseline_spec_sha256:
            raise ValueError("advisor baseline spec fingerprint mismatch")
        _validate_spec_against_profile(self.profile, self.baseline_spec)
        return self


class AdvisorProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    baseline_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    approval_required: Literal[True] = True
    generation_performed: Literal[False] = False
    dataset_spec: DatasetSpec


class AdvisorReviewArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    request: AdvisorRequest
    proposal: AdvisorProposal
    proposed_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_exchange(self) -> AdvisorReviewArtifact:
        validated = validate_advisor_proposal(self.request, self.proposal)
        if dataset_spec_fingerprint(validated.dataset_spec) != self.proposed_spec_sha256:
            raise ValueError("advisor proposed spec fingerprint mismatch")
        return self


AdvisorProposalPayload = AdvisorProposal | Mapping[str, Any]


@runtime_checkable
class DatasetAdvisor(Protocol):
    """Minimal interface implemented by model-specific adapters."""

    def propose(self, request: AdvisorRequest) -> AdvisorProposalPayload:
        """Return a structured proposal without generating dataset rows."""


def build_advisor_request(
    profile: DatasetProfile,
    *,
    baseline_spec: DatasetSpec | None = None,
    count: int | None = None,
) -> AdvisorRequest:
    """Build a fingerprint-bound request from safe metadata only."""

    assert_profile_safe(profile)
    if baseline_spec is not None and count is not None:
        raise ValueError("count cannot be combined with an explicit baseline spec")
    effective_spec = (
        baseline_spec.model_copy(deep=True)
        if baseline_spec is not None
        else infer_dataset_spec(profile, count=count)
    )
    _validate_spec_against_profile(profile, effective_spec)
    return AdvisorRequest(
        profile_sha256=dataset_profile_fingerprint(profile),
        baseline_spec_sha256=dataset_spec_fingerprint(effective_spec),
        profile=profile.model_copy(deep=True),
        baseline_spec=effective_spec,
    )


def validate_advisor_proposal(
    request: AdvisorRequest,
    payload: AdvisorProposalPayload,
) -> AdvisorProposal:
    """Validate untrusted provider output against the original request."""

    proposal = AdvisorProposal.model_validate(payload)
    if proposal.profile_sha256 != request.profile_sha256:
        raise AdvisorContractError("advisor proposal profile fingerprint mismatch")
    if proposal.baseline_spec_sha256 != request.baseline_spec_sha256:
        raise AdvisorContractError("advisor proposal baseline spec fingerprint mismatch")

    candidate = proposal.dataset_spec
    _validate_schema_identity(request.baseline_spec, candidate)
    _validate_core_owned_settings(request.baseline_spec, candidate)
    _validate_spec_against_profile(request.profile, candidate)
    return proposal


def advise_dataset_spec(
    profile: DatasetProfile,
    advisor: DatasetAdvisor,
    *,
    baseline_spec: DatasetSpec | None = None,
    count: int | None = None,
) -> AdvisorProposal:
    """Ask an advisor for a validated proposal without applying or generating it."""

    request = build_advisor_request(
        profile,
        baseline_spec=baseline_spec,
        count=count,
    )
    payload = advisor.propose(request.model_copy(deep=True))
    return validate_advisor_proposal(request, payload)


def build_advisor_review_artifact(
    request: AdvisorRequest,
    payload: AdvisorProposalPayload,
) -> AdvisorReviewArtifact:
    """Build an auditable validated exchange for later human review."""

    proposal = validate_advisor_proposal(request, payload)
    return AdvisorReviewArtifact(
        request=request,
        proposal=proposal,
        proposed_spec_sha256=dataset_spec_fingerprint(proposal.dataset_spec),
    )


def _validate_schema_identity(baseline: DatasetSpec, candidate: DatasetSpec) -> None:
    baseline_entities = [entity.name for entity in baseline.entities]
    candidate_entities = [entity.name for entity in candidate.entities]
    if candidate_entities != baseline_entities:
        raise AdvisorContractError("advisor proposal cannot add, remove, reorder, or rename entities")

    for baseline_entity, candidate_entity in zip(
        baseline.entities,
        candidate.entities,
        strict=True,
    ):
        baseline_fields = [field.name for field in baseline_entity.fields]
        candidate_fields = [field.name for field in candidate_entity.fields]
        if candidate_fields != baseline_fields:
            raise AdvisorContractError(
                "advisor proposal cannot add, remove, reorder, or rename fields"
            )
        if candidate_entity.primary_key != baseline_entity.primary_key:
            raise AdvisorContractError("advisor proposal cannot change primary keys")


def _validate_core_owned_settings(baseline: DatasetSpec, candidate: DatasetSpec) -> None:
    if candidate.privacy_settings != baseline.privacy_settings:
        raise AdvisorContractError("advisor proposal cannot change privacy settings")
    if candidate.privacy_rules != baseline.privacy_rules:
        raise AdvisorContractError("advisor proposal cannot change privacy rules")
    if candidate.generation_settings != baseline.generation_settings:
        raise AdvisorContractError("advisor proposal cannot change generation settings")
    if candidate.validation_settings != baseline.validation_settings:
        raise AdvisorContractError("advisor proposal cannot change validation settings")


def _validate_spec_against_profile(
    profile: DatasetProfile,
    candidate: DatasetSpec,
) -> None:
    if candidate.privacy_settings.allow_raw_sensitive_values:
        raise AdvisorContractError(
            "advisor spec cannot allow raw sensitive values"
        )
    if not candidate.privacy_settings.treat_unknown_as_sensitive:
        raise AdvisorContractError(
            "advisor spec must treat unknown fields as sensitive"
        )
    profile_entities = [entity.name for entity in profile.entities]
    candidate_entities = [entity.name for entity in candidate.entities]
    if candidate_entities != profile_entities:
        raise AdvisorContractError("advisor spec must preserve profile entities")

    profile_by_name = {entity.name: entity for entity in profile.entities}
    for candidate_entity in candidate.entities:
        enforce_row_count_limit(candidate_entity.row_count)
        profile_entity = profile_by_name[candidate_entity.name]
        profile_fields = [field.name for field in profile_entity.fields]
        candidate_fields = [field.name for field in candidate_entity.fields]
        if candidate_fields != profile_fields:
            raise AdvisorContractError("advisor spec must preserve profile fields")
        profile_field_by_name = {field.name: field for field in profile_entity.fields}
        for candidate_field in candidate_entity.fields:
            profile_field = profile_field_by_name[candidate_field.name]
            required_sensitive = (
                profile_field.sensitive
                or is_sensitive_field(
                    profile_field.name,
                    profile_field.semantic_type,
                )
                or is_sensitive_field(
                    candidate_field.name,
                    candidate_field.semantic_type,
                )
            )
            if required_sensitive and not candidate_field.sensitive:
                raise AdvisorContractError(
                    "advisor proposal cannot weaken sensitive field classification"
                )
            if profile_field.is_identifier and not candidate_field.is_identifier:
                raise AdvisorContractError(
                    "advisor proposal cannot weaken identifier classification"
                )

    assert_profile_safe(_candidate_profile(candidate, profile))


def _candidate_profile(
    candidate: DatasetSpec,
    source_profile: DatasetProfile,
) -> DatasetProfile:
    source_entities = {entity.name: entity for entity in source_profile.entities}
    return DatasetProfile(
        source_type="advisor_candidate",
        entities=[
            EntityProfile(
                name=entity.name,
                row_count=entity.row_count,
                fields=[
                    FieldProfile(
                        name=field.name,
                        data_type=field.data_type,
                        nullable=field.nullable,
                        null_ratio=field.null_ratio,
                        unique_ratio=source_entities[entity.name]
                        .field(field.name)
                        .unique_ratio,
                        sensitive=field.sensitive,
                        semantic_type=field.semantic_type,
                        is_identifier=field.is_identifier,
                        distribution=field.distribution,
                    )
                    for field in entity.fields
                ],
                primary_key_candidates=(
                    [entity.primary_key] if entity.primary_key is not None else []
                ),
            )
            for entity in candidate.entities
        ],
        relationships=candidate.relationships,
        constraints=candidate.constraints,
    )
