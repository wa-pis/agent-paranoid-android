"""Condition models and evaluators for domain-agnostic rule handling."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Condition(BaseModel):
    field: str
    equals: Any | None = None
    not_equals: Any | None = None
    in_values: list[Any] | None = None


def condition_matches(row: dict[str, Any], condition: Condition) -> bool:
    value = row.get(condition.field)
    if condition.equals is not None and value != condition.equals:
        return False
    if condition.not_equals is not None and value == condition.not_equals:
        return False
    if condition.in_values is not None and value not in condition.in_values:
        return False
    return True
