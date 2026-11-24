"""Summarize precise parity and intentional metadata/behavior differences."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent


def paths(old, new, prefix=""):
    if isinstance(old, dict) and isinstance(new, dict):
        return [item for key in sorted(set(old) | set(new))
                for item in paths(old.get(key), new.get(key), f"{prefix}.{key}".lstrip("."))]
    return [] if old == new else [prefix]


def normalize_optional_dependency(value):
    value = deepcopy(value)
    metadata = value.get("manifest", {}).get("reproducibility", {})
    versions = metadata.get("normalized_dependencies", {})
    versions.pop("duckdb", None)
    if "normalized_dependencies_sha256" in metadata:
        metadata["normalized_dependencies_sha256"] = hashlib.sha256(json.dumps(
            versions, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return value


def main():
    os.umask(0o077)
    old = json.loads((ROOT / "release-complete.json").read_text())
    new = json.loads((ROOT / "target-complete.json").read_text())
    shared_dependencies_match = all(version == new["dependencies"][name]
                                    for name, version in old["dependencies"].items() if version is not None)
    unchanged = {}
    expected = {}
    for name, before in old["cases"].items():
        after = new["cases"][name]
        if name.startswith("intentional_"):
            expected[name] = {"release_status": before["status"], "target_status": after["status"],
                              "release_exception": before.get("exception_type"),
                              "target_direct_rows_sha256": after.get("direct_rows_sha256"),
                              "target_validation_valid": after.get("result", {}).get("validation", {}).get("valid")}
            continue
        raw = paths(before, after)
        normalized = paths(normalize_optional_dependency(before), normalize_optional_dependency(after))
        unchanged[name] = {"release_status": before["status"], "target_status": after["status"],
                           "raw_difference_paths": raw, "normalized_difference_paths": normalized,
                           "csv_artifact_count": len(after.get("csv_sha256", {})),
                           "row_counts": after.get("result", {}).get("row_counts", {}),
                           "field_types": after["field_types"],
                           "direct_decimal_native_cells": after.get("direct_decimal_native_cells")}
        assert before["status"] == after["status"] == "ok"
        assert not normalized, (name, normalized)
        assert raw == ["manifest.reproducibility.normalized_dependencies.duckdb",
                       "manifest.reproducibility.normalized_dependencies_sha256"], (name, raw)
    worker_invariance = {}
    for side, evidence in (("release", old), ("target", new)):
        worker_invariance[side] = {}
        for engine in ("scalable-v1", "scalable-relational-v1"):
            for mode in ("valid", "edge"):
                a = evidence["cases"][f"{engine}_{mode}_workers1_batch7"]
                b = evidence["cases"][f"{engine}_{mode}_workers2_batch19"]
                worker_invariance[side][f"{engine}_{mode}"] = {
                    "csv_bytes_equal": a["csv_sha256"] == b["csv_sha256"],
                    "logical_rows_equal": a["loaded_rows_sha256"] == b["loaded_rows_sha256"]}
                assert all(worker_invariance[side][f"{engine}_{mode}"].values())
    intended_hashes = {item["target_direct_rows_sha256"] for item in expected.values()}
    assert len(intended_hashes) == 1
    assert all(item["release_status"] == "error" and item["target_status"] == "ok"
               and item["target_validation_valid"] for item in expected.values())
    summary = {
        "seed": old["seed"], "python": old["python"],
        "own_source_roots": {"release": old["module"], "target": new["module"]},
        "shared_dependency_versions_match": shared_dependencies_match,
        "dependencies": {"release": old["dependencies"], "target": new["dependencies"]},
        "intentional_environment_metadata_delta": "DuckDB2.0.1 is the new optional profiling extra; no generation case imports or uses it. Target now records it in normalized dependency metadata; frozen release does not enumerate DuckDB.",
        "unchanged_case_count": len(unchanged), "unchanged_runtime_mismatch_count": 0,
        "unchanged_cases": unchanged, "worker_and_batch_invariance": worker_invariance,
        "intended_calculation_order_fix": expected,
        "persistence": "Private directory; generated CSV bundles removed in finally; only synthetic fixture/probe and metadata/hashes retained.",
    }
    assert old["python"] == new["python"] and shared_dependencies_match
    (ROOT / "comparison.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps({"unchanged": len(unchanged), "runtime_mismatches": 0,
                      "expected_fix_cases": len(expected), "worker_invariance_checks": 8,
                      "summary": str(ROOT / "comparison.json")}))


if __name__ == "__main__":
    main()
