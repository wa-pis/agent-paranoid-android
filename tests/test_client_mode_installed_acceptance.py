"""Fictional installed-CLI mode/ratio acceptance, without private inputs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_explicit_negative_mode_reaches_installed_generation(tmp_path: Path) -> None:
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

    spec = {
        "entities": [{"name": "fictional_orders", "row_count": 12, "fields": [
            {"name": "amount", "data_type": "integer"},
        ]}],
        "generation_settings": {"seed": 31, "mode": "valid", "invalid_ratio": 0,
                                "output_format": "json"},
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "test_data_agent.cli", "generate", "spec.json",
         "--mode", "negative", "--invalid-ratio", "1", "--output", "out"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode in {0, 1}
    rows = json.loads((tmp_path / "out/fictional_orders.json").read_text())
    manifest = json.loads((tmp_path / "out/generation_manifest.json").read_text())
    report = json.loads((tmp_path / "out/validation_report.json").read_text())
    assert len(rows) == 12
    assert all(isinstance(row["amount"], str) for row in rows)
    assert manifest["effective_rules"]["generation_mode"] == "negative"
    assert manifest["effective_rules"]["invalid_ratio"] == 1
    assert report["valid"] is False
    assert json.loads((tmp_path / "spec.json").read_text()) == spec
