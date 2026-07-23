"""Business rule models and bounded YAML loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Any, Literal, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from test_data_agent.core.limits import max_business_rules_bytes, read_limited_text
from test_data_agent.core.serialization import load_limited_yaml
from test_data_agent.rules.conditions import Condition


MAX_BUSINESS_RULE_COUNT = 1_000
MAX_RULE_VALUES = 1_000
MAX_RULE_FIELDS = 1_000
MAX_SCENARIO_TABLES = 100
RuleIdentifier: TypeAlias = Annotated[str, Field(min_length=1, max_length=255)]
RuleValues: TypeAlias = Annotated[list[Any], Field(min_length=1, max_length=MAX_RULE_VALUES)]


class StrictRuleModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        str_strip_whitespace=True,
    )


class FieldRule(StrictRuleModel):
    table: RuleIdentifier
    field: RuleIdentifier
    required: bool = False
    allowed_values: RuleValues | None = None
    min_value: float | None = None
    max_value: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError("field rule min_value must be <= max_value")
        return self


class ConditionalRequiredRule(StrictRuleModel):
    type: Literal["conditional_required"]
    table: RuleIdentifier
    when: Condition
    required_fields: Annotated[
        list[RuleIdentifier],
        Field(min_length=1, max_length=MAX_RULE_FIELDS),
    ]


class ConditionalAllowedValuesRule(StrictRuleModel):
    type: Literal["conditional_allowed_values"]
    table: RuleIdentifier
    field: RuleIdentifier
    when: Condition
    allowed_values: RuleValues


class TemporalOrderingRule(StrictRuleModel):
    type: Literal["temporal_ordering"]
    table: RuleIdentifier
    start_field: RuleIdentifier
    end_field: RuleIdentifier
    allow_equal: bool = True


class FormulaRule(StrictRuleModel):
    type: Literal["formula"]
    table: RuleIdentifier
    field: RuleIdentifier
    expression: Annotated[str, Field(min_length=1, max_length=1_024)]
    tolerance: float = Field(default=0.000001, ge=0)


class ForeignKeyRule(StrictRuleModel):
    type: Literal["foreign_key"]
    child_table: RuleIdentifier
    child_field: RuleIdentifier
    parent_table: RuleIdentifier
    parent_field: RuleIdentifier


class AggregateFormulaRule(StrictRuleModel):
    type: Literal["aggregate_formula"]
    table: RuleIdentifier
    field: RuleIdentifier
    expression: Annotated[str, Field(min_length=1, max_length=1_024)]
    expected: float | int | None = None
    tolerance: float = Field(default=0.000001, ge=0)


class ScenarioRule(StrictRuleModel):
    name: RuleIdentifier
    weight: float = Field(gt=0)
    field_values: dict[RuleIdentifier, dict[RuleIdentifier, Any]] = Field(
        default_factory=dict,
        max_length=MAX_SCENARIO_TABLES,
    )


RowRule: TypeAlias = Annotated[
    ConditionalRequiredRule
    | ConditionalAllowedValuesRule
    | TemporalOrderingRule
    | FormulaRule,
    Field(discriminator="type"),
]
CrossTableRule: TypeAlias = Annotated[
    ForeignKeyRule | AggregateFormulaRule,
    Field(discriminator="type"),
]


class BusinessRules(StrictRuleModel):
    field_rules: list[FieldRule] = Field(
        default_factory=list,
        max_length=MAX_BUSINESS_RULE_COUNT,
    )
    row_rules: list[RowRule] = Field(
        default_factory=list,
        max_length=MAX_BUSINESS_RULE_COUNT,
    )
    cross_table_rules: list[CrossTableRule] = Field(
        default_factory=list,
        max_length=MAX_BUSINESS_RULE_COUNT,
    )
    scenarios: list[ScenarioRule] = Field(
        default_factory=list,
        max_length=MAX_BUSINESS_RULE_COUNT,
    )

    @property
    def rule_count(self) -> int:
        return (
            len(self.field_rules)
            + len(self.row_rules)
            + len(self.cross_table_rules)
            + len(self.scenarios)
        )

    @model_validator(mode="after")
    def validate_total_rule_count(self) -> Self:
        if self.rule_count > MAX_BUSINESS_RULE_COUNT:
            raise ValueError(
                f"business rules must contain <= {MAX_BUSINESS_RULE_COUNT} rules"
            )
        return self


_ROW_RULE_ADAPTER: TypeAdapter[RowRule] = TypeAdapter(RowRule)
_CROSS_TABLE_RULE_ADAPTER: TypeAdapter[CrossTableRule] = TypeAdapter(CrossTableRule)


def load_business_rules(path: Path) -> BusinessRules:
    data = load_limited_yaml(
        read_limited_text(path, max_bytes=max_business_rules_bytes())
    ) or {}
    return business_rules_from_dict(data)


def business_rules_from_dict(data: dict[str, Any]) -> BusinessRules:
    return BusinessRules.model_validate(data)


def business_rules_fingerprint(rules: BusinessRules) -> str:
    canonical = json.dumps(
        rules.model_dump(mode="json", exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def parse_row_rule(item: dict[str, Any]) -> RowRule:
    return _ROW_RULE_ADAPTER.validate_python(item)


def parse_cross_table_rule(item: dict[str, Any]) -> CrossTableRule:
    return _CROSS_TABLE_RULE_ADAPTER.validate_python(item)


__all__ = [
    "AggregateFormulaRule",
    "BusinessRules",
    "ConditionalAllowedValuesRule",
    "ConditionalRequiredRule",
    "CrossTableRule",
    "FieldRule",
    "ForeignKeyRule",
    "FormulaRule",
    "RowRule",
    "ScenarioRule",
    "TemporalOrderingRule",
    "business_rules_fingerprint",
    "business_rules_from_dict",
    "load_business_rules",
    "parse_cross_table_rule",
    "parse_row_rule",
]
