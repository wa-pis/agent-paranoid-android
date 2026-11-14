"""Bounded, declarative options for inference from safe profile metadata."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


Selector = Annotated[str, Field(min_length=1, max_length=128)]


class IdentifierRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)

    field_suffix: Selector
    entity: Selector | None = None


class FieldInferenceRule(IdentifierRule):
    action: Literal["synthetic_identifier", "keep_builtin"]
    priority: int = Field(default=0, ge=-100, le=100)


class FieldInferenceEffect(BaseModel):
    entity_index: int = Field(ge=0)
    field_index: int = Field(ge=0)
    rule_index: int = Field(ge=0, lt=128)
    action: Literal["synthetic_identifier", "keep_builtin"]


class InferenceEvidence(BaseModel):
    options_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    field_effects: list[FieldInferenceEffect] = Field(max_length=100_000)
    min_relationship_confidence: float = Field(ge=0, le=1)
    min_constraint_confidence: float = Field(ge=0, le=1)
    relationships_filtered: int = Field(ge=0)
    constraints_filtered: int = Field(ge=0)


class InferenceOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)

    version: Literal["1"]
    identifier_rules: tuple[IdentifierRule, ...] = Field(default=(), max_length=64, strict=False)
    field_rules: tuple[FieldInferenceRule, ...] = Field(default=(), max_length=64, strict=False)
    min_relationship_confidence: float = Field(default=0.0, ge=0, le=1)
    min_constraint_confidence: float = Field(default=0.0, ge=0, le=1)

    def fingerprint(self) -> str:
        from test_data_agent.core.fingerprints import model_fingerprint


        return model_fingerprint(self)

    def effective_rules(self) -> tuple[FieldInferenceRule, ...]:
        return tuple(
            FieldInferenceRule(field_suffix=rule.field_suffix, entity=rule.entity, action="synthetic_identifier")
            for rule in self.identifier_rules
        ) + self.field_rules


def parse_inference_options(payload: object) -> InferenceOptions:
    try:
        return InferenceOptions.model_validate(payload)
    except ValidationError:
        raise ValueError("invalid inference options; expected version 1 and supported settings") from None
