"""Business-rule validation for synthetic datasets."""

from __future__ import annotations

import ast
import operator
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.business_rules import (
    AggregateFormulaRule,
    BusinessRules,
    ConditionalAllowedValuesRule,
    ConditionalRequiredRule,
    Condition,
    FieldRule,
    ForeignKeyRule,
    FormulaRule,
    TemporalOrderingRule,
)


class RuleResult(BaseModel):
    rule_type: str
    passed: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)


class BusinessValidationReport(BaseModel):
    valid: bool
    rule_pass_count: int
    rule_fail_count: int
    results: list[RuleResult]


def validate_business_rules(rows_by_table: dict[str, list[dict[str, Any]]], rules: BusinessRules) -> BusinessValidationReport:
    results: list[RuleResult] = []
    for rule in rules.field_rules:
        results.append(validate_field_rule(rows_by_table, rule))
    for rule in rules.row_rules:
        if isinstance(rule, ConditionalRequiredRule):
            results.append(validate_conditional_required(rows_by_table, rule))
        elif isinstance(rule, ConditionalAllowedValuesRule):
            results.append(validate_conditional_allowed_values(rows_by_table, rule))
        elif isinstance(rule, TemporalOrderingRule):
            results.append(validate_temporal_ordering(rows_by_table, rule))
        elif isinstance(rule, FormulaRule):
            results.append(validate_formula(rows_by_table, rule))
    for rule in rules.cross_table_rules:
        if isinstance(rule, ForeignKeyRule):
            results.append(validate_foreign_key(rows_by_table, rule))
        elif isinstance(rule, AggregateFormulaRule):
            results.append(validate_aggregate_formula(rows_by_table, rule))

    passed = sum(result.passed for result in results)
    failed = sum(result.failed for result in results)
    return BusinessValidationReport(
        valid=failed == 0,
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
        if rule.min_value is not None and comparable_number(value) is not None and comparable_number(value) < rule.min_value:
            errors.append("min_value")
        if rule.max_value is not None and comparable_number(value) is not None and comparable_number(value) > rule.max_value:
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
        expected = safe_eval(rule.expression, row)
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
    expected = rule.expected if rule.expected is not None else safe_eval(rule.expression, {"rows": rows})
    record_result(result, numbers_close(actual, expected, rule.tolerance), f"{rule.table}.{rule.field} aggregate expected {expected}, got {actual}")
    return result


def condition_matches(row: dict[str, Any], condition: Condition) -> bool:
    value = row.get(condition.field)
    if condition.equals is not None and value != condition.equals:
        return False
    if condition.not_equals is not None and value == condition.not_equals:
        return False
    if condition.in_values is not None and value not in condition.in_values:
        return False
    return True


def record_result(result: RuleResult, ok: bool, message: str) -> None:
    if ok:
        result.passed += 1
    else:
        result.failed += 1
        result.errors.append(message)


def comparable_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def numbers_close(actual: Any, expected: Any, tolerance: float) -> bool:
    actual_number = comparable_number(actual)
    expected_number = comparable_number(expected)
    return actual_number is not None and expected_number is not None and abs(actual_number - expected_number) <= tolerance


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def aggregate(field: str, rows: list[dict[str, Any]]) -> float:
    if field == "*":
        return float(len(rows))
    return sum(comparable_number(row.get(field)) or 0.0 for row in rows)


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_eval(expression: str, row: dict[str, Any]) -> Any:
    node = ast.parse(expression, mode="eval")
    return eval_node(node.body, row)


def eval_node(node: ast.AST, row: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return row.get(node.id)
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_node(node.left, row), eval_node(node.right, row))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_node(node.operand, row))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "sum":
            field = expect_field_name(node.args[0])
            return aggregate(field, row.get("rows", []))
        if node.func.id == "count":
            return float(len(row.get("rows", [])))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def expect_field_name(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise ValueError("aggregate field name must be a string literal")
