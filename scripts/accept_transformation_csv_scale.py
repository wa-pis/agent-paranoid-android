"""Opt-in fictional private CSV acceptance; no DB, API, receipts or permanent output.

Run against an installed candidate with --rows 300000 --columns 50. This is
private replacement-only evidence, not public activation or full RC acceptance.
"""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_from_paths
from test_data_agent.io.transformation_publish import temporary_csv_publication


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=300_000)
    parser.add_argument("--columns", type=int, default=50)
    parser.add_argument("--max-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--max-seconds", type=float, default=1800)
    args = parser.parse_args()
    if not 1 <= args.rows <= 1_000_000 or not 2 <= args.columns <= 100:
        parser.error("fixture supports 1..1000000 rows and 2..100 columns")
    if not 0 < args.max_bytes <= 2**63 - 1:
        parser.error("max-bytes must be a positive signed 64-bit integer")
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("max-seconds must be finite and positive")
    started = monotonic()
    budget = GenerationBudget(args.max_seconds)
    max_bytes = args.max_bytes
    names = ["field_" + chr(97 + i // 26) + chr(97 + i % 26) for i in range(args.columns)]
    with TemporaryDirectory(prefix="apa-scale-fictional-") as directory:
        root = Path(directory).resolve()
        source_path = root / "items.csv"
        with source_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(names)
            for index in range(args.rows):
                writer.writerow(["alpha" if index % 2 == 0 else "beta"] * args.columns)
        def mapping(path: str) -> dict:
            return {"kind": "csv", "path": path, "source_columns": ["old"], "replacement_columns": ["new"]}
        (root / "global.csv").write_text("old,new\nalpha,omega\nbeta,theta\nomega,cascade\n", encoding="utf-8")
        (root / "column.csv").write_text("old,new\nalpha,first\nbeta,second\n", encoding="utf-8")
        policy = {"schema_version": "0.1", "schema_fingerprint": "0" * 64, "seed": 7,
                  "resource_limits": {"max_input_rows": 1_000_000, "max_input_columns": 100,
                      "max_input_cells": 100_000_000, "max_input_file_bytes": max_bytes,
                      "max_total_input_bytes": max_bytes,
                      "max_output_bytes": max_bytes},
                  "file_text_mapping": mapping("global.csv"), "fields": [
                      {"entity": "items", "field": name, "sensitivity": "non_sensitive",
                       "behavior": {"action": "replace_text", **({"mapping": mapping("column.csv")} if i == 0 else {})}}
                      for i, name in enumerate(names)]}
        source = SnapshotPart("source", "items", source_path.read_bytes())
        source_hash = hashlib.sha256(source.payload).hexdigest()
        profile = _profile_transformation_source(source, BehaviorPolicy.model_validate(policy),
            budget=budget, max_bytes=max_bytes)
        policy["schema_fingerprint"] = transformation_schema_fingerprint(profile)
        (root / "behavior.yaml").write_text(yaml.safe_dump(policy), encoding="utf-8")
        del source, profile
        print(json.dumps({"stage": "profile", "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
        request = prepare_csv_review_from_paths(source_path, "items", root, "behavior.yaml",
            max_total_bytes=max_bytes, max_review_bytes=1024 * 1024, budget=budget)
        print(json.dumps({"stage": "review", "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
        with temporary_csv_publication(request, max_total_bytes=max_bytes,
                max_review_bytes=1024 * 1024, max_output_bytes=max_bytes, budget=budget) as output:
            manifest = json.loads((output / "manifest.json").read_text())
            count = 0
            with (output / "dataset.csv").open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                assert next(reader) == names
                for index, row in enumerate(reader):
                    budget.check("scale acceptance readback")
                    expected = ["first" if index % 2 == 0 else "second"] + [
                        "omega" if index % 2 == 0 else "theta"] * (args.columns - 1)
                    assert row == expected, "ordered replacement readback mismatch"
                    count += 1
            assert count == args.rows
            assert manifest["origin"] == "transformed_mixed"
            assert manifest["provenance"]["output_cells"] == args.rows * args.columns
            assert manifest["provenance"]["replacement_percent"] == "100.00"
            output_bytes = (output / "dataset.csv").stat().st_size
            assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
        assert not output.parent.exists(), "temporary publication not removed"
    assert not root.exists(), "fictional inputs not removed"
    print(json.dumps({"status": "passed", "rows": args.rows, "columns": args.columns,
        "cells": args.rows * args.columns, "output_bytes": output_bytes,
        "max_bytes": max_bytes, "max_seconds": args.max_seconds,
        "elapsed_seconds": round(monotonic() - started, 3),
        "scope": "private replacement-only CSV; no public activation"}), flush=True)


if __name__ == "__main__":
    main()
