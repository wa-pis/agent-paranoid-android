from __future__ import annotations

import ast
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from test_data_agent.rules import expressions


@pytest.mark.parametrize("formula,row", [
    ('"a" * 1000000000000', {}),
    ('1000000000000 * "a"', {}),
    ('value * count', {"value": "SYNTHETIC_MARKER", "count": 1000000000000}),
    ('value * count', {"value": b"SYNTHETIC_MARKER", "count": 1000000000000}),
])
def test_sequence_expansion_rejects_before_operator(monkeypatch, formula, row):
    def forbidden(*args):
        pytest.fail("unsafe multiplication reached operator")
    monkeypatch.setitem(expressions.BINARY_OPERATORS, ast.Mult, forbidden)
    with pytest.raises(ValueError, match="^expression resource limit exceeded$") as caught:
        expressions.safe_eval(formula, row)
    assert caught.value.__context__ is None
    assert "SYNTHETIC_MARKER" not in str(caught.value)


def test_intermediate_sequences_and_concatenation_are_bounded(monkeypatch):
    monkeypatch.setattr(expressions, "MAX_EXPRESSION_SEQUENCE_LENGTH", 8)
    assert expressions.safe_eval('"abcd" + "efgh"', {}) == "abcdefgh"
    assert expressions.safe_eval('"é" * 8', {}) == "é" * 8
    assert expressions.safe_eval('"a" * -2', {}) == ""
    assert expressions.safe_eval('"a" * 0', {}) == ""
    for formula, row in [('"abc" * 3 * 0', {}), ('"abcd" + "efghi"', {}), ('value', {"value": "x" * 9})]:
        with pytest.raises(ValueError, match="resource limit"):
            expressions.safe_eval(formula, row)


@pytest.mark.parametrize("value", [[], (), bytearray(b"x")])
def test_unmodeled_sequences_are_rejected(value):
    with pytest.raises(ValueError, match="resource limit"):
        expressions.safe_eval("value * 1000000000000", {"value": value})


@pytest.mark.parametrize("left,right,expected", [
    (4, 2, 10), (4.0, 2.0, 10.0),
    (Decimal("4"), Decimal("2"), Decimal("10")),
    (Fraction(4), Fraction(2), Fraction(10)),
])
def test_bounded_numeric_arithmetic_is_preserved(left, right, expected):
    assert expressions.safe_eval("left * right + right", {"left": left, "right": right}) == expected


def test_numeric_width_and_decimal_precision_are_bounded():
    bits = expressions.MAX_EXACT_EXPRESSION_BITS
    with pytest.raises(ValueError, match="resource limit"):
        expressions.safe_eval("value", {"value": 1 << bits})
    with pytest.raises(ValueError, match="resource limit"):
        expressions.safe_eval("value * value", {"value": 1 << (bits - 1)})
    with localcontext() as context:
        context.prec = 1000000
        with pytest.raises(ValueError, match="resource limit"):
            expressions.safe_eval("left / right", {"left": Decimal(1), "right": Decimal(3)})


def test_user_defined_operators_cannot_bypass_limits():
    class Operand:
        def __mul__(self, other):
            pytest.fail("untrusted overloaded operator invoked")
    with pytest.raises(ValueError, match="resource limit"):
        expressions.safe_eval("value * 2", {"value": Operand()})


def test_all_formula_services_reject_before_allocation(monkeypatch):
    from test_data_agent.core.constraint import Constraint, ConstraintType
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.core.entity import EntitySpec
    from test_data_agent.core.field import FieldSpec, FieldType
    from test_data_agent.generation.constraint_solver import apply_formula_constraints
    from test_data_agent.validation.constraint_validator import validate_formula
    from test_data_agent.rules.models import business_rules_from_dict
    from test_data_agent.rules.engine import apply_business_rules
    from test_data_agent.rules.validation import validate_business_rules

    formula = '"SYNTHETIC_MARKER" * 1000000000000'
    def forbidden(*args):
        pytest.fail("unsafe multiplication reached service operator")
    monkeypatch.setitem(expressions.BINARY_OPERATORS, ast.Mult, forbidden)
    constraint = Constraint(type=ConstraintType.FORMULA, entity="orders", fields=["value"],
                            expression=formula, confidence=1.0)
    spec = DatasetSpec(entities=[EntitySpec(name="orders", row_count=1,
                       fields=[FieldSpec(name="value", data_type=FieldType.STRING)])], constraints=[constraint])
    rows = {"orders": [{"value": "synthetic"}]}
    with pytest.raises(ValueError, match="^formula evaluation failed$"):
        apply_formula_constraints(rows, spec)
    assert validate_formula(rows, constraint) == ["formula evaluation failed"]
    rules = business_rules_from_dict({"row_rules": [{"type": "formula", "table": "orders",
                                                   "field": "value", "expression": formula}]})
    with pytest.raises(ValueError, match="^formula evaluation failed$"):
        apply_business_rules(rows, rules, seed=7, mode="valid", invalid_ratio=0.0)
    report = validate_business_rules(rows, rules)
    assert [error for result in report.results for error in result.errors] == ["formula evaluation failed"]
