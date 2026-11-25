"""Source-free differential probe. Persist hashes and metadata, never generated rows."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
import hashlib
import importlib.metadata
from itertools import permutations
import json
import os
from pathlib import Path
import platform
import shutil
import tempfile
from typing import Any

import test_data_agent
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.settings import OutputFormat
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.io.readers import load_dataset_rows, load_dataset_spec
from test_data_agent.io.workflows import generate_dataset_bundle
from test_data_agent.validation import validate_dataset

SEED = 170117


def decimal_field(name: str, low: str = "-7.25", high: str = "23.75", *, nullable: bool = False,
                  null_ratio: float = 0) -> dict[str, Any]:
    return {"name": name, "data_type": "decimal", "nullable": nullable, "null_ratio": null_ratio,
            "distribution": {"kind": "decimal_range", "precision": 6, "scale": 2,
                             "min": low, "max": high}}


def fields() -> list[dict[str, Any]]:
    return [
        {"name": "row_id", "data_type": "integer", "is_identifier": True},
        {"name": "quantity", "data_type": "integer",
         "distribution": {"kind": "numeric", "min_value": -7, "max_value": 27}},
        {"name": "ratio", "data_type": "float",
         "distribution": {"kind": "numeric", "min_value": -0.75, "max_value": 3.5}},
        decimal_field("amount"),
        {"name": "active", "data_type": "boolean",
         "distribution": {"kind": "boolean", "true_ratio": 0.3}},
        {"name": "label", "data_type": "string",
         "distribution": {"kind": "string_pattern", "min_length": 3, "max_length": 23}},
        {"name": "day", "data_type": "date",
         "distribution": {"kind": "date_range", "min": "2023-02-01", "max": "2023-03-01"}},
        {"name": "moment", "data_type": "datetime",
         "distribution": {"kind": "date_range", "min": "2023-02-01T01:02:03+00:00",
                          "max": "2023-03-01T04:05:06+00:00"}},
        decimal_field("optional_amount", nullable=True, null_ratio=0.3),
        decimal_field("absent_amount", nullable=True, null_ratio=1),
        {"name": "optional_label", "data_type": "string", "nullable": True, "null_ratio": 0.3},
        {"name": "repeated_key", "data_type": "string", "is_identifier": True,
         "distribution": {"kind": "synthetic_identifier", "pool_size": 5}},
        {"name": "email", "data_type": "string", "sensitive": True, "semantic_type": "email"},
        {"name": "phone", "data_type": "string", "sensitive": True, "semantic_type": "phone"},
        {"name": "ssn", "data_type": "string", "sensitive": True, "semantic_type": "ssn"},
    ]


def base(mode: str = "valid") -> dict[str, Any]:
    return {"schema_version": "1.1", "entities": [
        {"name": "items", "row_count": 31, "primary_key": "row_id", "fields": fields()}],
        "generation_settings": {"seed": SEED, "locale": "en_US", "mode": mode,
                                "invalid_ratio": 0.2 if mode in {"mixed", "negative"} else 0,
                                "load_multiplier": 3, "output_format": "csv"}}


def linked(mode: str = "valid") -> dict[str, Any]:
    result = base(mode)
    result["entities"] = []
    for name, count, parent in (("leaves", 37, "branches"), ("roots", 7, None),
                                ("branches", 17, "roots")):
        columns = fields()
        if parent:
            columns.insert(1, {"name": parent + "_id", "data_type": "integer", "is_identifier": True})
        result["entities"].append({"name": name, "row_count": count,
                                   "primary_key": "row_id", "fields": columns})
    result["relationships"] = [
        {"parent_entity": parent, "parent_field": "row_id", "child_entity": child,
         "child_field": parent + "_id", "relationship_type": "many_to_one", "confidence": 1}
        for parent, child in (("roots", "branches"), ("branches", "leaves"))]
    return result


def cases() -> list[tuple[str, dict[str, Any]]]:
    result = [("ordinary_" + mode, base(mode))
              for mode in ("valid", "edge", "mixed", "negative", "load_test")]
    native = base()
    native["entities"][0]["fields"].extend([
        {"name": "twice_quantity", "data_type": "integer"},
        {"name": "started", "data_type": "date"},
        {"name": "ended", "data_type": "date"},
    ])
    native["constraints"] = [
        {"type": "formula", "entity": "items", "fields": ["twice_quantity"],
         "expression": "quantity * 2", "confidence": 1},
        {"type": "temporal", "entity": "items", "fields": ["started", "ended"], "confidence": 1},
    ]
    result.append(("ordinary_native_formula_temporal", native))
    rules = base()
    rules["entities"][0]["fields"].append(decimal_field("total", "-30.00", "100.00"))
    rules["business_rules"] = {"row_rules": [
        {"type": "formula", "table": "items", "field": "total", "expression": "amount * 2"},
        {"type": "conditional_required", "table": "items", "when": {"field": "active", "equals": True},
         "required_fields": ["total"]},
    ]}
    result.append(("ordinary_decimal_business_formula", rules))
    conditional = deepcopy(rules)
    conditional["business_rules"]["row_rules"][0]["when"] = {"field": "active", "equals": True}
    result.append(("ordinary_conditional_decimal_formula", conditional))
    aggregate_rules = deepcopy(rules)
    aggregate_rules["business_rules"]["cross_table_rules"] = [
        {"type": "aggregate_formula", "table": "items", "field": "total", "expression": "sum('amount') * 2"}]
    result.append(("additional_decimal_business_aggregate", aggregate_rules))
    aggregate_native = linked()
    aggregate_native["entities"][1]["fields"].append(decimal_field("subtotal", "-1000.00", "1000.00"))
    aggregate_native["constraints"] = [{
        "type": "aggregate_mapping", "entity": "roots", "fields": ["subtotal"],
        "target_entity": "branches", "target_field": "amount", "aggregate": "sum", "confidence": 1}]
    result.append(("additional_decimal_native_aggregate", aggregate_native))
    result.append(("ordinary_relations_parent_after_child", linked()))
    for mode in ("valid", "mixed"):
        scenario = {"schema_version": "1.1", "entities": [
            {"name": "parents", "row_count": 3, "primary_key": "key", "fields": [
                {"name": "key", "data_type": "integer", "is_identifier": True},
                decimal_field("amount")]},
            {"name": "children", "row_count": 6, "fields": [
                {"name": "parent_key", "data_type": "integer", "is_identifier": True},
                decimal_field("amount")]},
        ], "relationships": [{"parent_entity": "parents", "parent_field": "key",
                              "child_entity": "children", "child_field": "parent_key", "confidence": 1}],
            "relational_scenarios": [{"parent_entity": "parents", "parent_field": "key",
                                       "child_entity": "children", "child_field": "parent_key",
                                       "orphan_count": 2 if mode == "mixed" else 0,
                                       "fanout_counts": [3, 1, 0] if mode == "mixed" else [1, 2, 3]}],
            "generation_settings": {"seed": SEED, "mode": mode, "locale": "en_US", "output_format": "csv"}}
        result.append(("ordinary_scenario_" + mode, scenario))
    for engine in ("scalable-v1", "scalable-relational-v1"):
        for mode in ("valid", "edge"):
            for workers, batch in ((1, 7), (2, 19)):
                spec = linked(mode) if engine == "scalable-relational-v1" else base(mode)
                spec["generation_settings"]["execution_policy"] = {
                    "engine": engine, "workers": workers, "batch_size": batch,
                    "max_rows": 500, "max_cells": 10000, "max_seconds": 120,
                    "max_memory_bytes": 2 * 1024**3, "max_output_bytes": 32 * 1024**2,
                    "max_temporary_bytes": 32 * 1024**2}
                result.append((f"{engine}_{mode}_workers{workers}_batch{batch}", spec))
    calculated = {"schema_version": "1.1", "entities": [
        {"name": "parents", "row_count": 2, "primary_key": "row_id", "fields": [
            {"name": "row_id", "data_type": "integer", "is_identifier": True},
            {"name": "subtotal", "data_type": "integer"},
            {"name": "total", "data_type": "integer"}]},
        {"name": "children", "row_count": 4, "fields": [
            {"name": name, "data_type": "integer"} for name in ("parent_key", "units", "amount")]},
    ], "relationships": [{"parent_entity": "parents", "parent_field": "row_id",
                           "child_entity": "children", "child_field": "parent_key", "confidence": 1}],
        "constraints": [
            {"type": "formula", "entity": "parents", "fields": ["total"],
             "expression": "subtotal * 2", "confidence": 1},
            {"type": "aggregate_mapping", "entity": "parents", "fields": ["subtotal"],
             "target_entity": "children", "target_field": "amount", "aggregate": "sum", "confidence": 1},
            {"type": "formula", "entity": "children", "fields": ["amount"],
             "expression": "units * 2", "confidence": 1}],
        "generation_settings": {"seed": SEED, "locale": "en_US", "mode": "valid", "output_format": "csv"}}
    for index, constraints in enumerate(permutations(calculated["constraints"])):
        candidate = deepcopy(calculated)
        candidate["constraints"] = list(constraints)
        result.append((f"intentional_mixed_calculation_fix_order{index}", candidate))
    return result


def canonical(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"type": "decimal", "text": str(value)}
    if isinstance(value, (date, datetime)):
        return {"type": type(value).__name__, "text": value.isoformat()}
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(item) for item in value]
    return value


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def stable_manifest(value: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(value)
    reproducibility = value.get("reproducibility")
    if reproducibility:
        reproducibility["output_sha256"].pop("generation_statistics.json", None)
    return value


def execute_case(name: str, payload: dict[str, Any], scratch: Path) -> dict[str, Any]:
    spec = DatasetSpec.model_validate(payload)
    spec_before = spec.model_dump(mode="json")
    summary: dict[str, Any] = {"input_sha256": digest(spec_before),
                               "engine": payload["generation_settings"].get("execution_policy", {}).get("engine", "ordinary"),
                               "mode": spec.generation_settings.mode.value,
                               "field_types": sorted({field.data_type.value for entity in spec.entities for field in entity.fields})}
    try:
        if spec.generation_settings.execution_policy is None:
            direct = generate_dataset(spec, seed=SEED)
            assert direct == generate_dataset(spec, seed=SEED)
            summary["direct_rows_sha256"] = digest(direct)
            summary["direct_row_counts"] = {key: len(rows) for key, rows in direct.items()}
            decimal_values = [row[field.name] for entity in spec.entities for row in direct[entity.name]
                              for field in entity.fields if field.data_type.value == "decimal"]
            summary["direct_decimal_native_cells"] = sum(isinstance(value, Decimal) for value in decimal_values)
            if spec.generation_settings.mode.value in {"valid", "edge", "load_test"}:
                assert all(value is None or isinstance(value, Decimal) for value in decimal_values)
        output = scratch / name
        result = generate_dataset_bundle(spec, output_folder=output, output_format=OutputFormat.CSV, seed=SEED)
        saved = load_dataset_spec(output / "dataset_spec.yaml")
        loaded = load_dataset_rows(output)
        roundtrip = validate_dataset(loaded, saved)
        summary.update({
            "result": result.model_dump(mode="json") if hasattr(result, "model_dump") else canonical(vars(result)),
            "loaded_rows_sha256": digest(loaded),
            "loaded_cell_types": {entity: dict(sorted(Counter(type(value).__name__ for row in rows for value in row.values()).items()))
                                  for entity, rows in loaded.items()},
            "saved_spec_sha256": digest(saved.model_dump(mode="json")),
            "roundtrip_validation_sha256": digest(roundtrip.model_dump(mode="json")),
            "roundtrip_valid": roundtrip.valid,
            "csv_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.glob("*.csv"))},
            "validation_report_sha256": digest(json.loads((output / "validation_report.json").read_text())),
            "manifest": stable_manifest(json.loads((output / "generation_manifest.json").read_text())),
            "spec_unmutated": spec_before == spec.model_dump(mode="json"),
        })
        if (output / "business_validation_report.json").exists():
            summary["business_validation_sha256"] = digest(json.loads((output / "business_validation_report.json").read_text()))
        if (output / "generation_statistics.json").exists():
            statistics = json.loads((output / "generation_statistics.json").read_text())
            summary["stable_statistics"] = {key: statistics[key] for key in ("engine", "rows", "task_count", "dataset_bytes")}
        summary["status"] = "ok"
    except Exception as error:
        summary.update({"status": "error", "exception_type": type(error).__name__,
                        "exception_message_sha256": digest(str(error))})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--only-prefix", default="")
    args = parser.parse_args()
    os.umask(0o077)
    scratch = Path(tempfile.mkdtemp(prefix="rows-", dir=args.output.parent))
    names = ("Faker", "pydantic", "PyYAML", "pyarrow", "mcp", "duckdb")
    dependencies = {}
    for name in names:
        try:
            dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            dependencies[name] = None
    evidence: dict[str, Any] = {"python": platform.python_version(),
                               "module": str(Path(test_data_agent.__file__).resolve()),
                               "dependencies": dependencies,
                               "seed": SEED, "cases": {}}
    try:
        for name, payload in cases():
            if not name.startswith(args.only_prefix):
                continue
            evidence["cases"][name] = execute_case(name, payload, scratch)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True))
    finally:
        shutil.rmtree(scratch)
    print(json.dumps({"cases": len(evidence["cases"]), "ok": sum(item["status"] == "ok" for item in evidence["cases"].values()),
                      "output": str(args.output)}))


if __name__ == "__main__":
    main()
