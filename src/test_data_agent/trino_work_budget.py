"""Typed monotonic work budget for one Trino invocation."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum
from functools import wraps
from typing import Any, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


class QueryWorkDimension(StrEnum):
    RAW_TRANSPORT_PAYLOAD_BYTES = "raw transport payload bytes"
    CANONICAL_ARGUMENT_BYTES = "canonical argument bytes"
    SQL_FORMULA_CHARS = "SQL/formula characters"
    AST_NODES = "AST nodes"
    AST_DEPTH = "AST depth"
    PROJECTED_COLUMNS = "projected columns"
    STATEMENTS = "statements"
    RESPONSE_BYTES = "response bytes"


class QueryWorkBudgetExceeded(ValueError):
    """Raised before an invocation can exceed a configured work limit."""

    def __init__(
        self,
        *,
        dimension: QueryWorkDimension,
        attempted: int,
        limit: int,
    ) -> None:
        self.dimension = dimension
        self.attempted = attempted
        self.limit = limit
        super().__init__(
            f"query work budget exceeded for {dimension.value}: "
            f"attempted {attempted}, limit {limit}"
        )


@dataclass(frozen=True, slots=True)
class QueryWorkLimits:
    raw_transport_payload_bytes: int
    canonical_argument_bytes: int
    sql_formula_chars: int
    ast_nodes: int
    ast_depth: int
    projected_columns: int
    statements: int
    response_bytes: int

    def __post_init__(self) -> None:
        for name, value in (
            ("raw_transport_payload_bytes", self.raw_transport_payload_bytes),
            ("canonical_argument_bytes", self.canonical_argument_bytes),
            ("sql_formula_chars", self.sql_formula_chars),
            ("ast_nodes", self.ast_nodes),
            ("ast_depth", self.ast_depth),
            ("projected_columns", self.projected_columns),
            ("statements", self.statements),
            ("response_bytes", self.response_bytes),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")


DEFAULT_QUERY_WORK_LIMITS = QueryWorkLimits(
    raw_transport_payload_bytes=1024 * 1024,
    canonical_argument_bytes=256 * 1024,
    sql_formula_chars=100_000,
    ast_nodes=10_000,
    ast_depth=100,
    projected_columns=1_000,
    statements=2_048,
    response_bytes=4 * 1024 * 1024,
)


@dataclass(frozen=True, slots=True)
class QueryWorkSnapshot:
    raw_transport_payload_bytes: int
    canonical_argument_bytes: int
    sql_formula_chars: int
    ast_nodes: int
    ast_depth: int
    projected_columns: int
    statements: int
    response_bytes: int


class QueryWorkBudget:
    """Track work monotonically without exposing a reset operation."""

    __slots__ = (
        "_ast_depth",
        "_ast_nodes",
        "_canonical_argument_bytes",
        "_limits",
        "_projected_columns",
        "_raw_transport_payload_bytes",
        "_response_bytes",
        "_sql_formula_chars",
        "_statements",
    )

    def __init__(self, limits: QueryWorkLimits) -> None:
        self._limits = limits
        self._raw_transport_payload_bytes = 0
        self._canonical_argument_bytes = 0
        self._sql_formula_chars = 0
        self._ast_nodes = 0
        self._ast_depth = 0
        self._projected_columns = 0
        self._statements = 0
        self._response_bytes = 0

    @property
    def limits(self) -> QueryWorkLimits:
        return self._limits

    def snapshot(self) -> QueryWorkSnapshot:
        return QueryWorkSnapshot(
            raw_transport_payload_bytes=self._raw_transport_payload_bytes,
            canonical_argument_bytes=self._canonical_argument_bytes,
            sql_formula_chars=self._sql_formula_chars,
            ast_nodes=self._ast_nodes,
            ast_depth=self._ast_depth,
            projected_columns=self._projected_columns,
            statements=self._statements,
            response_bytes=self._response_bytes,
        )

    def consume_raw_transport_payload_bytes(self, amount: int) -> None:
        self._raw_transport_payload_bytes = self._consume(
            QueryWorkDimension.RAW_TRANSPORT_PAYLOAD_BYTES,
            current=self._raw_transport_payload_bytes,
            amount=amount,
            limit=self._limits.raw_transport_payload_bytes,
        )

    def consume_canonical_argument_bytes(self, amount: int) -> None:
        self._canonical_argument_bytes = self._consume(
            QueryWorkDimension.CANONICAL_ARGUMENT_BYTES,
            current=self._canonical_argument_bytes,
            amount=amount,
            limit=self._limits.canonical_argument_bytes,
        )

    def consume_sql_formula_chars(self, amount: int) -> None:
        self._sql_formula_chars = self._consume(
            QueryWorkDimension.SQL_FORMULA_CHARS,
            current=self._sql_formula_chars,
            amount=amount,
            limit=self._limits.sql_formula_chars,
        )

    def consume_ast_nodes(self, amount: int) -> None:
        self._ast_nodes = self._consume(
            QueryWorkDimension.AST_NODES,
            current=self._ast_nodes,
            amount=amount,
            limit=self._limits.ast_nodes,
        )

    def observe_ast_depth(self, depth: int) -> None:
        self._validate_non_negative(QueryWorkDimension.AST_DEPTH, depth)
        if depth > self._limits.ast_depth:
            raise QueryWorkBudgetExceeded(
                dimension=QueryWorkDimension.AST_DEPTH,
                attempted=depth,
                limit=self._limits.ast_depth,
            )
        self._ast_depth = max(self._ast_depth, depth)

    def consume_projected_columns(self, amount: int) -> None:
        self._projected_columns = self._consume(
            QueryWorkDimension.PROJECTED_COLUMNS,
            current=self._projected_columns,
            amount=amount,
            limit=self._limits.projected_columns,
        )

    def consume_statements(self, amount: int = 1) -> None:
        self._statements = self._consume(
            QueryWorkDimension.STATEMENTS,
            current=self._statements,
            amount=amount,
            limit=self._limits.statements,
        )

    def consume_response_bytes(self, amount: int) -> None:
        self._response_bytes = self._consume(
            QueryWorkDimension.RESPONSE_BYTES,
            current=self._response_bytes,
            amount=amount,
            limit=self._limits.response_bytes,
        )

    @classmethod
    def _consume(
        cls,
        dimension: QueryWorkDimension,
        *,
        current: int,
        amount: int,
        limit: int,
    ) -> int:
        cls._validate_non_negative(dimension, amount)
        attempted = current + amount
        if attempted > limit:
            raise QueryWorkBudgetExceeded(
                dimension=dimension,
                attempted=attempted,
                limit=limit,
            )
        return attempted

    @staticmethod
    def _validate_non_negative(
        dimension: QueryWorkDimension,
        amount: int,
    ) -> None:
        if amount < 0:
            raise ValueError(f"{dimension.value} must be non-negative")


_CURRENT_QUERY_WORK_BUDGET: ContextVar[QueryWorkBudget | None] = ContextVar(
    "current_query_work_budget",
    default=None,
)


def current_query_work_budget() -> QueryWorkBudget | None:
    """Return the budget shared by the current invocation, when present."""
    return _CURRENT_QUERY_WORK_BUDGET.get()


def canonical_argument_size(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> int:
    """Return the stable UTF-8 JSON size of validated application arguments."""
    bound = inspect.signature(function).bind(*args, **kwargs)
    bound.apply_defaults()
    payload = json.dumps(
        dict(bound.arguments),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return len(payload)


def with_query_work_budget(
    function: Callable[P, R],
    limits: QueryWorkLimits,
    *,
    budget_provider: Callable[[], QueryWorkBudget | None] | None = None,
) -> Callable[P, R]:
    """Create and isolate one work budget around an application invocation."""

    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        budget = budget_provider() if budget_provider is not None else None
        if budget is None:
            budget = QueryWorkBudget(limits)
        elif budget.limits != limits:
            raise ValueError("transport and application work limits must match")
        token = _CURRENT_QUERY_WORK_BUDGET.set(budget)
        try:
            budget.consume_canonical_argument_bytes(
                canonical_argument_size(function, *args, **kwargs)
            )
            return function(*args, **kwargs)
        finally:
            _CURRENT_QUERY_WORK_BUDGET.reset(token)

    return wrapper
