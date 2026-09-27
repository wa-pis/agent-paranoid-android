"""Exact bounded base-ten units for declared DECIMAL fields."""

from __future__ import annotations

import re
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP
from random import Random
from typing import Any


MAX_DECIMAL_DIGITS = 38  # Arrow decimal128; decimal256 is outside this RC.
_DECIMAL_TEXT = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z", re.ASCII)


class ExactDecimalError(ValueError):
    """Value-free invalid exact-decimal input."""


def _check_shape(precision: int, scale: int) -> None:
    if (
        type(precision) is not int or not 1 <= precision <= MAX_DECIMAL_DIGITS
        or type(scale) is not int or not 0 <= scale <= precision
    ):
        raise ExactDecimalError("invalid decimal precision or scale")


def decimal_to_units(value: str, *, precision: int, scale: int) -> int:
    """Parse plain decimal text without float conversion or rounding."""
    _check_shape(precision, scale)
    if type(value) is not str or len(value) > MAX_DECIMAL_DIGITS + 2 or not _DECIMAL_TEXT.fullmatch(value):
        raise ExactDecimalError("invalid decimal value")
    negative = value.startswith("-")
    whole, _, fractional = value.lstrip("-").partition(".")
    if len(fractional) > scale:
        raise ExactDecimalError("invalid decimal value")
    units: int = int(whole) * 10**scale + int(fractional.ljust(scale, "0") or "0")
    if units >= 10**precision:
        raise ExactDecimalError("invalid decimal value")
    return -units if negative else units


def decimal_from_units(units: int, *, precision: int, scale: int) -> Decimal:
    """Construct Decimal exactly, regardless of ambient decimal context."""
    _check_shape(precision, scale)
    if type(units) is not int or abs(units) >= 10**precision:
        raise ExactDecimalError("invalid decimal value")
    digits = tuple(int(character) for character in str(abs(units)))
    return Decimal((int(units < 0), digits, -scale))


def round_decimal_result(value: Decimal, *, precision: int, scale: int) -> Decimal:
    """Round an exact formula result HALF_UP; reject declared-width overflow."""
    _check_shape(precision, scale)
    if type(value) is not Decimal or not value.is_finite():
        raise ExactDecimalError("invalid decimal formula result")
    try:
        rounded = value.quantize(Decimal((0, (1,), -scale)),
                                 context=Context(prec=MAX_DECIMAL_DIGITS, rounding=ROUND_HALF_UP))
        units = decimal_to_units(format(rounded, "f"), precision=precision, scale=scale)
        return decimal_from_units(units, precision=precision, scale=scale)
    except (DecimalException, ExactDecimalError):
        pass
    raise ExactDecimalError("invalid decimal formula result") from None


def sample_decimal(
    rng: Random, *, low: str, high: str, precision: int, scale: int,
) -> Decimal:
    """Generate an exact synthetic value from explicit inclusive text bounds."""
    low_units = decimal_to_units(low, precision=precision, scale=scale)
    high_units = decimal_to_units(high, precision=precision, scale=scale)
    if low_units > high_units:
        raise ExactDecimalError("invalid decimal range")
    return decimal_from_units(
        rng.randrange(low_units, high_units + 1), precision=precision, scale=scale,
    )


def value_matches_decimal(
    value: Any, *, precision: int, scale: int, low: str | None = None, high: str | None = None,
) -> bool:
    if isinstance(value, Decimal):
        text = format(value, "f")
    elif isinstance(value, str):
        text = value
    else:
        return False
    try:
        units = decimal_to_units(text, precision=precision, scale=scale)
        if low is not None and units < decimal_to_units(low, precision=precision, scale=scale):
            return False
        if high is not None and units > decimal_to_units(high, precision=precision, scale=scale):
            return False
    except ExactDecimalError:
        return False
    return True
