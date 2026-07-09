import json

from test_data_agent.core.settings import GenerationMode as CoreGenerationMode
from test_data_agent.business_rules import ScenarioRule, load_business_rules
from test_data_agent.business_validator import validate_business_rules
from test_data_agent.rules.scenarios import apply_scenarios as apply_neutral_scenarios
from test_data_agent.cli import main
from test_data_agent.rules_engine import GenerationMode, apply_business_rules
from test_data_agent.scenario import apply_scenarios as apply_legacy_scenarios


def test_legacy_rules_engine_mode_aliases_core_generation_mode() -> None:
    assert GenerationMode is CoreGenerationMode


def test_business_validator_supports_every_rule_type(tmp_path) -> None:
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        """
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [paid, refunded]
row_rules:
  - type: conditional_required
    table: orders
    when: {field: status, equals: refunded}
    required_fields: [refund_reason]
  - type: conditional_allowed_values
    table: orders
    field: shipping_method
    when: {field: status, equals: paid}
    allowed_values: [ground, air]
  - type: temporal_ordering
    table: orders
    start_field: created_at
    end_field: shipped_at
  - type: formula
    table: orders
    field: total
    expression: quantity * unit_price
cross_table_rules:
  - type: foreign_key
    child_table: orders
    child_field: customer_id
    parent_table: customers
    parent_field: customer_id
  - type: aggregate_formula
    table: orders
    field: total
    expression: "100"
    expected: 100
scenarios:
  - name: paid_ground
    weight: 1
    field_values:
      orders:
        status: paid
        shipping_method: ground
"""
    )
    rules = load_business_rules(rules_path)
    rows_by_table = {
        "customers": [{"customer_id": 1}],
        "orders": [
            {
                "customer_id": 1,
                "status": "paid",
                "shipping_method": "ground",
                "refund_reason": None,
                "created_at": "2024-01-01T00:00:00",
                "shipped_at": "2024-01-02T00:00:00",
                "quantity": 2,
                "unit_price": 10,
                "total": 20,
            },
            {
                "customer_id": 1,
                "status": "refunded",
                "shipping_method": "ground",
                "refund_reason": "damaged",
                "created_at": "2024-01-03T00:00:00",
                "shipped_at": "2024-01-04T00:00:00",
                "quantity": 4,
                "unit_price": 20,
                "total": 80,
            },
        ],
    }

    report = validate_business_rules(rows_by_table, rules)

    assert report.valid is True
    assert report.rule_fail_count == 0
    assert {result.rule_type for result in report.results} == {
        "field",
        "conditional_required",
        "conditional_allowed_values",
        "temporal_ordering",
        "formula",
        "foreign_key",
        "aggregate_formula",
    }


def test_business_validator_reports_rule_fail_counts(tmp_path) -> None:
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        """
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [paid]
row_rules:
  - type: temporal_ordering
    table: orders
    start_field: created_at
    end_field: shipped_at
cross_table_rules:
  - type: foreign_key
    child_table: orders
    child_field: customer_id
    parent_table: customers
    parent_field: customer_id
"""
    )
    rows_by_table = {
        "customers": [{"customer_id": 1}],
        "orders": [
            {
                "customer_id": 2,
                "status": "cancelled",
                "created_at": "2024-01-03T00:00:00",
                "shipped_at": "2024-01-01T00:00:00",
            }
        ],
    }

    report = validate_business_rules(rows_by_table, load_business_rules(rules_path))

    assert report.valid is False
    assert report.rule_fail_count == 3


def test_scenario_distribution_and_controlled_invalid_generation_are_deterministic(tmp_path) -> None:
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        """
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [paid, pending]
scenarios:
  - name: paid
    weight: 1
    field_values:
      orders:
        status: paid
  - name: pending
    weight: 1
    field_values:
      orders:
        status: pending
"""
    )
    rules = load_business_rules(rules_path)
    rows_a = {"orders": [{"status": "other"} for _ in range(6)]}
    rows_b = {"orders": [{"status": "other"} for _ in range(6)]}

    apply_business_rules(rows_a, rules, seed=42, mode="negative", invalid_ratio=0)
    apply_business_rules(rows_b, rules, seed=42, mode="negative", invalid_ratio=0)
    report = validate_business_rules(rows_a, rules)

    assert rows_a == rows_b
    assert report.valid is False
    assert report.rule_fail_count == 6


def test_conditional_required_defaults_only_apply_when_condition_matches(tmp_path) -> None:
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        """
row_rules:
  - type: conditional_required
    table: orders
    when: {field: status, equals: refunded}
    required_fields: [refund_reason]
"""
    )
    rules = load_business_rules(rules_path)
    rows_by_table = {
        "orders": [
            {"status": "paid", "refund_reason": None},
            {"status": "refunded", "refund_reason": None},
        ]
    }

    apply_business_rules(rows_by_table, rules, seed=4, mode="valid", invalid_ratio=0)

    assert rows_by_table["orders"][0]["refund_reason"] is None
    assert rows_by_table["orders"][1]["refund_reason"] == "required"


def test_scenario_helpers_remain_deterministic_through_neutral_and_legacy_imports() -> None:
    scenarios = [
        ScenarioRule(name="paid", weight=1, field_values={"orders": {"status": "paid"}}),
        ScenarioRule(name="pending", weight=1, field_values={"orders": {"status": "pending"}}),
    ]
    rows_a = {"orders": [{"status": "unknown"} for _ in range(8)]}
    rows_b = {"orders": [{"status": "unknown"} for _ in range(8)]}

    apply_neutral_scenarios(rows_a, scenarios, seed=11)
    apply_legacy_scenarios(rows_b, scenarios, seed=11)

    assert rows_a == rows_b


def test_cli_writes_business_validation_report_for_csv_profile(tmp_path) -> None:
    rules_path = tmp_path / "rules.yaml"
    output = tmp_path / "out" / "customers.json"
    rules_path.write_text(
        """
field_rules:
  - table: customers
    field: status
    required: true
    allowed_values: [new, active, paused]
"""
    )

    exit_code = main(
        [
            "generate-from-csv",
            "tests/fixtures/customers.csv",
            "--count",
            "5",
            "--mode",
            "valid",
            "--seed",
            "9",
            "--format",
            "json",
            "--output",
            str(output),
            "--business-rules",
            str(rules_path),
        ]
    )

    report = json.loads((output.parent / "business_validation_report.json").read_text())

    assert exit_code == 0
    assert report["rule_fail_count"] == 0


def test_cli_valid_mode_fails_when_business_rules_fail(tmp_path) -> None:
    rules_path = tmp_path / "rules.yaml"
    output = tmp_path / "out" / "customers.json"
    rules_path.write_text(
        """
cross_table_rules:
  - type: foreign_key
    child_table: customers
    child_field: customer_id
    parent_table: accounts
    parent_field: customer_id
"""
    )

    exit_code = main(
        [
            "generate-from-csv",
            "tests/fixtures/customers.csv",
            "--count",
            "5",
            "--mode",
            "valid",
            "--seed",
            "9",
            "--format",
            "json",
            "--output",
            str(output),
            "--business-rules",
            str(rules_path),
        ]
    )

    report = json.loads((output.parent / "business_validation_report.json").read_text())

    assert exit_code == 1
    assert report["rule_fail_count"] > 0
