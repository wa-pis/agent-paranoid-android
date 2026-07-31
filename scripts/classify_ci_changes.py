"""Classify a GitHub change set without trusting path input."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections.abc import Callable, Iterable


_SHA_RE = re.compile(r"[0-9a-fA-F]{40,64}")
_DOCUMENTATION_ROOTS = {"docs", "openspec"}
_DOCUMENTATION_FILES = {"mkdocs.yml"}


def is_documentation_path(raw_path: str) -> bool:
    path = raw_path.removeprefix("./")
    if not path or path.startswith("/") or ".." in path.split("/"):
        return False
    first = path.split("/", maxsplit=1)[0]
    return (
        path.endswith(".md")
        or path in _DOCUMENTATION_FILES
        or first in _DOCUMENTATION_ROOTS
    )


def requires_heavy_checks(paths: Iterable[str]) -> bool:
    changed = tuple(path for path in paths if path)
    return not changed or any(not is_documentation_path(path) for path in changed)


def git_changed_paths(base: str, head: str) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", base, head, "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(result.stdout.splitlines())


def should_run_heavy_checks(
    *,
    event: str,
    ref: str,
    base: str,
    head: str,
    path_loader: Callable[[str, str], Iterable[str]] = git_changed_paths,
) -> bool:
    if event not in {"pull_request", "push"} or ref.startswith("refs/tags/"):
        return True
    if (
        not _SHA_RE.fullmatch(base)
        or not _SHA_RE.fullmatch(head)
        or set(base) == {"0"}
    ):
        return True
    try:
        return requires_heavy_checks(path_loader(base, head))
    except (OSError, subprocess.SubprocessError):
        return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="")
    args = parser.parse_args()
    run_heavy = should_run_heavy_checks(
        event=args.event,
        ref=args.ref,
        base=args.base,
        head=args.head,
    )
    print(f"code={'true' if run_heavy else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
