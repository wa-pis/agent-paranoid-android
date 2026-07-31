import pytest

from test_data_agent.business_validator import validate_business_rules
from test_data_agent.rules.models import business_rules_from_dict


@pytest.mark.parametrize(
    ("rule", "valid_row", "invalid_row"),
    [
        pytest.param(
            {
                "type": "formula",
                "table": "shipments",
                "field": "total_cost",
                "expression": "transport_cost + handling_cost",
            },
            {"transport_cost": 12, "handling_cost": 3, "total_cost": 15},
            {"transport_cost": 12, "handling_cost": 3, "total_cost": 14},
            id="logistics-components",
        ),
        pytest.param(
            {
                "type": "formula",
                "table": "samples",
                "field": "sample_count",
                "expression": "accepted_count + rejected_count",
            },
            {"accepted_count": 8, "rejected_count": 2, "sample_count": 10},
            {"accepted_count": 8, "rejected_count": 2, "sample_count": 9},
            id="scientific-partition",
        ),
        pytest.param(
            {
                "type": "temporal_ordering",
                "table": "service_windows",
                "start_field": "opens_at",
                "end_field": "closes_at",
                "allow_equal": False,
            },
            {"opens_at": "2026-01-01T08:00:00", "closes_at": "2026-01-01T12:00:00"},
            {"opens_at": "2026-01-01T12:00:00", "closes_at": "2026-01-01T08:00:00"},
            id="service-temporal-window",
        ),
        pytest.param(
            {
                "type": "formula",
                "table": "inventory_movements",
                "field": "quantity_out",
                "expression": "quantity_in",
            },
            {"quantity_in": 25, "quantity_out": 25},
            {"quantity_in": 25, "quantity_out": 24},
            id="inventory-paired-values",
        ),
    ],
)
def test_business_invariants_are_domain_agnostic(
    rule: dict[str, object],
    valid_row: dict[str, object],
    invalid_row: dict[str, object],
) -> None:
    rules = business_rules_from_dict({"row_rules": [rule]})
    table = str(rule["table"])

    valid_report = validate_business_rules({table: [valid_row]}, rules)
    invalid_report = validate_business_rules({table: [invalid_row]}, rules)

    assert valid_report.valid is True
    assert valid_report.rule_fail_count == 0
    assert invalid_report.valid is False
    assert invalid_report.rule_fail_count == 1
