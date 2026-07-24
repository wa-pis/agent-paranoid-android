from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.check_pypi_artifacts import (
    ArtifactValidationError,
    check_pypi_artifacts,
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
