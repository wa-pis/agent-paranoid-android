from __future__ import annotations

import json
from pathlib import Path

import pytest

from examples.reference_agent import main


FIXTURE_EXAMPLE_DATASET = Path("tests/fixtures/example_dataset")


def test_reference_agent_stops_for_review_then_requires_exact_hash(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = tmp_path / "agent"

    assert main(
        [
            "plan",
            str(FIXTURE_EXAMPLE_DATASET),
            "--workspace",
            str(workspace),
            "--count",
            "7",
            "--seed",
            "42",
        ]
    ) == 0
    pending = json.loads(capsys.readouterr().out)
    reviewed_hash = pending["review"]["current_spec_sha256"]

    assert pending["phase"] == "awaiting_approval"
    assert pending["approval_required"] is True
    assert (workspace / "advisor_review.json").is_file()
    assert "alice@example.com" not in (
        workspace / "advisor_review.json"
    ).read_text()
    assert not (workspace / "generated").exists()

    assert main(["status", str(workspace)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["review"]["current_spec_sha256"] == reviewed_hash
    assert status["next_action"] == "review_and_approve"

    with pytest.raises(SystemExit) as rejected:
        main(
            [
                "approve",
                str(workspace),
                "--reviewed-spec-sha256",
                "0" * 64,
            ]
        )
    assert rejected.value.code == 2
    assert "fingerprint mismatch" in capsys.readouterr().err
    assert not (workspace / "generated").exists()

    assert main(
        [
            "approve",
            str(workspace),
            "--reviewed-spec-sha256",
            reviewed_hash,
        ]
    ) == 0
    completed = json.loads(capsys.readouterr().out)
    manifest = json.loads(
        (workspace / "generated" / "generation_manifest.json").read_text()
    )

    assert completed["phase"] == "completed"
    assert completed["approval_required"] is False
    assert completed["summary"]["seed"] == 42
    assert completed["summary"]["row_counts"] == {"customers": 7, "orders": 7}
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
