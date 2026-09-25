"""Internal private behavior-policy structure, not execution authorization."""

import hashlib
import json
from graphlib import CycleError, TopologicalSorter
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StrictInt, StrictStr, ValidationError, model_validator

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.field import FieldProfile
from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS
from test_data_agent.core.privacy import is_sensitive_field, normalize_field_name
from test_data_agent.core.transformation_mapping import (
    CsvMapping, DomainMapping, InlineMapping, MappingSource, _PrivateModel,
)


Reference: TypeAlias = Annotated[StrictStr, Field(min_length=1, max_length=256)]


class PreserveAction(_PrivateModel):
    action: Literal["preserve"]
    authorization_ref: Reference = Field(repr=False)


class SynthesizeAction(_PrivateModel):
    action: Literal["synthesize"]
    generation_policy_ref: Reference = Field(repr=False)


class RejectUnmatched(_PrivateModel):
    action: Literal["reject"] = "reject"


UnmatchedPolicy: TypeAlias = Annotated[
    RejectUnmatched | PreserveAction | SynthesizeAction, Field(discriminator="action")
]


class SubstituteAction(_PrivateModel):
    action: Literal["substitute"]
    mapping: MappingSource = Field(repr=False)
    unmatched: UnmatchedPolicy = Field(default_factory=RejectUnmatched, repr=False)


class DeriveAction(_PrivateModel):
    action: Literal["derive"]
    expression: StrictStr = Field(min_length=1, repr=False)
    dependencies: tuple[Reference, ...] = Field(min_length=1, repr=False)


class DropAction(_PrivateModel):
    action: Literal["drop"]


FieldAction: TypeAlias = Annotated[
    PreserveAction | SynthesizeAction | SubstituteAction | DeriveAction | DropAction,
    Field(discriminator="action"),
]


class FieldDecision(_PrivateModel):
    entity: Reference = Field(repr=False)
    field: Reference = Field(repr=False)
    sensitivity: Literal["non_sensitive", "sensitive", "unknown"]
    behavior: FieldAction = Field(repr=False)

    @model_validator(mode="after")
    def require_preservation_declaration(self) -> "FieldDecision":
        preserve = isinstance(self.behavior, PreserveAction) or (
            isinstance(self.behavior, SubstituteAction)
            and isinstance(self.behavior.unmatched, PreserveAction)
        )
        if preserve and self.sensitivity != "non_sensitive":
            raise ValueError("preservation requires non-sensitive declaration")
        return self


class MappingDomain(_PrivateModel):
    name: Reference = Field(repr=False)
    mapping: Annotated[InlineMapping | CsvMapping, Field(discriminator="kind")] = Field(repr=False)


class BehaviorPolicy(_PrivateModel):
    schema_version: Literal["0.1"]
    schema_fingerprint: StrictStr = Field(pattern=r"^[0-9a-f]{64}$", repr=False)
    seed: StrictInt = Field(repr=False)
    fields: tuple[FieldDecision, ...] = Field(min_length=1, max_length=DEFAULT_MAX_INPUT_COLUMNS, repr=False)
    domains: tuple[MappingDomain, ...] = Field(default=(), max_length=DEFAULT_MAX_INPUT_COLUMNS, repr=False)

    @model_validator(mode="after")
    def require_unique_resolved_decisions(self) -> "BehaviorPolicy":
        identities = [(item.entity, item.field) for item in self.fields]
        names = [domain.name for domain in self.domains]
        if len(identities) != len(set(identities)) or len(names) != len(set(names)):
            raise ValueError("duplicate policy declaration")
        for item in self.fields:
            if isinstance(item.behavior, SubstituteAction):
                mapping = item.behavior.mapping
                if isinstance(mapping, DomainMapping) and mapping.name not in names:
                    raise ValueError("unresolved mapping domain")
        return self


class BehaviorPolicyError(ValueError):
    """Bounded structural error; no private policy values attached."""


def parse_behavior_policy(payload: object) -> BehaviorPolicy:
    """Parse a private draft; references are declarations, never approvals."""
    try:
        return BehaviorPolicy.model_validate(payload)
    except ValidationError:
        pass
    try:
        raise BehaviorPolicyError("invalid behavior policy")
    except BehaviorPolicyError as error:
        error.__context__ = None
        raise


def validate_policy_field_coverage(policy: BehaviorPolicy, profile: DatasetProfile) -> None:
    """Check coverage, local dependencies and preservation conflicts, not approval."""
    policy = parse_behavior_policy(policy)
    # Reparse mutable profile models, including nested instances, without retaining
    # source-derived Pydantic errors at this private boundary.
    valid = False
    try:
        profile = DatasetProfile.model_validate(profile.model_dump(warnings=False))
        source_fields = {(entity.name, field.name): field for entity in profile.entities for field in entity.fields}
        expected = set(source_fields)
        actual = {(decision.entity, decision.field) for decision in policy.fields}
        valid = expected == actual
        decisions = {(item.entity, item.field): item for item in policy.fields}
        graph: dict[tuple[str, str], set[tuple[str, str]]] = {}
        for identity, decision in decisions.items():
            graph[identity] = set()
            behavior = decision.behavior
            preserves = isinstance(behavior, PreserveAction) or (
                isinstance(behavior, SubstituteAction) and isinstance(behavior.unmatched, PreserveAction)
            )
            if preserves and identity in source_fields:
                field = source_fields[identity]
                if field.sensitive or is_sensitive_field(field.name, field.semantic_type):
                    valid = False
            if isinstance(behavior, DeriveAction):
                dependencies = {(decision.entity, name) for name in behavior.dependencies}
                if len(dependencies) != len(behavior.dependencies):
                    valid = False
                for dependency in dependencies:
                    if dependency not in decisions or isinstance(decisions[dependency].behavior, DropAction):
                        valid = False
                graph[identity] = dependencies
        tuple(TopologicalSorter(graph).static_order())
    except (ValidationError, CycleError):
        valid = False
    if not valid:
        try:
            raise BehaviorPolicyError("invalid policy field coverage")
        except BehaviorPolicyError as error:
            error.__context__ = None
            raise


def transformation_schema_fingerprint(profile: DatasetProfile) -> str:
    """Private ordered column-schema identity; never source-content identity."""
    valid = False
    try:
        profile = DatasetProfile.model_validate(profile.model_dump(warnings=False))
        valid = True
    except ValidationError:
        pass
    if not valid:
        try:
            raise BehaviorPolicyError("invalid source schema")
        except BehaviorPolicyError as error:
            error.__context__ = None
            raise
    schema = [{"entity": entity.name, "fields": [
        {"name": field.name, "type": field.data_type.value, "nullable": field.nullable}
        for field in entity.fields]} for entity in profile.entities]
    canonical = json.dumps({"version": "0.1", "entities": schema},
                           sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_policy_profile(policy: BehaviorPolicy, profile: DatasetProfile) -> None:
    """Validate column-schema binding; not mapping types, formulas or approval."""
    policy = parse_behavior_policy(policy)
    validate_policy_field_coverage(policy, profile)
    if policy.schema_fingerprint != transformation_schema_fingerprint(profile):
        try:
            raise BehaviorPolicyError("source schema mismatch")
        except BehaviorPolicyError as error:
            error.__context__ = None
            raise


def _system_field_comment(field: FieldProfile) -> str:
    """Fixed, value-free hint from metadata; never a preservation decision."""
    name = normalize_field_name(field.name)
    semantic = (field.semantic_type or "").lower()
    for markers, meaning in (
        (("token", "password", "secret", "credential", "card", "ssn"), "credential or private identifier"),
        (("email", "mail"), "email or contact"),
        (("phone",), "phone or contact"),
        (("address",), "address"),
        (("name",), "personal name"),
    ):
        if any(marker in name or marker == semantic for marker in markers):
            return f"Possible {meaning} field from metadata; treat as potentially sensitive."
    if field.sensitive:
        return "Profile flags possible sensitive data; field meaning unverified."
    if field.is_identifier:
        return "Likely identifier from profile metadata; sensitivity unverified."
    return f"Likely {field.data_type.value} field; meaning and sensitivity unverified."


def render_policy_review(policy: BehaviorPolicy, profile: DatasetProfile, *, max_bytes: int) -> bytes:
    """Value-free local review; bind these bytes with full policy/evidence bytes."""
    policy = parse_behavior_policy(policy)
    profile = profile.model_copy(deep=True)
    validate_policy_profile(policy, profile)
    if type(max_bytes) is not int or max_bytes < 1:
        raise BehaviorPolicyError("invalid policy review") from None
    observed = {(entity.name, field.name): field
                for entity in profile.entities for field in entity.fields}
    fields = []
    for decision in policy.fields:
        behavior = decision.behavior
        unmatched = behavior.unmatched.action if isinstance(behavior, SubstituteAction) else None
        field = observed[(decision.entity, decision.field)]
        fields.append({
            "entity": decision.entity,
            "field": decision.field,
            "action": behavior.action,
            "unmatched": unmatched,
            "preserves_original": behavior.action == "preserve" or unmatched == "preserve",
            "declared_sensitivity": decision.sensitivity,
            "observed_sensitivity": (
                "sensitive" if field.sensitive or is_sensitive_field(field.name, field.semantic_type)
                else "unknown"
            ),
            "system_comment": _system_field_comment(field),
        })
    payload = json.dumps({"version": 1, "fields": fields}, ensure_ascii=True, indent=2).encode("ascii")
    if len(payload) > max_bytes:
        raise BehaviorPolicyError("invalid policy review") from None
    return payload
