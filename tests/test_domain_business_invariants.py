import pytest

from test_data_agent.business_validator import validate_business_rules
from test_data_agent.core.constraint import Constraint, ConstraintType
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.relationship import Relationship
from test_data_agent.rules.models import business_rules_from_dict
from test_data_agent.validation import validate_dataset


def grouped_total_spec(
    *,
    summary_entity: str,
    detail_entity: str,
    key_field: str,
    total_field: str,
    value_field: str,
) -> DatasetSpec:
    return DatasetSpec(
        entities=[
            EntitySpec(
                name=summary_entity,
                row_count=2,
                fields=[
                    FieldSpec(
                        name=key_field,
                        data_type=FieldType.INTEGER,
                        is_identifier=True,
                    ),
                    FieldSpec(name=total_field, data_type=FieldType.FLOAT),
                ],
            ),
            EntitySpec(
                name=detail_entity,
                row_count=3,
                fields=[
                    FieldSpec(name=key_field, data_type=FieldType.INTEGER),
                    FieldSpec(name=value_field, data_type=FieldType.FLOAT),
                ],
            ),
        ],
        relationships=[
            Relationship(
                parent_entity=summary_entity,
                parent_field=key_field,
                child_entity=detail_entity,
                child_field=key_field,
                confidence=1.0,
            )
        ],
        constraints=[
            Constraint(
                type=ConstraintType.AGGREGATE_MAPPING,
                entity=summary_entity,
                fields=[total_field],
                target_entity=detail_entity,
                target_field=value_field,
                aggregate="sum",
                confidence=1.0,
            )
        ],
    )


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


def test_grouped_totals_and_parent_coverage_are_validated() -> None:
    spec = grouped_total_spec(
        summary_entity="depots",
        detail_entity="parcels",
        key_field="depot_id",
        total_field="total_weight",
        value_field="weight",
    )
    valid_rows = {
        "depots": [
            {"depot_id": 1, "total_weight": 12},
            {"depot_id": 2, "total_weight": 4},
        ],
        "parcels": [
            {"depot_id": 1, "weight": 5},
            {"depot_id": 1, "weight": 7},
            {"depot_id": 2, "weight": 4},
        ],
    }

    assert validate_dataset(valid_rows, spec).valid is True

    mismatched_rows = {
        table: [dict(row) for row in rows]
        for table, rows in valid_rows.items()
    }
    mismatched_rows["depots"][0]["total_weight"] = 11
    mismatch_report = validate_dataset(mismatched_rows, spec)
    assert mismatch_report.valid is False
    assert "aggregate mismatch" in next(
        section for section in mismatch_report.sections if section.name == "constraints"
    ).errors[0]

    uncovered_rows = {
        table: [dict(row) for row in rows]
        for table, rows in valid_rows.items()
    }
    uncovered_rows["parcels"][2]["depot_id"] = 99
    coverage_report = validate_dataset(uncovered_rows, spec)
    assert coverage_report.valid is False
    assert "has no parent" in next(
        section for section in coverage_report.sections if section.name == "relationships"
    ).errors[0]


def test_financial_fixture_uses_generic_cross_table_reconciliation() -> None:
    spec = grouped_total_spec(
        summary_entity="ledger_balances",
        detail_entity="postings",
        key_field="ledger_id",
        total_field="balance",
        value_field="amount",
    )
    rows = {
        "ledger_balances": [
            {"ledger_id": 1, "balance": 60},
            {"ledger_id": 2, "balance": 25},
        ],
        "postings": [
            {"ledger_id": 1, "amount": 100},
            {"ledger_id": 1, "amount": -40},
            {"ledger_id": 2, "amount": 25},
        ],
    }

    assert validate_dataset(rows, spec).valid is True

    rows["ledger_balances"][0]["balance"] = 61
    report = validate_dataset(rows, spec)
    assert report.valid is False
    assert "aggregate mismatch" in next(
        section for section in report.sections if section.name == "constraints"
    ).errors[0]
