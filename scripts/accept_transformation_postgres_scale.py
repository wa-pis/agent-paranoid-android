"""Fictional installed SQL capture -> review -> CSV/Parquet/SQL acceptance.

No database connection, monkeypatch, receipt creation or public activation.
PostgreSQL uses an injected driver through the actual private worker.
Trino uses a supplied Arrow stream through query authorization/capture only;
its network adapter, server execution and worker supervision are not exercised.
"""

import argparse
import csv
import hashlib
import json
import math
import multiprocessing
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import pyarrow as pa
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.privacy import infer_sensitive_from_name
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.io.transformation_postgres_capture import _PostgresCapture, _capture_postgres_isolated
from test_data_agent.io.transformation_publish import temporary_csv_publication
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_request
from test_data_agent.postgres_config import PostgresConfig, PostgresProfileLimits
from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryAdapter, SqlQueryProfileRequest


class FictionalDriver:
    """Trusted local fixture, not a user-supplied replacement/API adapter."""

    def __init__(self, rows: int, names: tuple[str, ...], counters):
        self.total, self.names, self.counters = rows, names, counters
        self.description = [(name,) for name in names]

    def connect(self, **options):
        assert options["host"] == "fictional.invalid"
        assert "default_transaction_read_only=on" in options["options"]
        self.counters[1] += 1
        return self

    def cursor(self, **options):
        assert options == dict(name="apa_transform", scrollable=False, withhold=False)
        self.counters[2] += 1
        return self

    def execute(self, sql):
        assert sql.startswith(f'SELECT "{self.names[0]}"') and sql.endswith(f"LIMIT {self.total + 1}")
        assert "SELECT *" not in sql
        self.counters[3] += 1

    def fetchmany(self, size):
        assert size == 1
        index = self.counters[0]
        if index == self.total:
            return []
        self.counters[0] += 1
        return [("alpha" if index % 2 == 0 else "beta",) * len(self.names)]

    def close(self):
        self.counters[4] += 1

    def rollback(self):
        self.counters[5] += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=300_000)
    parser.add_argument("--columns", type=int, default=50)
    parser.add_argument("--adapter", choices=("postgres", "trino"), default="postgres")
    parser.add_argument("--output-format", choices=("csv", "parquet", "postgresql_sql"), default="csv")
    parser.add_argument("--max-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--capture-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--max-seconds", type=float, default=1800)
    args = parser.parse_args()
    if not 1 <= args.rows <= 1_000_000 or not 2 <= args.columns <= 100:
        parser.error("fixture supports 1..1000000 rows and 2..100 columns")
    if not 0 < args.capture_bytes <= args.max_bytes <= 2**63 - 1:
        parser.error("byte budgets must satisfy 0 < capture-bytes <= max-bytes <= 2**63 - 1")
    if not math.isfinite(args.max_seconds) or not 0.1 <= args.max_seconds <= 3600:
        parser.error("max-seconds must be finite and between 0.1 and 3600")
    started = monotonic()
    budget = GenerationBudget(args.max_seconds)
    names = tuple(f"field_{i:03d}" for i in range(args.columns))
    assert not any(infer_sensitive_from_name(name) for name in names)
    max_bytes = args.max_bytes
    capture_bytes = args.capture_bytes
    counters = multiprocessing.get_context("spawn").RawArray("q", 6)
    previous_children = {child.pid for child in multiprocessing.active_children()}
    with TemporaryDirectory(prefix="apa-postgres-scale-fictional-") as directory:
        root = Path(directory).resolve()
        query_path = root / "query.sql"
        table = "public.items" if args.adapter == "postgres" else "demo.public.items"
        query_path.write_text("SELECT " + ", ".join(names) + " FROM " + table, encoding="utf-8")
        policy_data = {"schema_version": "0.1", "schema_fingerprint": "0" * 64,
            "input_format": args.adapter + "_query", "seed": 7,
            "resource_limits": {"max_input_rows": 1_000_000, "max_input_columns": 100,
                "max_input_cells": 100_000_000, "max_input_file_bytes": capture_bytes,
                "max_total_input_bytes": max_bytes,
                "max_parquet_expanded_bytes": max_bytes, "max_output_bytes": max_bytes},
            "fields": [{"entity": "fictional.items", "field": name, "sensitivity": "non_sensitive",
                "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                    {"original": ["alpha"], "replacement": ["omega"]},
                    {"original": ["beta"], "replacement": ["theta"]}]}}} for name in names]}
        if args.output_format != "csv":
            policy_data["output"] = {"format": args.output_format, "fields": [
                {"name": name, "type": "string"} for name in names]}
            if args.output_format == "postgresql_sql":
                policy_data["output"]["table"] = "fictional_items"
        policy_path = root / "behavior.yaml"
        policy_path.write_text(yaml.safe_dump(policy_data), encoding="utf-8")
        policy = load_behavior_policy_yaml(policy_path.read_bytes(), max_bytes=max_bytes, budget=budget)
        schema = pa.schema([pa.field(name, pa.string(), nullable=False) for name in names])
        columns = tuple(QuerySourceColumn(name, "text", False) for name in names)
        config = None
        if args.adapter == "postgres":
            config = PostgresConfig(source_id="fictional", host="fictional.invalid", port=5432,
                database="fictional", user="fictional", allowed_schemas=frozenset({"public"}),
                allowed_tables=frozenset({"public.items"}),
                allowed_columns=frozenset("public.items." + name for name in names),
                limits=PostgresProfileLimits(max_seconds=args.max_seconds))
            capture = _PostgresCapture(
                request=SqlQueryProfileRequest(SqlQueryAdapter.POSTGRES, "fictional", "items", query_path),
                config=config, source_columns=tuple(QuerySourceColumn(name, "text", False) for name in names),
                schema=pa.schema([pa.field(name, pa.string(), nullable=False) for name in names]),
                policy=policy, max_rows=args.rows, max_bytes=capture_bytes)
            source = _capture_postgres_isolated(capture,
                driver_factory=partial(FictionalDriver, args.rows, names, counters), max_seconds=args.max_seconds)
            assert list(counters) == [args.rows, 1, 1, 1, 2, 1], "driver lifecycle/count mismatch"
            assert {child.pid for child in multiprocessing.active_children()} == previous_children
        else:
            lifecycle = [0, 0]

            @contextmanager
            def stream(query):
                assert query.adapter == "trino" and query.table == table
                assert query.columns == names and query.max_rows == args.rows + 1
                assert query.sql.startswith(f'SELECT "{names[0]}"')
                assert query.sql.endswith(f"LIMIT {args.rows + 1}") and "SELECT *" not in query.sql

                def batches():
                    for start in range(0, args.rows, 1024):
                        budget.check("fictional Trino stream")
                        values = ["alpha" if index % 2 == 0 else "beta"
                                  for index in range(start, min(start + 1024, args.rows))]
                        column = pa.array(values, type=pa.string())
                        lifecycle[0] += len(values)
                        yield pa.RecordBatch.from_arrays([column] * args.columns, schema=schema)
                try:
                    yield batches()
                finally:
                    lifecycle[1] += 1

            source = _capture_authorized_result(
                SqlQueryProfileRequest(SqlQueryAdapter.TRINO, "fictional", "items", query_path),
                allowed_tables=frozenset({table}), source_columns=columns, schema=schema,
                policy=policy, max_rows=args.rows, max_bytes=capture_bytes, budget=budget, stream=stream)
            assert lifecycle == [args.rows, 1], "fictional stream lifecycle/count mismatch"
            assert {child.pid for child in multiprocessing.active_children()} == previous_children
        source_hash = hashlib.sha256(source.payload).hexdigest()
        print(json.dumps({"stage": "capture", "rows": args.rows, "captured_bytes": len(source.payload),
            "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
        profile = _profile_transformation_source(source, policy, budget=budget, max_bytes=max_bytes)
        policy_data["schema_fingerprint"] = transformation_schema_fingerprint(profile)
        policy_path.write_text(yaml.safe_dump(policy_data), encoding="utf-8")
        del profile
        print(json.dumps({"stage": "profile", "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
        request = prepare_csv_review_request(policy_path.read_bytes(), source, (),
            max_total_bytes=max_bytes, max_review_bytes=1024 * 1024, budget=budget)
        print(json.dumps({"stage": "review", "elapsed_seconds": round(monotonic() - started, 3)}), flush=True)
        with temporary_csv_publication(request, max_total_bytes=max_bytes,
                max_review_bytes=1024 * 1024, max_output_bytes=max_bytes, budget=budget) as output:
            manifest = json.loads((output / "manifest.json").read_text())
            count = 0
            filename = "dataset." + ("sql" if args.output_format == "postgresql_sql" else args.output_format)
            if args.output_format == "csv":
                with (output / filename).open(newline="", encoding="utf-8") as handle:
                    reader = csv.reader(handle)
                    assert next(reader) == list(names)
                    for index, row in enumerate(reader):
                        budget.check("PostgreSQL scale acceptance readback")
                        assert row == ["omega" if index % 2 == 0 else "theta"] * args.columns
                        count += 1
            elif args.output_format == "parquet":
                import pyarrow.parquet as pq

                parquet = pq.ParquetFile(output / filename)
                assert parquet.schema_arrow.names == list(names)
                assert all(field.type == pa.string() and not field.nullable
                           for field in parquet.schema_arrow)
                for batch in parquet.iter_batches(batch_size=1024):
                    budget.check("PostgreSQL scale acceptance readback")
                    for row in batch.to_pylist():
                        budget.check("PostgreSQL scale acceptance readback")
                        assert [row[name] for name in names] == ["omega" if count % 2 == 0 else "theta"] * args.columns
                        count += 1
            else:
                # Fixed fictional alphabetic literals only; never execute SQL.
                columns = ", ".join(f'"{name}"' for name in names)
                definitions = ", ".join(f'"{name}" TEXT NOT NULL' for name in names)
                prefix = f'INSERT INTO "fictional_items" ({columns}) VALUES ('
                with (output / filename).open(encoding="utf-8") as handle:
                    assert handle.readline() == "BEGIN;\n"
                    assert handle.readline() == "SET LOCAL standard_conforming_strings = on;\n"
                    assert handle.readline() == f'CREATE TABLE "fictional_items" ({definitions});\n'
                    for index in range(args.rows):
                        budget.check("PostgreSQL scale acceptance SQL readback")
                        values = ", ".join(["'omega'" if index % 2 == 0 else "'theta'"] * args.columns)
                        assert handle.readline() == prefix + values + ");\n"
                        count += 1
                    assert handle.readline() == "COMMIT;\n" and handle.read(1) == ""
            assert count == args.rows
            assert manifest["origin"] == "transformed_mixed"
            assert manifest["provenance"]["output_cells"] == args.rows * args.columns
            assert manifest["provenance"]["replacement_percent"] == "100.00"
            output_bytes = (output / filename).stat().st_size
            assert hashlib.sha256(source.payload).hexdigest() == source_hash
        assert not output.parent.exists(), "temporary publication not removed"
    assert not root.exists(), "fixture directory not removed"
    print(json.dumps({"status": "passed", "rows": args.rows, "columns": args.columns,
        "cells": args.rows * args.columns, "captured_bytes": len(source.payload), "output_bytes": output_bytes,
        "elapsed_seconds": round(monotonic() - started, 3),
        "adapter": args.adapter, "output_format": args.output_format,
        "max_bytes": max_bytes, "capture_bytes_limit": capture_bytes, "max_seconds": args.max_seconds,
        "profiling_result_rows_limit": config.limits.max_result_rows if config else None,
        "profiling_result_cells_limit": config.limits.max_result_cells if config else None,
        "scope": "fictional private SQL capture; no live database/public activation"}), flush=True)


if __name__ == "__main__":
    main()
