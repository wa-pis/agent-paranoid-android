"""Neutral business rule application and controlled invalid generation."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from test_data_agent.core.settings import GenerationMode
from test_data_agent.rules.conditions import Condition, condition_matches
from test_data_agent.rules.expressions import (
    aggregate,
    comparable_number,
    numbers_close,
    parse_datetime,
    safe_eval,
)
from test_data_agent.rules.models import (
    AggregateFormulaRule,
    BusinessRules,
    ConditionalAllowedValuesRule,
    ConditionalRequiredRule,
    FieldRule,
    ForeignKeyRule,
    FormulaRule,
    TemporalOrderingRule,
)
from test_data_agent.rules.scenarios import apply_scenarios


@dataclass(frozen=True)
class InvalidCase:
    kind: Literal[
        "required",
        "allowed_values",
        "min_value",
        "max_value",
        "conditional_required",
        "conditional_allowed_values",
        "temporal_ordering",
        "formula",
        "foreign_key",
        "aggregate_formula",
    ]
    rule: (
        FieldRule
        | ConditionalRequiredRule
        | ConditionalAllowedValuesRule
        | TemporalOrderingRule
        | FormulaRule
        | ForeignKeyRule
        | AggregateFormulaRule
    )
    field: str | None = None
    rule_index: int = 0


def apply_business_rules(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    seed: int,
    mode: str = GenerationMode.VALID,
    invalid_ratio: float = 0.0,
    field_defaults: Mapping[str, Mapping[str, Any]] | None = None,
    expected_rule_failures: dict[int, int] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    apply_scenarios(rows_by_table, rules.scenarios, seed)
    apply_valid_defaults(rows_by_table, rules, field_defaults=field_defaults)

    selected_mode = GenerationMode(mode)
    if selected_mode == GenerationMode.EDGE:
        apply_edge_cases(rows_by_table, rules)
    if selected_mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        ratio = 1.0 if selected_mode == GenerationMode.NEGATIVE else invalid_ratio
        inject_invalid_cases(
            rows_by_table,
            rules,
            rng,
            ratio,
            expected_rule_failures=expected_rule_failures,
        )
    return rows_by_table


def apply_valid_defaults(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    *,
    field_defaults: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    for field_rule in rules.field_rules:
        for row in rows_by_table.get(field_rule.table, []):
            if field_rule.required and row.get(field_rule.field) in (None, ""):
                row[field_rule.field] = default_value(
                    field_rule,
                    field_defaults.get(field_rule.table, {}).get(field_rule.field)
                    if field_defaults is not None
                    else None,
                )
            if (
                field_rule.allowed_values
                and row.get(field_rule.field) not in field_rule.allowed_values
            ):
                row[field_rule.field] = field_rule.allowed_values[0]

    for row_rule in rules.row_rules:
        if isinstance(row_rule, ConditionalRequiredRule):
            for row in rows_by_table.get(row_rule.table, []):
                if not condition_matches(row, row_rule.when):
                    continue
                for field in row_rule.required_fields:
                    if row.get(field) in (None, ""):
                        if (
                            field_defaults is not None
                            and field in field_defaults.get(row_rule.table, {})
                        ):
                            row[field] = field_defaults[row_rule.table][field]
                        else:
                            row[field] = "required"
        elif isinstance(row_rule, ConditionalAllowedValuesRule):
            for row in rows_by_table.get(row_rule.table, []):
                if (
                    condition_matches(row, row_rule.when)
                    and row.get(row_rule.field) not in row_rule.allowed_values
                ):
                    row[row_rule.field] = row_rule.allowed_values[0]
        elif isinstance(row_rule, TemporalOrderingRule):
            for row in rows_by_table.get(row_rule.table, []):
                start = parse_datetime(row.get(row_rule.start_field))
                end = parse_datetime(row.get(row_rule.end_field))
                if start is not None and (end is None or start > end):
                    row[row_rule.end_field] = row.get(row_rule.start_field)
        elif isinstance(row_rule, FormulaRule):
            for row in rows_by_table.get(row_rule.table, []):
                try:
                    row[row_rule.field] = safe_eval(row_rule.expression, row)
                except Exception as exc:
                    raise ValueError(
                        f"{row_rule.table}.{row_rule.field} formula failed: {exc}"
                    ) from exc


def apply_edge_cases(rows_by_table: dict[str, list[dict[str, Any]]], rules: BusinessRules) -> None:
    for rule in rules.field_rules:
        rows = rows_by_table.get(rule.table, [])
        if not rows:
            continue
        if rule.min_value is not None:
            rows[0][rule.field] = rule.min_value
        if len(rows) > 1 and rule.max_value is not None:
            rows[1][rule.field] = rule.max_value


def inject_invalid_cases(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    rng: random.Random,
    invalid_ratio: float,
    *,
    expected_rule_failures: dict[int, int] | None = None,
) -> None:
    for table, rows in rows_by_table.items():
        cases = invalid_cases_for_table(table, rules)
        if not cases:
            continue
        case_index = rng.randrange(len(cases))
        for row in rows:
            if rng.random() > invalid_ratio:
                continue
            case = cases[case_index]
            apply_invalid_case(row, case, rows_by_table)
            if expected_rule_failures is not None:
                if case.kind == "aggregate_formula":
                    expected_rule_failures[case.rule_index] = 1
                else:
                    expected_rule_failures[case.rule_index] = (
                        expected_rule_failures.get(case.rule_index, 0) + 1
                    )
            case_index = (case_index + 1) % len(cases)


def invalid_cases_for_table(table: str, rules: BusinessRules) -> list[InvalidCase]:
    cases: list[InvalidCase] = []
    for rule_index, field_rule in enumerate(rules.field_rules):
        if field_rule.table != table:
            continue
        if field_rule.required:
            cases.append(InvalidCase("required", field_rule, rule_index=rule_index))
        if field_rule.allowed_values:
            cases.append(
                InvalidCase("allowed_values", field_rule, rule_index=rule_index)
            )
        if field_rule.min_value is not None:
            cases.append(InvalidCase("min_value", field_rule, rule_index=rule_index))
        if field_rule.max_value is not None:
            cases.append(InvalidCase("max_value", field_rule, rule_index=rule_index))
    row_offset = len(rules.field_rules)
    for row_index, row_rule in enumerate(rules.row_rules):
        if row_rule.table != table:
            continue
        rule_index = row_offset + row_index
        if isinstance(row_rule, ConditionalRequiredRule):
            cases.extend(
                InvalidCase(
                    "conditional_required",
                    row_rule,
                    field,
                    rule_index,
                )
                for field in row_rule.required_fields
            )
        elif isinstance(row_rule, ConditionalAllowedValuesRule):
            cases.append(
                InvalidCase(
                    "conditional_allowed_values",
                    row_rule,
                    rule_index=rule_index,
                )
            )
        elif isinstance(row_rule, TemporalOrderingRule):
            cases.append(
                InvalidCase("temporal_ordering", row_rule, rule_index=rule_index)
            )
        elif isinstance(row_rule, FormulaRule):
            cases.append(InvalidCase("formula", row_rule, rule_index=rule_index))
    cross_table_offset = row_offset + len(rules.row_rules)
    for cross_table_index, cross_table_rule in enumerate(rules.cross_table_rules):
        rule_index = cross_table_offset + cross_table_index
        if (
            isinstance(cross_table_rule, ForeignKeyRule)
            and cross_table_rule.child_table == table
        ):
            cases.append(
                InvalidCase(
                    "foreign_key",
                    cross_table_rule,
                    rule_index=rule_index,
                )
            )
        elif (
            isinstance(cross_table_rule, AggregateFormulaRule)
            and cross_table_rule.table == table
            and cross_table_rule.field != "*"
        ):
            cases.append(
                InvalidCase(
                    "aggregate_formula",
                    cross_table_rule,
                    rule_index=rule_index,
                )
            )
    return cases


def apply_invalid_case(
    row: dict[str, Any],
    case: InvalidCase,
    rows_by_table: Mapping[str, list[dict[str, Any]]],
) -> None:
    rule = case.rule
    if isinstance(rule, FieldRule):
        if case.kind == "required":
            row[rule.field] = None
        elif case.kind == "allowed_values":
            row[rule.field] = value_outside(rule.allowed_values or [])
        elif case.kind == "min_value":
            row[rule.field] = value_below(rule.min_value)
        elif case.kind == "max_value":
            row[rule.field] = value_above(rule.max_value)
        return
    if isinstance(rule, ConditionalRequiredRule):
        force_condition_match(row, rule.when)
        if case.field is not None:
            row[case.field] = None
        return
    if isinstance(rule, ConditionalAllowedValuesRule):
        force_condition_match(row, rule.when)
        row[rule.field] = value_outside(rule.allowed_values)
        return
    if isinstance(rule, TemporalOrderingRule):
        start = parse_datetime(row.get(rule.start_field)) or datetime(2000, 1, 2)
        row[rule.start_field] = start.isoformat()
        row[rule.end_field] = (start - timedelta(microseconds=1)).isoformat()
        return
    if isinstance(rule, FormulaRule):
        row[rule.field] = perturbed_formula_value(
            row.get(rule.field),
            rule.tolerance,
        )
        return
    if isinstance(rule, ForeignKeyRule):
        parent_values = [
            parent.get(rule.parent_field)
            for parent in rows_by_table.get(rule.parent_table, [])
        ]
        row[rule.child_field] = missing_parent_value(
            parent_values,
            row.get(rule.child_field),
        )
        return
    if isinstance(rule, AggregateFormulaRule):
        break_aggregate_formula(
            row,
            rows_by_table.get(rule.table, []),
            rule,
        )


def force_condition_match(row: dict[str, Any], condition: Condition) -> None:
    candidates = []
    if condition.equals is not None:
        candidates.append(condition.equals)
    if condition.in_values:
        candidates.extend(condition.in_values)
    candidates.extend([row.get(condition.field), "__condition_match__"])
    for candidate in candidates:
        candidate_row = dict(row)
        candidate_row[condition.field] = candidate
        if condition_matches(candidate_row, condition):
            row[condition.field] = candidate
            return
    raise ValueError(f"condition for {condition.field!r} cannot be satisfied")


def value_outside(allowed_values: list[Any]) -> str:
    value = "__invalid__"
    while value in allowed_values:
        value += "_"
    return value


def value_below(bound: float | None) -> float | str:
    if bound is None:
        raise ValueError("minimum bound is required")
    value = math.nextafter(bound, -math.inf)
    return value if math.isfinite(value) else "__invalid__"


def value_above(bound: float | None) -> float | str:
    if bound is None:
        raise ValueError("maximum bound is required")
    value = math.nextafter(bound, math.inf)
    return value if math.isfinite(value) else "__invalid__"


def perturbed_formula_value(value: Any, tolerance: float) -> float | str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "__invalid__"
    delta = max(1.0, tolerance * 2)
    for candidate in (value + delta, value - delta):
        if math.isfinite(candidate) and not numbers_close(
            candidate,
            value,
            tolerance,
        ):
            return candidate
    return "__invalid__"


def missing_parent_value(parent_values: list[Any], child_value: Any) -> Any:
    used = set(parent_values)
    typed_values = [value for value in parent_values if value is not None]
    sample = typed_values[0] if typed_values else child_value
    if isinstance(sample, int) and not isinstance(sample, bool):
        integer_candidate = max(
            (
                value
                for value in typed_values
                if isinstance(value, int) and not isinstance(value, bool)
            ),
            default=sample,
        ) + 1
        while integer_candidate in used:
            integer_candidate += 1
        return integer_candidate
    if isinstance(sample, float):
        float_candidate = math.nextafter(
            max(
                (
                    value
                    for value in typed_values
                    if isinstance(value, (int, float))
                    and not isinstance(value, bool)
                ),
                default=sample,
            ),
            math.inf,
        )
        if math.isfinite(float_candidate) and float_candidate not in used:
            return float_candidate
    return value_outside(parent_values)


def break_aggregate_formula(
    row: dict[str, Any],
    rows: list[dict[str, Any]],
    rule: AggregateFormulaRule,
) -> None:
    actual = aggregate(rule.field, rows)
    try:
        expected = (
            rule.expected
            if rule.expected is not None
            else safe_eval(rule.expression, {"rows": rows})
        )
    except Exception:
        return
    current = comparable_number(row.get(rule.field)) or 0.0
    delta = max(1.0, rule.tolerance * 2)
    for candidate in (current + delta, current - delta):
        changed_actual = actual - current + candidate
        if math.isfinite(candidate) and not numbers_close(
            changed_actual,
            expected,
            rule.tolerance,
        ):
            row[rule.field] = candidate
            return
    row[rule.field] = "__invalid__"


def default_value(rule: FieldRule, typed_default: Any = None) -> Any:
    if rule.allowed_values:
        return rule.allowed_values[0]
    if rule.min_value is not None:
        return rule.min_value
    if typed_default is not None:
        return typed_default
    return "required"
