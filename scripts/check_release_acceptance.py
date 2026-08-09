"""Validate the RC6 acceptance manifest embedded in a signed release tag."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MAX_MANIFEST_BYTES = 128 * 1024
MAX_URL_LENGTH = 2048
TAG_PATTERN = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+[0-9A-Za-z.+-]*")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")
SIGNATURE_MARKER = b"\n-----BEGIN SSH SIGNATURE-----\n"
REQUIRED_FINDINGS = frozenset(
    {
        "RC6-S1",
        "RC6-S2",
        "RC6-S3",
        "RC6-S4",
        "RC6-S7",
        "RC6-S8",
        "RC6-S9",
        "RC6-S10",
        "RC6-S11",
        "RC6-S12",
        "RC6-S13",
        "RC6-S14",
        "RC6-S15",
        "RC6-S16",
        "RC6-S17",
        "RC6-S18",
        "RC6-S19",
        "RC6-S20",
    }
)
REQUIRED_GATES = frozenset({"ci", "containers", "documentation", "security"})


class AcceptanceManifestError(ValueError):
    """Raised when release acceptance evidence is missing or inconsistent."""


def check_release_acceptance(
    tag: str,
    accepted_commit: str,
    *,
    root: Path = Path.cwd(),
    artifacts: Path | None = None,
) -> None:
    """Validate signed-tag evidence and optional built artifact digests."""
    if TAG_PATTERN.fullmatch(tag) is None:
        raise AcceptanceManifestError("release tag is invalid")
    if COMMIT_PATTERN.fullmatch(accepted_commit) is None:
        raise AcceptanceManifestError("accepted commit must be a full lowercase SHA-1")

    manifest = _load_tag_manifest(root, tag)
    expected_artifacts = _validate_manifest(manifest, tag, accepted_commit)
    if artifacts is not None:
        _check_artifacts(artifacts, expected_artifacts)


def _load_tag_manifest(root: Path, tag: str) -> Mapping[str, Any]:
    tag_ref = f"refs/tags/{tag}"
    try:
        size_result = subprocess.run(
            ["git", "cat-file", "-s", tag_ref],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        size = int(size_result.stdout.strip())
        if size > MAX_MANIFEST_BYTES:
            raise AcceptanceManifestError("acceptance tag is too large")
        tag_result = subprocess.run(
            ["git", "cat-file", "tag", tag_ref],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        raise AcceptanceManifestError("acceptance manifest cannot be read") from None

    _, header_separator, message = tag_result.stdout.partition(b"\n\n")
    manifest_bytes, signature_separator, _ = message.partition(SIGNATURE_MARKER)
    if not header_separator or not signature_separator:
        raise AcceptanceManifestError("signed acceptance manifest is missing")
    try:
        manifest = json.loads(manifest_bytes, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AcceptanceManifestError("acceptance manifest is invalid JSON") from None
    if not isinstance(manifest, Mapping):
        raise AcceptanceManifestError("acceptance manifest must be an object")
    return manifest


def _validate_manifest(
    manifest: Mapping[str, Any],
    tag: str,
    accepted_commit: str,
) -> Mapping[str, str]:
    required_keys = {
        "schema_version",
        "release",
        "findings",
        "approvals",
        "gates",
        "artifacts",
    }
    if set(manifest) != required_keys or type(manifest["schema_version"]) is not int:
        raise AcceptanceManifestError("acceptance manifest schema is invalid")
    if manifest["schema_version"] != 1:
        raise AcceptanceManifestError("acceptance manifest schema is unsupported")

    release = _mapping(manifest["release"], "release identity")
    if set(release) != {"tag", "reviewed_commit"}:
        raise AcceptanceManifestError("release identity is incomplete")
    if release["tag"] != tag or release["reviewed_commit"] != accepted_commit:
        raise AcceptanceManifestError("release identity does not match accepted source")

    _validate_findings(manifest["findings"])
    _validate_approvals(manifest["approvals"], accepted_commit)
    _validate_gates(manifest["gates"], accepted_commit)
    return _validate_artifact_entries(manifest["artifacts"])


def _validate_findings(value: Any) -> None:
    findings = _mapping(value, "findings")
    if set(findings) != REQUIRED_FINDINGS:
        raise AcceptanceManifestError("release-blocking findings are incomplete")
    for finding_id in sorted(REQUIRED_FINDINGS):
        finding = _mapping(findings[finding_id], "finding")
        if set(finding) != {"disposition", "evidence"}:
            raise AcceptanceManifestError(f"{finding_id} disposition is incomplete")
        disposition = finding["disposition"]
        if not isinstance(disposition, str) or disposition not in {
            "closed",
            "approved",
        }:
            raise AcceptanceManifestError(f"{finding_id} is not accepted")
        _require_url(finding["evidence"], f"{finding_id} evidence")


def _validate_approvals(value: Any, accepted_commit: str) -> None:
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise AcceptanceManifestError("independent approval is missing")
    seen_urls: set[str] = set()
    for item in value:
        approval = _mapping(item, "approval")
        if set(approval) != {"reviewer", "reviewed_commit", "url"}:
            raise AcceptanceManifestError("approval is incomplete")
        reviewer = approval["reviewer"]
        if (
            not isinstance(reviewer, str)
            or not 1 <= len(reviewer) <= 128
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in reviewer
            )
            or reviewer.casefold() in {"pending", "tbd", "unknown"}
        ):
            raise AcceptanceManifestError("reviewer identity is invalid")
        if approval["reviewed_commit"] != accepted_commit:
            raise AcceptanceManifestError("approval does not match accepted source")
        url = _require_url(approval["url"], "approval URL")
        if url in seen_urls:
            raise AcceptanceManifestError("approval URL is duplicated")
        seen_urls.add(url)


def _validate_gates(value: Any, accepted_commit: str) -> None:
    gates = _mapping(value, "gates")
    if set(gates) != REQUIRED_GATES:
        raise AcceptanceManifestError("required gate results are incomplete")
    for gate_name in sorted(REQUIRED_GATES):
        gate = _mapping(gates[gate_name], "gate")
        if set(gate) != {"commit", "status", "url"}:
            raise AcceptanceManifestError(f"{gate_name} gate result is incomplete")
        if gate["status"] != "passed" or gate["commit"] != accepted_commit:
            raise AcceptanceManifestError(f"{gate_name} gate did not pass accepted source")
        _require_url(gate["url"], f"{gate_name} gate URL")


def _validate_artifact_entries(value: Any) -> Mapping[str, str]:
    artifacts = _mapping(value, "artifacts")
    if len(artifacts) != 2:
        raise AcceptanceManifestError("artifact digests are incomplete")
    wheels = 0
    sdists = 0
    validated: dict[str, str] = {}
    for name, digest in artifacts.items():
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not 1 <= len(name) <= 255
            or any(ord(character) < 32 for character in name)
        ):
            raise AcceptanceManifestError("artifact name is invalid")
        if not isinstance(digest, str) or DIGEST_PATTERN.fullmatch(digest) is None:
            raise AcceptanceManifestError("artifact digest is invalid")
        wheels += name.endswith(".whl")
        sdists += name.endswith(".tar.gz")
        validated[name] = digest
    if wheels != 1 or sdists != 1:
        raise AcceptanceManifestError("wheel and sdist digests are required")
    return validated


def _check_artifacts(directory: Path, expected: Mapping[str, str]) -> None:
    if not directory.is_dir() or directory.is_symlink():
        raise AcceptanceManifestError("artifact directory is invalid")
    distributions = {
        path.name: path
        for path in directory.iterdir()
        if path.name.endswith((".whl", ".tar.gz"))
    }
    if set(distributions) != set(expected):
        raise AcceptanceManifestError("built artifacts do not match acceptance manifest")
    for name, path in distributions.items():
        if path.is_symlink() or not path.is_file():
            raise AcceptanceManifestError("built artifact is invalid")
        if _sha256(path) != expected[name]:
            raise AcceptanceManifestError("built artifact digest does not match")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not all(
        isinstance(key, str) for key in value
    ):
        raise AcceptanceManifestError(f"{label} must be an object")
    return value


def _require_url(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= MAX_URL_LENGTH
        or any(ord(character) <= 32 or ord(character) == 127 for character in value)
    ):
        raise AcceptanceManifestError(f"{label} is invalid")
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise AcceptanceManifestError(f"{label} is invalid")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AcceptanceManifestError("acceptance manifest has duplicate keys")
        result[key] = value
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) not in {2, 3}:
        print(
            "usage: check_release_acceptance.py TAG ACCEPTED_COMMIT [ARTIFACT_DIR]",
            file=sys.stderr,
        )
        return 2
    try:
        check_release_acceptance(
            arguments[0],
            arguments[1],
            artifacts=Path(arguments[2]) if len(arguments) == 3 else None,
        )
    except (AcceptanceManifestError, OSError) as exc:
        print(f"release acceptance check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
