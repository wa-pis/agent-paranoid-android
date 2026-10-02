from decimal import Decimal, Inexact, localcontext

import pytest

from test_data_agent.core import decimal_units


@pytest.mark.parametrize("value, expected", [
    ("1.005", "1.01"), ("-1.005", "-1.01"),
    ("1.004", "1.00"), ("0", "0.00"), ("99.994", "99.99"),
])
def test_formula_rounding_is_half_up_and_context_independent(value, expected):
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        result = decimal_units.round_decimal_result(Decimal(value), precision=4, scale=2)
    assert str(result) == expected


@pytest.mark.parametrize("value", [Decimal("99.995"), Decimal("NaN"),
    Decimal("Infinity"), Decimal("1e100000"), 1.005, "1.005"])
def test_formula_rounding_rejects_overflow_and_non_decimal(value):
    with pytest.raises(decimal_units.ExactDecimalError):
        decimal_units.round_decimal_result(value, precision=4, scale=2)


def test_formula_rounding_preserves_decimal38_low_digits():
    value = Decimal("1234567890123456789012.12345678901234565")
    assert str(decimal_units.round_decimal_result(value, precision=38, scale=16)) == (
        "1234567890123456789012.1234567890123457")


@pytest.mark.parametrize("precision,scale", [(True, 0), (0, 0), (39, 2), (3, 4), (3, -1)])
def test_formula_rounding_validates_declared_shape(precision, scale):
    with pytest.raises(decimal_units.ExactDecimalError):
        decimal_units.round_decimal_result(Decimal("1"), precision=precision, scale=scale)
