"""Fictional aggregate result -> saved policy -> real TTY approval -> CLI output.

Injected bounded driver stream, not a product monkeypatch or database connection.
"""
import csv
import errno
import json
import os
import pty
import select
import subprocess
import sys
import time
from contextlib import contextmanager
from decimal import Decimal

import pyarrow as pa
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.io.transformation_source import _profile_transformation_source
from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryAdapter, SqlQueryProfileRequest


def test_finance_aggregate_saved_profile(tmp_path):
    entity = "fictional.items"
    categories = [("fictional-product-a", "fictional-segment-a", "fictional-bank-a"),
                  ("fictional-product-b", "fictional-segment-b", "fictional-bank-b")]
    table = pa.table({**{name: [row[index] for row in categories]
                        for index, name in enumerate(("product", "segment", "bank"))},
                      "bucket": [1, 2],
                      "amount": pa.array([Decimal("1.25"), Decimal("2.50")],
                                         type=pa.decimal128(8, 2))})
    fields = [{"entity": entity, "field": name, "sensitivity": "non_sensitive",
               "behavior": {"action": "preserve", "authorization_ref": "fictional-local",
                            "comment": "Fictional business grouping reviewed locally"}}
              for name in ("product", "segment", "bank")]
    for name, pairs in (("bucket", [(1, 11), (2, 12)]),
                        ("amount", [("1.25", "7.50"), ("2.50", "8.25")])):
        fields.append({"entity": entity, "field": name, "sensitivity": "non_sensitive",
                       **({"decimal_type": {"precision": 8, "scale": 2}} if name == "amount" else {}),
                       "behavior": {"action": "substitute", "mapping": {"kind": "inline",
                           "entries": [{"original": [a], "replacement": [b]} for a, b in pairs]}}})
    policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
        "schema_fingerprint": "0" * 64, "input_format": "postgres_query", "fields": fields})
    query_path = tmp_path / "query.sql"
    query_path.write_text("SELECT product, segment, bank, bucket, SUM(amount) AS amount "
                          "FROM public.items GROUP BY product, segment, bank, bucket")

    @contextmanager
    def stream(query):
        assert "SUM" in query.sql.upper() and "GROUP BY" in query.sql.upper()
        assert query.sql.endswith("LIMIT 4")
        yield iter(table.to_batches())

    source = _capture_authorized_result(
        SqlQueryProfileRequest(SqlQueryAdapter.POSTGRES, "fictional", "items", query_path),
        allowed_tables=frozenset({"public.items"}),
        source_columns=tuple(QuerySourceColumn(name, "text", True)
                             for name in ("product", "segment", "bank")) + (
                                 QuerySourceColumn("bucket", "bigint", True),
                                 QuerySourceColumn("amount", "numeric(8,2)", True)),
        schema=table.schema, policy=policy, stream=stream,
        max_rows=3, max_bytes=32768, budget=GenerationBudget(10))
    profile = _profile_transformation_source(source, policy,
        max_bytes=65536, budget=GenerationBudget(10))
    policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
    source_path, policy_path = tmp_path / "source.bin", tmp_path / "behavior.yaml"
    source_path.write_bytes(source.payload)
    policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")))
    before = (source_path.read_bytes(), policy_path.read_bytes())

    def cli(command, *arguments):
        response = subprocess.run([sys.executable, "-m", "test_data_agent.cli", command,
            str(source_path), str(policy_path), *map(str, arguments), "--table", entity, "--json"],
            capture_output=True, text=True, timeout=20)
        assert all(value not in response.stdout + response.stderr
                   for row in categories for value in row)
        return response

    review = cli("transform-review")
    assert review.returncode == 0, review.stderr
    digest = json.loads(review.stdout)["result"]["snapshot_sha256"]
    receipt = tmp_path / "receipt.json"
    rejected = cli("transform-execute", tmp_path / "rejected", "--snapshot-sha256", digest)
    assert rejected.returncode != 0 and not (tmp_path / "rejected").exists()
    master, slave = pty.openpty()
    program = ("import fcntl,termios,os,sys; fcntl.ioctl(0,termios.TIOCSCTTY,0); "
               "os.tcsetpgrp(0,os.getpgrp()); from test_data_agent.cli import main; sys.exit(main())")
    process = subprocess.Popen([sys.executable, "-c", program, "transform-approve",
        str(source_path), str(policy_path), str(receipt), "--table", entity,
        "--snapshot-sha256", digest, "--json"],
        stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
    os.close(slave)
    transcript = bytearray()
    deadline = time.monotonic() + 20
    try:
        approved = False
        while process.poll() is None:
            assert time.monotonic() < deadline
            if select.select([master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(master, 16384)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    break
                transcript.extend(chunk)
                if not approved and b"Type APPROVE" in transcript:
                    os.write(master, b"APPROVE\n")
                    approved = True
        process.wait(timeout=5)
        assert approved and process.returncode == 0, bytes(transcript)
        assert all(value.encode() not in transcript for row in categories for value in row)
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    assert receipt.stat().st_mode & 0o077 == 0
    result = cli("transform-execute", tmp_path / "output", "--snapshot-sha256", digest,
                 "--receipt", receipt, "--max-output-bytes", 8192)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["result"]["status"] == "transformation_completed"
    with (tmp_path / "output" / "dataset.csv").open(newline="") as output:
        rows = list(csv.DictReader(output))
    assert [tuple(row[name] for name in ("product", "segment", "bank")) for row in rows] == categories
    assert [row["bucket"] for row in rows] == ["11", "12"]
    assert [Decimal(row["amount"]) for row in rows] == [Decimal("7.50"), Decimal("8.25")]
    assert before == (source_path.read_bytes(), policy_path.read_bytes())
