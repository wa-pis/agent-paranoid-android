"""Finite behavioral option coverage; this is not an arbitrary-combination proof."""

from decimal import Decimal
from itertools import product
import json
import re

import pytest

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec
from test_data_agent.core.decimal_units import decimal_from_units, decimal_to_units
from test_data_agent.core.distribution import SyntheticIdentifierDistribution
from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.settings import OutputFormat, ValidationSettings
from test_data_agent.generation import generate_dataset
from test_data_agent.io.csv_encoding import decode_csv_cell, encode_csv_cell
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import (
    generate_dataset_bundle,
    generate_dataset_from_profile_artifacts,
)
from test_data_agent.rules.models import BusinessRules
from test_data_agent.rules.typed_values import numeric_row
from test_data_agent.validation import validate_dataset


def _typed_rows(folder, spec):
    return {
        name: [numeric_row(row, spec.entity(name), budget=GenerationBudget()) for row in rows]
        for name, rows in load_dataset_rows(folder).items()
    }


def _distribution_spec():
    def field(name, data_type, kind, **distribution):
        return {"name": name, "data_type": data_type,
                "distribution": {"kind": kind, **distribution}}

    return DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 6,
        "fields": [
            field("low_scale", "float", "numeric", min_value=20, max_value=20,
                  p05=5, p95=5, scale_factor=0.1),
            field("high_scale", "float", "numeric", min_value=0.5, max_value=0.5,
                  scale_factor=10),
            field("false_only", "boolean", "boolean", true_ratio=0),
            field("true_only", "boolean", "boolean", true_ratio=1),
            field("category", "string", "categorical", categories=[
                {"value": "excluded", "count": 0}, {"value": "ready", "count": 1}]),
            field("zero_only", "float", "numeric_shape", max_abs_magnitude=0,
                  zero_ratio=1),
            field("tiny_positive", "float", "numeric_shape", max_abs_magnitude=-10,
                  has_positive=True, zero_ratio=0, subunit_ratio=1,
                  min_subunit_magnitude=-10),
            field("negative_only", "float", "numeric_shape", max_abs_magnitude=1,
                  has_negative=True),
            {**field("empty", "string", "string_pattern", min_length=0, max_length=0),
             "nullable": True},
            field("short", "string", "string_pattern", min_length=2, max_length=2),
            field("day", "date", "date_range", min="2024-02-29", max="2024-02-29"),
            field("instant", "datetime", "datetime_range",
                  min="2024-02-29T12:00:00+03:00", max="2024-02-29T12:00:00+03:00"),
            field("whole", "decimal", "decimal_range", precision=1, scale=0,
                  min="9", max="9"),
            {**field("exact_tiny", "decimal", "decimal_range", precision=38, scale=38,
                     min="0.00000000000000000000000000000000000001",
                     max="0.00000000000000000000000000000000000001"),
             "semantic_type": "numeric_measure"},
            {**field("exact_negative_tiny", "decimal", "decimal_range", precision=38, scale=38,
                     min="-0.00000000000000000000000000000000000001",
                     max="-0.00000000000000000000000000000000000001"),
             "semantic_type": "numeric_measure"},
            {**field("exact_largest_fraction", "decimal", "decimal_range", precision=38, scale=38,
                     min="0." + "9" * 38, max="0." + "9" * 38),
             "semantic_type": "numeric_measure"},
            {**field("exact_negative_largest_fraction", "decimal", "decimal_range",
                     precision=38, scale=38, min="-0." + "9" * 38, max="-0." + "9" * 38),
             "semantic_type": "numeric_measure"},
            {**field("contact", "string", "masked_patterns",
                     patterns=[{"pattern": "email", "count": 0}]),
             "sensitive": True, "semantic_type": "email"},
        ]}]})


@pytest.mark.parametrize("text", ["1E-38", "-1E-38", "1E+3", "0E-38"])
def test_typed_csv_decimal_uses_plain_text_without_reinterpreting_strings(text):
    value = Decimal(text)
    assert encode_csv_cell(value) == format(value, "f")
    assert decode_csv_cell(encode_csv_cell(value)) == format(value, "f")
    assert decode_csv_cell(encode_csv_cell(text)) == text


@pytest.mark.parametrize("text", [
    "1E+1000000000", "-1E+1000000000", "1E-1000000000", "-1E-1000000000",
    "NaN", "sNaN", "Infinity", "-Infinity",
])
def test_csv_decimal_rejects_unbounded_or_nonfinite_values_before_formatting(monkeypatch, text):
    import test_data_agent.io.csv_encoding as encoding

    def unexpected_format(*args):
        pytest.fail("unbounded decimal reached fixed-point formatting")

    monkeypatch.setattr(encoding, "format", unexpected_format, raising=False)
    with pytest.raises(ValueError, match="decimal CSV value") as error:
        encoding.encode_csv_cell(Decimal(text))
    assert text not in str(error.value)


@pytest.mark.parametrize("units", [1, -1, 10**38 - 1, -(10**38 - 1)])
@pytest.mark.parametrize("scale", [0, 38])
def test_signed_decimal_extremes_use_full_declared_precision(units, scale):
    exact = decimal_from_units(units, precision=38, scale=scale)
    assert decimal_to_units(format(exact, "f"), precision=38, scale=scale) == units


@pytest.mark.parametrize("text", [
    "1E-38", "-1e-38", "+0." + "0" * 37 + "1", "1." + "0" * 38,
    "-0." + "0" * 38 + "1", "0." + "0" * 1000,
])
def test_decimal_extreme_length_support_keeps_strict_input_bounds(text):
    with pytest.raises(ValueError, match="invalid decimal value"):
        decimal_to_units(text, precision=38, scale=38)


@pytest.mark.parametrize("output", list(OutputFormat))
@pytest.mark.parametrize("seed", [0, 2**63 - 1])
def test_distribution_boundaries_replay_and_roundtrip(tmp_path, output, seed):
    if output is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    spec = _distribution_spec()
    folder = tmp_path / "generated"
    result = generate_dataset_bundle(spec, output_folder=folder, output_format=output, seed=seed)
    saved = load_dataset_spec(folder / "dataset_spec.yaml")
    restored = _typed_rows(folder, saved)
    assert restored == generate_dataset(saved, seed=seed)
    assert result.validation.valid and validate_dataset(load_dataset_rows(folder), saved).valid
    for row in restored["items"]:
        assert row["low_scale"] == 0.5 and row["high_scale"] == 5
        assert row["false_only"] is False and row["true_only"] is True
        assert row["category"] == "ready" and row["zero_only"] == 0
        assert 1e-10 <= row["tiny_positive"] <= 9.5e-10
        assert row["negative_only"] < 0
        assert row["empty"] == "" and len(row["short"]) == 2
        assert row["day"] == "2024-02-29"
        assert row["instant"] == "2024-02-29T12:00:00+03:00"
        assert row["whole"] == Decimal(9) and row["exact_tiny"] == Decimal("1e-38")
        assert row["exact_negative_tiny"] == Decimal("-1e-38")
        assert row["exact_largest_fraction"] == Decimal("0." + "9" * 38)
        assert row["exact_negative_largest_fraction"] == Decimal("-0." + "9" * 38)
        assert row["contact"].endswith("@example.test")


@pytest.mark.parametrize("output", list(OutputFormat))
def test_identifier_prefix_is_retained_metadata_and_never_output_text(tmp_path, output):
    if output is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    prefix = "fictional_source_marker_"
    spec = DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 6,
        "fields": [{"name": name, "data_type": "string", "is_identifier": True, "sensitive": True,
                    "semantic_type": "email", "distribution": {
                        "kind": "synthetic_identifier", "pool_size": size, "prefix": prefix}}
                   for name, size in [("left_key", 1), ("right_key", 2)]]}]})
    folder = tmp_path / "generated"
    generate_dataset_bundle(spec, output_folder=folder, output_format=output, seed=17)
    saved = load_dataset_spec(folder / "dataset_spec.yaml")
    assert all(field.distribution["prefix"] == prefix for field in saved.entities[0].fields)
    rows = _typed_rows(folder, saved)
    assert all(re.fullmatch(r"synthetic_[0-9]+", value)
               for row in rows["items"] for value in row.values())
    left = {row["left_key"] for row in rows["items"]}
    right = {row["right_key"] for row in rows["items"]}
    assert len(left) == 1 and len(right) == 2 and left.isdisjoint(right)
    for field in saved.entities[0].fields:
        field.distribution = {**field.distribution, "prefix": None}
    assert generate_dataset(saved, seed=17) == rows
    assert "Legacy metadata" in SyntheticIdentifierDistribution.model_json_schema()[
        "properties"]["prefix"]["description"]


def _rule_spec():
    return DatasetSpec.model_validate({"entities": [{"name": "items", "row_count": 3,
        "fields": [
            {"name": "quantity", "data_type": "integer", "distribution": {
                "kind": "numeric", "min_value": 2, "max_value": 2}},
            {"name": "doubled", "data_type": "integer", "distribution": {
                "kind": "numeric", "min_value": 0, "max_value": 4}},
            {"name": "adjusted", "data_type": "integer", "distribution": {
                "kind": "numeric", "min_value": 0, "max_value": 5}},
        ]}], "constraints": [{"type": "formula", "entity": "items",
            "fields": ["doubled"], "expression": "quantity * 2", "confidence": 1}]})


def _rules():
    return BusinessRules.model_validate({"field_rules": [
        {"table": "items", "field": "quantity", "min_value": 2, "max_value": 2}],
        "row_rules": [
            {"type": "formula", "table": "items", "field": "adjusted",
             "expression": "doubled + 1", "mode": "assign"},
            {"type": "formula", "table": "items", "field": "adjusted",
             "expression": "doubled + 1", "mode": "check"}]})


@pytest.mark.parametrize("delivery", ["embedded", "file", "payload"])
@pytest.mark.parametrize("output", list(OutputFormat))
@pytest.mark.parametrize("report_sections", [False, True])
def test_rule_delivery_native_formula_and_validation_toggles(
    tmp_path, monkeypatch, delivery, output, report_sections,
):
    """Direct MCP service payload coverage supplements the installed stdio matrix."""
    import test_data_agent.mcp_generator_server as server

    if output is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    spec, rules = _rule_spec(), _rules()
    spec.validation_settings = ValidationSettings(**{
        name: report_sections for name in (
            "validate_schema", "validate_relationships", "validate_constraints", "validate_privacy")
    })
    arguments = {}
    if delivery == "embedded":
        spec.business_rules = rules
    elif delivery == "file":
        (tmp_path / "rules.json").write_text(rules.model_dump_json())
        arguments["business_rules_path"] = "rules.json"
    else:
        arguments["business_rules_payload"] = rules.model_dump(mode="json")
    (tmp_path / "spec.json").write_text(spec.model_dump_json())
    result = server.generate_dataset("spec.json", "output", output_format=output.value,
                                     seed=17, **arguments)
    folder = tmp_path / "output"
    saved = load_dataset_spec(folder / "dataset_spec.yaml")
    assert saved.business_rules == rules
    assert saved.validation_settings == spec.validation_settings
    assert _typed_rows(folder, saved) == {
        "items": [{"quantity": 2, "doubled": 4, "adjusted": 5}] * 3}
    report = validate_dataset(load_dataset_rows(folder), saved)
    assert report.valid and result["validation"]["valid"]
    assert [section.name for section in report.sections] == (
        ["schema", "relationships", "constraints", "privacy", "business_rules"]
        if report_sections else ["business_rules"])
    manifest = json.loads((folder / "generation_manifest.json").read_text())
    assert manifest["business_validation"]["assigned_row_count"] == 3
    assert manifest["business_validation"] == result["business_validation"]
    assert manifest["source_rows_copied"] is False
    altered = _typed_rows(folder, saved)
    altered["items"][0]["adjusted"] = 0
    assert not validate_dataset(altered, saved).valid


@pytest.mark.parametrize("flags", list(product([False, True], repeat=4)))
@pytest.mark.parametrize("fail_fast", [False, True])
def test_validation_toggle_lattice_and_fail_fast_preserve_business_checks(flags, fail_fast):
    spec = DatasetSpec.model_validate({"entities": [
        {"name": "parents", "row_count": 1, "primary_key": "key", "fields": [
            {"name": "key", "data_type": "string", "is_identifier": True}]},
        {"name": "children", "row_count": 1, "fields": [
            {"name": "key", "data_type": "string", "is_identifier": True},
            {"name": "quantity", "data_type": "integer"},
            {"name": "doubled", "data_type": "integer"},
            {"name": "label", "data_type": "string"},
            {"name": "contact", "data_type": "string", "sensitive": True,
             "semantic_type": "email"}]}],
        "relationships": [{"parent_entity": "parents", "parent_field": "key",
                           "child_entity": "children", "child_field": "key", "confidence": 1}],
        "constraints": [{"type": "formula", "entity": "children", "fields": ["doubled"],
                         "expression": "quantity * 2", "confidence": 1}],
        "business_rules": {"field_rules": [
            {"table": "children", "field": "label", "allowed_values": ["ready"]}]}})
    rows = generate_dataset(spec, seed=17)
    rows["children"][0].update({"key": "synthetic_999", "quantity": "invalid",
                                "doubled": -1, "label": "blocked",
                                "contact": "fictional@example.invalid"})
    names = ["schema", "relationships", "constraints", "privacy"]
    spec.validation_settings = ValidationSettings(**{
        **{f"validate_{name}": enabled for name, enabled in zip(names, flags)},
        "fail_fast": fail_fast,
    })
    report = validate_dataset(rows, spec)
    enabled = [name for name, enabled in zip(names, flags) if enabled]
    expected = (enabled[:1] if fail_fast else enabled) + ["business_rules"]
    assert [section.name for section in report.sections] == expected
    assert all(section.failed for section in report.sections)
    assert not report.valid and not report.business_validation.valid


@pytest.mark.parametrize("output", list(OutputFormat))
@pytest.mark.parametrize("multi", [False, True], ids=["custom_single", "multi_folder"])
def test_profile_entity_mapping_overwrite_success_and_publication_rollback(
    tmp_path, monkeypatch, output, multi,
):
    from test_data_agent.io import path_policy, workflows

    if output is OutputFormat.PARQUET:
        pytest.importorskip("pyarrow")
    profile = DatasetProfile.model_validate({"entities": [
        {"name": name, "row_count": 2, "fields": [{"name": "amount", "data_type": "integer"}]}
        for name in (["first", "second"] if multi else ["first"])]})
    folder = tmp_path / "output"
    target = folder if multi else folder / f"custom.{output.value}"

    def generate(count, seed, overwrite=False):
        return generate_dataset_from_profile_artifacts(
            profile, count=count, seed=seed, output_path=target,
            output_format=output, overwrite=overwrite,
        )

    assert generate(2, 17)[0].valid
    before = {path.name: path.read_bytes() for path in folder.iterdir()}
    with monkeypatch.context() as patch:
        if multi:
            original = path_policy.os.replace

            def interrupt_directory(source, destination, **kwargs):
                result = original(source, destination, **kwargs)
                if destination == folder.name and str(source).startswith(f".{folder.name}."):
                    raise RuntimeError("fictional directory publication interruption")
                return result

            patch.setattr(path_policy.os, "replace", interrupt_directory)
        else:
            original = workflows.replace_path
            interrupted = False

            def interrupt_file(source, destination):
                nonlocal interrupted
                result = original(source, destination)
                if (not interrupted and source.name == "profile.json"
                        and destination.parent == folder):
                    interrupted = True
                    raise RuntimeError("fictional file publication interruption")
                return result

            patch.setattr(workflows, "replace_path", interrupt_file)
        with pytest.raises(RuntimeError, match="fictional .* publication interruption"):
            generate(3, 18, overwrite=True)
    assert {path.name: path.read_bytes() for path in folder.iterdir()} == before
    assert not list(tmp_path.glob(".output.*")) and not list(folder.glob(".*"))
    assert generate(3, 18, overwrite=True)[0].valid
    saved = load_dataset_spec(folder / ("dataset_spec.yaml" if multi else "dataset_spec.json"))
    rows = load_dataset_rows(folder)
    assert {name: len(values) for name, values in rows.items()} == {
        entity.name: 3 for entity in profile.entities}
    assert validate_dataset(rows, saved).valid
    manifest = json.loads((folder / "generation_manifest.json").read_text())
    if not multi:
        assert manifest["entity_artifacts"] == {"first": target.name}
    assert {path.name: path.read_bytes() for path in folder.iterdir()} != before
