"""Bounded decoding of generated INSERT artifacts; never execute SQL."""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from test_data_agent.core.limits import (
    enforce_input_row_count,
    enforce_input_cell_count,
    enforce_input_column_count,
    max_input_cell_chars,
)
from test_data_agent.profiling.budget import LocalProfileBudget

_TOKEN = re.compile(
    r"""\s+|"(?:[^"]|"")*"|'(?:[^']|'')*'|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_]+|[(),;]"""
)
_ERROR = "SQL dataset input accepts only generated INSERT statements"


def read_insert_rows(
    text: str,
    entity: str,
    *,
    budget: LocalProfileBudget,
    start_rows: int = 0,
    start_cells: int = 0,
) -> list[dict[str, Any]]:
    def tokens() -> Iterator[str]:
        position = 0
        while position < len(text):
            budget.check_deadline("SQL dataset token")
            match = _TOKEN.match(text, position)
            if match is None:
                raise ValueError(_ERROR)
            position = match.end()
            token = match.group()
            if not token.isspace():
                yield token

    stream = iter(tokens())
    pending = next(stream, None)

    def take() -> str:
        nonlocal pending
        if pending is None:
            raise ValueError(_ERROR)
        token = pending
        pending = next(stream, None)
        return token

    def expect(value: str) -> None:
        if take() != value:
            raise ValueError(_ERROR)

    def identifier() -> str:
        token = take()
        if not token.startswith('"'):
            raise ValueError(_ERROR)
        value = token[1:-1].replace('""', '"')
        if not value or len(value) > max_input_cell_chars():
            raise ValueError(_ERROR)
        return value

    rows: list[dict[str, Any]] = []
    cells = start_cells
    columns: list[str] | None = None
    while pending is not None:
        expect("INSERT")
        expect("INTO")
        if identifier() != entity:
            raise ValueError(_ERROR)
        expect("(")
        names = [identifier()]
        while pending == ",":
            take()
            names.append(identifier())
            enforce_input_column_count(len(names), label="SQL dataset")
        expect(")")
        if len(set(names)) != len(names) or columns is not None and columns != names:
            raise ValueError(_ERROR)
        columns = names
        expect("VALUES")
        expect("(")
        row: dict[str, Any] = {}
        for index, name in enumerate(names):
            if index:
                expect(",")
            token = take()
            if len(token) > 2 * max_input_cell_chars() + 2:
                raise ValueError("SQL dataset cell exceeds limit")
            value: Any
            if token == "NULL":
                value = None
            elif token in {"TRUE", "FALSE"}:
                value = token == "TRUE"
            elif token.startswith("'"):
                value = token[1:-1].replace("''", "'")
            elif token[0] in "+-.0123456789":
                value = token  # Numeric text retains exact decimal digits and scale.
            else:
                raise ValueError(_ERROR)
            if isinstance(value, str) and len(value) > max_input_cell_chars():
                raise ValueError("SQL dataset cell exceeds limit")
            row[name] = value
            cells += 1
            enforce_input_cell_count(cells, label="dataset")
        expect(")")
        expect(";")
        enforce_input_row_count(start_rows + len(rows) + 1, label="dataset")
        rows.append(row)
    return rows
