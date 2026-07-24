"""Neutral accessors for business rule configuration and execution."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.constraint_solver import default_value_for_field
from test_data_agent.rules.contract import (
    validate_business_rule_literals,
    validate_business_rules_for_spec,
)
from test_data_agent.rules.engine import apply_business_rules
from test_data_agent.rules.models import BusinessRules, business_rules_from_dict, load_business_rules
from test_data_agent.rules.validation import BusinessValidationReport, validate_business_rules

BusinessRulesApplier = Callable[
    [dict[str, list[dict[str, Any]]], int, DatasetSpec],
    BusinessValidationReport,
]

__all__ = [
    "BusinessRules",
    "BusinessRulesApplier",
    "BusinessValidationReport",
    "apply_and_validate_business_rules",
    "apply_and_validate_business_rules_from_path",
    "business_rules_from_dict",
    "load_business_rules",
    "make_business_rules_applier",
    "Path",
]


def apply_and_validate_business_rules(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    *,
    seed: int,
    mode: str,
    invalid_ratio: float,
    field_defaults: dict[str, dict[str, Any]] | None = None,
) -> BusinessValidationReport:
    apply_business_rules(
        rows_by_table,
        rules,
        seed=seed,
        mode=mode,
        invalid_ratio=invalid_ratio,
        field_defaults=field_defaults,
    )
    return validate_business_rules(rows_by_table, rules)


def apply_and_validate_business_rules_from_path(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules_path: Path | None,
    *,
    seed: int,
    mode: str,
    invalid_ratio: float,
    field_defaults: dict[str, dict[str, Any]] | None = None,
    spec: DatasetSpec | None = None,
) -> BusinessValidationReport | None:
    if rules_path is None:
        return None
    rules = load_business_rules(rules_path)
    validate_business_rule_literals(rules)
    if spec is not None:
        validate_business_rules_for_spec(rules, spec)
    return apply_and_validate_business_rules(
        rows_by_table,
        rules,
        seed=seed,
        mode=mode,
        invalid_ratio=invalid_ratio,
        field_defaults=field_defaults,
    )


def make_business_rules_applier(rules: BusinessRules) -> BusinessRulesApplier:
    def apply_rules(
        rows_by_table: dict[str, list[dict[str, Any]]],
        seed: int,
        spec: DatasetSpec,
    ) -> BusinessValidationReport:
        validate_business_rules_for_spec(rules, spec)
        field_defaults = {
            entity.name: {
                field.name: default_value_for_field(field)
                for field in entity.fields
            }
            for entity in spec.entities
        }
        return apply_and_validate_business_rules(
            rows_by_table,
            rules,
            seed=seed,
            mode=spec.generation_settings.mode,
            invalid_ratio=spec.generation_settings.invalid_ratio,
            field_defaults=field_defaults,
        )

    return apply_rules
