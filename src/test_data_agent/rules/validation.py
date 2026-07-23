"""Neutral business-rule validation helpers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.rules.models import (
    AggregateFormulaRule,
    BusinessRules,
    ConditionalAllowedValuesRule,
    ConditionalRequiredRule,
    FieldRule,
    ForeignKeyRule,
    FormulaRule,
    TemporalOrderingRule,
    business_rules_fingerprint,
)
from test_data_agent.rules.conditions import condition_matches
from test_data_agent.rules.expressions import aggregate, comparable_number, numbers_close, parse_datetime, safe_eval


MAX_REPORTED_RULE_ERRORS = 100
MAX_TOTAL_REPORTED_RULE_ERRORS = 1_000


class RuleResult(BaseModel):
    rule_type: str
    passed: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)
    errors_truncated: bool = False


class BusinessValidationReport(BaseModel):
    valid: bool
    rule_count: int
    rules_sha256: str
    rule_pass_count: int
    rule_fail_count: int
    results: list[RuleResult]


def validate_business_rules(rows_by_table: dict[str, list[dict[str, Any]]], rules: BusinessRules) -> BusinessValidationReport:
    results: list[RuleResult] = []
    for field_rule in rules.field_rules:
        results.append(validate_field_rule(rows_by_table, field_rule))
    for row_rule in rules.row_rules:
        if isinstance(row_rule, ConditionalRequiredRule):
            results.append(validate_conditional_required(rows_by_table, row_rule))
        elif isinstance(row_rule, ConditionalAllowedValuesRule):
            results.append(
                validate_conditional_allowed_values(rows_by_table, row_rule)
            )
        elif isinstance(row_rule, TemporalOrderingRule):
            results.append(validate_temporal_ordering(rows_by_table, row_rule))
        elif isinstance(row_rule, FormulaRule):
            results.append(validate_formula(rows_by_table, row_rule))
    for cross_table_rule in rules.cross_table_rules:
        if isinstance(cross_table_rule, ForeignKeyRule):
            results.append(validate_foreign_key(rows_by_table, cross_table_rule))
        elif isinstance(cross_table_rule, AggregateFormulaRule):
            results.append(
                validate_aggregate_formula(rows_by_table, cross_table_rule)
            )

    truncate_report_errors(results)
    passed = sum(result.passed for result in results)
    failed = sum(result.failed for result in results)
    return BusinessValidationReport(
        valid=failed == 0,
        rule_count=rules.rule_count,
        rules_sha256=business_rules_fingerprint(rules),
        rule_pass_count=passed,
        rule_fail_count=failed,
        results=results,
    )


def validate_field_rule(rows_by_table: dict[str, list[dict[str, Any]]], rule: FieldRule) -> RuleResult:
    result = RuleResult(rule_type="field")
    for index, row in enumerate(rows_by_table.get(rule.table, [])):
        value = row.get(rule.field)
        errors = []
        if rule.required and value in (None, ""):
            errors.append("required")
        if rule.allowed_values is not None and value not in (None, "") and value not in rule.allowed_values:
            errors.append("allowed_values")
        number = comparable_number(value)
        if rule.min_value is not None and number is not None and number < rule.min_value:
            errors.append("min_value")
        if rule.max_value is not None and number is not None and number > rule.max_value:
            errors.append("max_value")
        record_result(result, not errors, f"{rule.table}[{index}].{rule.field}: {', '.join(errors)}")
    return result


def validate_conditional_required(rows_by_table: dict[str, list[dict[str, Any]]], rule: ConditionalRequiredRule) -> RuleResult:
    result = RuleResult(rule_type="conditional_required")
    for index, row in enumerate(rows_by_table.get(rule.table, [])):
        if not condition_matches(row, rule.when):
            continue
        missing = [field for field in rule.required_fields if row.get(field) in (None, "")]
        record_result(result, not missing, f"{rule.table}[{index}] missing {missing}")
    return result


def validate_conditional_allowed_values(rows_by_table: dict[str, list[dict[str, Any]]], rule: ConditionalAllowedValuesRule) -> RuleResult:
    result = RuleResult(rule_type="conditional_allowed_values")
    for index, row in enumerate(rows_by_table.get(rule.table, [])):
        if not condition_matches(row, rule.when):
            continue
        value = row.get(rule.field)
        record_result(result, value in rule.allowed_values, f"{rule.table}[{index}].{rule.field}={value!r}")
    return result


def validate_temporal_ordering(rows_by_table: dict[str, list[dict[str, Any]]], rule: TemporalOrderingRule) -> RuleResult:
    result = RuleResult(rule_type="temporal_ordering")
    for index, row in enumerate(rows_by_table.get(rule.table, [])):
        start = parse_datetime(row.get(rule.start_field))
        end = parse_datetime(row.get(rule.end_field))
        ok = start is not None and end is not None and (start <= end if rule.allow_equal else start < end)
        record_result(result, ok, f"{rule.table}[{index}] {rule.start_field}>{rule.end_field}")
    return result


def validate_formula(rows_by_table: dict[str, list[dict[str, Any]]], rule: FormulaRule) -> RuleResult:
    result = RuleResult(rule_type="formula")
    for index, row in enumerate(rows_by_table.get(rule.table, [])):
        try:
            expected = safe_eval(rule.expression, row)
        except Exception as exc:
            record_result(result, False, f"{rule.table}[{index}].{rule.field} formula evaluation failed: {exc}")
            continue
        actual = row.get(rule.field)
        ok = numbers_close(actual, expected, rule.tolerance)
        record_result(result, ok, f"{rule.table}[{index}].{rule.field} expected {expected}, got {actual}")
    return result


def validate_foreign_key(rows_by_table: dict[str, list[dict[str, Any]]], rule: ForeignKeyRule) -> RuleResult:
    result = RuleResult(rule_type="foreign_key")
    parent_values = {row.get(rule.parent_field) for row in rows_by_table.get(rule.parent_table, [])}
    for index, row in enumerate(rows_by_table.get(rule.child_table, [])):
        value = row.get(rule.child_field)
        record_result(result, value in parent_values, f"{rule.child_table}[{index}].{rule.child_field} missing parent")
    return result


def validate_aggregate_formula(rows_by_table: dict[str, list[dict[str, Any]]], rule: AggregateFormulaRule) -> RuleResult:
    result = RuleResult(rule_type="aggregate_formula")
    rows = rows_by_table.get(rule.table, [])
    actual = aggregate(rule.field, rows)
    try:
        expected = rule.expected if rule.expected is not None else safe_eval(rule.expression, {"rows": rows})
    except Exception as exc:
        record_result(result, False, f"{rule.table}.{rule.field} aggregate formula evaluation failed: {exc}")
        return result
    record_result(result, numbers_close(actual, expected, rule.tolerance), f"{rule.table}.{rule.field} aggregate expected {expected}, got {actual}")
    return result


def record_result(result: RuleResult, ok: bool, message: str) -> None:
    if ok:
        result.passed += 1
    else:
        result.failed += 1
        if len(result.errors) < MAX_REPORTED_RULE_ERRORS:
            result.errors.append(message)
        else:
            result.errors_truncated = True


def truncate_report_errors(results: list[RuleResult]) -> None:
    remaining = MAX_TOTAL_REPORTED_RULE_ERRORS
    for result in results:
        if len(result.errors) > remaining:
            result.errors = result.errors[:remaining]
            result.errors_truncated = True
        remaining -= len(result.errors)
        if remaining == 0 and result.failed > len(result.errors):
            result.errors_truncated = True
