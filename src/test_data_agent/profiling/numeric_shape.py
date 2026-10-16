"""Value-free prevalence aggregates shared by database numeric profiles."""

from collections.abc import Mapping
from typing import Any


def prevalence_sql(column: str, magnitude: str) -> str:
    """Arguments are trusted quoted SQL fragments, never caller SQL."""
    return (
        f"sum(CASE WHEN {column} = 0 THEN 1 ELSE 0 END) AS zero_count, "
        f"sum(CASE WHEN abs({column}) > 0 AND abs({column}) < 1 THEN 1 ELSE 0 END) AS subunit_count, "
        f"min(CASE WHEN abs({column}) > 0 AND abs({column}) < 1 THEN {magnitude} END) AS min_subunit_magnitude"
    )


def shape_prevalence(summary: Mapping[str, Any], non_null_count: int) -> dict[str, Any]:
    """Legacy aggregate responses omit this optional extension entirely."""
    if not {"zero_count", "subunit_count", "min_subunit_magnitude"}.intersection(
        summary
    ):
        return {}
    zero, small = summary.get("zero_count"), summary.get("subunit_count")
    if non_null_count == 0 and zero is None and small is None:
        return {}
    if (
        type(zero) is not int
        or type(small) is not int
        or min(zero, small) < 0
        or zero + small > non_null_count
    ):
        raise ValueError("numeric prevalence aggregate counts are invalid")
    lower = summary.get("min_subunit_magnitude")
    if small and (type(lower) is not int or not -308 <= lower <= -1):
        raise ValueError("numeric prevalence magnitude is invalid")
    if not small and lower is not None:
        raise ValueError("numeric prevalence magnitude is inconsistent")
    if not non_null_count:
        return {}
    result: dict[str, Any] = {
        "zero_ratio": zero / non_null_count,
        "subunit_ratio": small / non_null_count,
    }
    if small:
        result["min_subunit_magnitude"] = lower
    return result
