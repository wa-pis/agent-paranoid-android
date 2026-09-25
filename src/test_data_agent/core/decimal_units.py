"""Exact bounded base-ten units for declared DECIMAL fields."""

from __future__ import annotations

import re
from decimal import Decimal


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
