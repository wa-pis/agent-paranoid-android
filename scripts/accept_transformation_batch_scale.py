"""Opt-in installed MCP common/configured acceptance, using fictional data only."""

import argparse
import asyncio
import csv
from datetime import timedelta
from functools import partial
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory, TemporaryFile
from time import monotonic
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint


MIB = 1024**2
TOTAL_BYTES = 1024 * MIB
SQL_OUTPUT_BYTES = 3 * TOTAL_BYTES
OUTPUT_SUFFIXES = {"csv": "csv", "parquet": "parquet", "postgresql_sql": "sql"}
CAPTURE_BYTES = 512 * MIB
REVIEW_BYTES = MIB
SECONDS = 3600
SOURCE_VALUES = ("q", "z")
OUTPUT_VALUES = ("x", "y")


def names_for(columns):
    return [f"field_{i:03d}" for i in range(columns)]


class FictionalDriver:
    """Closed worker driver fixture; no sockets or supplied query execution."""

    def __init__(self, adapter, rows, columns, log):
        self.adapter, self.rows, self.names, self.log = adapter, rows, names_for(columns), log
        self.dbapi = self

    def connect(self, **options):
        assert options["host"] == "fictional.invalid"
        if self.adapter == "postgres":
            assert "default_transaction_read_only=on" in options["options"]
        with self.log.open("a", encoding="utf-8") as handle:
            handle.write("connected\n")
        return self

    def cursor(self, **kwargs):
        return self

    def execute(self, sql, parameters=None):
        self.position = 0
        if "information_schema.columns" in sql or "pg_catalog.pg_attribute" in sql:
            self.description = [(name,) for name in ("column_name", "data_type", "is_nullable")]
            self.metadata = [(name, "text", False) if self.adapter == "postgres"
                             else (name, "varchar", "NO") for name in self.names]
            self.count = 0
            return
        assert sql.startswith("SELECT ") and "SELECT *" not in sql
        self.metadata = []
        if self.adapter == "postgres":
            self.description = [(name, SimpleNamespace(name="text"), None, None, None, None, False)
                                for name in self.names]
        else:
            self.description = [(name, "varchar") for name in self.names]
        self.count = 0 if sql.endswith("WHERE FALSE") else self.rows
        if self.count:
            assert sql.endswith(f"LIMIT {self.rows + 1}")

    def fetchmany(self, size):
        if self.metadata:
            values, self.metadata = self.metadata[:size], self.metadata[size:]
            return values
        end = min(self.position + size, self.count)
        batch = [(SOURCE_VALUES[i % 2],) * len(self.names) for i in range(self.position, end)]
        self.position = end
        return batch

    def rollback(self):
        pass

    def close(self):
        pass


def server(adapter, rows, columns):
    from test_data_agent.io import transformation_postgres_capture, transformation_trino_stream
    from test_data_agent.mcp_generator_server import main

    factory = partial(FictionalDriver, adapter, rows, columns, Path("connections.log").resolve())
    if adapter == "postgres":
        transformation_postgres_capture._configured_postgres_driver = factory
    else:
        transformation_trino_stream._configured_trino_driver = factory
    return main()


def fixture(root, route, rows, columns, input_format, output_format, output_bytes):
    inputs, entities = [], []
    for index, (count, width) in enumerate(((rows, columns), (2, 2))):
        names = names_for(width)
        is_query = index == 0 and route != "common"
        entity = ("warehouse.items" if route == "postgres" else "trino.items") if is_query else f"items{index}"
        source_format = f"{route}_query" if is_query else input_format if index == 0 else "parquet"
        source_path = f"items{index}." + ("query" if is_query else source_format)
        fields = [{"name": name, "data_type": "string"} for name in names]
        profile = DatasetProfile.model_validate({"entities": [{"name": entity, "row_count": count, "fields": fields}]})
        policy = {"schema_version": "0.1", "schema_fingerprint": transformation_schema_fingerprint(profile),
                  "input_format": source_format, "seed": 7,
                  "resource_limits": {"max_input_rows": 1_000_000, "max_input_columns": 100,
                      "max_input_cells": 100_000_000, "max_input_file_bytes": CAPTURE_BYTES,
                      "max_total_input_bytes": TOTAL_BYTES, "max_parquet_expanded_bytes": TOTAL_BYTES,
                      "max_output_bytes": output_bytes},
                  "fields": [{"entity": entity, "field": name, "sensitivity": "non_sensitive",
                      "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                          {"original": [a], "replacement": [b]} for a, b in zip(SOURCE_VALUES, OUTPUT_VALUES)]}}}
                      for name in names]}
        if index == 0 and output_format != "csv":
            policy["output"] = {"format": output_format,
                                "fields": [{"name": name, "type": "string"} for name in names]}
            if output_format == "postgresql_sql":
                policy["output"]["table"] = "fictional_items"
        policy_path = f"policy{index}.yaml"
        (root / policy_path).write_text(yaml.safe_dump(policy))
        inputs.append({"entity": entity, "source": source_path, "policy": policy_path})
        entities.append({"name": entity, "row_count": count, "fields": fields})
        if is_query:
            table = "public.items" if route == "postgres" else "lake.safe.items"
            (root / "query.sql").write_text("SELECT " + ", ".join(names) + " FROM " + table)
            references = {"schema_version": "0.1", "queries": {source_path: {
                "adapter": route, "source_id": entity.split(".")[0], "entity": "items",
                "query_file": "query.sql", "max_rows": count, "max_bytes": CAPTURE_BYTES, "max_seconds": SECONDS}}}
            (root / "references.yaml").write_text(yaml.safe_dump(references))
        elif source_format == "csv":
            with (root / source_path).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle, lineterminator="\n")
                writer.writerow(names)
                patterns = [[value] * width for value in SOURCE_VALUES]
                writer.writerows(patterns[i % 2] for i in range(count))
        else:
            schema = pa.schema([pa.field(name, pa.string(), nullable=False) for name in names])
            with pq.ParquetWriter(root / source_path, schema) as writer:
                for start in range(0, count, 1024):
                    values = pa.array([SOURCE_VALUES[i % 2] for i in range(start, min(start + 1024, count))])
                    writer.write_table(pa.Table.from_arrays([values] * width, schema=schema))
    (root / "validation.yaml").write_text(yaml.safe_dump({"schema_version": "1.1", "entities": entities}))
    (root / "batch.yaml").write_text(yaml.safe_dump({"schema_version": "0.1", "validation": "validation.yaml",
        "resource_limits": {"max_total_input_bytes": TOTAL_BYTES, "max_output_bytes": output_bytes},
        "inputs": inputs}))


async def run_route(root, route, rows, columns, output_bytes, started):
    env = {key: os.environ[key] for key in ("PATH", "LANG", "TMPDIR", "SYSTEMROOT") if key in os.environ}
    env.update(TEST_DATA_AGENT_WORKSPACE_ROOT=str(root), TEST_DATA_AGENT_MAX_GENERATION_SECONDS=str(SECONDS),
        TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS=str(SECONDS), TEST_DATA_AGENT_QUERY_SESSION_MAX_ACTIVE="1",
        TEST_DATA_AGENT_QUERY_SESSION_MAX_SECONDS=str(SECONDS),
        TEST_DATA_AGENT_QUERY_SESSION_MAX_CUMULATIVE_BYTES=str(TOTAL_BYTES))
    names = names_for(columns)
    if route == "postgres":
        env.update(POSTGRES_SOURCE_ID="warehouse", POSTGRES_HOST="fictional.invalid",
            POSTGRES_ALLOWED_SCHEMAS="public", POSTGRES_ALLOWED_TABLES="public.items",
            POSTGRES_ALLOWED_COLUMNS=",".join(f"public.items.{name}" for name in names))
    if route == "trino":
        env.update(TRINO_HOST="fictional.invalid", TRINO_MAX_INVOCATION_SECONDS=str(SECONDS),
            TRINO_ALLOWED_CATALOGS="lake", TRINO_ALLOWED_SCHEMAS="safe",
            TRINO_ALLOWED_TABLE_COLUMNS=",".join(f"lake.safe.items.{name}" for name in names))
    args = (["-I", "-m", "test_data_agent.mcp_generator_server"] if route == "common" else
            ["-I", str(Path(__file__).resolve()), "--server", route, str(rows), str(columns)])
    parameters = StdioServerParameters(command=sys.executable, args=args, env=env, cwd=str(root))
    timeout = SECONDS if int(version("mcp").split(".")[0]) >= 2 else timedelta(seconds=SECONDS)
    with TemporaryFile(mode="w+", encoding="utf-8") as stderr:
        async with asyncio.timeout(SECONDS), stdio_client(parameters, errlog=stderr) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=timeout) as session:
                await session.initialize()
                tool = "common_transformation" if route == "common" else "configured_query_session"
                tools = {item.name for item in (await session.list_tools()).tools}
                assert tool in tools and "transform-approve" not in tools

                async def call(operation, **kwargs):
                    result = (await session.call_tool(tool, {"operation": operation, **kwargs})).model_dump(by_alias=True)
                    assert not any(json.dumps(value) in json.dumps(result) for value in SOURCE_VALUES)
                    if result.get("isError"):
                        # Only fixed product errors and fictional metadata are sent here.
                        raise RuntimeError(f"{operation} failed: {result.get('structuredContent') or result['content']}")
                    return result["structuredContent"]

                bounds = dict(profile="batch.yaml", max_total_bytes=TOTAL_BYTES, max_review_bytes=REVIEW_BYTES,
                              max_output_bytes=output_bytes)
                if route == "common":
                    review = await call("review", **bounds)
                    execute_args = bounds
                else:
                    review = await call("open", references="references.yaml", **bounds)
                    owned = Path(review["local_approval"]["root"])
                    assert owned.is_dir()
                    connects = 2 if route == "postgres" else 3
                    log = root / "connections.log"
                    assert log.read_text().splitlines() == ["connected"] * connects
                    execute_args = {"handle": review["handle"]}
                assert review["status"] == "review_only"
                digest = review["snapshot_sha256"]
                print(json.dumps({"stage": "review", "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
                result = await call("execute", snapshot_sha256=digest, destination="selected", **execute_args)
                assert result["status"] == "closed_publication_completed"
                assert result["summary"]["snapshot_sha256"] == digest
                if route != "common":
                    assert not owned.exists() and log.read_text().splitlines() == ["connected"] * connects
        stderr.seek(0)
        diagnostics = stderr.read()
        assert not any(json.dumps(value) in diagnostics for value in SOURCE_VALUES)


def verify_artifact(path, output_format, count, width):
    names = names_for(width)
    if output_format == "csv":
        patterns = [[value] * width for value in OUTPUT_VALUES]
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            assert next(reader) == names
            for i in range(count):
                assert next(reader) == patterns[i % 2]
            assert next(reader, None) is None
    elif output_format == "parquet":
        parquet = pq.ParquetFile(path)
        assert parquet.schema_arrow.names == names
        assert all(field.type == pa.string() and not field.nullable for field in parquet.schema_arrow)
        seen = 0
        for batch in parquet.iter_batches(batch_size=1024):
            expected = pa.array([OUTPUT_VALUES[i % 2] for i in range(seen, seen + batch.num_rows)])
            assert all(column.equals(expected) for column in batch.columns)
            seen += batch.num_rows
        assert seen == count
    else:
        columns = ", ".join(f'"{name}"' for name in names)
        definitions = ", ".join(f'"{name}" TEXT NOT NULL' for name in names)
        prefix = f'INSERT INTO "fictional_items" ({columns}) VALUES ('
        inserts = [prefix + ", ".join([f"'{value}'"] * width) + ");\n" for value in OUTPUT_VALUES]
        with path.open(encoding="utf-8") as handle:
            assert handle.readline() == "BEGIN;\n"
            assert handle.readline() == "SET LOCAL standard_conforming_strings = on;\n"
            assert handle.readline() == f'CREATE TABLE "fictional_items" ({definitions});\n'
            for i in range(count):
                assert handle.readline() == inserts[i % 2]
            assert handle.readline() == "COMMIT;\n" and handle.read(1) == ""


def digest_file(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    if sys.argv[1:2] == ["--server"]:
        route, rows, columns = sys.argv[2:]
        return server(route, int(rows), int(columns))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route", choices=("common", "postgres", "trino"))
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--columns", type=int, default=100)
    parser.add_argument("--input-format", choices=("csv", "parquet"), help="Common MCP input only.")
    parser.add_argument("--output-format", choices=tuple(OUTPUT_SUFFIXES), default="csv")
    args = parser.parse_args()
    if args.input_format is not None and args.route != "common":
        parser.error("--input-format is only for the common route")
    input_format = args.input_format or "parquet"
    output_cap = SQL_OUTPUT_BYTES if args.output_format == "postgresql_sql" else TOTAL_BYTES
    if not 1 <= args.rows <= 1_000_000 or not 2 <= args.columns <= 100:
        parser.error("fixture supports 1..1000000 rows and 2..100 columns")
    started = monotonic()
    with TemporaryDirectory(prefix="apa-batch-scale-fictional-") as directory:
        root = Path(directory).resolve()
        fixture(root, args.route, args.rows, args.columns, input_format, args.output_format, output_cap)
        inputs = {p: digest_file(p) for p in root.iterdir()}
        asyncio.run(run_route(root, args.route, args.rows, args.columns, output_cap, started))
        output = root / "selected"
        manifest = json.loads((output / "manifest.json").read_bytes())
        assert manifest["origin"] == "transformed_mixed"
        target = output / f"input-0.{OUTPUT_SUFFIXES[args.output_format]}"
        control = output / "input-1.csv"
        assert set(output.iterdir()) == {target, control, output / "manifest.json"}
        for index, (count, width, output_format, path) in enumerate((
                (args.rows, args.columns, args.output_format, target), (2, 2, "csv", control))):
            assert manifest["provenance"][index]["output_cells"] == count * width
            assert manifest["provenance"][index]["replacement_percent"] == "100.00"
            verify_artifact(path, output_format, count, width)
        assert all(digest_file(p) == digest for p, digest in inputs.items())
        output_bytes = target.stat().st_size
    assert not root.exists()
    print(json.dumps({"status": "passed", "route": args.route, "rows": args.rows, "columns": args.columns,
        "cells": args.rows * args.columns, "output_bytes": output_bytes, "max_total_bytes": TOTAL_BYTES,
        "input_format": input_format if args.route == "common" else f"{args.route}_query",
        "output_format": args.output_format, "max_output_bytes": output_cap,
        "capture_bytes_limit": CAPTURE_BYTES, "max_seconds": SECONDS,
        "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
