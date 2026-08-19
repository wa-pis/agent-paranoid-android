"""Typed monotonic work budget for one Trino invocation."""

from __future__ import annotations

import inspect
import json
import os
from collections.abc import Callable, Iterable
from contextvars import ContextVar
from dataclasses import dataclass, replace
from enum import StrEnum
from functools import wraps
from time import monotonic
from typing import Any, ParamSpec, TypeVar

from test_data_agent.trino_config import (
    TrinoDeploymentProfile,
    deployment_profile_from_env,
)

P = ParamSpec("P")
R = TypeVar("R")
MIN_TRANSPORT_RESPONSE_BYTES = 350
MAX_INVOCATION_PROFILED_COLUMNS_ENV = "TRINO_MAX_INVOCATION_PROFILED_COLUMNS"
MAX_INVOCATION_STATEMENTS_ENV = "TRINO_MAX_INVOCATION_STATEMENTS"
MAX_INVOCATION_SECONDS_ENV = "TRINO_MAX_INVOCATION_SECONDS"
MAX_INVOCATION_ESTIMATED_SCAN_BYTES_ENV = (
    "TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES"
)


class QueryWorkDimension(StrEnum):
    RAW_TRANSPORT_PAYLOAD_BYTES = "raw transport payload bytes"
    CANONICAL_ARGUMENT_BYTES = "canonical argument bytes"
    SQL_FORMULA_CHARS = "SQL/formula characters"
    AST_NODES = "AST nodes"
    AST_DEPTH = "AST depth"
    PROJECTED_COLUMNS = "projected columns"
    STATEMENTS = "statements"
    PROFILED_COLUMNS = "profiled columns"
    INVOCATION_SECONDS = "invocation seconds"
    CUMULATIVE_ESTIMATED_SCAN_BYTES = "cumulative estimated scan bytes"
    DATABASE_RESULT_BYTES = "database result bytes"
    TRANSPORT_RESPONSE_BYTES = "transport response bytes"


class QueryWorkBudgetExceeded(ValueError):
    """Raised before an invocation can exceed a configured work limit."""

    def __init__(
        self,
        *,
        dimension: QueryWorkDimension,
        attempted: int | float,
        limit: int | float,
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
    database_result_bytes: int
    transport_response_bytes: int
    max_profiled_columns: int = 100
    max_invocation_seconds: float = 120.0
    max_cumulative_estimated_scan_bytes: int | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("raw_transport_payload_bytes", self.raw_transport_payload_bytes),
            ("canonical_argument_bytes", self.canonical_argument_bytes),
            ("sql_formula_chars", self.sql_formula_chars),
            ("ast_nodes", self.ast_nodes),
            ("ast_depth", self.ast_depth),
            ("projected_columns", self.projected_columns),
            ("statements", self.statements),
            ("max_profiled_columns", self.max_profiled_columns),
            ("max_invocation_seconds", self.max_invocation_seconds),
            ("database_result_bytes", self.database_result_bytes),
            ("transport_response_bytes", self.transport_response_bytes),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if (
            self.max_cumulative_estimated_scan_bytes is not None
            and self.max_cumulative_estimated_scan_bytes <= 0
        ):
            raise ValueError(
                "max_cumulative_estimated_scan_bytes must be positive when set"
            )
        if self.transport_response_bytes < MIN_TRANSPORT_RESPONSE_BYTES:
            raise ValueError(
                "transport_response_bytes must be at least "
                f"{MIN_TRANSPORT_RESPONSE_BYTES}"
            )


DEFAULT_QUERY_WORK_LIMITS = QueryWorkLimits(
    raw_transport_payload_bytes=1024 * 1024,
    canonical_argument_bytes=256 * 1024,
    sql_formula_chars=100_000,
    ast_nodes=10_000,
    ast_depth=100,
    projected_columns=1_000,
    statements=150,
    max_profiled_columns=100,
    max_invocation_seconds=120.0,
    max_cumulative_estimated_scan_bytes=None,
    database_result_bytes=4 * 1024 * 1024,
    transport_response_bytes=4 * 1024 * 1024,
)


def query_work_limits_from_env(
    *, deployment_profile: TrinoDeploymentProfile | None = None
) -> QueryWorkLimits:
    """Load cumulative Trino invocation limits for one deployment profile."""
    profile = deployment_profile or deployment_profile_from_env()
    cumulative_scan_bytes = _optional_positive_int_env(
        MAX_INVOCATION_ESTIMATED_SCAN_BYTES_ENV
    )
    if (
        profile is TrinoDeploymentProfile.SHARED_HARDENED
        and cumulative_scan_bytes is None
    ):
        raise ValueError(
            "shared-hardened deployment requires a finite "
            f"{MAX_INVOCATION_ESTIMATED_SCAN_BYTES_ENV}"
        )
    return replace(
        DEFAULT_QUERY_WORK_LIMITS,
        max_profiled_columns=_positive_int_env(
            MAX_INVOCATION_PROFILED_COLUMNS_ENV,
            DEFAULT_QUERY_WORK_LIMITS.max_profiled_columns,
        ),
        statements=_positive_int_env(
            MAX_INVOCATION_STATEMENTS_ENV,
            DEFAULT_QUERY_WORK_LIMITS.statements,
        ),
        max_invocation_seconds=_positive_float_env(
            MAX_INVOCATION_SECONDS_ENV,
            DEFAULT_QUERY_WORK_LIMITS.max_invocation_seconds,
        ),
        max_cumulative_estimated_scan_bytes=cumulative_scan_bytes,
    )


def _positive_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _optional_positive_int_env(name: str) -> int | None:
    if name not in os.environ:
        return None
    return _positive_int_env(name, 1)


def _positive_float_env(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not value > 0 or value == float("inf"):
        raise ValueError(f"{name} must be a finite positive number")
    return value


@dataclass(frozen=True, slots=True)
class QueryWorkSnapshot:
    raw_transport_payload_bytes: int
    canonical_argument_bytes: int
    sql_formula_chars: int
    ast_nodes: int
    ast_depth: int
    projected_columns: int
    statements: int
    database_result_bytes: int
    transport_response_bytes: int
    profiled_columns: int = 0
    cumulative_estimated_scan_bytes: int = 0
    terminal_error_bytes: int = 0


class QueryWorkBudget:
    """Track work monotonically without exposing a reset operation."""

    __slots__ = (
        "_ast_depth",
        "_ast_nodes",
        "_canonical_argument_bytes",
        "_cumulative_estimated_scan_bytes",
        "_database_result_bytes",
        "_limits",
        "_monotonic_clock",
        "_profiled_columns",
        "_projected_columns",
        "_raw_transport_payload_bytes",
        "_sql_formula_chars",
        "_started_at",
        "_statements",
        "_terminal_error_bytes",
        "_transport_response_bytes",
    )

    def __init__(
        self,
        limits: QueryWorkLimits,
        *,
        monotonic_clock: Callable[[], float] = monotonic,
    ) -> None:
        self._limits = limits
        self._monotonic_clock = monotonic_clock
        self._started_at = monotonic_clock()
        self._raw_transport_payload_bytes = 0
        self._canonical_argument_bytes = 0
        self._sql_formula_chars = 0
        self._ast_nodes = 0
        self._ast_depth = 0
        self._projected_columns = 0
        self._statements = 0
        self._profiled_columns = 0
        self._cumulative_estimated_scan_bytes = 0
        self._database_result_bytes = 0
        self._terminal_error_bytes = 0
        self._transport_response_bytes = 0

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
            profiled_columns=self._profiled_columns,
            cumulative_estimated_scan_bytes=self._cumulative_estimated_scan_bytes,
            database_result_bytes=self._database_result_bytes,
            transport_response_bytes=self._transport_response_bytes,
            terminal_error_bytes=self._terminal_error_bytes,
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

    def consume_profiled_columns(self, amount: int = 1) -> None:
        self._profiled_columns = self._consume(
            QueryWorkDimension.PROFILED_COLUMNS,
            current=self._profiled_columns,
            amount=amount,
            limit=self._limits.max_profiled_columns,
        )

    def consume_cumulative_estimated_scan_bytes(self, amount: int) -> None:
        self._cumulative_estimated_scan_bytes = self._consume_optional(
            QueryWorkDimension.CUMULATIVE_ESTIMATED_SCAN_BYTES,
            current=self._cumulative_estimated_scan_bytes,
            amount=amount,
            limit=self._limits.max_cumulative_estimated_scan_bytes,
        )

    def elapsed_invocation_seconds(self) -> float:
        return max(0.0, self._monotonic_clock() - self._started_at)

    def remaining_invocation_seconds(self) -> float:
        elapsed = self.elapsed_invocation_seconds()
        remaining = self._limits.max_invocation_seconds - elapsed
        if remaining <= 0:
            raise QueryWorkBudgetExceeded(
                dimension=QueryWorkDimension.INVOCATION_SECONDS,
                attempted=elapsed,
                limit=self._limits.max_invocation_seconds,
            )
        return remaining

    def check_invocation_deadline(self) -> None:
        self.remaining_invocation_seconds()

    def consume_database_result_bytes(self, amount: int) -> None:
        self._database_result_bytes = self._consume(
            QueryWorkDimension.DATABASE_RESULT_BYTES,
            current=self._database_result_bytes,
            amount=amount,
            limit=self._limits.database_result_bytes,
        )

    def consume_transport_response_bytes(self, amount: int) -> None:
        normal_limit = (
            self._limits.transport_response_bytes - MIN_TRANSPORT_RESPONSE_BYTES
        )
        normal_current = self._transport_response_bytes - self._terminal_error_bytes
        normal_total = self._consume(
            QueryWorkDimension.TRANSPORT_RESPONSE_BYTES,
            current=normal_current,
            amount=amount,
            limit=normal_limit,
        )
        self._transport_response_bytes = normal_total + self._terminal_error_bytes

    def consume_terminal_error_bytes(self, amount: int) -> None:
        """Consume only the fixed allowance reserved for a bounded error."""
        terminal_total = self._consume(
            QueryWorkDimension.TRANSPORT_RESPONSE_BYTES,
            current=self._terminal_error_bytes,
            amount=amount,
            limit=MIN_TRANSPORT_RESPONSE_BYTES,
        )
        response_total = self._consume(
            QueryWorkDimension.TRANSPORT_RESPONSE_BYTES,
            current=self._transport_response_bytes,
            amount=amount,
            limit=self._limits.transport_response_bytes,
        )
        self._terminal_error_bytes = terminal_total
        self._transport_response_bytes = response_total

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

    @classmethod
    def _consume_optional(
        cls,
        dimension: QueryWorkDimension,
        *,
        current: int,
        amount: int,
        limit: int | None,
    ) -> int:
        cls._validate_non_negative(dimension, amount)
        attempted = current + amount
        if limit is not None and attempted > limit:
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


def consume_profiled_column_work(amount: int = 1) -> None:
    """Charge nested column operations to the current invocation."""
    budget = current_query_work_budget()
    if budget is not None:
        budget.check_invocation_deadline()
        budget.consume_profiled_columns(amount)


def consume_sql_formula_chars(value: str) -> None:
    """Charge text work to the current invocation before parsing or I/O."""
    budget = current_query_work_budget()
    if budget is not None:
        budget.consume_sql_formula_chars(len(value))


def consume_ast_work(
    root: Any,
    *,
    child_nodes: Callable[[Any], Iterable[Any]],
) -> None:
    """Charge one parsed tree iteratively before downstream work can use it."""
    budget = current_query_work_budget()
    if budget is None:
        return

    pending = [(root, 1)]
    while pending:
        node, depth = pending.pop()
        budget.consume_ast_nodes(1)
        budget.observe_ast_depth(depth)
        pending.extend((child, depth + 1) for child in child_nodes(node))


def consume_database_result_payload(value: Any) -> None:
    """Charge one database-result fragment before the client retains it."""
    budget = current_query_work_budget()
    if budget is None:
        return

    payload = json.dumps(
        value,
        default=str,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    budget.consume_database_result_bytes(len(payload))


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
        budget = current_query_work_budget()
        if budget is None and budget_provider is not None:
            budget = budget_provider()
        if budget is None:
            budget = QueryWorkBudget(limits)
        elif budget.limits != limits:
            raise ValueError("transport and application work limits must match")
        token = _CURRENT_QUERY_WORK_BUDGET.set(budget)
        try:
            budget.check_invocation_deadline()
            budget.consume_canonical_argument_bytes(
                canonical_argument_size(function, *args, **kwargs)
            )
            return function(*args, **kwargs)
        finally:
            _CURRENT_QUERY_WORK_BUDGET.reset(token)

    return wrapper
