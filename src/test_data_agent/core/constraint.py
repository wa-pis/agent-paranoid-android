"""Constraint metadata with auditable inference state."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ConstraintType(StrEnum):
    FORMULA = "formula"
    TEMPORAL = "temporal"
    CONDITIONAL_REQUIRED = "conditional_required"
    AGGREGATE_MAPPING = "aggregate_mapping"


class ConstraintStatus(StrEnum):
    INFERRED = "inferred"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Constraint(BaseModel):
    type: ConstraintType
    entity: str
    fields: list[str] = Field(default_factory=list)
    expression: str | None = None
    condition: dict[str, Any] | None = None
    target_entity: str | None = None
    target_field: str | None = None
    aggregate: str | None = None
    expected: Any | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    status: ConstraintStatus = ConstraintStatus.INFERRED
