"""Fictional dictionary expansion; isolated environment, no product monkeypatch."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("width,accepted", [(128, True), (768, False), (4096, False)])
def test_decoded_parquet_limit_across_batches(width, accepted):
    pytest.importorskip("pyarrow")
    script = '''
import io
import sys
import pyarrow as pa
import pyarrow.parquet as pq
from test_data_agent.core.limits import GenerationBudget, InputLimitError
from test_data_agent.core.transformation_policy import BehaviorPolicy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader

width = int(sys.argv[1])
buffer = io.BytesIO()
pq.write_table(pa.table({"code": ["x" * width] * 2048}), buffer,
               use_dictionary=True)
metadata = pq.ParquetFile(io.BytesIO(buffer.getvalue())).metadata
assert metadata.row_group(0).column(0).total_uncompressed_size < 1024 * 1024
policy = BehaviorPolicy.model_validate({"schema_version": "0.1",
    "schema_fingerprint": "0" * 64, "seed": 7, "input_format": "parquet",
    "fields": [{"entity": "items", "field": "code",
        "sensitivity": "non_sensitive", "behavior": {"action": "drop"}}]})
try:
    rows = source_reader(SnapshotPart("source", "items", buffer.getvalue()),
                         policy, budget=GenerationBudget(5))
except InputLimitError as error:
    assert "decoded size" in str(error)
    print("rejected")
else:
    assert len(rows.rows) == 2048
    print("accepted")
'''
    result = subprocess.run([sys.executable, "-c", script, str(width)],
        env={**os.environ, "TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES": "1048576",
             "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ("accepted" if accepted else "rejected")
