"""Verify deployed documentation identity and its portable artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import urlopen

MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
EXPORT_NAMES = ("handbook.pdf", "handbook.html", "handbook.md.zip", "site.zip")


def download(url: str) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ValueError("documentation verification requires HTTPS")
    with urlopen(url, timeout=20) as response:
        if urlsplit(response.url).scheme != "https":
            raise ValueError("documentation verification redirected away from HTTPS")
        payload = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(payload) > MAX_DOWNLOAD_BYTES:
        raise ValueError("documentation artifact exceeds verification budget")
    return payload


def _verify_identity(base: str, expected: dict[str, str]) -> str:
    if expected["documentation_revision"].endswith("+dirty"):
        raise ValueError("uncommitted documentation cannot be publicly verified")
    base = base.rstrip("/") + "/"
    identity = json.loads(download(base + "documentation.json"))
    if identity != expected:
        raise ValueError(
            "public documentation identity does not match the built artifact"
        )
    return base


def verify(base: str, expected: dict[str, str]) -> None:
    """Verify the accepted Pages root, including both native mike mappings."""
    base = _verify_identity(base, expected)
    versions = json.loads(download(base + "versions/versions.json"))
    if not any(
        item.get("version") == expected["package_version"]
        and "stable" in item.get("aliases", [])
        for item in versions
    ):
        raise ValueError("native mike stable alias does not match the built package")
    if json.loads(download(base + "versions/stable/documentation.json")) != expected:
        raise ValueError("version selector stable destination has a different identity")
    _verify_exports(
        base, expected, json.loads(download(base + "downloads/documentation.json"))
    )


def _verify_exports(
    base: str, expected: dict[str, str], manifest: dict[str, Any]
) -> None:
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("portable documentation has a different version identity")
    if hashlib.sha256(download(base)).hexdigest() != manifest.get("index_sha256"):
        raise ValueError("public documentation entry page does not match the build")
    for name in EXPORT_NAMES:
        payload = download(base + "downloads/" + name)
        if hashlib.sha256(payload).hexdigest() != manifest["sha256"].get(name):
            raise ValueError("portable documentation hash mismatch")


def verify_edition(
    base: str, expected: dict[str, str], built_manifest: dict[str, Any]
) -> None:
    """Compare one public edition against a retained build, without promoting it.

    A matching public manifest alone cannot prove the served files match a
    reviewed build: both could have changed together. Require the local manifest.
    """
    hashes = built_manifest.get("sha256")
    chapters = built_manifest.get("chapters")
    if (
        any(built_manifest.get(key) != value for key, value in expected.items())
        or not isinstance(hashes, dict)
        or set(hashes) != set(EXPORT_NAMES)
        or not all(
            isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
            for value in [built_manifest.get("index_sha256"), *hashes.values()]
        )
        or not isinstance(chapters, list)
        or not chapters
        or not all(
            isinstance(chapter, str) and chapter.endswith(".md") for chapter in chapters
        )
        or len(set(chapters)) != len(chapters)
    ):
        raise ValueError(
            "retained build manifest is incomplete or has a different identity"
        )
    base = _verify_identity(base, expected)
    if json.loads(download(base + "downloads/documentation.json")) != built_manifest:
        raise ValueError("public export manifest differs from the retained build")
    _verify_exports(base, expected, built_manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--expected-json", required=True)
    parser.add_argument(
        "--edition-manifest",
        type=Path,
        help="Retained normal-edition export manifest; verifies bytes, not stable/default promotion",
    )
    args = parser.parse_args()
    expected = json.loads(args.expected_json)
    if args.edition_manifest is None:
        verify(args.url, expected)
        print("Public documentation identity and downloads verified.")
    else:
        verify_edition(
            args.url, expected, json.loads(args.edition_manifest.read_text())
        )
        print(
            "Public edition matches the retained build; stable/default promotion is not verified."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
