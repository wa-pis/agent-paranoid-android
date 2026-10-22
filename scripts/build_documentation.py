"""Assemble GitHub Pages with mike and MkDocs print-site; never read datasets.

Version storage/aliases/selector belong to mike. Print-site assembles the
handbook; HTMLArk embeds assets; Chrome prints PDF. This module only coordinates
those tools, release evidence, legacy root URLs and atomic local publication.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://wa-pis.github.io/agent-paranoid-android/"
REPOSITORY = "wa-pis/agent-paranoid-android"


@dataclass(frozen=True)
class Release:
    version: str
    commit: str
    verification_run: int


@dataclass(frozen=True)
class Identity:
    package_version: str
    package_commit: str
    documentation_revision: str
    status: str


def command(args: list[str], *, cwd: Path = ROOT) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True, timeout=300
    ).stdout.strip()


def releases(root: Path) -> tuple[str, tuple[Release, ...]]:
    data = json.loads((root / "docs/releases.json").read_text())
    items = tuple(Release(**item) for item in data["releases"])
    if not items or len({r.version for r in items}) != len(items):
        raise ValueError("documentation releases must be nonempty and unique")
    for release in items:
        if (
            not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", release.version)
            or not re.fullmatch(r"[0-9a-f]{40}", release.commit)
            or type(release.verification_run) is not int
            or release.verification_run <= 0
        ):
            raise ValueError("invalid stable documentation identity")
    if data["stable"] not in {r.version for r in items}:
        raise ValueError("stable documentation release is missing")
    return data["stable"], items


def verify_release(release: Release, root: Path) -> None:
    commit = command(["git", "rev-parse", f"v{release.version}^{{commit}}"], cwd=root)
    if commit != release.commit:
        raise ValueError("release tag does not match documentation catalog")
    run = json.loads(
        command(
            [
                "gh",
                "api",
                f"repos/{REPOSITORY}/actions/runs/{release.verification_run}",
            ],
            cwd=root,
        )
    )
    if (
        run.get("conclusion") != "success"
        or run.get("status") != "completed"
        or run.get("head_sha") != release.commit
        or run.get("path") != ".github/workflows/verify-published-release.yml"
    ):
        raise ValueError(
            "documentation promotion requires exact-source public verification"
        )
    published = json.loads(
        command(
            [
                "gh",
                "api",
                f"repos/{REPOSITORY}/releases/tags/v{release.version}",
            ],
            cwd=root,
        )
    )
    if published.get("draft") is not False or published.get("prerelease") is not False:
        raise ValueError("documentation default must be a published stable release")


def publish(staged: Path, output: Path) -> None:
    """Keep rollback outside staging cleanup, including on interruption."""
    backup_root = Path(tempfile.mkdtemp(prefix=".apa-docs-backup-", dir=output.parent))
    previous = backup_root / "previous"
    try:
        if output.exists():
            output.rename(previous)
        staged.rename(output)
    except BaseException:
        if previous.exists() and not output.exists():
            previous.rename(output)
        # If another writer occupied output or restore failed, retain the backup.
        # The staging TemporaryDirectory must never delete the previous site.
        raise
    else:
        if previous.exists():
            shutil.rmtree(previous)
    finally:
        if not previous.exists():
            backup_root.rmdir()


def extract_state(repository: Path, destination: Path) -> None:
    archive = subprocess.run(
        ["git", "archive", "gh-pages"],
        cwd=repository,
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source.getmembers():
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination.resolve()) or not (
                member.isfile() or member.isdir()
            ):
                raise ValueError("unsafe documentation branch archive")
        for member in source.getmembers():
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = source.extractfile(member)
                assert stream is not None
                target.write_bytes(stream.read())


def build(
    root: Path,
    output: Path,
    browser: str,
    *,
    check_public: bool = False,
    state_ref: str = "refs/remotes/origin/gh-pages",
    bundle: Path | None = None,
) -> None:
    root, output = root.resolve(), output.resolve()
    if (
        output == root
        or root.is_relative_to(output)
        or output.is_relative_to(root / "docs")
        or (output.exists() and not output.is_dir())
    ):
        raise ValueError("documentation output must not overwrite source files")
    stable, catalog = releases(root)
    selected = next(release for release in catalog if release.version == stable)
    if check_public:
        verify_release(selected, root)
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    revision = command(["git", "rev-parse", "HEAD"], cwd=root)
    if command(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "docs",
            "mkdocs.yml",
            "pyproject.toml",
            "uv.lock",
            "scripts/build_documentation.py",
            "scripts/documentation_hooks.py",
        ],
        cwd=root,
    ):
        revision += "+dirty"
    preview = version != stable
    identity = Identity(
        version,
        revision.split("+")[0] if preview else selected.commit,
        revision,
        "Development / not stable" if preview else "Maintained stable guidance",
    )
    environment = {
        **os.environ,
        "DOCS_IDENTITY": json.dumps(asdict(identity)),
        "DOCS_EXPORTS": "1",
        "DOCS_BROWSER": str(Path(browser).resolve()),
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".apa-docs-", dir=output.parent
    ) as temporary:
        work = Path(temporary)
        repository, staged = work / "source", work / "site"
        repository.mkdir()
        for folder in ("docs", "scripts"):
            # Copy documentation and its two build hooks only; no runtime/data files.
            if folder == "docs":
                shutil.copytree(root / folder, repository / folder)
            else:
                (repository / folder).mkdir()
                shutil.copyfile(
                    root / "scripts/documentation_hooks.py",
                    repository / folder / "documentation_hooks.py",
                )
        shutil.copyfile(root / "mkdocs.yml", repository / "mkdocs.yml")
        command(["git", "init", "--initial-branch=build"], cwd=repository)
        command(["git", "config", "user.name", "Documentation builder"], cwd=repository)
        command(["git", "config", "user.email", "docs@invalid.example"], cwd=repository)
        command(["git", "add", "."], cwd=repository)
        command(
            ["git", "commit", "-m", "docs: stage documentation sources"], cwd=repository
        )
        exists = (
            subprocess.run(
                ["git", "rev-parse", "--verify", state_ref],
                cwd=root,
                capture_output=True,
                timeout=30,
            ).returncode
            == 0
        )
        if exists:
            command(
                ["git", "fetch", str(root), f"{state_ref}:refs/heads/gh-pages"],
                cwd=repository,
            )
        elif preview:
            raise ValueError(
                "publish stable documentation before building a next-version preview"
            )
        # mike updates one version and preserves all other already-rendered versions.
        target = "next" if preview else stable
        arguments = [
            str(Path(sys.executable).parent / "mike"),
            "deploy",
            "--ignore-remote-status",
            "--update-aliases",
            "--title",
            f"{version} (development)" if preview else version,
            target,
        ]
        if not preview:
            arguments.append("stable")
        subprocess.run(
            arguments, cwd=repository, env=environment, check=True, timeout=300
        )
        extract_state(repository, staged)
        if not preview:
            # Keep the original unversioned URL tree working, without mike's
            # selector (which expects a version directory). The banner links to it.
            current = work / "current"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mkdocs",
                    "build",
                    "--strict",
                    "--site-dir",
                    str(current),
                ],
                cwd=repository,
                env=environment,
                check=True,
                timeout=300,
            )
            shutil.copytree(current, staged, dirs_exist_ok=True)
        elif not (staged / "documentation.json").is_file():
            raise ValueError(
                "documentation branch is missing its maintained stable root"
            )
        # Persist the compatibility root alongside mike's native version state.
        # All Git mutations stay inside this disposable build repository.
        command(["git", "symbolic-ref", "HEAD", "refs/heads/gh-pages"], cwd=repository)
        command(["git", "read-tree", "gh-pages"], cwd=repository)
        command(["git", f"--work-tree={staged}", "add", "--all"], cwd=repository)
        command(
            [
                "git",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--allow-empty",
                "-m",
                "docs: retain stable compatibility URLs",
            ],
            cwd=repository,
        )
        if bundle is not None:
            state = work / "state.bundle"
            command(["git", "bundle", "create", str(state), "gh-pages"], cwd=repository)
            bundle.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(state, bundle)
        publish(staged, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "site")
    parser.add_argument(
        "--browser", default=shutil.which("google-chrome") or shutil.which("chromium")
    )
    parser.add_argument("--verify-release", action="store_true")
    parser.add_argument("--state-ref", default="refs/remotes/origin/gh-pages")
    parser.add_argument("--state-bundle", type=Path)
    args = parser.parse_args()
    if not args.browser:
        parser.error("Chrome/Chromium is required for PDF export; pass --browser PATH")
    build(
        ROOT,
        args.output,
        args.browser,
        check_public=args.verify_release,
        state_ref=args.state_ref,
        bundle=args.state_bundle,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
