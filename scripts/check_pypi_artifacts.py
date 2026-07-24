"""Verify release distribution identity before publishing to PyPI."""

from __future__ import annotations

import re
import sys
import tarfile
import zipfile
from email.message import Message
from email.parser import BytesParser
from pathlib import Path


DISTRIBUTION_NAME = "agent-paranoid-android"
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
MAX_METADATA_BYTES = 1024 * 1024
TAG_PATTERN = re.compile(r"^v([0-9]+\.[0-9]+\.[0-9]+[A-Za-z0-9.+-]*)$")


class ArtifactValidationError(ValueError):
    """Raised when release distributions cannot be trusted for publication."""


def check_pypi_artifacts(tag: str, directory: Path) -> None:
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ArtifactValidationError("release tag must use vX.Y.Z syntax")
    version = match.group(1)

    if not directory.is_dir() or directory.is_symlink():
        raise ArtifactValidationError("distribution path must be a real directory")
    files = sorted(directory.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in files):
        raise ArtifactValidationError("distribution directory must contain regular files")

    wheels = [path for path in files if path.suffix == ".whl"]
    sdists = [path for path in files if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1 or len(files) != 2:
        raise ArtifactValidationError(
            "distribution directory must contain exactly one wheel and one sdist"
        )

    for path in files:
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            raise ArtifactValidationError(
                f"distribution exceeds {MAX_ARTIFACT_BYTES} bytes: {path.name}"
            )

    _check_metadata(_read_wheel_metadata(wheels[0]), version, wheels[0])
    _check_metadata(_read_sdist_metadata(sdists[0]), version, sdists[0])


def _read_wheel_metadata(path: Path) -> Message:
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise ArtifactValidationError("wheel contains too many members")
            candidates = [
                member
                for member in members
                if member.filename.endswith(".dist-info/METADATA")
            ]
            if len(candidates) != 1:
                raise ArtifactValidationError(
                    "wheel must contain exactly one dist-info/METADATA file"
                )
            member = candidates[0]
            if member.file_size > MAX_METADATA_BYTES:
                raise ArtifactValidationError("wheel metadata is too large")
            payload = archive.read(member)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ArtifactValidationError(f"invalid wheel archive: {path.name}") from exc
    return BytesParser().parsebytes(payload)


def _read_sdist_metadata(path: Path) -> Message:
    payload: bytes | None = None
    metadata_count = 0
    member_count = 0
    try:
        with tarfile.open(path, mode="r|gz") as archive:
            for member in archive:
                member_count += 1
                if member_count > MAX_ARCHIVE_MEMBERS:
                    raise ArtifactValidationError("sdist contains too many members")
                if not member.isfile() or not member.name.endswith("/PKG-INFO"):
                    continue
                metadata_count += 1
                if member.size > MAX_METADATA_BYTES:
                    raise ArtifactValidationError("sdist metadata is too large")
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ArtifactValidationError("sdist metadata cannot be read")
                payload = extracted.read(MAX_METADATA_BYTES + 1)
    except (OSError, tarfile.TarError) as exc:
        raise ArtifactValidationError(f"invalid sdist archive: {path.name}") from exc
    if metadata_count != 1 or payload is None:
        raise ArtifactValidationError(
            "sdist must contain exactly one top-level PKG-INFO file"
        )
    return BytesParser().parsebytes(payload)


def _check_metadata(metadata: Message, version: str, path: Path) -> None:
    names = metadata.get_all("Name", [])
    versions = metadata.get_all("Version", [])
    if len(names) != 1 or _canonical_name(names[0]) != DISTRIBUTION_NAME:
        raise ArtifactValidationError(
            f"distribution name does not match {DISTRIBUTION_NAME}: {path.name}"
        )
    if versions != [version]:
        raise ArtifactValidationError(
            f"distribution version does not match {version}: {path.name}"
        )


def _canonical_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "usage: check_pypi_artifacts.py vX.Y.Z DIST_DIRECTORY",
            file=sys.stderr,
        )
        return 2
    try:
        check_pypi_artifacts(argv[1], Path(argv[2]))
    except ArtifactValidationError as exc:
        print(f"PyPI artifact check failed: {exc}", file=sys.stderr)
        return 1
    print(f"PyPI distributions verified for {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
