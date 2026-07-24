from __future__ import annotations

import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path
from urllib.error import URLError

import pytest

from scripts.check_pypi_artifacts import (
    ArtifactValidationError,
    check_pypi_artifacts,
)
from scripts.verify_pypi_release import (
    PublishedReleaseValidationError,
    fetch_pypi_metadata,
    hashed_wheel_requirement,
    verify_pypi_release,
)


def write_distributions(
    directory: Path,
    *,
    name: str = "agent-paranoid-android",
    version: str = "0.5.0",
) -> None:
    normalized = name.replace("-", "_")
    wheel = directory / f"{normalized}-{version}-py3-none-any.whl"
    metadata = (
        "Metadata-Version: 2.4\n"
        f"Name: {name}\n"
        f"Version: {version}\n"
        "\n"
    ).encode()
    with zipfile.ZipFile(wheel, mode="w") as archive:
        archive.writestr(f"{normalized}-{version}.dist-info/METADATA", metadata)

    sdist = directory / f"{normalized}-{version}.tar.gz"
    with tarfile.open(sdist, mode="w:gz") as archive:
        member = tarfile.TarInfo(f"{normalized}-{version}/PKG-INFO")
        member.size = len(metadata)
        archive.addfile(member, io.BytesIO(metadata))


def published_metadata(directory: Path, *, version: str = "0.5.0") -> dict:
    urls = []
    for path in sorted(directory.iterdir()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        urls.append(
            {
                "filename": path.name,
                "packagetype": (
                    "bdist_wheel" if path.name.endswith(".whl") else "sdist"
                ),
                "digests": {"sha256": digest},
                "yanked": False,
            }
        )
    return {
        "info": {
            "name": "agent-paranoid-android",
            "version": version,
        },
        "urls": urls,
    }


def test_check_pypi_artifacts_accepts_matching_distributions(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)

    check_pypi_artifacts("v0.5.0", tmp_path)


def test_check_pypi_artifacts_rejects_mismatched_version(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path, version="0.4.0")

    with pytest.raises(ArtifactValidationError, match="does not match 0.5.0"):
        check_pypi_artifacts("v0.5.0", tmp_path)


def test_check_pypi_artifacts_rejects_extra_or_nonregular_files(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)
    (tmp_path / "SHA256SUMS").write_text("not a distribution")

    with pytest.raises(ArtifactValidationError, match="exactly one wheel and one sdist"):
        check_pypi_artifacts("v0.5.0", tmp_path)

    (tmp_path / "SHA256SUMS").unlink()
    (tmp_path / "nested").mkdir()
    with pytest.raises(ArtifactValidationError, match="regular files"):
        check_pypi_artifacts("v0.5.0", tmp_path)


def test_verify_pypi_release_accepts_matching_public_digests(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)

    verify_pypi_release("0.5.0", tmp_path, published_metadata(tmp_path))


def test_hashed_wheel_requirement_uses_verified_distribution(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)
    wheel = next(tmp_path.glob("*.whl"))

    requirement = hashed_wheel_requirement("0.5.0", tmp_path)

    assert requirement == (
        "agent-paranoid-android==0.5.0 "
        f"--hash=sha256:{hashlib.sha256(wheel.read_bytes()).hexdigest()}\n"
    )


def test_hashed_wheel_requirement_rejects_ambiguous_wheels(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)
    (tmp_path / "second.whl").write_bytes(b"synthetic wheel")

    with pytest.raises(PublishedReleaseValidationError, match="exactly one wheel"):
        hashed_wheel_requirement("0.5.0", tmp_path)


def test_verify_pypi_release_rejects_digest_mismatch(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)
    metadata = published_metadata(tmp_path)
    metadata["urls"][0]["digests"]["sha256"] = "0" * 64

    with pytest.raises(PublishedReleaseValidationError, match="SHA-256"):
        verify_pypi_release("0.5.0", tmp_path, metadata)


def test_verify_pypi_release_rejects_extra_or_yanked_public_file(
    tmp_path: Path,
) -> None:
    write_distributions(tmp_path)
    metadata = published_metadata(tmp_path)
    metadata["urls"].append(
        {
            "filename": "unexpected.zip",
            "packagetype": "sdist",
            "digests": {"sha256": "0" * 64},
            "yanked": False,
        }
    )

    with pytest.raises(PublishedReleaseValidationError, match="filenames"):
        verify_pypi_release("0.5.0", tmp_path, metadata)

    metadata = published_metadata(tmp_path)
    metadata["urls"][0]["yanked"] = True
    with pytest.raises(PublishedReleaseValidationError, match="yanked"):
        verify_pypi_release("0.5.0", tmp_path, metadata)


def test_fetch_pypi_metadata_retries_without_external_requests() -> None:
    expected = {"info": {"name": "agent-paranoid-android"}, "urls": []}
    attempts: list[object] = [URLError("not ready"), JsonResponse(expected)]
    delays: list[float] = []

    def open_url(*_args, **_kwargs):
        result = attempts.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    metadata = fetch_pypi_metadata(
        "0.5.0",
        attempts=2,
        retry_delay_seconds=0.25,
        open_url=open_url,
        sleep=delays.append,
    )

    assert metadata == expected
    assert delays == [0.25]


class JsonResponse:
    def __init__(self, value: dict) -> None:
        self.payload = json.dumps(value).encode()

    def __enter__(self) -> JsonResponse:
        return self

    def __exit__(self, *_args) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self.payload
