from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.check_release_acceptance import (
    REQUIRED_FINDINGS,
    REQUIRED_GATES,
    AcceptanceManifestError,
    _unique_object,
    _validate_manifest,
    check_release_acceptance,
)


TAG = "v1.0.0rc6"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _manifest(commit: str, artifacts: Path) -> dict[str, Any]:
    evidence_url = "https://example.test/rc6-evidence"
    artifact_digests = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in artifacts.iterdir()
    }
    return {
        "schema_version": 1,
        "release": {"tag": TAG, "reviewed_commit": commit},
        "findings": {
            finding_id: {"disposition": "closed", "evidence": evidence_url}
            for finding_id in REQUIRED_FINDINGS
        },
        "approvals": [
            {
                "reviewer": "independent-reviewer",
                "reviewed_commit": commit,
                "url": "https://example.test/rc6-approval",
            }
        ],
        "gates": {
            gate: {
                "commit": commit,
                "status": "passed",
                "url": f"https://example.test/gates/{gate}",
            }
            for gate in REQUIRED_GATES
        },
        "artifacts": artifact_digests,
    }


def test_signed_tag_manifest_binds_evidence_and_artifact_digests(
    tmp_path: Path,
) -> None:
    if shutil.which("ssh-keygen") is None:
        pytest.skip("ssh-keygen is required for SSH signature verification")

    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.name", "Release Test")
    _git(repository, "config", "user.email", "release@example.test")
    (repository / "payload.txt").write_text("accepted\n")
    _git(repository, "add", "payload.txt")
    _git(repository, "commit", "--quiet", "-m", "accepted")
    accepted_commit = _git(repository, "rev-parse", "HEAD")

    artifacts = tmp_path / "dist"
    artifacts.mkdir()
    wheel = artifacts / "agent_paranoid_android-1.0.0rc6-py3-none-any.whl"
    wheel.write_bytes(b"synthetic wheel")
    (artifacts / "agent_paranoid_android-1.0.0rc6.tar.gz").write_bytes(
        b"synthetic sdist"
    )
    manifest_path = tmp_path / "acceptance.json"
    manifest_path.write_text(json.dumps(_manifest(accepted_commit, artifacts)))

    signing_key = tmp_path / "signing-key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(signing_key)],
        check=True,
    )
    _git(
        repository,
        "-c",
        "gpg.format=ssh",
        "-c",
        f"user.signingKey={signing_key}",
        "tag",
        "-s",
        TAG,
        "-F",
        str(manifest_path),
    )

    check_release_acceptance(
        TAG,
        accepted_commit,
        root=repository,
        artifacts=artifacts,
    )

    wheel.write_bytes(b"changed wheel")
    with pytest.raises(
        AcceptanceManifestError,
        match="built artifact digest does not match",
    ):
        check_release_acceptance(
            TAG,
            accepted_commit,
            root=repository,
            artifacts=artifacts,
        )


def test_manifest_rejects_incomplete_or_stale_acceptance(tmp_path: Path) -> None:
    commit = "1" * 40
    artifacts = tmp_path / "dist"
    artifacts.mkdir()
    (artifacts / "package.whl").write_bytes(b"wheel")
    (artifacts / "package.tar.gz").write_bytes(b"sdist")
    manifest = _manifest(commit, artifacts)

    missing_finding = copy.deepcopy(manifest)
    del missing_finding["findings"]["RC6-S20"]
    with pytest.raises(AcceptanceManifestError, match="findings are incomplete"):
        _validate_manifest(missing_finding, TAG, commit)

    pending_finding = copy.deepcopy(manifest)
    pending_finding["findings"]["RC6-S12"]["disposition"] = "pending"
    with pytest.raises(AcceptanceManifestError, match="RC6-S12 is not accepted"):
        _validate_manifest(pending_finding, TAG, commit)

    invalid_finding = copy.deepcopy(manifest)
    invalid_finding["findings"]["RC6-S12"]["disposition"] = ["closed"]
    with pytest.raises(AcceptanceManifestError, match="RC6-S12 is not accepted"):
        _validate_manifest(invalid_finding, TAG, commit)

    stale_approval = copy.deepcopy(manifest)
    stale_approval["approvals"][0]["reviewed_commit"] = "2" * 40
    with pytest.raises(AcceptanceManifestError, match="approval does not match"):
        _validate_manifest(stale_approval, TAG, commit)

    failed_gate = copy.deepcopy(manifest)
    failed_gate["gates"]["security"]["status"] = "failed"
    with pytest.raises(AcceptanceManifestError, match="security gate did not pass"):
        _validate_manifest(failed_gate, TAG, commit)

    missing_digest = copy.deepcopy(manifest)
    del missing_digest["artifacts"]["package.whl"]
    with pytest.raises(AcceptanceManifestError, match="artifact digests are incomplete"):
        _validate_manifest(missing_digest, TAG, commit)

    with pytest.raises(AcceptanceManifestError, match="duplicate keys"):
        _unique_object([("status", "passed"), ("status", "failed")])
