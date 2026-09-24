"""Private approval material preparation; no receipt or execution authority."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS, GenerationBudget
from test_data_agent.core.transformation_mapping import CsvMapping
from test_data_agent.core.transformation_policy import (
    SubstituteAction,
    SynthesizeAction,
    render_policy_review,
)
from test_data_agent.core.transformation_snapshot import SnapshotPart, snapshot_identity
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml


class ApprovalMaterialError(ValueError):
    """Value-free invalid review material; not a permission result."""


@dataclass(frozen=True, repr=False)
class ApprovalRequest:
    review: bytes = field(repr=False)
    parts: tuple[SnapshotPart, ...] = field(repr=False)
    snapshot_sha256: str = field(repr=False)


def prepare_approval_request(
    policy_yaml: bytes,
    evidence_json: bytes,
    external_parts: Sequence[SnapshotPart],
    *,
    max_total_bytes: int,
    max_review_bytes: int,
    budget: GenerationBudget,
) -> ApprovalRequest:
    """Bind displayed actions, full policy/evidence and exact referenced bytes."""
    try:
        budget.check("transformation approval material")
        if (
            type(policy_yaml) is not bytes or type(evidence_json) is not bytes
            or type(max_total_bytes) is not int or max_total_bytes < 1
            or type(max_review_bytes) is not int or max_review_bytes < 1
            or len(policy_yaml) + len(evidence_json) > max_total_bytes
            or len(external_parts) > 3 * DEFAULT_MAX_INPUT_COLUMNS
        ):
            raise ValueError
        policy = load_behavior_policy_yaml(policy_yaml, max_bytes=max_total_bytes, budget=budget)
        profile = DatasetProfile.model_validate_json(evidence_json)
        review = render_policy_review(policy, profile, max_bytes=max_review_bytes)
        mapping_refs: set[str] = set()
        generation_refs: set[str] = set()
        for domain in policy.domains:
            if isinstance(domain.mapping, CsvMapping):
                mapping_refs.add(domain.mapping.path)
        for decision in policy.fields:
            action = decision.behavior
            if isinstance(action, SynthesizeAction):
                generation_refs.add(action.generation_policy_ref)
            elif isinstance(action, SubstituteAction):
                if isinstance(action.mapping, CsvMapping):
                    mapping_refs.add(action.mapping.path)
                if isinstance(action.unmatched, SynthesizeAction):
                    generation_refs.add(action.unmatched.generation_policy_ref)
        actual_mappings = {part.name for part in external_parts if part.kind == "mapping"}
        actual_generation = {part.name for part in external_parts if part.kind == "generation_policy"}
        if mapping_refs != actual_mappings or generation_refs != actual_generation:
            raise ValueError
        parts = (
            SnapshotPart("review", "display", review),
            SnapshotPart("policy", "behavior.yaml", policy_yaml),
            SnapshotPart("evidence", "profile.json", evidence_json),
            *external_parts,
        )
        digest = snapshot_identity(parts, max_total_bytes=max_total_bytes)
        budget.check("transformation approval material")
        return ApprovalRequest(review, parts, digest)
    except (ValueError, TypeError, AttributeError):
        pass
    try:
        raise ApprovalMaterialError("invalid transformation approval material")
    except ApprovalMaterialError as error:
        error.__context__ = None
        raise
