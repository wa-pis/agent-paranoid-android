"""Neutral accessors for business rule configuration and execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.distribution import NumericDistribution
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.generation.constraint_solver import default_value_for_field
from test_data_agent.rules.contract import (
    validate_business_rule_literals,
    validate_business_rules_for_spec,
)
from test_data_agent.rules.engine import apply_business_rules
from test_data_agent.rules.models import BusinessRules, FormulaRule, business_rules_from_dict, load_business_rules
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
    budget: GenerationBudget | None = None,
    spec: DatasetSpec | None = None,
) -> BusinessValidationReport:
    budget = budget or GenerationBudget()
    if spec is not None:
        validate_business_rules_for_spec(rules, spec)
    expected_rule_failures: dict[int, int] = {}
    apply_business_rules(
        rows_by_table,
        rules,
        seed=seed,
        mode=mode,
        invalid_ratio=invalid_ratio,
        field_defaults=field_defaults,
        expected_rule_failures=expected_rule_failures,
        budget=budget,
        spec=spec,
    )
    report = validate_business_rules(
        rows_by_table,
        rules,
        expected_rule_failures=expected_rule_failures,
        budget=budget,
        spec=spec,
    )
    for index, rule in enumerate(rules.row_rules, start=len(rules.field_rules)):
        if isinstance(rule, FormulaRule):
            report.results[index].application = rule.mode
            if rule.mode == "assign":
                report.results[index].assigned_row_count = len(rows_by_table.get(rule.table, []))
    if spec is not None and mode not in {"mixed", "negative"}:
        _report_assigned_numeric_bounds(rows_by_table, rules, spec, report, budget=budget)
    return report


def apply_and_validate_business_rules_from_path(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules_path: Path | None,
    *,
    seed: int,
    mode: str,
    invalid_ratio: float,
    field_defaults: dict[str, dict[str, Any]] | None = None,
    budget: GenerationBudget | None = None,
    spec: DatasetSpec | None = None,
) -> BusinessValidationReport | None:
    if rules_path is None:
        return None
    budget = budget or GenerationBudget()
    rules = load_business_rules(rules_path)
    if spec is None:
        validate_business_rule_literals(rules)
    if spec is not None:
        if spec.business_rules is not None:
            raise ValueError("business rules are already embedded in the reviewed spec; use one rule source")
        validate_business_rules_for_spec(rules, spec)
    report = apply_and_validate_business_rules(
        rows_by_table,
        rules,
        seed=seed,
        mode=mode,
        invalid_ratio=invalid_ratio,
        field_defaults=field_defaults,
        budget=budget,
        spec=spec,
    )
    if spec is not None:
        spec.business_rules = rules
    return report


@dataclass(frozen=True)
class ConfiguredBusinessRulesApplier:
    rules: BusinessRules

    def __call__(
        self,
        rows_by_table: dict[str, list[dict[str, Any]]],
        seed: int,
        spec: DatasetSpec,
        *,
        budget: GenerationBudget | None = None,
    ) -> BusinessValidationReport:
        rules = self.rules
        budget = budget or GenerationBudget()
        validate_business_rules_for_spec(rules, spec)
        field_defaults = {
            entity.name: {
                field.name: default_value_for_field(field)
                for field in entity.fields
            }
            for entity in spec.entities
        }
        report = apply_and_validate_business_rules(
            rows_by_table,
            rules,
            seed=seed,
            mode=spec.generation_settings.mode,
            invalid_ratio=spec.generation_settings.invalid_ratio,
            field_defaults=field_defaults,
            budget=budget,
            spec=spec,
        )
        spec.business_rules = rules
        return report


def make_business_rules_applier(rules: BusinessRules) -> ConfiguredBusinessRulesApplier:
    return ConfiguredBusinessRulesApplier(rules)


def embed_configured_business_rules(spec: DatasetSpec, applier: Any) -> bool:
    """Route configured rules through generation; retain custom callback compatibility."""
    if not isinstance(applier, ConfiguredBusinessRulesApplier):
        return False
    if spec.business_rules is not None:
        raise ValueError("business rules are already embedded in the reviewed spec; use one rule source")
    validate_business_rules_for_spec(applier.rules, spec)
    spec.business_rules = applier.rules.model_copy(deep=True)
    return True


def _report_assigned_numeric_bounds(
    rows: dict[str, list[dict[str, Any]]], rules: BusinessRules, spec: DatasetSpec, report: BusinessValidationReport,
    *, budget: GenerationBudget | None,
) -> None:
    """Report generation-domain drift separately from explicit business constraints."""
    budget = budget or GenerationBudget()
    for rule in budget.iter_rule_work(rules.row_rules):
        if not isinstance(rule, FormulaRule) or rule.mode != "assign":
            continue
        field = next(field for field in budget.iter_rule_work(spec.entity(rule.table).fields) if field.name == rule.field)
        distribution = field.typed_distribution
        if not isinstance(distribution, NumericDistribution) or field.is_identifier:
            continue
        for row in budget.iter_rule_work(rows.get(rule.table, [])):
            value = row.get(rule.field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue  # The unconditional schema validator handles wrong types.
            report.distribution_bounds_checked_count += 1
            if (
                distribution.min_value is not None and value < distribution.min_value * distribution.scale_factor
                or distribution.max_value is not None and value > distribution.max_value * distribution.scale_factor
            ):
                report.distribution_bounds_violation_count += 1
