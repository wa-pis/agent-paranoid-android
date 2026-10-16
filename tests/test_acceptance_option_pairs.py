"""Measured finite representative option pairs, beyond the route matrix.

This covers the declared values below, not every arbitrary DatasetSpec value.
The compatibility rules are part of the denominator, not runtime skip logic.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from itertools import combinations, product
import json

import pytest

from test_data_agent.cli import main
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec


AXES = {
    "output": ("csv", "json", "parquet", "sql"),
    "mode": ("valid", "edge", "load_test", "mixed", "negative"),
    "family": ("synthetic_identifier", "masked_patterns", "numeric", "decimal_range",
               "numeric_shape", "boolean", "date_range", "datetime_range", "categorical", "string_pattern"),
    "locale": ("en_US", "ru_RU"),
    "count": ("saved_3", "override_7"),
    "seed": ("saved_7", "override_19"),
    "validation": ("all_on", "optional_off"),
    "rules": ("embedded", "external_json"),
    "native": ("none", "formula", "temporal", "conditional_required", "aggregate_mapping"),
}
NUMERIC = frozenset({"numeric", "decimal_range", "numeric_shape"})
TEMPORAL = frozenset({"date_range", "datetime_range"})
TEXT = frozenset({"synthetic_identifier", "masked_patterns", "categorical", "string_pattern"})


def compatible(values):
    family, native = values[2], values[8]
    return (native != "formula" or family in NUMERIC) and (
        native != "temporal" or family in TEMPORAL) and (
        native != "conditional_required" or family in TEXT)


def _pairs(values):
    return frozenset((left, values[left], right, values[right])
                     for left, right in combinations(range(len(AXES)), 2))


@lru_cache(maxsize=1)
def covering_array():
    candidates = [values for values in product(*AXES.values()) if compatible(values)]
    coverage = [_pairs(values) for values in candidates]
    denominator = frozenset().union(*coverage)
    uncovered = set(denominator)
    selected = []
    while uncovered:
        best = max(range(len(candidates)), key=lambda index: len(coverage[index] & uncovered))
        assert coverage[best] & uncovered
        selected.append(candidates[best])
        uncovered.difference_update(coverage[best])
    return tuple(selected), denominator, len(candidates)


def pairwise_ledger():
    selected, denominator, feasible_count = covering_array()
    names = tuple(AXES)
    return {
        "scope": "finite representative option pairs through CLI main; source/interface routes are separate evidence",
        "axes": {key: list(values) for key, values in AXES.items()},
        "compatibility": ["native formula requires numeric/decimal_range/numeric_shape",
                          "native temporal requires date_range/datetime_range",
                          "native conditional_required uses one of four text families"],
        "feasible_combinations": feasible_count,
        "feasible_pair_denominator": len(denominator),
        "covered_pairs": len(set().union(*(_pairs(values) for values in selected))),
        "selected_cases": [{"id": f"pair-{index:03d}", "options": dict(zip(names, values))}
                           for index, values in enumerate(selected)],
        "limits": ["Only the listed representative values and declared compatible pairs are covered.",
                   "This does not establish all arbitrary values, boundaries, triples, or 179-property exhaustiveness.",
                   "No live database/provider or manual client acceptance is performed."],
    }


def _subject(family):
    distribution = {
        "synthetic_identifier": {"kind": family, "pool_size": 4},
        "masked_patterns": {"kind": family, "patterns": [{"pattern": "text_len_6", "count": 2}]},
        "numeric": {"kind": family, "min_value": 2, "max_value": 4, "scale_factor": 2},
        "decimal_range": {"kind": family, "precision": 38, "scale": 3,
                          "min": "9007199254740993.125", "max": "9007199254740993.125"},
        "numeric_shape": {"kind": family, "max_abs_magnitude": 1, "has_negative": True, "has_positive": True},
        "boolean": {"kind": family, "true_ratio": 1},
        "date_range": {"kind": family, "min": "2030-01-02", "max": "2030-01-04"},
        "datetime_range": {"kind": family, "min": "2030-01-02T01:02:03", "max": "2030-01-04T01:02:03"},
        "categorical": {"kind": family, "categories": [{"value": "ready", "count": 2}, {"value": "paused", "count": 1}]},
        "string_pattern": {"kind": family, "min_length": 3, "max_length": 8},
    }[family]
    data_type = {"numeric": "integer", "decimal_range": "decimal", "numeric_shape": "float",
                 "boolean": "boolean", "date_range": "date", "datetime_range": "datetime"}.get(family, "string")
    result = {"name": "subject", "data_type": data_type, "distribution": distribution}
    if family == "synthetic_identifier":
        result["is_identifier"] = True
    if family == "masked_patterns":
        result["sensitive"] = True
    if family in NUMERIC:
        result["semantic_type"] = "numeric_measure"
    return result


def _spec(options):
    subject = _subject(options["family"])
    fields = [subject, {"name": "pid", "data_type": "string", "is_identifier": True},
              {"name": "gate", "data_type": "string", "distribution": {
                  "kind": "categorical", "categories": [{"value": "ready"}]}},
              {"name": "contact", "data_type": "string", "sensitive": True, "semantic_type": "email"}]
    payload = {"entities": [{"name": "items", "row_count": 3, "primary_key": "pid", "fields": fields}],
               "generation_settings": {"seed": 7, "mode": options["mode"], "locale": options["locale"],
                                       "invalid_ratio": 0.5 if options["mode"] == "mixed" else 0,
                                       "output_format": options["output"]},
               "validation_settings": {name: options["validation"] == "all_on" for name in (
                   "validate_schema", "validate_relationships", "validate_constraints", "validate_privacy")}}
    native = options["native"]
    constraint = {"type": native, "entity": "items", "confidence": 1}
    if native == "formula":
        target = dict(subject, name="derived")
        fields.append(target)
        constraint.update(fields=["derived"], expression="subject")
    elif native == "temporal":
        fields.append(dict(subject, name="end"))
        constraint.update(fields=["subject", "end"])
    elif native == "conditional_required":
        fields.extend([{"name": "active", "data_type": "boolean", "distribution": {"kind": "boolean", "true_ratio": 1}},
                       {"name": "detail", "data_type": "string", "nullable": True, "null_ratio": 1}])
        constraint.update(fields=["detail"], condition={"field": "active", "equals": True})
    elif native == "aggregate_mapping":
        fields.append({"name": "child_count", "data_type": "integer", "semantic_type": "numeric_measure"})
        payload["entities"].append({"name": "children", "row_count": 3, "fields": [
            {"name": "parent_id", "data_type": "string", "is_identifier": True}]})
        payload["relationships"] = [{"parent_entity": "items", "parent_field": "pid",
                                    "child_entity": "children", "child_field": "parent_id", "confidence": 1}]
        constraint.update(fields=["child_count"], target_entity="children", aggregate="count")
    if native != "none":
        payload["constraints"] = [constraint]
    rules = {"field_rules": [{"table": "items", "field": "gate", "required": True}]}
    if options["rules"] == "embedded":
        payload["business_rules"] = rules
    return DatasetSpec.model_validate(payload), rules


def _assert_domain(family, values):
    assert all(value is not None for value in values)
    if family == "synthetic_identifier":
        assert all(value.startswith("synthetic_") for value in values)
        assert len(set(values)) == min(len(values), 4)
    elif family == "masked_patterns":
        assert all(value.startswith("synthetic_") for value in values)
        assert all("text_len_6" not in value for value in values)
    elif family == "numeric":
        assert all(4 <= Decimal(str(value)) <= 8 for value in values)
    elif family == "decimal_range":
        assert all(Decimal(str(value)) == Decimal("9007199254740993.125") for value in values)
    elif family == "numeric_shape":
        assert all(-90 <= float(value) <= 90 for value in values)
    elif family == "boolean":
        assert all(value is True or value == "True" for value in values)
    elif family == "date_range":
        assert all(date(2030, 1, 2) <= date.fromisoformat(str(value)) <= date(2030, 1, 4) for value in values)
    elif family == "datetime_range":
        assert all(datetime(2030, 1, 2, 1, 2, 3) <= datetime.fromisoformat(str(value)) <=
                   datetime(2030, 1, 4, 1, 2, 3) for value in values)
    elif family == "categorical":
        assert set(values) <= {"ready", "paused"}
    else:
        assert all(3 <= len(value) <= 8 for value in values)


def test_finite_pairwise_array_covers_every_feasible_pair():
    selected, denominator, feasible_count = covering_array()
    # Cartesian sizes minus the 21 explicitly incompatible family/native pairs.
    assert feasible_count == 18_560
    assert len(denominator) == 464
    assert len(selected) == 52
    assert all(compatible(values) for values in selected)
    assert set().union(*(_pairs(values) for values in selected)) == denominator
    assert pairwise_ledger()["covered_pairs"] == 464


@pytest.mark.parametrize("values", covering_array()[0], ids=lambda values: "-".join(values))
def test_finite_option_pair_case_has_independent_behavioral_oracles(tmp_path, capsys, values):
    options = dict(zip(AXES, values))
    spec, rules = _spec(options)
    source = tmp_path / "spec.json"
    source.write_text(spec.model_dump_json())
    output = tmp_path / "output"
    args = ["generate", str(source), "--output", str(output)]
    if options["count"] == "override_7":
        args.extend(["--count", "7"])
    if options["seed"] == "override_19":
        args.extend(["--seed", "19"])
    if options["rules"] == "external_json":
        rule_path = tmp_path / "rules.json"
        rule_path.write_text(json.dumps(rules))
        args.extend(["--business-rules", str(rule_path)])
    status = main(args)
    assert status in (0, 1)
    capsys.readouterr()
    rows = load_dataset_rows(output)
    expected_count = 7 if options["count"] == "override_7" else (30 if options["mode"] == "load_test" else 3)
    seed = 19 if options["seed"] == "override_19" else 7
    assert len(rows["items"]) == expected_count
    assert len({row["pid"] for row in rows["items"]}) == expected_count
    _assert_domain(options["family"], [row["subject"] for row in rows["items"]])
    assert all(row["contact"].endswith("@example.test") for row in rows["items"])
    broken = sum(row["gate"] in (None, "") for row in rows["items"])
    if options["mode"] == "negative":
        assert broken == expected_count
    elif options["mode"] == "mixed":
        assert 0 <= broken <= expected_count
    else:
        assert broken == 0
    assert status == int(broken > 0)
    native = options["native"]
    if native == "formula":
        assert all(Decimal(str(row["derived"])) == Decimal(str(row["subject"])) for row in rows["items"])
    elif native == "temporal":
        assert all(str(row["end"]) >= str(row["subject"]) for row in rows["items"])
    elif native == "conditional_required":
        assert all(row["detail"] for row in rows["items"])
    elif native == "aggregate_mapping":
        assert len(rows["children"]) == expected_count
        counts = Counter(row["parent_id"] for row in rows["children"])
        assert set(counts) <= {row["pid"] for row in rows["items"]}
        assert all(int(row["child_count"]) == counts[row["pid"]] for row in rows["items"])
    saved = load_dataset_spec(output / "dataset_spec.yaml")
    assert saved.generation_settings.seed == seed
    assert saved.generation_settings.locale == options["locale"]
    assert saved.business_rules is not None
    manifest = json.loads((output / "generation_manifest.json").read_text())
    assert manifest["seed"] == seed
    assert manifest["source_rows_copied"] is False
    assert manifest["business_validation"]["expectations_met"]
    assert manifest["business_validation"]["unexpected_violation_count"] == 0
    assert manifest["validation_valid"] is (broken == 0)
    replay = tmp_path / "replay"
    replay_args = list(args)
    replay_args[replay_args.index("--output") + 1] = str(replay)
    assert main(replay_args) == status
    assert load_dataset_rows(replay) == rows
