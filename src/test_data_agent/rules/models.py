"""Business rule models and YAML loading for the neutral rules package."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from test_data_agent.rules.conditions import Condition


class FieldRule(BaseModel):
    table: str
    field: str
    required: bool = False
    allowed_values: list[Any] | None = None
    min_value: float | None = None
    max_value: float | None = None


class ConditionalRequiredRule(BaseModel):
    table: str
    when: Condition
    required_fields: list[str]


class ConditionalAllowedValuesRule(BaseModel):
    table: str
    field: str
    when: Condition
    allowed_values: list[Any]


class TemporalOrderingRule(BaseModel):
    table: str
    start_field: str
    end_field: str
    allow_equal: bool = True


class FormulaRule(BaseModel):
    table: str
    field: str
    expression: str
    tolerance: float = 0.000001


class ForeignKeyRule(BaseModel):
    child_table: str
    child_field: str
    parent_table: str
    parent_field: str


class AggregateFormulaRule(BaseModel):
    table: str
    field: str
    expression: str
    expected: float | int | None = None
    tolerance: float = 0.000001


class ScenarioRule(BaseModel):
    name: str
    weight: float = Field(gt=0)
    field_values: dict[str, dict[str, Any]] = Field(default_factory=dict)


class BusinessRules(BaseModel):
    field_rules: list[FieldRule] = Field(default_factory=list)
    row_rules: list[
        ConditionalRequiredRule
        | ConditionalAllowedValuesRule
        | TemporalOrderingRule
        | FormulaRule
    ] = Field(default_factory=list)
    cross_table_rules: list[ForeignKeyRule | AggregateFormulaRule] = Field(default_factory=list)
    scenarios: list[ScenarioRule] = Field(default_factory=list)


def load_business_rules(path: Path) -> BusinessRules:
    data = yaml.safe_load(path.read_text()) or {}
    return business_rules_from_dict(data)


def business_rules_from_dict(data: dict[str, Any]) -> BusinessRules:
    return BusinessRules(
        field_rules=[FieldRule.model_validate(item) for item in data.get("field_rules", [])],
        row_rules=[parse_row_rule(item) for item in data.get("row_rules", [])],
        cross_table_rules=[parse_cross_table_rule(item) for item in data.get("cross_table_rules", [])],
        scenarios=[ScenarioRule.model_validate(item) for item in data.get("scenarios", [])],
    )


def parse_row_rule(item: dict[str, Any]) -> ConditionalRequiredRule | ConditionalAllowedValuesRule | TemporalOrderingRule | FormulaRule:
    kind = item.get("type")
    if kind == "conditional_required":
        return ConditionalRequiredRule.model_validate(item)
    if kind == "conditional_allowed_values":
        return ConditionalAllowedValuesRule.model_validate(item)
    if kind == "temporal_ordering":
        return TemporalOrderingRule.model_validate(item)
    if kind == "formula":
        return FormulaRule.model_validate(item)
    raise ValueError(f"unsupported row rule type: {kind}")


def parse_cross_table_rule(item: dict[str, Any]) -> ForeignKeyRule | AggregateFormulaRule:
    kind = item.get("type")
    if kind == "foreign_key":
        return ForeignKeyRule.model_validate(item)
    if kind == "aggregate_formula":
        return AggregateFormulaRule.model_validate(item)
    raise ValueError(f"unsupported cross-table rule type: {kind}")


__all__ = [
    "AggregateFormulaRule",
    "BusinessRules",
    "ConditionalAllowedValuesRule",
    "ConditionalRequiredRule",
    "FieldRule",
    "ForeignKeyRule",
    "FormulaRule",
    "ScenarioRule",
    "TemporalOrderingRule",
    "business_rules_from_dict",
    "load_business_rules",
    "parse_cross_table_rule",
    "parse_row_rule",
]
