"""Business rule models and bounded YAML loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated, Any, Literal, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_serializer, model_validator

from test_data_agent.core.limits import max_business_rules_bytes, read_limited_text
from test_data_agent.core.serialization import load_limited_yaml
from test_data_agent.rules.conditions import Condition
from test_data_agent.rules.expressions import exact_number as _rule_number


MAX_BUSINESS_RULE_COUNT = 1_000
MAX_RULE_VALUES = 1_000
MAX_RULE_FIELDS = 1_000
MAX_SCENARIO_TABLES = 100
RuleIdentifier: TypeAlias = Annotated[str, Field(min_length=1, max_length=255)]
RuleValues: TypeAlias = Annotated[list[Any], Field(min_length=1, max_length=MAX_RULE_VALUES)]


class StrictRuleModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        allow_inf_nan=False,
        str_strip_whitespace=True,
    )

    @model_serializer(mode="wrap")
    def serialize(self, handler: Any) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        # Unspecified tolerance is type-dependent; preserve that intent on reload.
        if "tolerance" in type(self).model_fields and "tolerance" not in self.model_fields_set:
            result.pop("tolerance", None)
        if isinstance(self, FormulaRule) and self.when is None:
            result.pop("when", None)
        return result


class FieldRule(StrictRuleModel):
    table: RuleIdentifier
    field: RuleIdentifier
    required: bool = False
    allowed_values: RuleValues | None = None
    min_value: float | str | None = None
    max_value: float | str | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        for value in (self.min_value, self.max_value):
            if value is not None:
                _rule_number(value)
        if (
            self.min_value is not None
            and self.max_value is not None
            and _rule_number(self.min_value) > _rule_number(self.max_value)
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
    when: Condition | None = None
    mode: Literal["assign", "check"] = "assign"
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
    expected: float | int | str | None = None
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
        validate_conditional_formula_writers(self.row_rules)
        return self


def _selection_values(condition: Condition | None) -> set[object] | None:
    if condition is None or condition.gte is not None or condition.lte is not None or "not_equals" in condition.model_fields_set:
        return None
    values = ([condition.equals] if "equals" in condition.model_fields_set
              else condition.in_values)
    if values is None:
        return None
    result: set[object] = set()
    for value in values:
        if value is None:
            result.add(None)
        elif type(value) in {str, int, float, bool}:
            try:
                result.add(_rule_number(int(value) if isinstance(value, bool) else value))
            except (ValueError, TypeError, ArithmeticError):
                if not isinstance(value, str):
                    return None
                result.add(("text", value))
        else:
            return None
    return result


def validate_conditional_formula_writers(rules: list[RowRule]) -> None:
    writes: set[tuple[str, str]] = set()
    assignments: dict[tuple[str, str], list[FormulaRule]] = {}
    for rule in rules:
        if isinstance(rule, FormulaRule) and rule.mode == "assign":
            writes.add((rule.table, rule.field))
            assignments.setdefault((rule.table, rule.field), []).append(rule)
        elif isinstance(rule, ConditionalRequiredRule):
            writes.update((rule.table, field) for field in rule.required_fields)
        elif isinstance(rule, ConditionalAllowedValuesRule):
            writes.add((rule.table, rule.field))
        elif isinstance(rule, TemporalOrderingRule):
            writes.add((rule.table, rule.end_field))
    for rule in rules:
        if isinstance(rule, FormulaRule) and rule.when is not None:
            if rule.when.field == rule.field or (rule.table, rule.when.field) in writes:
                raise ValueError("formula predicate field must not be a row-rule target")
    for group in assignments.values():
        if not any(rule.when is not None for rule in group) or len(group) < 2:
            continue
        field = group[0].when.field if group[0].when is not None else None
        seen: set[object] = set()
        for rule in group:
            values = _selection_values(rule.when)
            if rule.when is None or rule.when.field != field or values is None or seen.intersection(values):
                raise ValueError("conditional formula assignments require disjoint predicates")
            seen.update(values)


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
