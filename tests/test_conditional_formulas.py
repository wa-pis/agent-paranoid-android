"""Conditional formulas select synthetic rows without weakening rule boundaries."""
from copy import deepcopy

import pytest

from test_data_agent.rules.models import BusinessRules, business_rules_fingerprint
from test_data_agent.rules.engine import apply_valid_defaults
from test_data_agent.rules.validation import validate_business_rules


def rules(when=None, **kwargs):
    payload = dict(type="formula", table="observations", field="value", expression="numerator / divisor", **kwargs)
    if when is not None:
        payload["when"] = when
    return BusinessRules(row_rules=[payload])


def test_false_predicate_skips_assignment_expression_and_success_count():
    selected = rules({"field": "attribute", "equals": "ratio"})
    rows = {"observations": [
        {"attribute": "ratio", "numerator": 6, "divisor": 2, "value": 0},
        {"attribute": "other", "numerator": 6, "divisor": 0, "value": 17},
    ]}
    apply_valid_defaults(rows, selected)
    assert [row["value"] for row in rows["observations"]] == [3, 17]
    report = validate_business_rules(rows, selected)
    result = report.results[0]
    assert report.valid and result.passed == 1 and result.failed == 0
    assert (result.eligible_row_count, result.evaluated_row_count, result.skipped_row_count) == (1, 1, 1)


@pytest.mark.parametrize("when,expected", [
    ({"field": "attribute", "equals": None}, 2),
    ({"field": "attribute", "not_equals": None}, 1),
    ({"field": "attribute", "gte": "1"}, 0),
])
def test_null_and_missing_follow_existing_condition_semantics(when, expected):
    selected = rules(when)
    rows = {"observations": [
        {"attribute": None, "numerator": 6, "divisor": 2, "value": 3},
        {"numerator": 6, "divisor": 2, "value": 3},
        {"attribute": "ratio", "numerator": 6, "divisor": 2, "value": 3},
    ]}
    result = validate_business_rules(rows, selected).results[0]
    assert result.evaluated_row_count == expected
    assert result.skipped_row_count == 3 - expected


def test_check_mode_never_assigns_and_reports_only_selected_failure():
    selected = rules({"field": "attribute", "equals": "ratio"}, mode="check")
    rows = {"observations": [{"attribute": "ratio", "numerator": 6, "divisor": 2, "value": 19}]}
    before = deepcopy(rows)
    apply_valid_defaults(rows, selected)
    assert rows == before
    result = validate_business_rules(rows, selected).results[0]
    assert result.failed == 1 and result.evaluated_row_count == 1


def test_omitted_predicate_keeps_serialization_hash_and_report_shape():
    old = rules()
    explicit = old.model_dump()
    explicit["row_rules"][0]["when"] = None
    new = BusinessRules.model_validate(explicit)
    assert new.model_dump() == old.model_dump()
    assert business_rules_fingerprint(new) == business_rules_fingerprint(old)
    assert business_rules_fingerprint(old) == "98ab179c717a4c255e7183dc01ed501440a8822f219c0e3eb3e97f0e0d3aa945"
    assert "when" not in new.row_rules[0].model_dump()
    row = {"observations": [{"numerator": 6, "divisor": 2, "value": 3}]}
    result = validate_business_rules(row, old).results[0].model_dump()
    assert not {"eligible_row_count", "evaluated_row_count", "skipped_row_count"}.intersection(result)


def test_self_predicate_rejects_before_assignment():
    with pytest.raises(ValueError):
        rules({"field": "value", "equals": 1})


@pytest.mark.parametrize("second", [None, {"field": "attribute", "equals": "ratio"},
                                    {"field": "attribute", "gte": 1}])
def test_overlapping_or_unproven_assignments_reject(second):
    first = rules({"field": "attribute", "equals": "ratio"}).row_rules[0]
    other = rules(second).row_rules[0]
    with pytest.raises(ValueError):
        BusinessRules(row_rules=[first, other])


def test_disjoint_attribute_assignments_are_supported():
    first = rules({"field": "attribute", "equals": "ratio"}).row_rules[0]
    other = rules({"field": "attribute", "in_values": ["other", "third"]}).row_rules[0]
    assert BusinessRules(row_rules=[first, other]).rule_count == 2


def test_predicate_mutation_by_later_rule_rejects():
    first = rules({"field": "attribute", "equals": "ratio"}).row_rules[0]
    with pytest.raises(ValueError):
        BusinessRules(row_rules=[first, {"type": "conditional_allowed_values", "table": "observations",
            "field": "attribute", "when": {"field": "value", "equals": 1}, "allowed_values": ["other"]}])


def test_conditional_expression_syntax_stays_unsupported():
    from test_data_agent.rules.contract import validate_business_rule_literals
    selected = rules({"field": "attribute", "equals": "ratio"})
    selected.row_rules[0].expression = "numerator if divisor else 0"
    with pytest.raises(ValueError):
        validate_business_rule_literals(selected)


def test_conditional_decimal_uses_existing_exact_arithmetic():
    from decimal import Decimal
    from test_data_agent.core.field import FieldSpec
    from test_data_agent.rules.validation import validate_formula
    target = FieldSpec(name="value", data_type="decimal", semantic_type="numeric_measure",
        distribution={"kind": "decimal_range", "precision": 10, "scale": 3, "min": "0.001", "max": "9.999"})
    selected = rules({"field": "attribute", "equals": "ratio"}).row_rules[0]
    rows = {"observations": [{"attribute": "ratio", "numerator": Decimal("1.001"),
                              "divisor": Decimal("3"), "value": Decimal("0.334")}]}
    assert validate_formula(rows, selected, target=target).failed == 0
    rows["observations"][0]["value"] = Decimal("0.335")
    assert validate_formula(rows, selected, target=target).failed == 1


@pytest.mark.parametrize("bound", [False, True])
def test_predicate_literal_privacy_applies_even_to_false_conditions(bound):
    from test_data_agent.rules.contract import validate_business_rule_literals, validate_business_rules_for_spec
    from test_data_agent.core.dataset import DatasetSpec
    selected = rules({"field": "phone", "equals": "+1 (555) 010-0117"})
    spec = DatasetSpec.model_validate({"entities": [{"name": "observations", "row_count": 1,
        "fields": [{"name": "phone", "data_type": "string", "sensitive": True},
                   {"name": "value", "data_type": "integer"},
                   {"name": "numerator", "data_type": "integer"},
                   {"name": "divisor", "data_type": "integer"}]}]})
    with pytest.raises(ValueError) as error:
        if bound:
            validate_business_rules_for_spec(selected, spec)
        else:
            validate_business_rule_literals(selected)
    assert "+1 (555) 010-0117" not in str(error.value)


def test_unknown_predicate_field_rejects_spec_preflight():
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.rules.contract import validate_business_rules_for_spec
    selected = rules({"field": "attribute", "equals": "ratio"})
    spec = DatasetSpec.model_validate({"entities": [{"name": "observations", "row_count": 1,
        "fields": [{"name": name, "data_type": "integer"} for name in ("value", "numerator", "divisor")]}]})
    with pytest.raises(ValueError, match="unknown field"):
        validate_business_rules_for_spec(selected, spec)


@pytest.mark.parametrize("operation", ["assign", "validate"])
def test_false_conditions_still_consume_shared_work(operation, monkeypatch):
    from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
    selected = rules({"field": "attribute", "in_values": ["ratio", "other", "third"]})
    rows = {"observations": [{"attribute": "skip", "value": 17} for _ in range(20)]}
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS", "5")
    budget = GenerationBudget()
    with pytest.raises(GenerationLimitError):
        if operation == "assign":
            apply_valid_defaults(rows, selected, budget=budget)
        else:
            from test_data_agent.rules.validation import validate_formula
            validate_formula(rows, selected.row_rules[0], budget=budget)
    assert all(row["value"] == 17 for row in rows["observations"])


def test_static_work_estimate_accounts_for_predicate_membership():
    from test_data_agent.rules.contract import estimate_business_rule_evaluations_for_rows
    old = rules()
    new = rules({"field": "attribute", "in_values": ["ratio", "other", "third"]})
    assert estimate_business_rule_evaluations_for_rows(new, {"observations": 10}) == (
        estimate_business_rule_evaluations_for_rows(old, {"observations": 10}) + 40)


def test_negative_formula_forces_selected_condition_and_records_violation():
    from test_data_agent.rules.engine import apply_business_rules
    selected = rules({"field": "attribute", "equals": "ratio"})
    rows = {"observations": [{"attribute": "other", "numerator": 6, "divisor": 2, "value": 3}]}
    expected = {}
    apply_business_rules(rows, selected, seed=7, mode="negative", expected_rule_failures=expected)
    report = validate_business_rules(rows, selected, expected_rule_failures=expected)
    assert rows["observations"][0]["attribute"] == "ratio"
    assert report.observed_violation_count == report.expected_violation_count == 1
    assert report.expectations_met


def test_mutated_predicate_writer_rejects_before_row_mutation():
    from test_data_agent.rules.models import ConditionalAllowedValuesRule
    selected = rules({"field": "attribute", "equals": "ratio"})
    selected.row_rules.append(ConditionalAllowedValuesRule(type="conditional_allowed_values",
        table="observations", field="attribute", when={"field": "value", "equals": 1}, allowed_values=["other"]))
    rows = {"observations": [{"attribute": "ratio", "value": 0, "numerator": 6, "divisor": 2}]}
    before = deepcopy(rows)
    with pytest.raises(ValueError):
        apply_valid_defaults(rows, selected)
    assert rows == before


def test_cli_unknown_predicate_field_leaves_existing_output_unchanged(tmp_path, capsys):
    from test_data_agent.cli import main
    from test_data_agent.core.dataset import DatasetSpec
    selected = rules({"field": "absent", "equals": "ratio"})
    spec = DatasetSpec.model_validate({"entities": [{"name": "observations", "row_count": 1,
        "fields": [{"name": name, "data_type": "integer"} for name in ("value", "numerator", "divisor")]}],
        "business_rules": selected.model_dump()})
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("fictional previous output")
    assert main(["generate", str(source), "--output", str(output), "--format", "json", "--overwrite"]) == 2
    assert "unknown field" in capsys.readouterr().err
    assert sentinel.read_text() == "fictional previous output"
    assert sorted(path.name for path in output.iterdir()) == ["keep.txt"]


@pytest.mark.parametrize("operation", ["assign", "validate"])
def test_predicates_share_the_original_deadline(operation, monkeypatch):
    from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
    from test_data_agent.rules import engine, validation
    module = engine if operation == "assign" else validation
    clock = [0.0]
    original = module.condition_matches
    def timed(*args, **kwargs):
        clock[0] = 2.0
        return original(*args, **kwargs)
    monkeypatch.setattr(module, "condition_matches", timed)
    budget = GenerationBudget(max_seconds=1, clock=lambda: clock[0])
    selected = rules({"field": "attribute", "equals": "ratio"})
    rows = {"observations": [{"attribute": "skip", "value": 17}]}
    with pytest.raises(GenerationLimitError):
        if operation == "assign":
            apply_valid_defaults(rows, selected, budget=budget)
        else:
            validate_business_rules(rows, selected, budget=budget)


def test_fictional_eav_example_replays_disjoint_exact_formulas_and_cli(tmp_path):
    import json
    from decimal import Decimal
    from pathlib import Path
    from test_data_agent.cli import main
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.generation import generate_dataset
    source = Path(__file__).resolve().parents[1] / "examples/business_rules/conditional_eav.json"
    spec = DatasetSpec.model_validate_json(source.read_text())
    rows = generate_dataset(spec, seed=7)
    assert rows == generate_dataset(spec, seed=7)
    assert {row["attribute"] for row in rows["observations"]} == {"ratio", "total"}
    for row in rows["observations"]:
        expected = (Decimal(row["numerator"]) / Decimal(row["divisor"]) if row["attribute"] == "ratio"
                    else Decimal(row["numerator"]) + Decimal(row["divisor"]))
        assert row["value"] == expected
    report = validate_business_rules(rows, spec.business_rules, spec=spec)
    assert report.valid
    assert sum(result.evaluated_row_count for result in report.results) == 12
    assert sum(result.skipped_row_count for result in report.results) == 12
    output = tmp_path / "generated"
    assert main(["generate", str(source), "--output", str(output), "--format", "json"]) == 0
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert manifest["synthetic"] is True and manifest["source_rows_copied"] is False
    assert len(json.loads((output / "observations.json").read_text())) == 12
    published = json.loads((output / "business_validation_report.json").read_text())
    assert sum(result["assigned_row_count"] for result in published["results"]) == 12


def test_selected_expression_failure_counts_attempt_without_source_values():
    selected = rules({"field": "attribute", "equals": "ratio"})
    rows = {"observations": [{"attribute": "ratio", "numerator": 6, "divisor": 0, "value": 19}]}
    report = validate_business_rules(rows, selected)
    result = report.results[0]
    assert not report.valid and result.failed == 1
    assert (result.eligible_row_count, result.evaluated_row_count, result.skipped_row_count) == (1, 1, 0)
    assert result.errors == ["formula evaluation failed"]


def test_omitted_predicate_matches_prior_runtime_seeded_output_hash():
    import hashlib
    import json
    from pathlib import Path
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.generation import generate_dataset
    payload = json.loads((Path(__file__).resolve().parents[1] /
        "examples/business_rules/conditional_eav.json").read_text())
    payload["business_rules"] = rules().model_dump()
    rows = generate_dataset(DatasetSpec.model_validate(payload), seed=7)
    encoded = json.dumps(rows, sort_keys=True, default=str, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == "ce1ae1cd4ba1d00caa76f0e4dc20a265cd25f8970c0c36e1052221754fb15bed"


def test_service_assignment_counts_exclude_skipped_and_forced_negative_rows():
    from test_data_agent.rules.business_config import apply_and_validate_business_rules
    selected = rules({"field": "attribute", "equals": "ratio"})
    rows = {"observations": [
        {"attribute": "ratio", "numerator": 6, "divisor": 2, "value": 0},
        {"attribute": "other", "numerator": 6, "divisor": 2, "value": 17},
    ]}
    report = apply_and_validate_business_rules(rows, selected, seed=7, mode="valid", invalid_ratio=0)
    assert report.results[0].assigned_row_count == 1
    rows = {"observations": [{"attribute": "other", "numerator": 6, "divisor": 2, "value": 3}]}
    report = apply_and_validate_business_rules(rows, selected, seed=7, mode="negative", invalid_ratio=0)
    assert report.results[0].assigned_row_count == 0
    assert report.results[0].evaluated_row_count == 1


def test_service_enforces_unbound_predicate_privacy_before_mutation():
    from test_data_agent.rules.business_config import apply_and_validate_business_rules
    selected = rules({"field": "phone", "equals": "+1 (555) 010-0117"})
    rows = {"observations": [{"phone": "fictional-other", "value": 17}]}
    before = deepcopy(rows)
    with pytest.raises(ValueError):
        apply_and_validate_business_rules(rows, selected, seed=7, mode="valid", invalid_ratio=0)
    assert rows == before


@pytest.mark.parametrize("entry", ["apply", "validate"])
def test_public_rule_entry_rejects_private_predicate_literals(entry):
    from test_data_agent.rules.engine import apply_business_rules
    selected = rules({"field": "phone", "equals": "+1 (555) 010-0117"})
    rows = {"observations": [{"phone": "fictional-other", "value": 17}]}
    before = deepcopy(rows)
    with pytest.raises(ValueError) as error:
        if entry == "apply":
            apply_business_rules(rows, selected, seed=7)
        else:
            validate_business_rules(rows, selected)
    assert "+1 (555) 010-0117" not in str(error.value)
    assert rows == before


def test_sampling_bound_diagnostics_count_only_assigned_rows():
    from test_data_agent.core.dataset import DatasetSpec
    from test_data_agent.rules.business_config import apply_and_validate_business_rules
    selected = rules({"field": "attribute", "equals": "ratio"})
    spec = DatasetSpec.model_validate({"entities": [{"name": "observations", "row_count": 2,
        "fields": [{"name": "attribute", "data_type": "string"},
                   {"name": "value", "data_type": "integer", "distribution": {
                       "kind": "numeric", "min_value": 1, "max_value": 9}},
                   {"name": "numerator", "data_type": "integer"},
                   {"name": "divisor", "data_type": "integer"}]}]})
    rows = {"observations": [
        {"attribute": "ratio", "numerator": 6, "divisor": 2, "value": 0},
        {"attribute": "other", "numerator": 6, "divisor": 2, "value": 17},
    ]}
    report = apply_and_validate_business_rules(rows, selected, seed=7, mode="valid", invalid_ratio=0, spec=spec)
    assert report.distribution_bounds_checked_count == 1
    assert report.distribution_bounds_violation_count == 0
