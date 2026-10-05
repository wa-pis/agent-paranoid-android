"""Fictional installed-candidate PostgreSQL capture -> review -> CSV acceptance.

No database connection, monkeypatch, receipt creation or public activation.
The injected driver generates rows locally through the actual private worker.
"""

import argparse
import csv
import hashlib
import json
import math
import multiprocessing
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import pyarrow as pa
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import transformation_schema_fingerprint
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.io.transformation_postgres_capture import _PostgresCapture, _capture_postgres_isolated
from test_data_agent.io.transformation_publish import temporary_csv_publication
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
        assert sql.startswith('SELECT "field_aa"') and sql.endswith(f"LIMIT {self.total + 1}")
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
    parser.add_argument("--max-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--capture-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--max-seconds", type=float, default=1800)
    args = parser.parse_args()
    if not 1 <= args.rows <= 1_000_000 or not 2 <= args.columns <= 100:
        parser.error("fixture supports 1..1000000 rows and 2..100 columns")
    if not 0 < args.capture_bytes <= args.max_bytes <= 2**63 - 1:
        parser.error("byte budgets must satisfy 0 < capture-bytes <= max-bytes <= 2**63 - 1")
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("max-seconds must be finite and positive")
    started = monotonic()
    budget = GenerationBudget(args.max_seconds)
    names = tuple("field_" + chr(97 + i // 26) + chr(97 + i % 26) for i in range(args.columns))
    max_bytes = args.max_bytes
    capture_bytes = args.capture_bytes
    counters = multiprocessing.get_context("spawn").RawArray("q", 6)
    previous_children = {child.pid for child in multiprocessing.active_children()}
    with TemporaryDirectory(prefix="apa-postgres-scale-fictional-") as directory:
        root = Path(directory).resolve()
        query_path = root / "query.sql"
        query_path.write_text("SELECT " + ", ".join(names) + " FROM public.items", encoding="utf-8")
        policy_data = {"schema_version": "0.1", "schema_fingerprint": "0" * 64,
            "input_format": "postgres_query", "seed": 7,
            "resource_limits": {"max_input_rows": 1_000_000, "max_input_columns": 100,
                "max_input_cells": 100_000_000, "max_input_file_bytes": capture_bytes,
                "max_total_input_bytes": max_bytes,
                "max_parquet_expanded_bytes": max_bytes, "max_output_bytes": max_bytes},
            "fields": [{"entity": "fictional.items", "field": name, "sensitivity": "non_sensitive",
                "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                    {"original": ["alpha"], "replacement": ["omega"]},
                    {"original": ["beta"], "replacement": ["theta"]}]}}} for name in names]}
        policy_path = root / "behavior.yaml"
        policy_path.write_text(yaml.safe_dump(policy_data), encoding="utf-8")
        policy = load_behavior_policy_yaml(policy_path.read_bytes(), max_bytes=max_bytes, budget=budget)
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
            with (output / "dataset.csv").open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                assert next(reader) == list(names)
                for index, row in enumerate(reader):
                    budget.check("PostgreSQL scale acceptance readback")
                    assert row == ["omega" if index % 2 == 0 else "theta"] * args.columns
                    count += 1
            assert count == args.rows
            assert manifest["origin"] == "transformed_mixed"
            assert manifest["provenance"]["output_cells"] == args.rows * args.columns
            assert manifest["provenance"]["replacement_percent"] == "100.00"
            output_bytes = (output / "dataset.csv").stat().st_size
            assert hashlib.sha256(source.payload).hexdigest() == source_hash
        assert not output.parent.exists(), "temporary publication not removed"
    assert not root.exists(), "fixture directory not removed"
    print(json.dumps({"status": "passed", "rows": args.rows, "columns": args.columns,
        "cells": args.rows * args.columns, "captured_bytes": len(source.payload), "output_bytes": output_bytes,
        "elapsed_seconds": round(monotonic() - started, 3),
        "max_bytes": max_bytes, "capture_bytes_limit": capture_bytes, "max_seconds": args.max_seconds,
        "profiling_result_rows_limit": config.limits.max_result_rows,
        "profiling_result_cells_limit": config.limits.max_result_cells,
        "scope": "fictional private PostgreSQL-to-CSV; no live database/public activation"}), flush=True)


if __name__ == "__main__":
    main()
