"""Keep the complete business-rule reference tied to executable contracts."""

from __future__ import annotations

import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args

import pytest
import yaml
from pydantic import BaseModel

from scripts.export_business_rules_schema import build_business_rules_schema, main as export_schema
from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.rules.contract import validate_business_rules_for_spec
from test_data_agent.rules.models import BusinessRules, load_business_rules

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/business_rules"


def test_standalone_business_rules_schema_matches_runtime_and_export(tmp_path: Path) -> None:
    checked_in = (ROOT / "schemas/business_rules.schema.json").read_text()
    generated = build_business_rules_schema()
    assert checked_in == json.dumps(generated, indent=2, sort_keys=True) + "\n"
    output = tmp_path / "business_rules.schema.json"
    assert export_schema([str(output)]) == 0
    assert output.read_text() == checked_in
    embedded = DatasetSpec.model_json_schema()["$defs"]["BusinessRules"]
    assert generated["properties"] == embedded["properties"]
    assert generated["additionalProperties"] is False


def test_complete_rule_example_covers_runtime_models_and_options() -> None:
    payload = yaml.safe_load((EXAMPLE / "rules.yaml").read_text())
    assert payload == BusinessRules.model_validate(payload).model_dump(
        mode="json", exclude_unset=True,
    )
    rules = load_business_rules(EXAMPLE / "rules.yaml")
    spec = DatasetSpec.model_validate(yaml.safe_load((EXAMPLE / "dataset_spec.yaml").read_text()))
    validate_business_rules_for_spec(rules, spec)

    models: set[type[BaseModel]] = set()

    def discover(annotation: Any) -> None:
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            if annotation in models:
                return
            models.add(annotation)
            for field in annotation.model_fields.values():
                discover(field.annotation)
        else:
            for argument in get_args(annotation):
                discover(argument)

    used: dict[type[BaseModel], set[str]] = defaultdict(set)

    def visit(value: Any) -> None:
        if isinstance(value, BaseModel):
            used[type(value)].update(value.model_fields_set)
            for name in type(value).model_fields:
                visit(getattr(value, name))
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    discover(BusinessRules)
    visit(rules)
    assert set(used) == models
    for model in models:
        assert used[model] == set(model.model_fields), model.__name__
    assert {rule.mode for rule in rules.row_rules if rule.type == "formula"} == {"assign", "check"}
    assert {rule.allow_equal for rule in rules.row_rules if rule.type == "temporal_ordering"} == {True, False}


@pytest.mark.parametrize("embedded", [False, True], ids=["separate-file", "embedded"])
@pytest.mark.parametrize("mode", ["valid", "mixed"])
def test_complete_rule_example_generates_and_validates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], embedded: bool, mode: str,
) -> None:
    spec_path = EXAMPLE / "dataset_spec.yaml"
    arguments = []
    if embedded:
        payload = yaml.safe_load(spec_path.read_text())
        payload["business_rules"] = yaml.safe_load((EXAMPLE / "rules.yaml").read_text())
        spec_path = tmp_path / "embedded.yaml"
        spec_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    else:
        arguments = ["--business-rules", str(EXAMPLE / "rules.yaml")]
    output = tmp_path / "generated"
    code = main([
        "generate", str(spec_path), *arguments, "--output", str(output),
        "--format", "json", "--seed", "12345", "--mode", mode,
        "--invalid-ratio", "0.25" if mode == "mixed" else "0",
    ])
    capsys.readouterr()
    assert code == (0 if mode == "valid" else 1)
    manifest = json.loads((output / "generation_manifest.json").read_text())
    report = json.loads((output / "business_validation_report.json").read_text())
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["row_counts"] == {"customers": 4, "orders": 24}
    assert report["expectations_met"] is True
    assert report["unexpected_violation_count"] == 0
    assert report["missing_expected_violation_count"] == 0
    assert report["valid"] == (mode == "valid")
    assert report["rule_count"] == load_business_rules(EXAMPLE / "rules.yaml").rule_count
    if mode == "mixed":
        assert report["observed_violation_count"] > 0
        return
    assert report["rule_fail_count"] == 0
    orders = json.loads((output / "orders.json").read_text())
    customers = json.loads((output / "customers.json").read_text())
    assert {row["status"] for row in orders} == {"paid", "cancelled"}
    assert {row["customer_id"] for row in orders} <= {row["customer_id"] for row in customers}
    for row in orders:
        subtotal = row["quantity"] * Decimal(row["unit_price"])
        assert Decimal(row["subtotal"]) == subtotal
        assert Decimal(row["total"]) == subtotal - Decimal(row["discount"]) + Decimal(row["fee"])
        assert row["created_at"] < row["fulfilled_at"]
        if row["status"] == "cancelled":
            assert row["reason"]
    modes = [item for item in report["results"] if item["rule_type"] == "formula"]
    assert [item["application"] for item in modes] == ["assign", "assign", "check"]
    assert [item["assigned_row_count"] for item in modes] == [24, 24, 0]


def test_business_rule_reference_local_links_resolve() -> None:
    import re

    path = EXAMPLE / "README.md"
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
        if "://" not in target:
            assert (path.parent / target).exists(), target


def test_business_rules_schema_accepts_complete_example() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = build_business_rules_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    payload = yaml.safe_load((EXAMPLE / "rules.yaml").read_text())
    jsonschema.Draft202012Validator(schema).validate(payload)
