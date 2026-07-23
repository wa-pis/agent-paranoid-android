"""Fail a release when its Git tag and package version differ."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).parent.parent


def package_version() -> str:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return str(metadata["project"]["version"])


def check_release_tag(tag: str) -> None:
    if not tag.startswith("v"):
        raise ValueError("release tag must start with 'v'")
    expected = f"v{package_version()}"
    if tag != expected:
        raise ValueError(f"release tag {tag!r} does not match package version {expected!r}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_release_tag.py vX.Y.Z", file=sys.stderr)
        return 2
    try:
        check_release_tag(sys.argv[1])
    except ValueError as exc:
        print(f"release check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
