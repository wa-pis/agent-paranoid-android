from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.check_release_identity import (
    ReleaseIdentityError,
    check_release_identity,
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_release_identity_requires_signed_tag_on_exact_accepted_commit(
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

    signing_key = tmp_path / "signing-key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(signing_key)],
        check=True,
    )
    allowed_signers = tmp_path / "allowed-signers"
    allowed_signers.write_text(
        f"release@example.test {(tmp_path / 'signing-key.pub').read_text()}"
    )
    _git(
        repository,
        "-c",
        "gpg.format=ssh",
        "-c",
        f"user.signingKey={signing_key}",
        "tag",
        "-s",
        "v1.0.0rc6",
        "-m",
        "signed",
    )

    check_release_identity(
        "v1.0.0rc6",
        accepted_commit,
        allowed_signers,
        root=repository,
    )

    other_key = tmp_path / "other-key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(other_key)],
        check=True,
    )
    other_signers = tmp_path / "other-signers"
    other_signers.write_text(
        f"release@example.test {(tmp_path / 'other-key.pub').read_text()}"
    )
    with pytest.raises(
        ReleaseIdentityError,
        match="release identity verification failed",
    ):
        check_release_identity(
            "v1.0.0rc6",
            accepted_commit,
            other_signers,
            root=repository,
        )

    with pytest.raises(
        ReleaseIdentityError,
        match="release tag does not identify accepted commit",
    ):
        check_release_identity(
            "v1.0.0rc6",
            "1" * 40,
            allowed_signers,
            root=repository,
        )

    _git(repository, "tag", "-a", "v1.0.0rc7", "-m", "unsigned")
    with pytest.raises(
        ReleaseIdentityError,
        match="release identity verification failed",
    ):
        check_release_identity(
            "v1.0.0rc7",
            accepted_commit,
            allowed_signers,
            root=repository,
        )

    _git(repository, "tag", "v1.0.0rc8")
    with pytest.raises(ReleaseIdentityError, match="release tag must be annotated"):
        check_release_identity(
            "v1.0.0rc8",
            accepted_commit,
            allowed_signers,
            root=repository,
        )

    (repository / "payload.txt").write_text("different checkout\n")
    _git(repository, "commit", "--quiet", "--all", "-m", "different checkout")
    with pytest.raises(
        ReleaseIdentityError,
        match="checked-out source is not the accepted commit",
    ):
        check_release_identity(
            "v1.0.0rc6",
            accepted_commit,
            allowed_signers,
            root=repository,
        )


def test_release_identity_rejects_untrusted_inputs(tmp_path: Path) -> None:
    signers = tmp_path / "signers"
    signers.write_text("release@example.test ssh-ed25519 invalid\n")

    with pytest.raises(ReleaseIdentityError, match="release tag is invalid"):
        check_release_identity("--help", "1" * 40, signers, root=tmp_path)
    with pytest.raises(ReleaseIdentityError, match="full lowercase SHA-1"):
        check_release_identity("v1.0.0rc6", "main", signers, root=tmp_path)
