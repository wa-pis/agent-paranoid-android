"""Controlled-invalid accounting cannot excuse an invalid baseline or count twice."""
from __future__ import annotations

from decimal import Decimal
import random

import pytest

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.rules.business_config import apply_and_validate_business_rules
import test_data_agent.rules.engine as engine
from test_data_agent.rules.models import BusinessRules


@pytest.mark.parametrize("mode", ["negative", "mixed"])
@pytest.mark.parametrize("no_op", [False, True])
def test_primary_check_cannot_authorize_a_preexisting_row_failure(monkeypatch, mode, no_op):
    rules = BusinessRules.model_validate({"row_rules": [{"type": "formula", "table": "items",
        "field": "total", "expression": "quantity * 2", "mode": "check"}]})
    if no_op:
        monkeypatch.setattr(engine, "apply_invalid_case", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="valid business-rule baseline"):
        apply_and_validate_business_rules(
            {"items": [{"quantity": 2, "total": 99}]}, rules,
            seed=7, mode=mode, invalid_ratio=1,
        )


@pytest.mark.parametrize("mode", ["negative", "mixed"])
def test_preexisting_one_row_failure_is_not_hidden_by_another_planned_row(mode):
    rules = BusinessRules.model_validate({"row_rules": [{"type": "formula", "table": "items",
        "field": "total", "expression": "quantity * 2", "mode": "check"}]})
    with pytest.raises(ValueError, match="valid business-rule baseline"):
        apply_and_validate_business_rules(
            {"items": [{"quantity": 2, "total": 99}, {"quantity": 2, "total": 4}]},
            rules, seed=7, mode=mode, invalid_ratio=1,
        )


@pytest.mark.parametrize("mode", ["negative", "mixed"])
def test_negative_mutation_that_repairs_invalid_baseline_cannot_succeed(mode):
    rules = BusinessRules.model_validate({"row_rules": [{"type": "formula", "table": "items",
        "field": "total", "expression": "quantity * 2", "mode": "check"}]})
    with pytest.raises(ValueError, match="valid business-rule baseline"):
        apply_and_validate_business_rules(
            {"items": [{"quantity": 2, "total": 3}]}, rules,
            seed=7, mode=mode, invalid_ratio=1,
        )


@pytest.mark.parametrize("kind", ["foreign_key", "aggregate_formula"])
def test_primary_cross_table_rule_does_not_authorize_its_invalid_baseline(kind):
    if kind == "foreign_key":
        rule = {"type": kind, "parent_table": "parents", "parent_field": "id",
                "child_table": "items", "child_field": "pid"}
        rows = {"parents": [{"id": 1}], "items": [{"pid": 99}, {"pid": 99}]}
    else:
        rule = {"type": kind, "table": "items", "field": "total",
                "expression": "sum('quantity') * 2"}
        rows = {"items": [{"quantity": 2, "total": 99}]}
    rules = BusinessRules.model_validate({"cross_table_rules": [rule]})
    with pytest.raises(ValueError, match="valid business-rule baseline"):
        apply_and_validate_business_rules(rows, rules, seed=7, mode="negative", invalid_ratio=0)


@pytest.mark.parametrize("mode", ["negative", "mixed"])
@pytest.mark.parametrize("row_count", [1, 6])
def test_each_failed_row_rule_pair_is_counted_once_with_overlapping_primary_rules(mode, row_count):
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "items", "field": "label", "required": True}],
        "row_rules": [{"type": "conditional_required", "table": "items",
                       "when": {"field": "active", "equals": True},
                       "required_fields": ["label"]}],
    })
    report = apply_and_validate_business_rules(
        {"items": [{"active": True, "label": "ready"} for _ in range(row_count)]},
        rules, seed=7, mode=mode, invalid_ratio=1,
    )
    assert report.expectations_met
    assert report.expected_violation_count == report.observed_violation_count == 2 * row_count
    assert [result.expected_violation_count for result in report.results] == [row_count] * 2
    assert report.unexpected_violation_count == report.missing_expected_violation_count == 0


@pytest.mark.parametrize("cross_rule_count", [1, 2])
def test_parent_collateral_and_primary_fk_mutation_do_not_double_count(cross_rule_count):
    foreign_key = {"type": "foreign_key", "parent_table": "parents", "parent_field": "id",
                   "child_table": "items", "child_field": "pid"}
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "parents", "field": "id", "required": True}],
        "cross_table_rules": [foreign_key] * cross_rule_count,
    })
    report = apply_and_validate_business_rules(
        {"parents": [{"id": 1}], "items": [{"pid": 1}, {"pid": 1}]},
        rules, seed=7, mode="negative", invalid_ratio=0,
    )
    assert report.expectations_met
    assert [result.expected_violation_count for result in report.results] == [1] + [2] * cross_rule_count
    assert report.expected_violation_count == report.observed_violation_count == 1 + 2 * cross_rule_count


def test_decimal_collateral_checks_keep_exact_target_scale_and_no_duplicate_counts():
    def field(name):
        return {"name": name, "data_type": "decimal", "distribution": {
            "kind": "decimal_range", "precision": 38, "scale": 16, "min": "0", "max": "9"}}
    spec = DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 6,
        "fields": [field("quantity"), field("total")]}]})
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "items", "field": "total",
                         "min_value": "2.0000000000000000", "max_value": "2.0000000000000000"}],
        "row_rules": [{"type": "formula", "table": "items", "field": "total",
                       "expression": "quantity * 2", "mode": "check"}],
    })
    rows = {"items": [{"quantity": Decimal("1.0000000000000000"),
                        "total": Decimal("2.0000000000000000")} for _ in range(6)]}
    report = apply_and_validate_business_rules(rows, rules, seed=7, mode="negative", invalid_ratio=0, spec=spec)
    assert report.expectations_met
    assert [result.expected_violation_count for result in report.results] == [6, 6]
    assert report.expected_violation_count == report.observed_violation_count == 12
    assert all(isinstance(row["total"], Decimal) for row in rows["items"])


def test_row_local_audits_do_not_scan_the_whole_table_for_each_mutation(monkeypatch):
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "items", "field": "label", "required": True}],
    })
    original = engine.validate_field_rule
    row_visits = []

    def validate(values, rule, **kwargs):
        row_visits.append(len(values["items"]))
        return original(values, rule, **kwargs)

    monkeypatch.setattr(engine, "validate_field_rule", validate)
    report = apply_and_validate_business_rules(
        {"items": [{"label": "ready"} for _ in range(128)]}, rules,
        seed=7, mode="negative", invalid_ratio=0,
    )
    assert report.expectations_met
    assert max(row_visits) == 1
    assert sum(row_visits) <= 4 * 128


def test_local_before_audit_obeys_shared_deadline_before_mutation(monkeypatch):
    rules = BusinessRules.model_validate({
        "field_rules": [{"table": "items", "field": "label", "required": True}],
    })
    original = engine.validate_field_rule
    clock = [0.0]
    rows = {"items": [{"label": "ready"}]}

    def expire(values, rule, **kwargs):
        result = original(values, rule, **kwargs)
        clock[0] = 2.0
        return result

    monkeypatch.setattr(engine, "validate_field_rule", expire)
    with pytest.raises(GenerationLimitError, match="deterministic rule"):
        engine.inject_invalid_cases(rows, rules, random.Random(7), 1,
            expected_rule_failures={}, budget=GenerationBudget(max_seconds=1, clock=lambda: clock[0]))
    assert rows == {"items": [{"label": "ready"}]}
