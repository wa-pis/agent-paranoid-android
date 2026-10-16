"""Condition models and evaluators for domain-agnostic rule handling."""

from __future__ import annotations

from typing import Annotated, Any, Self
import math

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

from test_data_agent.core.limits import GenerationBudget


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    field: Annotated[str, Field(min_length=1, max_length=255)]
    equals: Any | None = None
    not_equals: Any | None = None
    in_values: Annotated[list[Any], Field(min_length=1, max_length=1_000)] | None = None

    gte: float | None = Field(default=None, allow_inf_nan=False)
    lte: float | None = Field(default=None, allow_inf_nan=False)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_defaults(cls, value: Any) -> Any:
        # Older serializers always emitted both equality keys with null defaults.
        # Explicit null predicates use one key, so their meaning is unambiguous.
        if isinstance(value, dict) and {"equals", "not_equals"} <= value.keys():
            return {key: item for key, item in value.items()
                    if key not in {"equals", "not_equals"} or item is not None}
        return value

    @model_validator(mode="after")
    def require_predicate(self) -> Self:
        if not (
            self.model_fields_set.intersection({"equals", "not_equals"})
            or self.in_values is not None or self.gte is not None or self.lte is not None
        ):
            raise ValueError("condition must define equals, not_equals, in_values, gte, or lte")
        if self.gte is not None and self.lte is not None and self.gte > self.lte:
            raise ValueError("condition lower bound must not exceed upper bound")
        return self

    @model_serializer(mode="wrap")
    def serialize(self, handler: Any) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for name in ("equals", "not_equals"):
            if name not in self.model_fields_set:
                result.pop(name, None)
        for name in ("gte", "lte"):
            if getattr(self, name) is None:
                result.pop(name, None)
        return result


def condition_matches(
    row: dict[str, Any], condition: Condition, *, budget: GenerationBudget | None = None,
) -> bool:
    if budget is not None:
        budget.consume_rule_work(1 + len(condition.in_values or []))
    value = row.get(condition.field)
    if "equals" in condition.model_fields_set and value != condition.equals:
        return False
    if "not_equals" in condition.model_fields_set and value == condition.not_equals:
        return False
    if condition.in_values is not None and value not in condition.in_values:
        return False
    if condition.gte is not None or condition.lte is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if isinstance(value, float) and not math.isfinite(value):
            return False
        if condition.gte is not None and not value >= condition.gte:
            return False
        if condition.lte is not None and not value <= condition.lte:
            return False
    return True
