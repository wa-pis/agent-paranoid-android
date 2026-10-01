"""Fictional twelve-route saved-policy/CLI-review/private-publication acceptance."""

import csv
import hashlib
import io
import json
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
                if input_format == "csv":
                    source = SnapshotPart("source", entity, b"label,measured\nalpha,2\nbeta,1\n")
                elif input_format == "parquet":
                    buffer = io.BytesIO()
                    pq.write_table(table, buffer)
                    source = SnapshotPart("source", entity, buffer.getvalue())
                else:
                    adapter = SqlQueryAdapter(input_format.removesuffix("_query"))
                    physical = "public.items" if adapter is SqlQueryAdapter.POSTGRES else "lake.safe.items"
                    query_path = root / "query.sql"
                    query_path.write_text(f"SELECT label, measured FROM {physical}", encoding="utf-8")

                    @contextmanager
                    def stream(query):
                        assert query.sql.endswith("LIMIT 4") and "SELECT *" not in query.sql
                        yield iter(table.to_batches())

                    source = _capture_authorized_result(
                        SqlQueryProfileRequest(adapter, "fictional", "items", query_path),
                        allowed_tables=frozenset({physical}),
                        source_columns=(QuerySourceColumn("label", "text", True),
                                        QuerySourceColumn("measured", "bigint", True)),
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
                summary = _run_temporary_transform(source_path, entity, policy_path,
                    expected_snapshot_sha256=request.snapshot_sha256, max_total_bytes=65536,
                    max_review_bytes=8192, max_output_bytes=32768, budget=GenerationBudget(10))
                assert summary["status"] == "temporary_test_completed"
                with temporary_csv_publication(request, max_total_bytes=65536,
                        max_review_bytes=8192, max_output_bytes=32768, budget=GenerationBudget(10)) as output:
                    manifest = json.loads((output / "manifest.json").read_bytes())
                    assert manifest["provenance"]["output_cells"] == 4
                    assert manifest["provenance"]["replacement_percent"] == "100.00"
                    if output_format == "csv":
                        assert list(csv.reader(io.StringIO((output / "dataset.csv").read_text()))) == [
                            ["label", "measured"], ["gamma", "8"], ["delta", "7"]]
                    elif output_format == "parquet":
                        assert pq.read_table(output / "dataset.parquet").to_pylist() == [
                            {"label": "gamma", "measured": 8}, {"label": "delta", "measured": 7}]
                    else:
                        sql = (output / "dataset.sql").read_text()
                        inserts = [line for line in sql.splitlines() if line.startswith("INSERT INTO")]
                        assert inserts == [
                            'INSERT INTO "items" ("label", "measured") VALUES (\'gamma\', 8);',
                            'INSERT INTO "items" ("label", "measured") VALUES (\'delta\', 7);']
                        assert sql.endswith("COMMIT;\n")
                assert not output.parent.exists()
                assert hashlib.sha256(source_path.read_bytes() + policy_path.read_bytes()).digest() == before
            assert not root.exists()
            passed.append(f"{input_format}->{output_format}")
    print(json.dumps({"status": "passed", "routes": passed,
        "scope": "fictional small replacement workflow; CLI review and private execution; no DB"}))


if __name__ == "__main__":
    main()
