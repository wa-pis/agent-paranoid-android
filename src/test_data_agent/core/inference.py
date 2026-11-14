"""Bounded, declarative options for inference from safe profile metadata."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

Selector = Annotated[str, Field(min_length=1, max_length=128)]


class IdentifierRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)

    field_suffix: Selector
    entity: Selector | None = None


class InferenceOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)

    version: Literal["1"]
    identifier_rules: tuple[IdentifierRule, ...] = Field(default=(), max_length=64, strict=False)
    min_relationship_confidence: float = Field(default=0.0, ge=0, le=1)


def parse_inference_options(payload: object) -> InferenceOptions:
    try:
        return InferenceOptions.model_validate(payload)
    except ValidationError:
        raise ValueError("invalid inference options; expected version 1 and supported settings") from None
