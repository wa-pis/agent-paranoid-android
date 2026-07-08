"""Safe expression and comparison helpers for rule evaluation."""

from __future__ import annotations

import ast
import operator
from datetime import datetime
from typing import Any


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def comparable_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def numbers_close(actual: Any, expected: Any, tolerance: float) -> bool:
    actual_number = comparable_number(actual)
    expected_number = comparable_number(expected)
    return actual_number is not None and expected_number is not None and abs(actual_number - expected_number) <= tolerance


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def aggregate(field: str, rows: list[dict[str, Any]]) -> float:
    if field == "*":
        return float(len(rows))
    return sum(comparable_number(row.get(field)) or 0.0 for row in rows)


def safe_eval(expression: str, row: dict[str, Any]) -> Any:
    node = ast.parse(expression, mode="eval")
    return eval_node(node.body, row)


def eval_node(node: ast.AST, row: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return row.get(node.id)
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_node(node.left, row), eval_node(node.right, row))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_node(node.operand, row))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "sum":
            field = expect_field_name(node.args[0])
            return aggregate(field, row.get("rows", []))
        if node.func.id == "count":
            return float(len(row.get("rows", [])))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def expect_field_name(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise ValueError("aggregate field name must be a string literal")
