"""Verify that PyPI published the exact GitHub Release distributions."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.check_pypi_artifacts import (
    DISTRIBUTION_NAME,
    ArtifactValidationError,
    check_pypi_artifacts,
)


MAX_PYPI_RESPONSE_BYTES = 2 * 1024 * 1024
DEFAULT_ATTEMPTS = 20
DEFAULT_RETRY_DELAY_SECONDS = 15.0
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.+-]*$")


class PublishedReleaseValidationError(ValueError):
    """Raised when the public PyPI release differs from trusted artifacts."""


def verify_pypi_release(
    version: str,
    directory: Path,
    metadata: Mapping[str, Any],
) -> None:
    if VERSION_PATTERN.fullmatch(version) is None:
        raise PublishedReleaseValidationError("version must use X.Y.Z syntax")

    try:
        check_pypi_artifacts(f"v{version}", directory)
    except ArtifactValidationError as exc:
        raise PublishedReleaseValidationError(str(exc)) from exc

    local_hashes = {
        path.name: _sha256(path)
        for path in sorted(directory.iterdir())
    }
    info = metadata.get("info")
    published_files = metadata.get("urls")
    if not isinstance(info, Mapping) or not isinstance(published_files, list):
        raise PublishedReleaseValidationError("PyPI response is missing info or urls")
    if _canonical_name(info.get("name")) != DISTRIBUTION_NAME:
        raise PublishedReleaseValidationError("PyPI project name does not match")
    if info.get("version") != version:
        raise PublishedReleaseValidationError("PyPI project version does not match")

    published: dict[str, Mapping[str, Any]] = {}
    for item in published_files:
        if not isinstance(item, Mapping):
            raise PublishedReleaseValidationError("PyPI file entry is invalid")
        filename = item.get("filename")
        if not isinstance(filename, str) or filename in published:
            raise PublishedReleaseValidationError("PyPI filenames are invalid or duplicated")
        published[filename] = item

    if set(published) != set(local_hashes):
        raise PublishedReleaseValidationError(
            "PyPI filenames do not match the GitHub Release distributions"
        )

    for filename, expected_digest in local_hashes.items():
        item = published[filename]
        digests = item.get("digests")
        actual_digest = digests.get("sha256") if isinstance(digests, Mapping) else None
        if actual_digest != expected_digest:
            raise PublishedReleaseValidationError(
                f"PyPI SHA-256 does not match GitHub Release: {filename}"
            )
        if item.get("yanked") is not False:
            raise PublishedReleaseValidationError(
                f"PyPI distribution is yanked or has unknown status: {filename}"
            )
        expected_type = "bdist_wheel" if filename.endswith(".whl") else "sdist"
        if item.get("packagetype") != expected_type:
            raise PublishedReleaseValidationError(
                f"PyPI package type is invalid: {filename}"
            )


def fetch_pypi_metadata(
    version: str,
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
    open_url: Callable[..., Any] = urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> Mapping[str, Any]:
    if VERSION_PATTERN.fullmatch(version) is None:
        raise PublishedReleaseValidationError("version must use X.Y.Z syntax")
    if attempts < 1:
        raise ValueError("attempts must be positive")

    url = f"https://pypi.org/pypi/{DISTRIBUTION_NAME}/{version}/json"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "agent-paranoid-android-release-verifier",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with open_url(request, timeout=30) as response:
                payload = response.read(MAX_PYPI_RESPONSE_BYTES + 1)
            if len(payload) > MAX_PYPI_RESPONSE_BYTES:
                raise PublishedReleaseValidationError("PyPI response is too large")
            decoded = json.loads(payload)
            if not isinstance(decoded, Mapping):
                raise PublishedReleaseValidationError("PyPI response must be an object")
            return decoded
        except (
            HTTPError,
            URLError,
            TimeoutError,
            json.JSONDecodeError,
            PublishedReleaseValidationError,
        ) as exc:
            last_error = exc
            if attempt < attempts:
                sleep(retry_delay_seconds)

    raise PublishedReleaseValidationError(
        f"PyPI metadata was not available after {attempts} attempts: {last_error}"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[-_.]+", "-", value).lower()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "usage: verify_pypi_release.py X.Y.Z DIST_DIRECTORY",
            file=sys.stderr,
        )
        return 2
    try:
        metadata = fetch_pypi_metadata(argv[1])
        verify_pypi_release(argv[1], Path(argv[2]), metadata)
    except PublishedReleaseValidationError as exc:
        print(f"Published PyPI verification failed: {exc}", file=sys.stderr)
        return 1
    print(f"Published PyPI release verified: {DISTRIBUTION_NAME} {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
