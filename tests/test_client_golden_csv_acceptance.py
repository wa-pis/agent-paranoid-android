"""Fictional source-free subset of the reviewed client golden_run.py.

Not preservation acceptance; private snapshot/pair cases remain unverified.
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path


def test_golden_csv_profile_infer_generate(tmp_path: Path) -> None:
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
    source = tmp_path / "source.csv"
    source.write_text(
        "id,domain_code,created_at,amount\n"
        "d7f9b4a3-0000-4000-8000-000000000001,ALL,2026-07-22,-5\n"
        "d7f9b4a3-0000-4000-8000-000000000002,RUB,2026-07-23,3000\n"
        "d7f9b4a3-0000-4000-8000-000000000003,RUB,2026-07-24,10\n"
        "d7f9b4a3-0000-4000-8000-000000000004,ALL,2026-07-25,20\n"
        "d7f9b4a3-0000-4000-8000-000000000005,ALL,2026-07-26,30\n",
        encoding="utf-8",
    )
    for args in [
        ["profile-csv", "source.csv", "--table", "deal", "--output", "profile.json"],
        ["infer-spec", "profile.json", "--output", "spec.yaml"],
        ["generate", "spec.yaml", "--count", "5", "--seed", "7", "--format", "csv", "--output", "out"],
    ]:
        completed = subprocess.run(
            [sys.executable, "-m", "test_data_agent.cli", *args], cwd=tmp_path,
            env=env, capture_output=True, text=True, timeout=30,
        )
        assert completed.returncode == 0, "fictional golden CSV CLI stage failed"
    profile = json.loads((tmp_path / "profile.json").read_text())
    fields = {field["name"]: field for field in profile["entities"][0]["fields"]}
    distribution = fields["domain_code"]["distribution"]
    assert distribution["kind"] == "categorical"
    categories = {item["value"] for item in distribution["categories"]}
    assert categories.isdisjoint({"ALL", "RUB"})
    with (tmp_path / "out/deal.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 5
    assert len({row["id"] for row in rows}) == 5
    assert {row["domain_code"] for row in rows} <= categories
    assert all(-5 <= int(row["amount"]) <= 3000 for row in rows)
    assert all("2026-07-22" <= row["created_at"] <= "2026-07-26" for row in rows)
    report = json.loads((tmp_path / "out/validation_report.json").read_text())
    assert report["valid"] is True
