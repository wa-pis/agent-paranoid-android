"""Safe relationship discovery and review workflow."""

from __future__ import annotations

import hashlib
import json
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from test_data_agent.advisor import (
    DiscoveryFieldReference,
    RelationshipDiscoveryCandidate,
    RelationshipDiscoveryEvidence,
    RelationshipDiscoveryProposal,
    validate_relationship_discovery_proposals,
)
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.field import FieldProfile, FieldType


@runtime_checkable
class RelationshipDiscoveryAdvisor(Protocol):
    """Provider-neutral interface for ranking deterministic candidates."""

    def rank(
        self, candidates: list[RelationshipDiscoveryCandidate]
    ) -> list[RelationshipDiscoveryProposal]: ...


class RelationshipDiscoveryReview(BaseModel):
    """Explicit human decision that still cannot authorize generation."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    proposal: RelationshipDiscoveryProposal
    decision: Literal["accepted", "rejected"]
    reviewer: str = Field(min_length=1, max_length=256)
    generation_authorized: Literal[False] = False


def mine_relationship_candidates(
    profile: DatasetProfile,
) -> list[RelationshipDiscoveryCandidate]:
    """Mine deterministic foreign-key candidates from safe profile metadata."""

    candidates: list[RelationshipDiscoveryCandidate] = []
    for parent in profile.entities:
        for parent_field_name in parent.primary_key_candidates:
            parent_field = parent.field(parent_field_name)
            for child in profile.entities:
                if child.name == parent.name:
                    continue
                for child_field in child.fields:
                    if child_field.name != parent_field.name:
                        continue
                    if not _key_types_compatible(parent_field, child_field):
                        continue
                    evidence = [
                        RelationshipDiscoveryEvidence(
                            metric="type_compatibility", value=1.0
                        ),
                        RelationshipDiscoveryEvidence(
                            metric="parent_unique_ratio",
                            value=parent_field.unique_ratio,
                        ),
                        RelationshipDiscoveryEvidence(
                            metric="child_null_ratio", value=child_field.null_ratio
                        ),
                        RelationshipDiscoveryEvidence(
                            metric="child_distinct_ratio",
                            value=child_field.unique_ratio,
                        ),
                    ]
                    fields = [
                        DiscoveryFieldReference(
                            entity=parent.name, field=parent_field.name
                        ),
                        DiscoveryFieldReference(
                            entity=child.name, field=child_field.name
                        ),
                    ]
                    identity = {
                        "kind": "foreign_key",
                        "fields": [item.model_dump(mode="json") for item in fields],
                        "evidence": [item.model_dump(mode="json") for item in evidence],
                    }
                    candidate_id = hashlib.sha256(
                        json.dumps(
                            identity, sort_keys=True, separators=(",", ":")
                        ).encode("utf-8")
                    ).hexdigest()
                    confidence = (
                        1.0
                        + parent_field.unique_ratio
                        + (1.0 - child_field.null_ratio)
                    ) / 3.0
                    candidates.append(
                        RelationshipDiscoveryCandidate(
                            candidate_id=candidate_id,
                            kind="foreign_key",
                            fields=fields,
                            confidence=round(confidence, 6),
                            evidence=evidence,
                            assumptions=[
                                "Matching field names may represent a foreign key."
                            ],
                        )
                    )
    return sorted(candidates, key=lambda candidate: candidate.candidate_id)


def rank_relationship_candidates(
    candidates: list[RelationshipDiscoveryCandidate],
    advisor: RelationshipDiscoveryAdvisor,
) -> list[RelationshipDiscoveryProposal]:
    """Validate untrusted provider rankings against deterministic candidates."""

    source = [candidate.model_copy(deep=True) for candidate in candidates]
    proposals = advisor.rank(
        [candidate.model_copy(deep=True) for candidate in candidates]
    )
    return validate_relationship_discovery_proposals(source, proposals)


def review_relationship_proposal(
    proposal: RelationshipDiscoveryProposal,
    *,
    decision: Literal["accepted", "rejected"],
    reviewer: str,
) -> RelationshipDiscoveryReview:
    """Record an explicit human decision without applying it to a DatasetSpec."""

    return RelationshipDiscoveryReview(
        proposal=proposal.model_copy(deep=True),
        decision=decision,
        reviewer=reviewer,
    )


def _key_types_compatible(parent: FieldProfile, child: FieldProfile) -> bool:
    if parent.data_type == child.data_type:
        return True
    return {parent.data_type, child.data_type} <= {
        FieldType.INTEGER,
        FieldType.FLOAT,
    }
