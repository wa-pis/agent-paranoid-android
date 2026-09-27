"""Value-free aggregate reporting for one-to-one transformation results."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, DropAction


class TransformationReportError(ValueError):
    """Invalid comparison input; never includes source or output values."""


@dataclass(frozen=True, slots=True)
class SourceRetentionSummary:
    status: Literal["measured", "unavailable"]
    scope: Literal["corresponding_output_cells"]
    unchanged_cells: int | None
    compared_cells: int
    excluded_dropped_cells: int
    unchanged_percent: str | None


def _is_scalar(value: object) -> bool:
    if value is None or type(value) in {str, bool, int, date, datetime}:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is Decimal:
        return value.is_finite()
    return False


def retention_summary_from_counts(
    unchanged: int, compared: int, dropped: int,
) -> SourceRetentionSummary:
    """Finalize bounded aggregate counts; no source values or authority."""
    if (any(type(count) is not int or count < 0 for count in (unchanged, compared, dropped))
            or unchanged > compared):
        raise TransformationReportError("invalid transformation retention report") from None
    if compared == 0:
        return SourceRetentionSummary(
            "unavailable", "corresponding_output_cells", None, 0, dropped, None)
    hundredths, remainder = divmod(unchanged * 10000, compared)
    hundredths += int(2 * remainder >= compared)
    return SourceRetentionSummary(
        "measured", "corresponding_output_cells", unchanged, compared, dropped,
        f"{hundredths // 100}.{hundredths % 100:02d}")


def summarize_source_retention(
    policy: BehaviorPolicy,
    entity: str,
    source_rows: Sequence[Mapping[str, object]],
    output_rows: Sequence[Mapping[str, object]],
    *,
    max_cells: int,
    budget: GenerationBudget,
) -> SourceRetentionSummary:
    """Count typed-equal corresponding cells without retaining their values."""
    try:
        budget.check("transformation retention report")
        if (
            not isinstance(policy, BehaviorPolicy)
            or type(entity) is not str
            or not entity
            or type(max_cells) is not int
            or max_cells < 1
            or not isinstance(source_rows, Sequence)
            or isinstance(source_rows, (str, bytes))
            or not isinstance(output_rows, Sequence)
            or isinstance(output_rows, (str, bytes))
            or len(source_rows) != len(output_rows)
        ):
            raise ValueError
        decisions = tuple(item for item in policy.fields if item.entity == entity)
        if not decisions:
            raise ValueError
        source_fields = tuple(item.field for item in decisions)
        output_fields = tuple(
            item.field for item in decisions if not isinstance(item.behavior, DropAction)
        )
        if len(source_rows) * len(source_fields) > max_cells:
            raise ValueError

        unchanged = 0
        compared = 0
        for source, output in zip(source_rows, output_rows, strict=True):
            budget.check("transformation retention report")
            if (
                not isinstance(source, Mapping)
                or not isinstance(output, Mapping)
                or set(source) != set(source_fields)
                or set(output) != set(output_fields)
            ):
                raise ValueError
            for field in output_fields:
                before = source[field]
                after = output[field]
                if not _is_scalar(before) or not _is_scalar(after):
                    raise ValueError
                compared += 1
                if type(before) is type(after) and before == after:
                    unchanged += 1

        dropped = len(source_rows) * (len(source_fields) - len(output_fields))
        budget.check("transformation retention report")
        return retention_summary_from_counts(unchanged, compared, dropped)
    except (ValueError, TypeError, AttributeError, ArithmeticError):
        pass
    try:
        raise TransformationReportError("invalid transformation retention report")
    except TransformationReportError as error:
        error.__context__ = None
        raise
