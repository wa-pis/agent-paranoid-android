"""Condition models and evaluators for domain-agnostic rule handling."""

from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    field: Annotated[str, Field(min_length=1, max_length=255)]
    equals: Any | None = None
    not_equals: Any | None = None
    in_values: Annotated[list[Any], Field(min_length=1, max_length=1_000)] | None = None

    @model_validator(mode="after")
    def require_predicate(self) -> Self:
        if (
            self.equals is None
            and self.not_equals is None
            and self.in_values is None
        ):
            raise ValueError("condition must define equals, not_equals, or in_values")
        return self


def condition_matches(row: dict[str, Any], condition: Condition) -> bool:
    value = row.get(condition.field)
    if condition.equals is not None and value != condition.equals:
        return False
    if condition.not_equals is not None and value == condition.not_equals:
        return False
    if condition.in_values is not None and value not in condition.in_values:
        return False
    return True
