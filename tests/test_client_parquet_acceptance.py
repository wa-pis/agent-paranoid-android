"""Fictional installed-package Parquet physical-schema acceptance."""

import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import pytest


def test_installed_cli_preserves_declared_parquet_temporal_types(tmp_path: Path) -> None:
    pq = pytest.importorskip("pyarrow.parquet")
    package_root = Path(os.environ.get(
        "TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT",
        str(Path(__file__).resolve().parents[1] / "src"),
    )).resolve(strict=True)
    env = {**os.environ, "PYTHONPATH": str(package_root), "PYTHONDONTWRITEBYTECODE": "1"}
    probe = subprocess.run(
        [sys.executable, "-c", "import test_data_agent; print(test_data_agent.__file__)"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert probe.returncode == 0
    assert Path(probe.stdout.strip()).resolve().is_relative_to(package_root)
    spec = tmp_path / "fictional-spec.json"
    spec.write_text(json.dumps({
        "schema_version": "1.0",
        "entities": [{"name": "orders", "row_count": 3, "fields": [
            {"name": "id", "data_type": "integer", "is_identifier": True},
            {"name": "created_on", "data_type": "date"},
            {"name": "created_at", "data_type": "datetime"},
        ]}],
        "generation_settings": {"seed": 7, "output_format": "parquet"},
    }), encoding="utf-8")
    output = tmp_path / "generated"

    result = subprocess.run(
        [sys.executable, "-m", "test_data_agent.cli", "generate", str(spec),
         "--output", str(output)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, "fictional installed Parquet CLI generation failed"
    schema = pq.read_schema(output / "orders.parquet")
    rows = pq.read_table(output / "orders.parquet").to_pylist()
    assert str(schema.field("id").type) == "int64"
    assert str(schema.field("created_on").type) == "date32[day]"
    assert str(schema.field("created_at").type) == "timestamp[us]"
    assert len(rows) == 3
    assert all(isinstance(row["created_on"], date) for row in rows)
    assert all(isinstance(row["created_at"], datetime) for row in rows)
    assert json.loads((output / "generation_manifest.json").read_text())["synthetic"]
