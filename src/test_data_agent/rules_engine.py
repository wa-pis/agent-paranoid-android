"""Business rule application and controlled invalid generation."""

from __future__ import annotations

import random
from enum import StrEnum
from typing import Any

from test_data_agent.business_rules import (
    BusinessRules,
    ConditionalAllowedValuesRule,
    ConditionalRequiredRule,
    FieldRule,
    FormulaRule,
    TemporalOrderingRule,
)
from test_data_agent.business_validator import condition_matches, parse_datetime, safe_eval
from test_data_agent.scenario import apply_scenarios


class GenerationMode(StrEnum):
    VALID = "valid"
    MIXED = "mixed"
    NEGATIVE = "negative"
    EDGE = "edge"
    LOAD_TEST = "load_test"


def apply_business_rules(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    seed: int,
    mode: str = GenerationMode.VALID,
    invalid_ratio: float = 0.0,
) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    apply_scenarios(rows_by_table, rules.scenarios, seed)
    apply_valid_defaults(rows_by_table, rules)

    selected_mode = GenerationMode(mode)
    if selected_mode == GenerationMode.EDGE:
        apply_edge_cases(rows_by_table, rules)
    if selected_mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        ratio = 1.0 if selected_mode == GenerationMode.NEGATIVE else invalid_ratio
        inject_invalid_cases(rows_by_table, rules, rng, ratio)
    return rows_by_table


def apply_valid_defaults(rows_by_table: dict[str, list[dict[str, Any]]], rules: BusinessRules) -> None:
    for rule in rules.field_rules:
        for row in rows_by_table.get(rule.table, []):
            if rule.required and row.get(rule.field) in (None, ""):
                row[rule.field] = default_value(rule)
            if rule.allowed_values and row.get(rule.field) not in rule.allowed_values:
                row[rule.field] = rule.allowed_values[0]

    for rule in rules.row_rules:
        if isinstance(rule, ConditionalRequiredRule):
            for row in rows_by_table.get(rule.table, []):
                if not condition_matches(row, rule.when):
                    continue
                for field in rule.required_fields:
                    if row.get(field) in (None, ""):
                        row[field] = "required"
        elif isinstance(rule, ConditionalAllowedValuesRule):
            for row in rows_by_table.get(rule.table, []):
                if condition_matches(row, rule.when) and row.get(rule.field) not in rule.allowed_values:
                    row[rule.field] = rule.allowed_values[0]
        elif isinstance(rule, TemporalOrderingRule):
            for row in rows_by_table.get(rule.table, []):
                start = parse_datetime(row.get(rule.start_field))
                end = parse_datetime(row.get(rule.end_field))
                if start is not None and (end is None or start > end):
                    row[rule.end_field] = row.get(rule.start_field)
        elif isinstance(rule, FormulaRule):
            for row in rows_by_table.get(rule.table, []):
                row[rule.field] = safe_eval(rule.expression, row)


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
) -> None:
    for table, rows in rows_by_table.items():
        for row in rows:
            if rng.random() > invalid_ratio:
                continue
            if break_field_rule(row, table, rules):
                continue
            if break_temporal_rule(row, table, rules):
                continue


def break_field_rule(row: dict[str, Any], table: str, rules: BusinessRules) -> bool:
    for rule in rules.field_rules:
        if rule.table != table:
            continue
        if rule.required:
            row[rule.field] = None
            return True
        if rule.allowed_values:
            row[rule.field] = "__invalid__"
            return True
    return False


def break_temporal_rule(row: dict[str, Any], table: str, rules: BusinessRules) -> bool:
    for rule in rules.row_rules:
        if isinstance(rule, TemporalOrderingRule) and rule.table == table:
            row[rule.end_field] = "1900-01-01T00:00:00"
            return True
    return False


def default_value(rule: FieldRule) -> Any:
    if rule.allowed_values:
        return rule.allowed_values[0]
    if rule.min_value is not None:
        return rule.min_value
    return "required"
