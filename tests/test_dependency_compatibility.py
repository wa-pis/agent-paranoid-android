from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.check_dependency_compatibility import (
    CompatibilityError,
    check_manifest,
    check_repository,
)
from test_data_agent.io import artifacts as artifacts_module


ROOT = Path(__file__).parent.parent


def test_dependency_compatibility_policy_matches_repository() -> None:
    reviewed = check_repository(ROOT)

    assert reviewed["faker"] == "40.35.0"
    assert reviewed["mcp"] == "1.28.1"
    assert reviewed["openai"] == "2.50.0"
    assert reviewed["psycopg"] == "3.3.4"


def test_manifest_dependency_evidence_must_be_complete_and_hashed(
    tmp_path: Path,
) -> None:
    dependencies = {
        "faker": "40.35.0",
        "pydantic": "2.13.4",
    }
    digest = hashlib.sha256(
        json.dumps(dependencies, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    manifest = tmp_path / "generation_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "package_version": "0.12.0",
                "reproducibility": {
                    "generator_algorithm_version": "0.12.0",
                    "normalized_dependencies": dependencies,
                    "normalized_dependencies_sha256": digest,
                }
            }
        )
    )

    check_manifest(manifest, {"faker": "40.35.0", "pydantic": "2.13.4"})

    with pytest.raises(CompatibilityError, match="incomplete"):
        check_manifest(manifest, {"faker": "40.35.0", "pyyaml": "6.0.3"})


def test_manifest_dependency_discovery_includes_installed_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(artifacts_module.importlib.metadata, "version", lambda name: name)

    assert artifacts_module.normalized_dependency_versions()["psycopg"] == "psycopg"
