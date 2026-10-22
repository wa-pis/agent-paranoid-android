"""Constraint validation for generated datasets."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from test_data_agent.core.constraint import ConstraintStatus, ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.generation.limits import enforce_dataset_rule_work
from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.rules.conditions import Condition, condition_matches
from test_data_agent.rules.expressions import parse_datetime, safe_eval, numbers_close
from test_data_agent.rules.typed_values import formula_value, numeric_row, aggregate_mapping_values


class TemporalMetrics(BaseModel):
    entity: str
    start_field: str
    end_field: str
    checked_rows: int = Field(ge=0)
    failed_rows: int = Field(ge=0)


def validate_constraints(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    spec: DatasetSpec,
    *,
    budget: GenerationBudget | None = None,
    temporal_metrics: list[TemporalMetrics] | None = None,
) -> list[str]:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    enforce_dataset_rule_work(spec, budget=budget,
        row_counts={name: len(rows) for name, rows in rows_by_entity.items()})
    errors: list[str] = []
    for constraint in budget.iter_rule_work(spec.constraints):
        if constraint.status == ConstraintStatus.REJECTED:
            continue
        if constraint.type == ConstraintType.FORMULA:
            errors.extend(validate_formula(rows_by_entity, constraint, budget=budget, spec=spec))
        elif constraint.type == ConstraintType.TEMPORAL:
            errors.extend(validate_temporal(rows_by_entity, constraint, budget=budget, metrics=temporal_metrics))
        elif constraint.type == ConstraintType.CONDITIONAL_REQUIRED:
            errors.extend(validate_conditional_required(rows_by_entity, constraint, budget=budget, spec=spec))
        elif constraint.type == ConstraintType.AGGREGATE_MAPPING:
            errors.extend(validate_aggregate_mapping(rows_by_entity, spec, constraint, budget=budget))
    return errors


def validate_formula(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    constraint: Any,
    *,
    budget: GenerationBudget | None = None,
    spec: DatasetSpec | None = None,
) -> list[str]:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    if not constraint.expression or not constraint.fields:
        return []
    target = constraint.fields[0]
    errors: list[str] = []
    for index, row in budget.iter_rule_work(enumerate(rows_by_entity.get(constraint.entity, []))):
        try:
            expected = (
                formula_value(constraint.expression, numeric_row(row, spec.entity(constraint.entity), budget=budget),
                              spec.entity(constraint.entity).field(target), budget=budget)
                if spec is not None else safe_eval(constraint.expression, coerce_numeric_row(row, budget=budget), budget=budget)
            )
        except GenerationLimitError:
            raise
        except Exception:
            errors.append("formula evaluation failed")
            continue
        actual = row.get(target)
        if not numbers_close(actual, expected, 0 if spec is not None and spec.entity(constraint.entity).field(target).data_type == "decimal" else 0.000001):
            errors.append("formula mismatch")
    return errors


def validate_temporal(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    constraint: Any,
    *,
    budget: GenerationBudget | None = None,
    metrics: list[TemporalMetrics] | None = None,
) -> list[str]:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    if len(constraint.fields) < 2:
        return []
    start_field, end_field = constraint.fields[:2]
    errors: list[str] = []
    checked_rows = 0
    for index, row in budget.iter_rule_work(enumerate(rows_by_entity.get(constraint.entity, []))):
        checked_rows += 1
        start = parse_datetime(row.get(start_field))
        end = parse_datetime(row.get(end_field))
        if start is None or end is None or start > end:
            errors.append(f"{constraint.entity}[{index}] temporal ordering failed")
    if metrics is not None:
        metrics.append(TemporalMetrics(
            entity=constraint.entity, start_field=start_field, end_field=end_field,
            checked_rows=checked_rows, failed_rows=len(errors),
        ))
    return errors


def validate_conditional_required(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    constraint: Any,
    *,
    budget: GenerationBudget | None = None,
    spec: DatasetSpec | None = None,
) -> list[str]:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    if not constraint.condition:
        return []
    condition = Condition(**constraint.condition)
    errors: list[str] = []
    for index, row in budget.iter_rule_work(enumerate(rows_by_entity.get(constraint.entity, []))):
        if not condition_matches(numeric_row(row, spec.entity(constraint.entity), budget=budget)
                                 if spec is not None else row, condition, budget=budget):
            continue
        missing = [field for field in budget.iter_rule_work(constraint.fields) if row.get(field) in (None, "")]
        if missing:
            errors.append(f"{constraint.entity}[{index}] missing conditional fields {missing}")
    return errors


def validate_aggregate_mapping(
    rows_by_entity: dict[str, list[dict[str, Any]]],
    spec: DatasetSpec,
    constraint: Any,
    *,
    budget: GenerationBudget | None = None,
) -> list[str]:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    try:
        return ["aggregate mismatch" for row, expected in aggregate_mapping_values(rows_by_entity, spec, constraint, budget=budget)
                if not numbers_close(row.get(constraint.fields[0]), expected, 0 if spec.entity(constraint.entity).field(constraint.fields[0]).data_type == "decimal" else 0.000001)]
    except GenerationLimitError:
        raise
    except (ValueError, ArithmeticError):
        return ["aggregate value is not numeric or aggregate mapping evaluation failed"]

def coerce_numeric_row(
    row: dict[str, Any], *, budget: GenerationBudget | None = None
) -> dict[str, Any]:
    budget = budget or GenerationBudget()
    budget.check("deterministic rule entry")
    coerced: dict[str, Any] = {}
    for key, value in budget.iter_rule_work(row.items()):
        if isinstance(value, str):
            try:
                number = float(value)
            except ValueError:
                coerced[key] = value
                continue
            coerced[key] = int(number) if number.is_integer() else number
        else:
            coerced[key] = value
    return coerced
