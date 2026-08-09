"""Verify that a signed release tag identifies the accepted source commit."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


TAG_PATTERN = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+[0-9A-Za-z.+-]*")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


class ReleaseIdentityError(ValueError):
    """Raised when release source identity cannot be verified."""


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        raise ReleaseIdentityError("release identity verification failed") from None
    return result.stdout.strip()


def check_release_identity(
    tag: str,
    accepted_commit: str,
    allowed_signers: Path,
    *,
    root: Path = Path.cwd(),
) -> None:
    """Require an accepted commit, annotated tag, and allowed SSH signature."""
    if TAG_PATTERN.fullmatch(tag) is None:
        raise ReleaseIdentityError("release tag is invalid")
    if COMMIT_PATTERN.fullmatch(accepted_commit) is None:
        raise ReleaseIdentityError("accepted commit must be a full lowercase SHA-1")
    if not allowed_signers.is_file() or allowed_signers.is_symlink():
        raise ReleaseIdentityError("release signer policy is unavailable")

    tag_ref = f"refs/tags/{tag}"
    if _git(root, "cat-file", "-t", tag_ref) != "tag":
        raise ReleaseIdentityError("release tag must be annotated")
    if _git(root, "rev-parse", f"{tag_ref}^{{commit}}") != accepted_commit:
        raise ReleaseIdentityError("release tag does not identify accepted commit")
    if _git(root, "rev-parse", "HEAD^{commit}") != accepted_commit:
        raise ReleaseIdentityError("checked-out source is not the accepted commit")
    _git(
        root,
        "-c",
        f"gpg.ssh.allowedSignersFile={allowed_signers.resolve()}",
        "verify-tag",
        tag_ref,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 3:
        print(
            "usage: check_release_identity.py TAG ACCEPTED_COMMIT ALLOWED_SIGNERS",
            file=sys.stderr,
        )
        return 2
    try:
        check_release_identity(arguments[0], arguments[1], Path(arguments[2]))
    except ReleaseIdentityError as exc:
        print(f"release identity check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
