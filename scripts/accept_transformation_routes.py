"""Fictional twelve-route saved-policy/CLI-review/private-publication acceptance."""

import csv
from datetime import date
from decimal import Decimal
import hashlib
import io
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_publish import _run_temporary_transform, temporary_csv_publication
from test_data_agent.io.transformation_query_capture import _capture_authorized_result
from test_data_agent.io.transformation_source import _profile_transformation_source, prepare_csv_review_from_paths
from test_data_agent.sql_query_source import QuerySourceColumn, SqlQueryAdapter, SqlQueryProfileRequest


def main() -> None:
    public = "--public" in sys.argv[1:]
    typed = public or "--typed" in sys.argv[1:]
    passed = []
    for input_format in ("csv", "parquet", "postgres_query", "trino_query"):
        for output_format in ("csv", "parquet", "postgresql_sql"):
            with TemporaryDirectory(prefix="apa-fictional-route-") as temporary:
                root = Path(temporary).resolve()
                entity = "items" if input_format in {"csv", "parquet"} else "fictional.items"
                policy = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": 7,
                    "schema_fingerprint": "0" * 64, "input_format": input_format,
                    "fields": [{"entity": entity, "field": name, "sensitivity": "non_sensitive",
                        "behavior": {"action": "substitute", "mapping": {"kind": "inline", "entries": [
                            {"original": [a], "replacement": [b]} for a, b in pairs]}}}
                        for name, pairs in [("label", [("alpha", "gamma"), ("beta", "delta")]),
                                            ("measured", [(2, 8), (1, 7)])]],
                    **({"output": {"format": output_format, "fields": [
                        {"name": "label", "type": "string"}, {"name": "measured", "type": "integer"}],
                        **({"table": "items"} if output_format == "postgresql_sql" else {})}}
                       if output_format != "csv" else {})})
                table = pa.Table.from_pylist([{"label": "alpha", "measured": 2},
                                             {"label": "beta", "measured": 1}])
                if typed:
                    data = policy.model_dump(mode="json")
                    for name, pairs, settings in (
                        ("amount", [("1.25", "7.50"), ("2.50", "8.25")],
                         {"decimal_type": {"precision": 5, "scale": 2}}),
                        ("day", [("2026-01-02", "2027-03-04"), ("2026-02-03", "2027-04-05")], {}),
                        ("optional", [(None, ""), ("", None)], {}),
                    ):
                        data["fields"].append({"entity": entity, "field": name,
                            "sensitivity": "non_sensitive", **settings,
                            "behavior": {"action": "substitute", "mapping": {"kind": "inline",
                                "entries": [{"original": [a], "replacement": [b]} for a, b in pairs]}}})
                    data["csv_nulls"] = {**({"input_token": "\\N"} if input_format == "csv" else {}),
                        **({"output_token": "\\N"} if output_format == "csv" else {})}
                    if output_format != "csv":
                        data["output"]["fields"].extend([
                            {"name": "amount", "type": "decimal", "decimal_type": {"precision": 5, "scale": 2}},
                            {"name": "day", "type": "date", "temporal_type": {
                                "type": "date", "format": "%Y-%m-%d", "output_format": "%Y-%m-%d"}},
                            {"name": "optional", "type": "string", "nullable": True}])
                    policy = BehaviorPolicy.model_validate(data)
                    table = table.append_column("amount", pa.array([Decimal("1.25"), Decimal("2.50")],
                        type=pa.decimal128(5, 2))).append_column("day", pa.array([
                            date(2026, 1, 2), date(2026, 2, 3)])).append_column(
                                "optional", pa.array([None, ""], type=pa.string()))
                if input_format == "csv":
                    source = SnapshotPart("source", entity,
                        b"label,measured,amount,day,optional\nalpha,2,1.25,2026-01-02,\\N\nbeta,1,2.50,2026-02-03,\n"
                        if typed else b"label,measured\nalpha,2\nbeta,1\n")
                elif input_format == "parquet":
                    buffer = io.BytesIO()
                    pq.write_table(table, buffer)
                    source = SnapshotPart("source", entity, buffer.getvalue())
                else:
                    adapter = SqlQueryAdapter(input_format.removesuffix("_query"))
                    physical = "public.items" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.items"
                    query_path = root / "query.sql"
                    columns = "label, measured, amount, day, optional" if typed else "label, measured"
                    query_path.write_text(f"SELECT {columns} FROM {physical}", encoding="utf-8")

                    @contextmanager
                    def stream(query):
                        assert query.sql.endswith("LIMIT 4") and "SELECT *" not in query.sql
                        yield iter(table.to_batches())

                    source = _capture_authorized_result(
                        SqlQueryProfileRequest(adapter, "fictional", "items", query_path),
                        allowed_tables=frozenset({physical}),
                        source_columns=(QuerySourceColumn("label", "text", True),
                                        QuerySourceColumn("measured", "bigint", True)) + (
                                            (QuerySourceColumn("amount", "numeric(5,2)", True),
                                             QuerySourceColumn("day", "date", True),
                                             QuerySourceColumn("optional", "text", True)) if typed else ()),
                        schema=table.schema, policy=policy, stream=stream,
                        max_rows=3, max_bytes=32768, budget=GenerationBudget(10))
                profile = _profile_transformation_source(source, policy,
                    max_bytes=65536, budget=GenerationBudget(10))
                policy = policy.model_copy(update={"schema_fingerprint": transformation_schema_fingerprint(profile)})
                policy_path, source_path = root / "behavior.yaml", root / "source.bin"
                policy_path.write_text(yaml.safe_dump(policy.model_dump(mode="json")), encoding="utf-8")
                source_path.write_bytes(source.payload)
                before = hashlib.sha256(source_path.read_bytes() + policy_path.read_bytes()).digest()
                request = prepare_csv_review_from_paths(source_path, entity, root, policy_path.name,
                    max_total_bytes=65536, max_review_bytes=8192, budget=GenerationBudget(10))
                cli = subprocess.run([sys.executable, "-m", "test_data_agent.cli", "transform-review",
                    str(source_path), str(policy_path), "--table", entity],
                    capture_output=True, text=True, timeout=30, check=True)
                review = json.loads(cli.stdout)
                assert review["snapshot_sha256"] == request.snapshot_sha256
                assert review["status"] == "review_only"
                assert all(value not in cli.stdout for value in ("alpha", "beta", "gamma", "delta"))
                mcp = subprocess.run([sys.executable, "-c",
                    "import json,sys; from test_data_agent.mcp_generator_server import review_transformation; "
                    "print(json.dumps(review_transformation(sys.argv[1],sys.argv[2],sys.argv[3])))",
                    source_path.name, policy_path.name, entity],
                    env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(root)},
                    capture_output=True, text=True, timeout=30, check=True)
                mcp_review = json.loads(mcp.stdout)
                assert mcp_review["status"] == "review_only"
                assert mcp_review["snapshot_sha256"] == review["snapshot_sha256"]
                assert mcp_review["review"] == review["review"]
                assert all(value not in mcp.stdout for value in ("alpha", "beta", "gamma", "delta"))
                summary = _run_temporary_transform(source_path, entity, policy_path,
                    expected_snapshot_sha256=request.snapshot_sha256, max_total_bytes=65536,
                    max_review_bytes=8192, max_output_bytes=32768, budget=GenerationBudget(10))
                assert summary["status"] == "temporary_test_completed"
                candidate_bundles = []
                for entrance in ("cli", "workspace"):
                    destination = root / f"candidate-{entrance}"
                    if entrance == "cli":
                        program = ("import json,sys; from test_data_agent.cli_transformation_candidate import "
                            "_run_candidate_execution; print(json.dumps(_run_candidate_execution(sys.argv[1:])))")
                        arguments = [str(source_path), str(policy_path), str(destination),
                            "--table", entity, "--snapshot-sha256", request.snapshot_sha256]
                    else:
                        program = ("import json,sys; from test_data_agent.mcp_transformation_candidate import "
                            "_execute_candidate_transformation; print(json.dumps(_execute_candidate_transformation("
                            "sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],table_name=sys.argv[5])))")
                        arguments = [source_path.name, policy_path.name, destination.name,
                            request.snapshot_sha256, entity]
                    command = [sys.executable, "-c", program, *arguments]
                    if public and entrance == "cli":
                        command = [sys.executable, "-m", "test_data_agent.cli", "transform-execute", *arguments, "--json"]
                    elif public:
                        command = [sys.executable, "-c",
                            "import json,sys; from test_data_agent.mcp_generator_server import execute_transformation; "
                            "print(json.dumps(execute_transformation(*sys.argv[1:5],table_name=sys.argv[5])))",
                            *arguments]
                    completed = subprocess.run(command,
                        env={**os.environ, "TEST_DATA_AGENT_WORKSPACE_ROOT": str(root)},
                        capture_output=True, text=True, timeout=30, check=True)
                    result = json.loads(completed.stdout)
                    if public and entrance == "cli":
                        result = result["result"]
                    assert result["snapshot_sha256"] == request.snapshot_sha256
                    assert all(value not in completed.stdout + completed.stderr
                               for value in ("alpha", "beta", "gamma", "delta"))
                    candidate_bundles.append({p.name: p.read_bytes() for p in destination.iterdir()})
                    if public and entrance == "cli":
                        for failure in ("digest", "budget", "overwrite"):
                            rejected = root / f"rejected-{failure}"
                            if failure == "overwrite":
                                rejected.mkdir()
                                (rejected / "owned.txt").write_bytes(b"fictional-owner-artifact")
                            before_paths = set(root.iterdir())
                            bad = [sys.executable, "-m", "test_data_agent.cli", "transform-execute",
                                str(source_path), str(policy_path), str(rejected), "--table", entity,
                                "--snapshot-sha256", "0" * 64 if failure == "digest" else request.snapshot_sha256,
                                "--json"]
                            if failure == "budget":
                                bad.extend(["--max-output-bytes", "1"])
                            refusal = subprocess.run(bad, capture_output=True, text=True,
                                timeout=30, check=False)
                            assert refusal.returncode != 0
                            assert set(root.iterdir()) == before_paths
                            if failure == "overwrite":
                                assert {p.name: p.read_bytes() for p in rejected.iterdir()} == {
                                    "owned.txt": b"fictional-owner-artifact"}
                            assert all(value not in refusal.stdout + refusal.stderr
                                       for value in ("alpha", "beta", "gamma", "delta"))
                with temporary_csv_publication(request, max_total_bytes=65536,
                        max_review_bytes=8192, max_output_bytes=32768, budget=GenerationBudget(10)) as output:
                    manifest = json.loads((output / "manifest.json").read_bytes())
                    assert all(bundle == {p.name: p.read_bytes() for p in output.iterdir()}
                               for bundle in candidate_bundles)
                    assert manifest["provenance"]["output_cells"] == (10 if typed else 4)
                    assert manifest["provenance"]["replacement_percent"] == "100.00"
                    if output_format == "csv":
                        expected = [["label", "measured"], ["gamma", "8"], ["delta", "7"]]
                        if typed:
                            expected = [expected[0] + ["amount", "day", "optional"],
                                expected[1] + ["7.50", "2027-03-04", ""],
                                expected[2] + ["8.25", "2027-04-05", "\\N"]]
                        assert list(csv.reader(io.StringIO((output / "dataset.csv").read_text()))) == expected
                    elif output_format == "parquet":
                        expected = [{"label": "gamma", "measured": 8}, {"label": "delta", "measured": 7}]
                        if typed:
                            expected[0].update(amount=Decimal("7.50"), day=date(2027, 3, 4), optional="")
                            expected[1].update(amount=Decimal("8.25"), day=date(2027, 4, 5), optional=None)
                        assert pq.read_table(output / "dataset.parquet").to_pylist() == expected
                    else:
                        sql = (output / "dataset.sql").read_text()
                        inserts = [line for line in sql.splitlines() if line.startswith("INSERT INTO")]
                        expected = [
                            'INSERT INTO "items" ("label", "measured") VALUES (\'gamma\', 8);',
                            'INSERT INTO "items" ("label", "measured") VALUES (\'delta\', 7);']
                        if typed:
                            expected = [
                                'INSERT INTO "items" ("label", "measured", "amount", "day", "optional") VALUES (\'gamma\', 8, 7.50, DATE \'2027-03-04\', \'\');',
                                'INSERT INTO "items" ("label", "measured", "amount", "day", "optional") VALUES (\'delta\', 7, 8.25, DATE \'2027-04-05\', NULL);']
                        assert inserts == expected
                        assert sql.endswith("COMMIT;\n")
                assert not output.parent.exists()
                assert hashlib.sha256(source_path.read_bytes() + policy_path.read_bytes()).digest() == before
            assert not root.exists()
            passed.append(f"{input_format}->{output_format}")
    print(json.dumps({"status": "passed", "routes": passed,
        "scope": "fictional small replacement workflow; CLI/MCP review and closed CLI/workspace execution; no DB"}))


if __name__ == "__main__":
    main()
