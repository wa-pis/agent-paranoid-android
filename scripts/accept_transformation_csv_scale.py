"""Opt-in fictional local-file acceptance; no DB, API, receipts or permanent output.

Run against an installed candidate with --rows 2051 --columns 3 --entrance cli
or --entrance mcp. The default private route retains historical scale coverage.
"""

import argparse
import asyncio
from contextlib import nullcontext
import csv
from datetime import timedelta
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory, TemporaryFile
from time import monotonic

import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_from_paths
from test_data_agent.io.transformation_publish import temporary_csv_publication


FIXTURE_VALUES = ("alpha", "beta", "first", "second", "omega", "theta", "cascade")


def _assert_summary(text: str) -> None:
    assert not any(f'"{value}"' in text for value in FIXTURE_VALUES), "fixture literal in response"


def _registered_output(entrance: str, source: Path, digest: str, max_bytes: int,
                       budget: GenerationBudget, *, include_refusals: bool, refusal: str | None) -> Path:
    root = source.parent
    destination = root / "registered-output"
    existing = root / "existing-output"
    sentinel = existing / "owner.txt"
    if include_refusals or refusal == "overwrite":
        existing.mkdir()
        sentinel.write_text("fictional owner artifact", encoding="utf-8")
    before = set(root.iterdir())
    policy_files = [root / name for name in ("behavior.yaml", "column.csv", "global.csv")]
    policy_hashes = [hashlib.sha256(path.read_bytes()).digest() for path in policy_files]
    env = {key: os.environ[key] for key in ("PATH", "LANG", "TMPDIR", "SYSTEMROOT") if key in os.environ}
    seconds = str(budget.remaining_seconds())
    env.update(TEST_DATA_AGENT_WORKSPACE_ROOT=str(root),
               TEST_DATA_AGENT_MAX_GENERATION_SECONDS=seconds,
               TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS=seconds)
    refusal_cases = {"digest": ("0" * 64, max_bytes, destination),
                     "budget": (digest, 1, destination), "overwrite": (digest, max_bytes, existing)}
    cases = ((refusal_cases[refusal],) if refusal is not None else
             (*tuple(refusal_cases.values() if include_refusals else ()), (digest, max_bytes, destination)))

    def refused_cleanly() -> None:
        assert set(root.iterdir()) == before
        assert [hashlib.sha256(path.read_bytes()).digest() for path in policy_files] == policy_hashes
        if sentinel.exists() or refusal == "overwrite" or include_refusals:
            assert list(existing.iterdir()) == [sentinel]
            assert sentinel.read_text(encoding="utf-8") == "fictional owner artifact"

    if entrance == "cli":
        def call(*arguments: str, failure: bool = False) -> dict:
            budget.check("installed CLI acceptance")
            result = subprocess.run([sys.executable, "-I", "-m", "test_data_agent.cli", *arguments],
                cwd=root, env=env, capture_output=True, text=True, timeout=budget.remaining_seconds())
            _assert_summary(result.stdout + result.stderr)
            assert (result.returncode != 0) == failure, "unexpected CLI result"
            return json.loads(result.stdout)

        policy = root / "behavior.yaml"
        review = call("transform-review", str(source), str(policy), "--table", "items")
        assert review["snapshot_sha256"] == digest
        for fingerprint, cap, output in cases:
            failure = (fingerprint, cap, output) != (digest, max_bytes, destination)
            result = call("transform-execute", str(source), str(policy), str(output),
                "--table", "items", "--snapshot-sha256", fingerprint, "--max-output-bytes", str(cap),
                "--max-total-input-bytes", str(max_bytes), "--json", failure=failure)
            if failure:
                assert "error" in result
                refused_cleanly()
            else:
                assert result["result"]["snapshot_sha256"] == digest
    else:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def invoke() -> None:
            timeout = budget.remaining_seconds()
            sdk_timeout = timeout if int(version("mcp").split(".")[0]) >= 2 else timedelta(seconds=timeout)
            parameters = StdioServerParameters(command=sys.executable,
                args=["-I", "-m", "test_data_agent.mcp_generator_server"], env=env, cwd=str(root))
            with TemporaryFile(mode="w+", encoding="utf-8") as stderr:
                async with asyncio.timeout(timeout), stdio_client(parameters, errlog=stderr) as (reader, writer):
                    async with ClientSession(reader, writer, read_timeout_seconds=sdk_timeout) as session:
                        await session.initialize()
                        names = {tool.name for tool in (await session.list_tools()).tools}
                        assert {"review_transformation", "execute_transformation"} <= names
                        assert not {"transform-approve", "issue_local_receipt"} & names
                        args = dict(input_path=source.name, policy_path="behavior.yaml", table_name="items")
                        review = (await session.call_tool("review_transformation", args)).model_dump(by_alias=True)
                        _assert_summary(json.dumps(review))
                        assert not review.get("isError") and review["structuredContent"]["snapshot_sha256"] == digest
                        for fingerprint, cap, output in cases:
                            failure = (fingerprint, cap, output) != (digest, max_bytes, destination)
                            response = (await session.call_tool("execute_transformation", dict(args,
                                output_path=output.name, snapshot_sha256=fingerprint, max_output_bytes=cap,
                                max_total_input_bytes=max_bytes))).model_dump(by_alias=True)
                            _assert_summary(json.dumps(response))
                            assert bool(response.get("isError")) == failure, "unexpected MCP result"
                            if failure:
                                if cap == 1:
                                    assert "limit_exceeded" in json.dumps(response), "expected output byte refusal"
                                refused_cleanly()
                            else:
                                assert response["structuredContent"]["snapshot_sha256"] == digest
                stderr.seek(0)
                _assert_summary(stderr.read())

        asyncio.run(invoke())
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=300_000)
    parser.add_argument("--columns", type=int, default=50)
    parser.add_argument("--input-format", choices=("csv", "parquet", "postgres_query", "trino_query"), default="csv")
    parser.add_argument("--output-format", choices=("csv", "parquet", "postgresql_sql"), default="csv")
    parser.add_argument("--max-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--max-seconds", type=float, default=1800)
    parser.add_argument("--entrance", choices=("private", "cli", "mcp"), default="private")
    parser.add_argument("--execution-only", action="store_true",
        help="Isolate registered review, publication and readback from the refusal suite.")
    parser.add_argument("--refusal", choices=("digest", "budget", "overwrite"),
        help="Run one isolated SDK stdio refusal; never publish a successful output.")
    args = parser.parse_args()
    if args.refusal and (args.entrance != "mcp" or args.execution_only):
        parser.error("--refusal requires MCP and excludes --execution-only")
    if args.execution_only and args.entrance == "private":
        parser.error("--execution-only requires a registered entrance")
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
        source_path = root / ("items." + args.input_format)
        if args.input_format == "csv":
            with source_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(names)
                for index in range(args.rows):
                    budget.check("scale fixture creation")
                    writer.writerow(["alpha" if index % 2 == 0 else "beta"] * args.columns)
        else:
            import pyarrow as pa
            import pyarrow.parquet as pq

            schema = pa.schema([pa.field(name, pa.string(), nullable=False) for name in names])
            native_path = root / "native.parquet" if args.input_format.endswith("_query") else source_path
            with pq.ParquetWriter(native_path, schema) as writer:
                for start in range(0, args.rows, 1024):
                    budget.check("scale fixture creation")
                    values = ["alpha" if index % 2 == 0 else "beta"
                              for index in range(start, min(start + 1024, args.rows))]
                    column = pa.array(values, type=pa.string())
                    writer.write_table(pa.Table.from_arrays([column] * args.columns, schema=schema))
            if native_path != source_path:
                from test_data_agent.io.transformation_query_snapshot import _capture_query_result

                query = "SELECT " + ", ".join(names) + " FROM fictional.items"
                source_path.write_bytes(_capture_query_result(native_path.read_bytes(),
                    adapter=args.input_format, query_sha256=hashlib.sha256(query.encode()).hexdigest(),
                    entity="items").payload)
                native_path.unlink()
        def mapping(path: str) -> dict:
            return {"kind": "csv", "path": path, "source_columns": ["old"], "replacement_columns": ["new"]}
        (root / "global.csv").write_text("old,new\nalpha,omega\nbeta,theta\nomega,cascade\n", encoding="utf-8")
        (root / "column.csv").write_text("old,new\nalpha,first\nbeta,second\n", encoding="utf-8")
        policy = {"schema_version": "0.1", "schema_fingerprint": "0" * 64, "seed": 7,
                  "input_format": args.input_format,
                  "resource_limits": {"max_input_rows": 1_000_000, "max_input_columns": 100,
                      "max_input_cells": 100_000_000, "max_input_file_bytes": max_bytes,
                      "max_total_input_bytes": max_bytes,
                      "max_parquet_expanded_bytes": max_bytes,
                      "max_output_bytes": max_bytes},
                  "file_text_mapping": mapping("global.csv"), "fields": [
                      {"entity": "items", "field": name, "sensitivity": "non_sensitive",
                       "behavior": {"action": "replace_text", **({"mapping": mapping("column.csv")} if i == 0 else {})}}
                      for i, name in enumerate(names)]}
        if args.output_format != "csv":
            policy["output"] = {"format": args.output_format, "fields": [
                {"name": name, "type": "string"} for name in names]}
            if args.output_format == "postgresql_sql":
                policy["output"]["table"] = "fictional_items"
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
        if args.refusal:
            _registered_output("mcp", source_path, request.snapshot_sha256, max_bytes, budget,
                include_refusals=False, refusal=args.refusal)
            assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
            output_bytes = 0
        else:
            publication = (temporary_csv_publication(request, max_total_bytes=max_bytes,
                max_review_bytes=1024 * 1024, max_output_bytes=max_bytes, budget=budget)
                if args.entrance == "private" else nullcontext(_registered_output(
                    args.entrance, source_path, request.snapshot_sha256, max_bytes, budget,
                    include_refusals=not args.execution_only, refusal=None)))
            with publication as output:
                manifest = json.loads((output / "manifest.json").read_text())
                count = 0
                filename = "dataset." + ("sql" if args.output_format == "postgresql_sql" else args.output_format)
                if args.output_format == "csv":
                    with (output / filename).open(newline="", encoding="utf-8") as handle:
                        reader = csv.reader(handle)
                        assert next(reader) == names
                        for index, row in enumerate(reader):
                            budget.check("scale acceptance readback")
                            expected = ["first" if index % 2 == 0 else "second"] + [
                                "omega" if index % 2 == 0 else "theta"] * (args.columns - 1)
                            assert row == expected, "ordered replacement readback mismatch"
                            count += 1
                elif args.output_format == "parquet":
                    import pyarrow as pa
                    import pyarrow.parquet as pq

                    parquet = pq.ParquetFile(output / filename)
                    assert parquet.schema_arrow.names == names
                    assert all(field.type == pa.string() and not field.nullable
                               for field in parquet.schema_arrow)
                    for batch in parquet.iter_batches(batch_size=1024):
                        budget.check("scale acceptance Parquet readback")
                        for row in batch.to_pylist():
                            budget.check("scale acceptance readback")
                            expected = ["first" if count % 2 == 0 else "second"] + [
                                "omega" if count % 2 == 0 else "theta"] * (args.columns - 1)
                            assert [row[name] for name in names] == expected, "ordered replacement readback mismatch"
                            count += 1
                else:
                    # This fixed fictional fixture uses only simple alphabetic text.
                    # Check every emitted statement; never execute it against a DB.
                    columns = ", ".join(f'"{name}"' for name in names)
                    definitions = ", ".join(f'"{name}" TEXT NOT NULL' for name in names)
                    prefix = f'INSERT INTO "fictional_items" ({columns}) VALUES ('
                    with (output / filename).open(encoding="utf-8") as handle:
                        assert handle.readline() == "BEGIN;\n"
                        assert handle.readline() == "SET LOCAL standard_conforming_strings = on;\n"
                        assert handle.readline() == f'CREATE TABLE "fictional_items" ({definitions});\n'
                        for index in range(args.rows):
                            budget.check("scale acceptance SQL readback")
                            expected = ["first" if index % 2 == 0 else "second"] + [
                                "omega" if index % 2 == 0 else "theta"] * (args.columns - 1)
                            values = ", ".join(f"'{value}'" for value in expected)
                            assert handle.readline() == prefix + values + ");\n", "ordered SQL readback mismatch"
                            count += 1
                        assert handle.readline() == "COMMIT;\n" and handle.read(1) == ""
                assert count == args.rows
                assert manifest["origin"] == "transformed_mixed"
                assert manifest["provenance"]["output_cells"] == args.rows * args.columns
                assert manifest["provenance"]["replacement_percent"] == "100.00"
                output_bytes = (output / filename).stat().st_size
                assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
            if args.entrance == "private":
                assert not output.parent.exists(), "temporary publication not removed"
    assert not root.exists(), "fictional inputs not removed"
    print(json.dumps({"status": "passed", "rows": args.rows, "columns": args.columns,
        "cells": args.rows * args.columns, "output_bytes": output_bytes,
        "max_bytes": max_bytes, "max_seconds": args.max_seconds,
        "input_format": args.input_format, "output_format": args.output_format,
        "elapsed_seconds": round(monotonic() - started, 3),
        "entrance": args.entrance, "refusal": args.refusal,
        "refusals_checked": 1 if args.refusal else 0 if args.entrance == "private" or args.execution_only else 3,
        "scope": "fictional replacement-only local snapshot; no preservation or live DB"}), flush=True)


if __name__ == "__main__":
    main()
