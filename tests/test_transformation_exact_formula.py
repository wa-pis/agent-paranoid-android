from decimal import Decimal, localcontext

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.rules import expressions


@pytest.mark.parametrize("formula, expected", [
    ("amount + 0.005", "1.01"),
    ("-(amount + 0.005)", "-1.01"),
    ("amount / 3 * 3", "1.00"),
    ("amount + 0.0049999999999999999999999999999999999", "1.00"),
])
def test_exact_formula_rounds_only_final_result(formula, expected):
    with localcontext() as context:
        context.prec = 2
        result = expressions.eval_exact_decimal(formula, {"amount": Decimal("1")},
            precision=38, scale=2, budget=GenerationBudget())
    assert str(result) == expected


@pytest.mark.parametrize("formula, row", [
    ("amount / 0", {"amount": Decimal("1")}),
    ("amount + 1", {"amount": 0.1}),
    ("amount + 1", {"amount": True}),
    ("missing + 1", {}), ("sum('amount')", {}),
    ("1e99999999", {}), ("'fictional-private'", {}),
    ("amount * amount", {"amount": 2**10000}),
    ("99.995", {}),
])
def test_exact_formula_rejects_invalid_inputs_without_values(formula, row):
    with pytest.raises(ValueError) as caught:
        expressions.eval_exact_decimal(formula, row, precision=4, scale=2,
                                       budget=GenerationBudget())
    assert str(caught.value) == "invalid exact decimal expression"
    assert caught.value.__context__ is None
