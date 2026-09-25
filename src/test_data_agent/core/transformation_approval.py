"""Private approval material preparation; no receipt or execution authority."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.field import FieldProfile, FieldType
from test_data_agent.core.distribution import DecimalRangeDistribution
from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS, GenerationBudget
from test_data_agent.core.transformation_csv import (
    compile_text_replacement_table, normalize_csv_mapping, parse_csv_mapping_bytes,
)
from test_data_agent.core.transformation_mapping import (
    CsvMapping, DomainMapping, InlineMapping, validate_inline_scalar_mapping,
)
from test_data_agent.core.transformation_policy import (
    ReplaceTextAction,
    SubstituteAction,
    SynthesizeAction,
    render_policy_review,
)
from test_data_agent.core.transformation_snapshot import SnapshotPart, snapshot_identity
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml, load_generation_policy_yaml


class ApprovalMaterialError(ValueError):
    """Value-free invalid review material; not a permission result."""


@dataclass(frozen=True, repr=False)
class ApprovalRequest:
    review: bytes = field(repr=False)
    parts: tuple[SnapshotPart, ...] = field(repr=False)
    snapshot_sha256: str = field(repr=False)


def _reject_identity_components(mapping: InlineMapping, data_types: tuple[FieldType, ...]) -> None:
    for entry in mapping.entries:
        for original, replacement, kind in zip(entry.original, entry.replacement, data_types, strict=True):
            if original is not None and original == replacement:
                raise ValueError
            if (kind == FieldType.DATETIME and isinstance(original, str) and isinstance(replacement, str)
                    and datetime.fromisoformat(original) == datetime.fromisoformat(replacement)):
                raise ValueError


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
            or any(not isinstance(part, SnapshotPart) or type(part.payload) is not bytes
                   for part in external_parts)
            or sum(len(part.payload) for part in external_parts) > max_total_bytes - len(policy_yaml) - len(evidence_json)
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
        if policy.file_text_mapping is not None:
            mapping_refs.add(policy.file_text_mapping.path)
        for decision in policy.fields:
            action = decision.behavior
            if isinstance(action, SynthesizeAction):
                generation_refs.add(action.generation_policy_ref)
            elif isinstance(action, SubstituteAction):
                if isinstance(action.mapping, CsvMapping):
                    mapping_refs.add(action.mapping.path)
                if isinstance(action.unmatched, SynthesizeAction):
                    generation_refs.add(action.unmatched.generation_policy_ref)
            elif isinstance(action, ReplaceTextAction):
                if action.mapping is not None:
                    mapping_refs.add(action.mapping.path)
                if isinstance(action.unmatched, SynthesizeAction):
                    generation_refs.add(action.unmatched.generation_policy_ref)
        actual_mappings = {part.name for part in external_parts if part.kind == "mapping"}
        actual_generation = {part.name for part in external_parts if part.kind == "generation_policy"}
        if mapping_refs != actual_mappings or generation_refs != actual_generation:
            raise ValueError
        fields = {(entity.name, field.name): field for entity in profile.entities for field in entity.fields}
        generation_specs = {
            part.name: load_generation_policy_yaml(part.payload, max_bytes=max_total_bytes, budget=budget)
            for part in external_parts if part.kind == "generation_policy"
        }
        for decision in policy.fields:
            action = decision.behavior
            synthesis = (action if isinstance(action, SynthesizeAction) else
                         action.unmatched if isinstance(action, (SubstituteAction, ReplaceTextAction)) else None)
            if not isinstance(synthesis, SynthesizeAction):
                continue
            budget.check("generation policy binding")
            spec = generation_specs[synthesis.generation_policy_ref]
            targets = [field for entity in spec.entities if entity.name == decision.entity
                       for field in entity.fields if field.name == decision.field]
            source_field = fields[(decision.entity, decision.field)]
            expected_type = FieldType.DECIMAL if decision.decimal_type is not None else source_field.data_type
            if len(targets) != 1 or targets[0].data_type != expected_type:
                raise ValueError
            if decision.decimal_type is not None:
                distribution = targets[0].typed_distribution
                if (not isinstance(distribution, DecimalRangeDistribution)
                        or distribution.precision != decision.decimal_type.precision
                        or distribution.scale != decision.decimal_type.scale):
                    raise ValueError
        domains = {domain.name: domain.mapping for domain in policy.domains}
        mapping_bytes = {part.name: part.payload for part in external_parts if part.kind == "mapping"}
        if policy.file_text_mapping is not None:
            compile_text_replacement_table(
                mapping_bytes[policy.file_text_mapping.path], policy.file_text_mapping, budget=budget,
            )
        domain_members: dict[str, dict[str, dict[int, tuple[FieldProfile, bool]]]] = {}
        for decision in policy.fields:
            action = decision.behavior
            if isinstance(action, ReplaceTextAction):
                if action.mapping is not None:
                    compile_text_replacement_table(
                        mapping_bytes[action.mapping.path], action.mapping, budget=budget,
                    )
                continue
            if not isinstance(action, SubstituteAction):
                continue
            field = fields[(decision.entity, decision.field)]
            if isinstance(action.mapping, DomainMapping):
                component = action.mapping.component
                members = domain_members.setdefault(action.mapping.name, {}).setdefault(decision.entity, {})
                position = component if component is not None else 0
                if position in members:
                    raise ValueError
                members[position] = (field, component is not None)
                continue
            mapping = action.mapping
            if isinstance(mapping, InlineMapping):
                typed = validate_inline_scalar_mapping(
                    mapping, data_types=(field.data_type,), nullable=(field.nullable,),
                )
            elif isinstance(mapping, CsvMapping):
                parsed = parse_csv_mapping_bytes(
                    mapping_bytes[mapping.path], mapping, budget=budget, max_bytes=max_total_bytes,
                )
                typed = normalize_csv_mapping(
                    parsed, data_types=(field.data_type,), nullable=(field.nullable,), budget=budget,
                )
            else:
                raise ValueError
            _reject_identity_components(typed, (field.data_type,))
        for name, mapping in domains.items():
            groups = domain_members.get(name)
            if not groups:
                raise ValueError
            width = len(mapping.entries[0].original) if isinstance(mapping, InlineMapping) else len(mapping.source_columns)
            expected = set(range(width))
            parsed = (mapping if isinstance(mapping, InlineMapping) else parse_csv_mapping_bytes(
                mapping_bytes[mapping.path], mapping, budget=budget, max_bytes=max_total_bytes,
            ))
            shared_types: tuple[FieldType, ...] | None = None
            for members in groups.values():
                if set(members) != expected or (width > 1 and any(not explicit for _, explicit in members.values())):
                    raise ValueError
                ordered = [members[index][0] for index in range(width)]
                data_types = tuple(field.data_type for field in ordered)
                nullable = tuple(field.nullable for field in ordered)
                if shared_types is not None and data_types != shared_types:
                    raise ValueError
                shared_types = data_types
                typed = (validate_inline_scalar_mapping(parsed, data_types=data_types, nullable=nullable)
                         if isinstance(mapping, InlineMapping) else
                         normalize_csv_mapping(parsed, data_types=data_types, nullable=nullable, budget=budget))
                _reject_identity_components(typed, data_types)
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
