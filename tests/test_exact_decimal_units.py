"""Fictional exact-decimal bounds; no source data or publication."""

from decimal import localcontext

import pytest

from test_data_agent.core.decimal_units import (
    ExactDecimalError, decimal_from_units, decimal_to_units,
)


@pytest.mark.parametrize(("value", "precision", "scale"), [
    ("9007199254740993.25", 20, 2),
    ("-9007199254740993.1234567890123456", 38, 16),
    ("0", 38, 16),
])
def test_decimal_round_trip_ignores_binary_float_and_context(value, precision, scale):
    units = decimal_to_units(value, precision=precision, scale=scale)
    with localcontext() as context:
        context.prec = 4
        exact = decimal_from_units(units, precision=precision, scale=scale)
    assert format(exact, "f") == f"{value.split('.')[0]}.{value.split('.')[1] if '.' in value else '0' * scale}"
    assert decimal_to_units(format(exact, "f"), precision=precision, scale=scale) == units


@pytest.mark.parametrize("value", [
    "1000000000000000000.00", "1.234", "NaN", "Infinity", "1e2", "+1.00", " 1.00",
])
def test_decimal_rejects_overflow_rounding_and_noncanonical_text(value):
    with pytest.raises(ExactDecimalError, match="^invalid decimal value$") as error:
        decimal_to_units(value, precision=20, scale=2)
    assert value not in str(error.value)
    assert error.value.__context__ is None


def test_decimal_rejects_invalid_shape_and_output_overflow():
    with pytest.raises(ExactDecimalError, match="precision or scale"):
        decimal_to_units("1", precision=39, scale=16)
    with pytest.raises(ExactDecimalError, match="precision or scale"):
        decimal_to_units("1", precision=38, scale=39)
    with pytest.raises(ExactDecimalError, match="^invalid decimal value$"):
        decimal_from_units(10**38, precision=38, scale=16)


def test_decimal_38_digit_boundary():
    value = "9" * 22 + "." + "9" * 16
    units = decimal_to_units(value, precision=38, scale=16)
    assert units == 10**38 - 1
    assert format(decimal_from_units(units, precision=38, scale=16), "f") == value
