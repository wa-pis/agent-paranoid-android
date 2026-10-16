"""Reversible synthetic CSV scalar encoding, declared in the bundle manifest."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from test_data_agent.core.decimal_units import MAX_DECIMAL_DIGITS

CSV_ENCODING: Literal["backslash-null-v1"] = "backslash-null-v1"


def is_formula_cell(value: str) -> bool:
    stripped = value.lstrip(" \t\r\n")
    return bool(value) and (
        value[0] in "\t\r\n" or bool(stripped) and stripped[0] in "=+-@"
    )


def encode_csv_cell(value: Any) -> Any:
    if value is None:
        return r"\N"
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("invalid exact decimal CSV value")
        sign, digits, exponent = value.as_tuple()
        assert isinstance(exponent, int)
        digit_count = len(digits)
        fixed_length = sign + (
            digit_count + exponent if exponent >= 0
            else digit_count + 1 if digit_count + exponent > 0
            else 2 - exponent
        )
        if fixed_length > MAX_DECIMAL_DIGITS + 3:
            raise ValueError("exact decimal CSV value exceeds bounded width")
        # Exact DECIMAL revalidation accepts plain decimal text, including tiny units.
        return format(value, "f")
    if isinstance(value, str):
        if value.startswith("\\"):
            return "\\" + value
        if is_formula_cell(value):
            return r"\F" + value
    return value


def decode_csv_cell(value: str | None) -> str | None:
    if value == r"\N":
        return None
    if value is not None:
        if value.startswith("\\\\"):
            return value[1:]
        if value.startswith(r"\F"):
            return value[2:]
    return value
