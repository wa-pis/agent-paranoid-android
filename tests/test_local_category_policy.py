from __future__ import annotations

from decimal import Decimal

import pytest

from test_data_agent.core.privacy import validate_local_category_values


@pytest.mark.parametrize(
    "values",
    [
        ["pending", "approved", "rejected"],
        ["North America", "Europe"],
        [1, 2, 3],
        [True, False],
    ],
)
def test_bounded_business_categories_are_allowed(values: list[object]) -> None:
    validate_local_category_values(
        field_name="status_code",
        semantic_type=None,
        sensitive=False,
        values=values,
    )


@pytest.mark.parametrize(
    ("field_name", "semantic_type", "sensitive"),
    [
        ("customer_id", None, False),
        ("account_key", None, False),
        ("record_uuid", None, False),
        ("age_group", None, False),
        ("postal_code", None, False),
        ("api_token", None, False),
        ("status", "identifier", False),
        ("status", "quasi_identifier", False),
        ("status", None, True),
    ],
)
def test_sensitive_or_identifier_fields_are_rejected(
    field_name: str,
    semantic_type: str | None,
    sensitive: bool,
) -> None:
    with pytest.raises(ValueError):
        validate_local_category_values(
            field_name=field_name,
            semantic_type=semantic_type,
            sensitive=sensitive,
            values=["active", "inactive"],
        )


@pytest.mark.parametrize(
    ("values", "message"),
    [
        (["person@example.test"], "sensitive content"),
        (["notes: call customer tomorrow"], "free text"),
        ([""], "free text"),
        (["active", "active"], "unique"),
        ([Decimal("1.5")], "bounded scalars"),
    ],
)
def test_unsafe_category_content_is_rejected_without_echoing_values(
    values: list[object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message) as error:
        validate_local_category_values(
            field_name="status",
            semantic_type=None,
            sensitive=False,
            values=values,
        )

    assert all(not str(value) or str(value) not in str(error.value) for value in values)


def test_cardinality_and_value_length_are_bounded() -> None:
    with pytest.raises(ValueError, match="cardinality"):
        validate_local_category_values(
            field_name="status",
            semantic_type=None,
            sensitive=False,
            values=["one", "two"],
            max_categories=1,
        )
    with pytest.raises(ValueError, match="length"):
        validate_local_category_values(
            field_name="status",
            semantic_type=None,
            sensitive=False,
            values=["too-long"],
            max_value_length=4,
        )


def test_empty_values_and_disabled_limits_fail_closed() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_local_category_values(
            field_name="status",
            semantic_type=None,
            sensitive=False,
            values=[],
        )
    with pytest.raises(ValueError, match="limits must be positive"):
        validate_local_category_values(
            field_name="status",
            semantic_type=None,
            sensitive=False,
            values=["active"],
            max_categories=0,
        )
