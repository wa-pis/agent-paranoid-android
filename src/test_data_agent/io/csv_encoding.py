"""Reversible synthetic CSV scalar encoding, declared in the bundle manifest."""

from __future__ import annotations

from typing import Any, Literal

CSV_ENCODING: Literal["backslash-null-v1"] = "backslash-null-v1"


def is_formula_cell(value: str) -> bool:
    stripped = value.lstrip(" \t\r\n")
    return bool(value) and (
        value[0] in "\t\r\n" or bool(stripped) and stripped[0] in "=+-@"
    )


def encode_csv_cell(value: Any) -> Any:
    if value is None:
        return r"\N"
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
