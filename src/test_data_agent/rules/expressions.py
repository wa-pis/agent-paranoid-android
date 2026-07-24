"""Safe expression and comparison helpers for rule evaluation."""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable
from datetime import datetime
from typing import Any


BinaryOperator = Callable[[Any, Any], Any]
UnaryOperator = Callable[[Any], Any]
BINARY_OPERATORS: dict[type[ast.operator], BinaryOperator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
UNARY_OPERATORS: dict[type[ast.unaryop], UnaryOperator] = {
    ast.USub: operator.neg,
}
MAX_EXPRESSION_CHARS = 1_024
MAX_EXPRESSION_NODES = 128


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
    return eval_node(parse_safe_expression(expression), row)


def parse_safe_expression(expression: str) -> ast.AST:
    if len(expression) > MAX_EXPRESSION_CHARS:
        raise ValueError(
            f"expression must contain <= {MAX_EXPRESSION_CHARS} characters"
        )
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("expression must be valid arithmetic syntax") from exc
    if sum(1 for _ in ast.walk(parsed)) > MAX_EXPRESSION_NODES:
        raise ValueError(f"expression must contain <= {MAX_EXPRESSION_NODES} nodes")
    validate_expression_node(parsed.body)
    return parsed.body


def validate_expression_node(node: ast.AST) -> None:
    if isinstance(node, (ast.Constant, ast.Name)):
        return
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
        validate_expression_node(node.left)
        validate_expression_node(node.right)
        return
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
        validate_expression_node(node.operand)
        return
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.keywords:
            raise ValueError("expression functions do not accept keyword arguments")
        if node.func.id == "sum" and len(node.args) == 1:
            expect_field_name(node.args[0])
            return
        if node.func.id == "count" and not node.args:
            return
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def expression_references(expression: str) -> tuple[set[str], set[str], set[str]]:
    node = parse_safe_expression(expression)
    names: set[str] = set()
    aggregate_fields: set[str] = set()
    functions: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
            functions.add(child.func.id)
            if child.func.id == "sum":
                aggregate_fields.add(expect_field_name(child.args[0]))
        elif isinstance(child, ast.Name) and child.id not in {"sum", "count"}:
            names.add(child.id)
    return names, aggregate_fields, functions


def expression_complexity(expression: str) -> int:
    return sum(1 for _ in ast.walk(parse_safe_expression(expression)))


def expression_constants(expression: str) -> list[Any]:
    return [
        child.value
        for child in ast.walk(parse_safe_expression(expression))
        if isinstance(child, ast.Constant)
    ]


def eval_node(node: ast.AST, row: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return row.get(node.id)
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
        return BINARY_OPERATORS[type(node.op)](
            eval_node(node.left, row),
            eval_node(node.right, row),
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
        return UNARY_OPERATORS[type(node.op)](eval_node(node.operand, row))
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
