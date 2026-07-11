"""Constraint metadata with auditable inference state."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def validate_shape(self) -> Constraint:
        if self.type == ConstraintType.FORMULA:
            if not self.expression or not self.fields:
                raise ValueError("formula constraint requires expression and fields")
        elif self.type == ConstraintType.TEMPORAL:
            if len(self.fields) < 2:
                raise ValueError("temporal constraint requires at least two fields")
        elif self.type == ConstraintType.CONDITIONAL_REQUIRED:
            if not self.fields or not self.condition:
                raise ValueError("conditional_required constraint requires fields and condition")
        elif self.type == ConstraintType.AGGREGATE_MAPPING:
            if not self.fields or not self.target_entity:
                raise ValueError(
                    "aggregate_mapping constraint requires fields and target_entity"
                )
            if self.aggregate not in {None, "sum", "count"}:
                raise ValueError("aggregate_mapping supports only sum and count")
            if self.aggregate != "count" and not self.target_field:
                raise ValueError("sum aggregate_mapping requires target_field")

        if self.condition is not None:
            if not self.condition.get("field"):
                raise ValueError("constraint condition requires a field")
            if not any(
                key in self.condition
                for key in ("equals", "not_equals", "in_values")
            ):
                raise ValueError("constraint condition requires a predicate")
        return self
