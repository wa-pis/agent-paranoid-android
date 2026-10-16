"""Schema-aware ordinary rule arithmetic, independent of I/O and transformation."""

from __future__ import annotations

from decimal import Decimal
from test_data_agent.csv_profiler import parse_bool, parse_date_value, parse_datetime_value
from typing import Any, TYPE_CHECKING
from collections import defaultdict
from collections.abc import Iterator
from fractions import Fraction

if TYPE_CHECKING:
    from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.constraint import Constraint

from test_data_agent.core.distribution import DecimalRangeDistribution
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.decimal_units import decimal_to_units, decimal_from_units
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.rules.expressions import eval_exact_decimal, safe_eval


def numeric_row(
    row: dict[str, Any], entity: EntitySpec, *, budget: GenerationBudget
) -> dict[str, Any]:
    result = dict(row)
    for field in budget.iter_rule_work(entity.fields):
        value = result.get(field.name)
        if value is None:
            continue
        if value == "" and (field.data_type != FieldType.STRING):
            result[field.name] = None
            continue
        if field.data_type == FieldType.DATE:
            parsed_date = parse_date_value(str(value))
            if parsed_date is not None:
                result[field.name] = parsed_date.isoformat()
            continue
        if field.data_type == FieldType.DATETIME:
            parsed_datetime = parse_datetime_value(str(value))
            if parsed_datetime is not None:
                result[field.name] = parsed_datetime.isoformat()
            continue
        if field.data_type == FieldType.BOOLEAN:
            parsed_bool = parse_bool(str(value))
            if parsed_bool is not None:
                result[field.name] = parsed_bool
            continue
        if not isinstance(value, str):
            continue
        try:
            if field.data_type == FieldType.DECIMAL:
                distribution = field.typed_distribution
                assert isinstance(distribution, DecimalRangeDistribution)
                units = decimal_to_units(
                    value, precision=distribution.precision, scale=distribution.scale
                )
                result[field.name] = decimal_from_units(
                    units, precision=distribution.precision, scale=distribution.scale
                )
            elif field.data_type == FieldType.INTEGER:
                result[field.name] = int(value)
            elif field.data_type == FieldType.FLOAT:
                result[field.name] = float(value)
        except (ValueError, ArithmeticError):
            continue  # Preserve invalid values for schema/rule validation.
    return result


def formula_value(
    expression: str,
    row: dict[str, Any],
    target: FieldSpec | None,
    *,
    budget: GenerationBudget,
) -> Any:
    if target is not None and isinstance(
        target.typed_distribution, DecimalRangeDistribution
    ):
        distribution = target.typed_distribution
        return eval_exact_decimal(
            expression,
            row,
            precision=distribution.precision,
            scale=distribution.scale,
            budget=budget,
            allow_float=True,
        )
    if any(isinstance(value, Decimal) for value in row.values()):
        # Reuse exact row evaluation via the bounded rational evaluator.
        from test_data_agent.rules.expressions import _eval_exact_fraction

        value = _eval_exact_fraction(expression, row, budget=budget, allow_float=True)
        if target is not None and target.data_type == FieldType.INTEGER:
            if value.denominator != 1:
                raise ValueError("integer formula result is not integral")
            return value.numerator
        if target is not None and target.data_type == FieldType.FLOAT:
            return float(value)
        return value
    return safe_eval(expression, row, budget=budget)


def aggregate_mapping_values(
    rows: dict[str, list[dict[str, Any]]],
    spec: DatasetSpec,
    constraint: Constraint,
    *,
    budget: GenerationBudget,
    skip_invalid: bool = False,
) -> Iterator[tuple[dict[str, Any], Any]]:
    from test_data_agent.rules.expressions import exact_number, decimal_from_fraction

    relationship = next(
        (
            item
            for item in budget.iter_rule_work(spec.relationships)
            if item.status != "rejected"
            and item.parent_entity == constraint.entity
            and item.child_entity == constraint.target_entity
        ),
        None,
    )
    if relationship is None:
        raise ValueError("aggregate mapping requires an active relationship")
    totals: dict[Any, Fraction] = defaultdict(Fraction)
    counts: dict[Any, int] = defaultdict(int)
    for child in budget.iter_rule_work(rows.get(relationship.child_entity, [])):
        key = child.get(relationship.child_field)
        if constraint.aggregate == "count":
            totals[key] += 1
        elif (
            constraint.target_field is not None
            and child.get(constraint.target_field) is not None
        ):
            try:
                totals[key] = exact_number(
                    totals[key] + exact_number(child[constraint.target_field])
                )
            except (ValueError, ArithmeticError):
                if skip_invalid:
                    continue
                raise ValueError("aggregate value is not numeric") from None
            counts[key] += 1
    target = spec.entity(constraint.entity).field(constraint.fields[0])
    distribution = target.typed_distribution
    for parent in budget.iter_rule_work(rows.get(relationship.parent_entity, [])):
        key = parent.get(relationship.parent_field)
        value = totals[key]
        if constraint.aggregate == "avg" and counts[key]:
            value /= counts[key]
        if isinstance(distribution, DecimalRangeDistribution):
            expected: Any = decimal_from_fraction(
                value,
                precision=distribution.precision,
                scale=distribution.scale,
                budget=budget,
            )
        else:
            rounded = round(float(value), 6)
            expected = int(rounded) if rounded.is_integer() else rounded
        yield parent, expected
