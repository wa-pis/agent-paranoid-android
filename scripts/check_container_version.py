#!/usr/bin/env python3
"""Fail when release container metadata disagrees with package metadata."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def package_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return str(payload["project"]["version"])


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("usage: check_container_version.py VERSION")
    expected = package_version()
    if args[0] != expected:
        raise SystemExit(
            f"container version {args[0]!r} does not match package version {expected!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
