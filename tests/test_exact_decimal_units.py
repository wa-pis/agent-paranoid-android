"""Fictional exact-decimal bounds; no source data or publication."""

from decimal import localcontext
from random import Random

import pytest

from test_data_agent.core.decimal_units import (
    ExactDecimalError, decimal_from_units, decimal_to_units, sample_decimal,
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


def test_decimal_sampling_is_seeded_and_exact():
    options = [
        sample_decimal(Random(seed), low="-0.02", high="0.02", precision=20, scale=2)
        for seed in range(8)
    ]
    assert [str(value) for value in options] == [
        "0.01", "-0.01", "-0.02", "-0.01", "-0.01", "0.02", "0.02", "0.00",
    ]
    assert all(-2 <= decimal_to_units(format(value, "f"), precision=20, scale=2) <= 2 for value in options)
    assert all(value.as_tuple().exponent == -2 for value in options)


def test_decimal_sampling_uses_all_38_digits_without_float():
    maximum = "9" * 22 + "." + "9" * 16
    value = sample_decimal(Random(17), low=maximum, high=maximum, precision=38, scale=16)
    assert format(value, "f") == maximum


def test_decimal_sampling_rejects_reversed_or_inexact_bounds_without_echoing_values():
    for low, high in [("1.01", "1.00"), ("1.001", "2.00")]:
        with pytest.raises(ExactDecimalError) as error:
            sample_decimal(Random(1), low=low, high=high, precision=20, scale=2)
        assert low not in str(error.value)
        assert high not in str(error.value)
