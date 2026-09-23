"""Internal private behavior-policy structure, not execution authorization."""

from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StrictInt, StrictStr, ValidationError, model_validator

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS
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
