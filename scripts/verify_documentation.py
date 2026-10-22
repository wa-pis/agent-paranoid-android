"""Verify deployed documentation identity and its portable artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from urllib.parse import urlsplit
from urllib.request import urlopen

MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024


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


def verify(base: str, expected: dict[str, str]) -> None:
    if expected["documentation_revision"].endswith("+dirty"):
        raise ValueError("uncommitted documentation cannot be publicly verified")
    base = base.rstrip("/") + "/"
    identity = json.loads(download(base + "documentation.json"))
    if identity != expected:
        raise ValueError(
            "public documentation identity does not match the built artifact"
        )
    versions = json.loads(download(base + "versions/versions.json"))
    if not any(
        item.get("version") == expected["package_version"]
        and "stable" in item.get("aliases", [])
        for item in versions
    ):
        raise ValueError("native mike stable alias does not match the built package")
    if json.loads(download(base + "versions/stable/documentation.json")) != expected:
        raise ValueError("version selector stable destination has a different identity")
    manifest = json.loads(download(base + "downloads/documentation.json"))
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("portable documentation has a different version identity")
    if hashlib.sha256(download(base)).hexdigest() != manifest.get("index_sha256"):
        raise ValueError("public documentation entry page does not match the build")
    for name in ("handbook.pdf", "handbook.html", "handbook.md.zip", "site.zip"):
        payload = download(base + "downloads/" + name)
        if hashlib.sha256(payload).hexdigest() != manifest["sha256"].get(name):
            raise ValueError("portable documentation hash mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--expected-json", required=True)
    args = parser.parse_args()
    verify(args.url, json.loads(args.expected_json))
    print("Public documentation identity and downloads verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
