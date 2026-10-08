"""Bounded synthetic regressions for native and business-rule work."""
from copy import deepcopy

import pytest

from test_data_agent.core.constraint import Constraint
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError, InputLimitError
from test_data_agent.core.relationship import Relationship
from test_data_agent.generation.constraint_solver import apply_relationships, solve_constraints
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.rules.contract import estimate_business_rule_evaluations_for_rows
from test_data_agent.rules.engine import apply_business_rules, inject_invalid_cases
from test_data_agent.rules.expressions import safe_eval
from test_data_agent.rules.models import BusinessRules, ForeignKeyRule, AggregateFormulaRule
from test_data_agent.rules.validation import validate_business_rules
from test_data_agent.validation.constraint_validator import validate_constraints


def temporal_spec(count: int = 3, rows: int = 2) -> DatasetSpec:
    return DatasetSpec(entities=[EntitySpec(name="events", row_count=rows,
        fields=[FieldSpec(name=name, data_type="date") for name in ("start", "end")])],
        constraints=[Constraint(type="temporal", entity="events", fields=["start", "end"],
            confidence=1) for _ in range(count)])


@pytest.mark.parametrize("validator", [False, True])
def test_deadline_stops_inside_native_rule_rows(monkeypatch, validator):
    from test_data_agent.generation import constraint_solver
    from test_data_agent.validation import constraint_validator
    module = constraint_validator if validator else constraint_solver
    original = module.parse_datetime
    clock = [0.0]
    calls = []
    def parse(value):
        calls.append(1)
        clock[0] = 2.0
        return original(value)
    monkeypatch.setattr(module, "parse_datetime", parse)
    budget = GenerationBudget(max_seconds=1, clock=lambda: clock[0])
    rows = {"events": [{"start": "2020-01-01", "end": "2020-01-02"} for _ in range(2)]}
    with pytest.raises(GenerationLimitError, match="deterministic rule"):
        if validator:
            validate_constraints(rows, temporal_spec(), budget=budget)
        else:
            solve_constraints(rows, temporal_spec(), 1, budget=budget)
    assert len(calls) == 2  # One bounded row, never the remaining 10 parses.


def test_native_amplification_rejected_before_generation(monkeypatch):
    from test_data_agent.generation import entity_generator
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "10")
    def forbidden(*args, **kwargs):
        pytest.fail("row generation preceded rule-work preflight")
    monkeypatch.setattr(entity_generator, "generate_row", forbidden)
    with pytest.raises(InputLimitError, match="estimated evaluations"):
        generate_dataset(temporal_spec(count=3, rows=4), seed=1)


def test_empty_dense_relationship_graph_is_bounded(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "20")
    spec = DatasetSpec(entities=[EntitySpec(name="nodes", row_count=1,
        fields=[FieldSpec(name="id", data_type="integer")])], relationships=[
        Relationship(parent_entity="nodes", parent_field="id", child_entity="nodes",
            child_field="id", confidence=1) for _ in range(5)])
    with pytest.raises(GenerationLimitError, match="evaluations"):
        apply_relationships({"nodes": []}, spec)


def foreign_key_rules() -> BusinessRules:
    return BusinessRules(cross_table_rules=[ForeignKeyRule(type="foreign_key", parent_table="parents",
        parent_field="id", child_table="children", child_field="parent_id")])


def fk_rows(count=4):
    return {"parents": [{"id": i} for i in range(count)],
        "children": [{"parent_id": 0} for _ in range(count)]}


def test_negative_foreign_key_estimate_covers_repeated_parent_scans(monkeypatch):
    rules = foreign_key_rules()
    counts = {"parents": 4, "children": 4}
    valid = estimate_business_rule_evaluations_for_rows(rules, counts)
    negative = estimate_business_rule_evaluations_for_rows(rules, counts, mode="negative")
    assert negative >= 4 * 4 * 4
    assert valid < 50 < negative
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "50")
    rows = fk_rows()
    before = deepcopy(rows)
    with pytest.raises(InputLimitError, match="estimated evaluations"):
        apply_business_rules(rows, rules, seed=1, mode="negative")
    assert rows == before
    apply_business_rules(rows, rules, seed=1)
    assert validate_business_rules(rows, rules).valid


def test_negative_aggregate_estimate_is_quadratic():
    rules = BusinessRules(cross_table_rules=[AggregateFormulaRule(type="aggregate_formula", table="items", field="amount",
        expression="sum('amount')")])
    small = estimate_business_rule_evaluations_for_rows(rules, {"items": 4}, mode="mixed")
    large = estimate_business_rule_evaluations_for_rows(rules, {"items": 8}, mode="mixed")
    assert large > 3 * small


def test_direct_negative_injection_cannot_bypass_cumulative_cap(monkeypatch):
    import random
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "10")
    with pytest.raises(GenerationLimitError, match="evaluations"):
        inject_invalid_cases(fk_rows(8), foreign_key_rules(), random.Random(1), 1)


@pytest.mark.parametrize("entry", ["expression", "validator", "engine"])
def test_aggregate_inner_deadline_is_not_swallowed(entry):
    clock = [0.0]
    calls = []
    class ClockRow(dict):
        def get(self, key, default=None):
            calls.append(1)
            clock[0] = 2.0
            return super().get(key, default)
    rows = [ClockRow(amount=1), ClockRow(amount=2)]
    budget = GenerationBudget(max_seconds=1, clock=lambda: clock[0])
    rules = BusinessRules(cross_table_rules=[AggregateFormulaRule(type="aggregate_formula", table="items", field="amount",
        expression="sum('amount')")])
    with pytest.raises(GenerationLimitError, match="deterministic rule"):
        if entry == "expression":
            safe_eval("sum('amount')", {"rows": rows}, budget=budget)
        elif entry == "validator":
            validate_business_rules({"items": rows}, rules, budget=budget)
        else:
            apply_business_rules({"items": rows}, rules, seed=1, mode="negative", budget=budget)
    assert len(calls) == 1


def test_budget_is_shared_across_successive_public_rule_calls(monkeypatch):
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "6")
    budget = GenerationBudget()
    assert safe_eval("1 + 2", {}, budget=budget) == 3
    with pytest.raises(GenerationLimitError, match="evaluations"):
        safe_eval("1 + 2", {}, budget=budget)


@pytest.mark.parametrize("with_spec", [False, True])
def test_custom_applier_arity_and_optional_budget_remain_compatible(with_spec):
    from test_data_agent.io.workflows import invoke_business_rules_applier
    spec = temporal_spec()
    budget = GenerationBudget()
    received = []
    if with_spec:
        def applier(rows, seed, supplied_spec, *, budget=None):
            received.append((rows, seed, supplied_spec, budget))
    else:
        def applier(rows, seed, *, budget=None):
            received.append((rows, seed, spec, budget))
    invoke_business_rules_applier(applier, {}, 7, spec, budget=budget)
    assert received == [({}, 7, spec, budget)]



def test_condition_membership_charges_actual_predicate_width(monkeypatch):
    from test_data_agent.rules.conditions import Condition, condition_matches
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "5")
    condition = Condition(field="status", in_values=list(range(6)))
    with pytest.raises(GenerationLimitError, match="evaluations"):
        condition_matches({"status": 0}, condition, budget=GenerationBudget())
    assert condition_matches({"status": 0}, condition)
