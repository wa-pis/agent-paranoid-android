"""Neutral accessors for business rule configuration and execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from test_data_agent.business_rules import BusinessRules, business_rules_from_dict, load_business_rules
from test_data_agent.business_validator import BusinessValidationReport, validate_business_rules
from test_data_agent.rules_engine import apply_business_rules

__all__ = [
    "BusinessRules",
    "BusinessValidationReport",
    "apply_and_validate_business_rules",
    "apply_and_validate_business_rules_from_path",
    "business_rules_from_dict",
    "load_business_rules",
    "Path",
]


def apply_and_validate_business_rules(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules: BusinessRules,
    *,
    seed: int,
    mode: str,
    invalid_ratio: float,
) -> BusinessValidationReport:
    apply_business_rules(
        rows_by_table,
        rules,
        seed=seed,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
    return validate_business_rules(rows_by_table, rules)


def apply_and_validate_business_rules_from_path(
    rows_by_table: dict[str, list[dict[str, Any]]],
    rules_path: Path | None,
    *,
    seed: int,
    mode: str,
    invalid_ratio: float,
) -> BusinessValidationReport | None:
    if rules_path is None:
        return None
    rules = load_business_rules(rules_path)
    return apply_and_validate_business_rules(
        rows_by_table,
        rules,
        seed=seed,
        mode=mode,
        invalid_ratio=invalid_ratio,
    )
