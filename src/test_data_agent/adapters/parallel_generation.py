"""Explicit process orchestration for the versioned tiled generation engine."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing import TimeoutError, get_context
from multiprocessing.pool import ApplyResult
import signal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import (
    GenerationBudget,
    GenerationLimitError,
    enforce_output_payload_size,
    enforce_row_count_limit,
)
from test_data_agent.core.settings import GenerationMode, MAX_GENERATION_SEED
from test_data_agent.generation.constraint_solver import solve_constraints
from test_data_agent.generation.limits import estimate_dataset_output_bytes, enforce_dataset_rule_work
from test_data_agent.generation.tiled_generator import TILE_ROWS, generate_tile
from test_data_agent.safety import assert_spec_safe
from test_data_agent.validation.reconciliation import assert_generated_dataset_valid


class ParallelGenerationPolicy(BaseModel):
    """Explicit local process and generation bounds; defaults retain row caps."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    engine: Literal["tiled-v1"] = "tiled-v1"
    workers: int = Field(default=1, strict=True, ge=1, le=4)
    max_rows: int | None = Field(default=None, strict=True, ge=1)
    max_cells: int = Field(default=10_000_000, strict=True, ge=1)


class ParallelGenerationError(ValueError):
    """Raised without worker exceptions or generated values crossing the boundary."""


@dataclass(slots=True)
class TileOutcome:
    rows: list[dict[str, Any]] | None = None
    error: Literal["limit", "worker"] | None = None


def _worker_signals() -> None:
    # The coordinator owns cancellation, including during pool startup.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    if hasattr(signal, "pthread_sigmask"):
        signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT})


def _worker_tile(
    spec: DatasetSpec, entity_index: int, start: int, seed: int, max_seconds: float,
) -> TileOutcome:
    try:
        rows = generate_tile(spec, entity_index, start, seed,
                             budget=GenerationBudget(max_seconds=max_seconds))
    except GenerationLimitError:
        return TileOutcome(error="limit")
    except BaseException:
        return TileOutcome(error="worker")
    return TileOutcome(rows=rows)


def _await_tile(result: ApplyResult[TileOutcome], budget: GenerationBudget) -> list[dict[str, Any]]:
    while True:
        budget.check("parallel row generation")
        failed = False
        try:
            outcome = result.get(timeout=0.1)
        except TimeoutError:
            continue
        except Exception:
            failed = True
        if failed:
            raise ParallelGenerationError("parallel generation worker failed")
        if outcome.error == "limit":
            raise GenerationLimitError("parallel generation exceeded a resource budget")
        if outcome.error is not None or outcome.rows is None:
            raise ParallelGenerationError("parallel generation worker failed")
        budget.check("parallel row generation")
        return outcome.rows


def _visit_generated_tiles(
    spec: DatasetSpec,
    seed: int,
    *,
    policy: ParallelGenerationPolicy,
    budget: GenerationBudget,
    consume: Callable[[int, int, list[dict[str, Any]]], None],
) -> None:
    """Visit ordered candidate tiles; consumers validate before external I/O."""
    if type(seed) is not int or not 0 <= seed <= MAX_GENERATION_SEED:
        raise ValueError("seed must be a nonnegative signed 64-bit integer")
    budget.check("parallel generation setup")
    snapshot = spec.model_copy(deep=True)
    if (snapshot.generation_settings.execution_policy is not None
            or snapshot.business_rules is not None or snapshot.relational_scenarios):
        raise ValueError("tiled-v1 requires a specification without execution policy or embedded rules")
    assert_spec_safe(snapshot)
    for entity in snapshot.entities:
        if not entity.fields:
            raise ValueError("parallel generation requires at least one field per entity")
        enforce_row_count_limit(entity.row_count, max_count=policy.max_rows)
    if sum(entity.row_count * len(entity.fields) for entity in snapshot.entities) > policy.max_cells:
        raise GenerationLimitError(f"parallel generation must be <= {policy.max_cells} cells")
    pool = None
    failure: BaseException | None = None
    failed = cleanup_failed = False
    try:
        # Retain a pool reference before a pending SIGINT can interrupt startup.
        mask = (signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
                if hasattr(signal, "pthread_sigmask") else None)
        try:
            pool = get_context("spawn").Pool(processes=policy.workers, initializer=_worker_signals)
        finally:
            if mask is not None:
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        for entity_index, entity in enumerate(snapshot.entities):
            starts = iter(range(0, entity.row_count, TILE_ROWS))
            pending: deque[tuple[int, ApplyResult[TileOutcome]]] = deque()
            while True:
                while len(pending) < policy.workers:
                    start = next(starts, None)
                    if start is None:
                        break
                    budget.check("parallel task submission")
                    result = pool.apply_async(_worker_tile, (
                        snapshot, entity_index, start, seed, budget.max_seconds,
                    ))
                    pending.append((start, result))
                if not pending:
                    break
                start, result = pending.popleft()
                batch = _await_tile(result, budget)
                if len(batch) != min(TILE_ROWS, entity.row_count - start):
                    raise ParallelGenerationError("parallel generation returned an incomplete tile")
                consume_failed = False
                try:
                    consume(entity_index, start, batch)
                except Exception:
                    consume_failed = True
                if consume_failed:
                    raise ParallelGenerationError("parallel generation tile consumer failed")
                budget.check("parallel tile consumption")
    except BaseException as error:
        if (isinstance(error, (GenerationLimitError, ParallelGenerationError))
                or not isinstance(error, Exception)):
            failure = error
        else:
            failed = True
    finally:
        if pool is not None:
            for close in (pool.terminate, pool.join):
                try:
                    close()
                except BaseException as error:
                    cleanup_failed = True
                    if failure is None and not isinstance(error, Exception):
                        failure = error
    if failure is not None:
        raise failure
    if failed or cleanup_failed:
        raise ParallelGenerationError("parallel generation process orchestration or cleanup failed")


def generate_dataset_parallel(
    spec: DatasetSpec,
    seed: int,
    *,
    policy: ParallelGenerationPolicy | None = None,
    budget: GenerationBudget | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Generate ordered rows with tiled-v1 streams, then validate globally.

    Call from an importable module guarded by ``if __name__ == '__main__'``.
    Seeded output is invariant across worker counts, and differs from legacy.
    The returned full dataset still consumes memory proportional to its size.
    """
    if type(seed) is not int or not 0 <= seed <= MAX_GENERATION_SEED:
        raise ValueError("seed must be a nonnegative signed 64-bit integer")
    policy = policy or ParallelGenerationPolicy()
    budget = budget or GenerationBudget()
    budget.check("parallel generation setup")
    snapshot = spec.model_copy(deep=True)
    if snapshot.generation_settings.mode == GenerationMode.LOAD_TEST:
        for entity in snapshot.entities:
            entity.row_count *= snapshot.generation_settings.load_multiplier
        snapshot.generation_settings.load_multiplier = 1
    enforce_output_payload_size(estimate_dataset_output_bytes(snapshot), label="estimated generated data")
    enforce_dataset_rule_work(snapshot, budget=budget)
    rows_by_entity: dict[str, list[dict[str, Any]]] = {
        entity.name: [] for entity in snapshot.entities
    }

    def collect(entity_index: int, start: int, rows: list[dict[str, Any]]) -> None:
        rows_by_entity[snapshot.entities[entity_index].name].extend(rows)

    _visit_generated_tiles(snapshot, seed, policy=policy, budget=budget, consume=collect)
    budget.check("parallel constraint solving")
    solve_constraints(rows_by_entity, snapshot, seed=seed, budget=budget)
    budget.check("parallel constraint solving")
    assert_generated_dataset_valid(rows_by_entity, snapshot, budget=budget)
    budget.check("parallel final validation")
    return rows_by_entity
