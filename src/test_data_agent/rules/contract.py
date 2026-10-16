"""Validate business rules against a DatasetSpec before generation."""

from __future__ import annotations

import math
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import GenerationMode
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.limits import enforce_business_rule_evaluations
from test_data_agent.core.privacy import is_sensitive_field, looks_sensitive_value
from test_data_agent.rules.conditions import Condition
from test_data_agent.rules.expressions import (
    aggregate_expression_constants,
    expression_complexity,
    expression_constants,
    expression_references,
)
from test_data_agent.rules.models import (
    AggregateFormulaRule,
    BusinessRules,
    ConditionalAllowedValuesRule,
    ConditionalRequiredRule,
    ForeignKeyRule,
    FormulaRule,
    TemporalOrderingRule,
)


class BusinessRuleContractError(ValueError):
    """Raised when a rule cannot safely apply to the selected DatasetSpec."""


def validate_business_rules_for_spec(
    rules: BusinessRules,
    spec: DatasetSpec,
) -> None:
    if rules.rule_count == 0:
        raise BusinessRuleContractError("business rules must not be empty")

    entities = {entity.name: entity for entity in spec.entities}
    enforce_business_rule_evaluations(
        estimate_business_rule_evaluations(rules, spec)
    )

    for field_rule in rules.field_rules:
        field = _require_field(entities, field_rule.table, field_rule.field)
        _validate_literals(
            [value for value in (field_rule.min_value, field_rule.max_value) if value is not None],
            field,
            f"{field_rule.table}.{field_rule.field} bounds",
            decimal_shape=False,
        )
        if field_rule.allowed_values is not None:
            _validate_literals(
                field_rule.allowed_values,
                field,
                f"{field_rule.table}.{field_rule.field} allowed_values",
            )
        if (
            (field_rule.min_value is not None or field_rule.max_value is not None)
            and field.data_type not in {FieldType.INTEGER, FieldType.FLOAT, FieldType.DECIMAL}
        ):
            raise BusinessRuleContractError(
                "numeric bounds require a numeric field: "
                f"{field_rule.table}.{field_rule.field}"
            )

    for row_rule in rules.row_rules:
        entity = _require_entity(entities, row_rule.table)
        if isinstance(row_rule, ConditionalRequiredRule):
            condition_field = _require_field(
                entities,
                row_rule.table,
                row_rule.when.field,
            )
            _validate_condition_literals(
                row_rule.when,
                condition_field,
                row_rule.table,
            )
            for field_name in row_rule.required_fields:
                _require_field(entities, row_rule.table, field_name)
        elif isinstance(row_rule, ConditionalAllowedValuesRule):
            condition_field = _require_field(
                entities,
                row_rule.table,
                row_rule.when.field,
            )
            _validate_condition_literals(
                row_rule.when,
                condition_field,
                row_rule.table,
            )
            field = _require_field(entities, row_rule.table, row_rule.field)
            _validate_literals(
                row_rule.allowed_values,
                field,
                f"{row_rule.table}.{row_rule.field} allowed_values",
            )
        elif isinstance(row_rule, TemporalOrderingRule):
            _require_field(entities, row_rule.table, row_rule.start_field)
            _require_field(entities, row_rule.table, row_rule.end_field)
        elif isinstance(row_rule, FormulaRule):
            target_field = _require_field(
                entities,
                row_rule.table,
                row_rule.field,
            )
            if target_field.data_type not in {FieldType.INTEGER, FieldType.FLOAT, FieldType.DECIMAL}:
                raise BusinessRuleContractError(
                    "row formula requires a numeric target field: "
                    f"{row_rule.table}.{row_rule.field}"
                )
            names, aggregate_fields, functions = expression_references(
                row_rule.expression
            )
            if aggregate_fields or functions:
                raise BusinessRuleContractError(
                    "row formula cannot use aggregate functions: "
                    f"{row_rule.table}.{row_rule.field}"
                )
            for field_name in names:
                if field_name not in {field.name for field in entity.fields}:
                    raise BusinessRuleContractError(
                        "formula references unknown field: "
                        f"{row_rule.table}.{field_name}"
                    )
            constants = expression_constants(row_rule.expression)
            for value in constants:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise BusinessRuleContractError(
                        "row formula constants must be numeric: "
                        f"{row_rule.table}.{row_rule.field}"
                    )
            _validate_literals(
                constants, target_field,
                f"{row_rule.table}.{row_rule.field} formula",
                decimal_shape=False,
            )

    for cross_table_rule in rules.cross_table_rules:
        if isinstance(cross_table_rule, ForeignKeyRule):
            _require_field(
                entities,
                cross_table_rule.child_table,
                cross_table_rule.child_field,
            )
            _require_field(
                entities,
                cross_table_rule.parent_table,
                cross_table_rule.parent_field,
            )
        elif isinstance(cross_table_rule, AggregateFormulaRule):
            entity = _require_entity(entities, cross_table_rule.table)
            field_names = {field.name for field in entity.fields}
            if (
                cross_table_rule.field != "*"
                and cross_table_rule.field not in field_names
            ):
                raise BusinessRuleContractError(
                    "aggregate rule references unknown field: "
                    f"{cross_table_rule.table}.{cross_table_rule.field}"
                )
            constants = aggregate_expression_constants(cross_table_rule.expression)
            if cross_table_rule.expected is not None:
                constants.append(cross_table_rule.expected)
            if cross_table_rule.field != "*":
                _validate_literals(constants, entity.field(cross_table_rule.field), "aggregate formula", decimal_shape=False)
            else:
                _validate_unbound_literals(constants, "*", "aggregate formula")
            names, aggregate_fields, _ = expression_references(
                cross_table_rule.expression
            )
            if names:
                raise BusinessRuleContractError(
                    f"aggregate formula cannot use row fields: {sorted(names)}"
                )
            for field_name in aggregate_fields:
                if field_name != "*" and field_name not in field_names:
                    raise BusinessRuleContractError(
                        "aggregate formula references unknown field: "
                        f"{cross_table_rule.table}.{field_name}"
                    )

    scenario_names: set[str] = set()
    for scenario in rules.scenarios:
        if scenario.name in scenario_names:
            raise BusinessRuleContractError(
                f"duplicate business-rule scenario: {scenario.name!r}"
            )
        scenario_names.add(scenario.name)
        for table, field_values in scenario.field_values.items():
            _require_entity(entities, table)
            for field_name, value in field_values.items():
                field = _require_field(entities, table, field_name)
                _validate_literals([value], field, f"{table}.{field_name} scenario value")


def validate_business_rule_literals(rules: BusinessRules) -> None:
    for field_rule in rules.field_rules:
        _validate_unbound_literals(
            [value for value in (field_rule.min_value, field_rule.max_value) if value is not None],
            field_rule.field,
            f"{field_rule.table}.{field_rule.field} bounds",
        )
        _validate_unbound_literals(
            field_rule.allowed_values or [],
            field_rule.field,
            f"{field_rule.table}.{field_rule.field} allowed_values",
        )
    for row_rule in rules.row_rules:
        if isinstance(
            row_rule,
            (ConditionalRequiredRule, ConditionalAllowedValuesRule),
        ):
            condition_values = [
                row_rule.when.equals, row_rule.when.not_equals,
                row_rule.when.gte, row_rule.when.lte,
            ]
            condition_values.extend(row_rule.when.in_values or [])
            _validate_unbound_literals(
                [value for value in condition_values if value is not None],
                row_rule.when.field,
                f"{row_rule.table}.{row_rule.when.field} condition",
            )
        if isinstance(row_rule, ConditionalAllowedValuesRule):
            _validate_unbound_literals(
                row_rule.allowed_values,
                row_rule.field,
                f"{row_rule.table}.{row_rule.field} allowed_values",
            )
        elif isinstance(row_rule, FormulaRule):
            _validate_unbound_literals(
                expression_constants(row_rule.expression),
                row_rule.field,
                f"{row_rule.table}.{row_rule.field} formula",
            )
    for scenario in rules.scenarios:
        for table, field_values in scenario.field_values.items():
            for field_name, value in field_values.items():
                _validate_unbound_literals(
                    [value],
                    field_name,
                    f"{table}.{field_name} scenario value",
                )
    for rule in rules.cross_table_rules:
        if isinstance(rule, AggregateFormulaRule):
            constants = aggregate_expression_constants(rule.expression)
            if rule.expected is not None:
                constants.append(rule.expected)
            _validate_unbound_literals(constants, rule.field, "aggregate formula")


def estimate_business_rule_evaluations(
    rules: BusinessRules,
    spec: DatasetSpec,
) -> int:
    return estimate_business_rule_evaluations_for_rows(
        rules, {entity.name: entity.row_count for entity in spec.entities},
        mode=spec.generation_settings.mode,
    )


def estimate_business_rule_evaluations_for_rows(
    rules: BusinessRules, row_counts: dict[str, int], *, mode: str = GenerationMode.VALID,
) -> int:
    negative = GenerationMode(mode) in {GenerationMode.MIXED, GenerationMode.NEGATIVE}
    estimated = rules.rule_count
    estimated += sum(
        row_counts.get(field_rule.table, 0)
        * max(1, len(field_rule.allowed_values or []))
        for field_rule in rules.field_rules
    )
    for row_rule in rules.row_rules:
        row_count = row_counts.get(row_rule.table, 0)
        if isinstance(row_rule, ConditionalRequiredRule):
            condition_cost = len(row_rule.when.in_values or []) or 1
            estimated += row_count * (
                condition_cost + len(row_rule.required_fields)
            )
        elif isinstance(row_rule, ConditionalAllowedValuesRule):
            condition_cost = len(row_rule.when.in_values or []) or 1
            estimated += row_count * (
                condition_cost + len(row_rule.allowed_values)
            )
        elif isinstance(row_rule, FormulaRule):
            estimated += row_count * expression_complexity(row_rule.expression)
        else:
            estimated += row_count
    if negative:
        # Baseline and before/after row audits account for collateral failures.
        # Rule dispatch visits every local rule for each selected row.
        estimated += 3 * estimated + 2 * rules.rule_count * sum(row_counts.values())
    for cross_table_rule in rules.cross_table_rules:
        if isinstance(cross_table_rule, ForeignKeyRule):
            parents = row_counts.get(cross_table_rule.parent_table, 0)
            children = row_counts.get(cross_table_rule.child_table, 0)
            estimated += (3 if negative else 1) * (parents + children)
            if negative:
                estimated += 4 * parents * children
        elif isinstance(cross_table_rule, AggregateFormulaRule):
            rows = row_counts.get(cross_table_rule.table, 0)
            complexity = expression_complexity(cross_table_rule.expression)
            estimated += (3 if negative else 1) * rows * (1 + complexity)
            if negative and cross_table_rule.field != "*":
                estimated += rows * rows * (1 + complexity)
    if rules.scenarios:
        estimated += sum(row_counts.values()) * len(rules.scenarios)
        for table, row_count in row_counts.items():
            max_assignments = max(
                len(scenario.field_values.get(table, {}))
                for scenario in rules.scenarios
            )
            estimated += row_count * max_assignments
    return estimated


def _validate_unbound_literals(
    values: list[Any],
    field_name: str,
    label: str,
) -> None:
    if is_sensitive_field(field_name) and values:
        raise BusinessRuleContractError(
            f"business rules cannot assign or compare sensitive field values: {label}"
        )
    for value in values:
        if not isinstance(value, (str, int, float, bool)) and value is not None:
            raise BusinessRuleContractError(
                f"business rule values must be JSON scalars: {label}"
            )
        if isinstance(value, float) and not math.isfinite(value):
            raise BusinessRuleContractError(
                f"business rule values must be finite: {label}"
            )
        if looks_sensitive_value(value):
            raise BusinessRuleContractError(
                f"business rules contain a raw-looking sensitive value: {label}"
            )


def _require_entity(
    entities: dict[str, EntitySpec],
    table: str,
) -> EntitySpec:
    try:
        return entities[table]
    except KeyError as exc:
        raise BusinessRuleContractError(
            f"business rule references unknown entity: {table!r}"
        ) from exc


def _require_field(
    entities: dict[str, EntitySpec],
    table: str,
    field_name: str,
) -> FieldSpec:
    entity = _require_entity(entities, table)
    try:
        return entity.field(field_name)
    except KeyError as exc:
        raise BusinessRuleContractError(
            f"business rule references unknown field: {table}.{field_name}"
        ) from exc


def _validate_condition_literals(
    condition: Condition,
    field: FieldSpec,
    table: str,
) -> None:
    if (condition.gte is not None or condition.lte is not None) and field.data_type not in {FieldType.INTEGER, FieldType.FLOAT, FieldType.DECIMAL}:
        raise BusinessRuleContractError("range condition requires an integer, float, or decimal field")
    values = [condition.equals, condition.not_equals, condition.gte, condition.lte]
    if condition.in_values is not None:
        values.extend(condition.in_values)
    _validate_literals(
        [value for value in values if value is not None],
        field,
        f"{table}.{condition.field} condition",
        decimal_shape=False,
    )


def _validate_literals(
    values: list[Any],
    field: FieldSpec,
    label: str,
    *,
    decimal_shape: bool = True,
) -> None:
    sensitive_target = field.sensitive or is_sensitive_field(
        field.name,
        field.semantic_type,
    )
    if sensitive_target and values:
        raise BusinessRuleContractError(
            f"business rules cannot assign or compare sensitive field values: {label}"
        )
    for value in values:
        if not isinstance(value, (str, int, float, bool)) and value is not None:
            raise BusinessRuleContractError(
                f"business rule values must be JSON scalars: {label}"
            )
        if isinstance(value, float) and not math.isfinite(value):
            raise BusinessRuleContractError(
                f"business rule values must be finite: {label}"
            )
        if value is not None and field.data_type == FieldType.DECIMAL:
            from test_data_agent.core.distribution import DecimalRangeDistribution
            from test_data_agent.core.decimal_units import value_matches_decimal
            exact = field.typed_distribution
            from test_data_agent.rules.expressions import exact_number
            exact_number(value)
            if decimal_shape and (not isinstance(exact, DecimalRangeDistribution) or not value_matches_decimal(
                str(value), precision=exact.precision, scale=exact.scale,
            )):
                raise BusinessRuleContractError("decimal rule values require exact supported decimal text")
            if field.semantic_type == "numeric_measure":
                continue
        if looks_sensitive_value(value):
            raise BusinessRuleContractError(
                f"business rules contain a raw-looking sensitive value: {label}"
            )


__all__ = [
    "BusinessRuleContractError",
    "estimate_business_rule_evaluations",
    "validate_business_rule_literals",
    "validate_business_rules_for_spec",
]
