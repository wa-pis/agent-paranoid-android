"""Value-free source-retention aggregate for fictional transformed rows."""

from decimal import Decimal, Inexact, localcontext

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import parse_behavior_policy
from test_data_agent.core.transformation_report import (
    TransformationReportError,
    retention_summary_from_counts,
    summarize_source_retention,
)


def test_retention_percentage_does_not_depend_on_decimal_context():
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        assert retention_summary_from_counts(1, 3, 0).unchanged_percent == "33.33"
        assert retention_summary_from_counts(1, 32, 0).unchanged_percent == "3.13"
        assert retention_summary_from_counts(3, 3, 0).unchanged_percent == "100.00"


def policy(*actions: tuple[str, dict[str, object]]):
    return parse_behavior_policy({
        "schema_version": "0.1",
        "schema_fingerprint": "a" * 64,
        "seed": 7,
        "fields": [
            {
                "entity": "items",
                "field": name,
                "sensitivity": "non_sensitive",
                "behavior": (
                    {"authorization_ref": "fictional-local-review", **behavior}
                    if behavior.get("action") == "preserve" else behavior
                ),
            }
            for name, behavior in actions
        ],
    })


def test_retention_summary_uses_typed_equality_and_nulls_without_values():
    result = summarize_source_retention(
        policy(
            ("flag", {"action": "preserve", "comment": "Reviewed fictional flag."}),
            ("code", {"action": "preserve", "comment": "Reviewed fictional code."}),
            ("optional", {"action": "preserve", "comment": "Reviewed optional value."}),
        ),
        "items",
        ({"flag": True, "code": "001", "optional": None},),
        ({"flag": 1, "code": "1", "optional": None},),
        max_cells=10,
        budget=GenerationBudget(5),
    )

    assert result.status == "measured"
    assert result.scope == "corresponding_output_cells"
    assert result.unchanged_cells == 1
    assert result.compared_cells == 3
    assert result.excluded_dropped_cells == 0
    assert result.unchanged_percent == "33.33"
    assert "001" not in repr(result)


def test_retention_summary_excludes_drop_and_includes_derive():
    result = summarize_source_retention(
        policy(
            ("removed", {"action": "drop"}),
            ("total", {"action": "derive", "expression": "amount * 2",
                       "dependencies": ["items.amount"]}),
        ),
        "items",
        ({"removed": "private-a", "total": Decimal("2.00")},),
        ({"total": Decimal("2.00")},),
        max_cells=10,
        budget=GenerationBudget(5),
    )

    assert result.unchanged_cells == 1
    assert result.compared_cells == 1
    assert result.excluded_dropped_cells == 1
    assert result.unchanged_percent == "100.00"


def test_empty_retention_scope_is_unavailable_not_zero():
    result = summarize_source_retention(
        policy(("removed", {"action": "drop"})),
        "items",
        (),
        (),
        max_cells=10,
        budget=GenerationBudget(5),
    )

    assert result.status == "unavailable"
    assert result.unchanged_cells is None
    assert result.compared_cells == 0
    assert result.unchanged_percent is None


@pytest.mark.parametrize(
    ("source", "output", "max_cells"),
    [
        (({"value": "one"},), (), 10),
        (({"value": "one"},), ({"other": "one"},), 10),
        (({"value": float("nan")},), ({"value": float("nan")},), 10),
        (({"value": "one"},), ({"value": "one"},), 0),
    ],
)
def test_invalid_retention_comparison_is_value_free(source, output, max_cells):
    with pytest.raises(TransformationReportError,
                       match="^invalid transformation retention report$") as caught:
        summarize_source_retention(
            policy(("value", {"action": "preserve", "comment": "Reviewed value."})),
            "items",
            source,
            output,
            max_cells=max_cells,
            budget=GenerationBudget(5),
        )
    assert caught.value.__context__ is None
    assert "one" not in str(caught.value)
