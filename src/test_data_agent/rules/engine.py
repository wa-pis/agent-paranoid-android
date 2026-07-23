"""Neutral business rule application and controlled invalid generation."""

from __future__ import annotations

import random
from collections.abc import Mapping
from typing import Any

from test_data_agent.core.settings import GenerationMode
from test_data_agent.rules.conditions import condition_matches
from test_data_agent.rules.expressions import parse_datetime, safe_eval
from test_data_agent.rules.models import (
    BusinessRules,
    ConditionalAllowedValuesRule,
    ConditionalRequiredRule,
    FieldRule,
    FormulaRule,
    TemporalOrderingRule,
)
from test_data_agent.rules.scenarios import apply_scenarios


def apply_business_rules(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    seed: int,
    mode: str = GenerationMode.VALID,
    invalid_ratio: float = 0.0,
    field_defaults: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    rng = random.Random(seed)
    apply_scenarios(rows_by_table, rules.scenarios, seed)
    apply_valid_defaults(rows_by_table, rules, field_defaults=field_defaults)

    selected_mode = GenerationMode(mode)
    if selected_mode == GenerationMode.EDGE:
        apply_edge_cases(rows_by_table, rules)
    if selected_mode in {GenerationMode.MIXED, GenerationMode.NEGATIVE}:
        ratio = 1.0 if selected_mode == GenerationMode.NEGATIVE else invalid_ratio
        inject_invalid_cases(rows_by_table, rules, rng, ratio)
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


def default_value(rule: FieldRule, typed_default: Any = None) -> Any:
    if rule.allowed_values:
        return rule.allowed_values[0]
    if rule.min_value is not None:
        return rule.min_value
    if typed_default is not None:
        return typed_default
    return "required"
