"""Build one parallel RTD edition; never change a host default or Pages state."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

from scripts.build_documentation import ROOT, Identity, command, publish


@dataclass(frozen=True)
class Edition:
    identity: Identity
    canonical_url: str
    preview: bool


def edition(root: Path, environment: Mapping[str, str]) -> Edition:
    """Host labels identify the build, never prove release acceptance."""
    canonical = environment.get("READTHEDOCS_CANONICAL_URL", "")
    url = urlsplit(canonical)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or not canonical.endswith("/")
    ):
        raise ValueError(
            "RTD requires an absolute HTTPS edition URL without credentials"
        )
    kind = environment.get("READTHEDOCS_VERSION_TYPE")
    if kind not in {"branch", "tag", "external"}:
        raise ValueError("unsupported RTD version type")
    revision = command(["git", "rev-parse", "HEAD"], cwd=root)
    if environment.get("READTHEDOCS_GIT_COMMIT_HASH", revision) != revision:
        raise ValueError("RTD source hash does not match the checkout")
    dirty = command(
        [
            "git",
            "status",
            "--porcelain",
            "--",
            "docs",
            "mkdocs.yml",
            "pyproject.toml",
            "uv.lock",
            "scripts",
            ".readthedocs.yaml",
        ],
        cwd=root,
    )
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:rc[0-9]+)?", version):
        raise ValueError("unsupported documentation package version")
    preview = kind == "external"
    package_commit = revision
    try:
        package_commit = command(
            ["git", "rev-parse", f"refs/tags/v{version}^{{commit}}"], cwd=root
        )
    except subprocess.CalledProcessError:
        if kind == "tag":
            raise ValueError("tagged edition requires its package source tag") from None
    status = "PR preview / not stable" if preview else "Development / not stable"
    if kind == "tag":
        if (
            environment.get("READTHEDOCS_GIT_IDENTIFIER") != f"v{version}"
            or package_commit != revision
            or dirty
        ):
            raise ValueError(
                "tagged edition does not match the package tag and clean source"
            )
        if "rc" in version:
            status = "Release candidate / not stable"
        else:
            # The release catalog and public evidence gate promotion separately.
            # A faithful tagged build is not proof of a published stable release.
            status = "Parallel edition / awaiting public acceptance"
    return Edition(
        Identity(
            version, package_commit, revision + ("+dirty" if dirty else ""), status
        ),
        canonical,
        preview,
    )


def build(
    root: Path, output: Path, browser: str | None, environment: Mapping[str, str]
) -> None:
    root, output = root.resolve(), output.resolve()
    if (
        output == root
        or root.is_relative_to(output)
        or output.is_relative_to(root / "docs")
        or (output.exists() and not output.is_dir())
    ):
        raise ValueError("documentation output must not overwrite source files")
    tracked = command(["git", "ls-files", "-z"], cwd=root).split("\0")
    if any((root / name).is_relative_to(output) for name in tracked if name):
        raise ValueError("documentation output contains tracked source files")
    selected = edition(root, environment)
    if not selected.preview and not browser:
        raise ValueError("normal editions require a browser for all four downloads")
    # Do not inherit caller export/identity/mike overrides into a host build.
    build_env = {
        key: value
        for key, value in environment.items()
        if not key.startswith("DOCS_") and key != "MIKE_DOCS_VERSION"
    }
    build_env.update(
        DOCS_IDENTITY=json.dumps(asdict(selected.identity)),
        DOCS_HOST_URL=selected.canonical_url,
        DOCS_HOST_PREVIEW="1" if selected.preview else "0",
        DOCS_EXPORTS="0" if selected.preview else "1",
        DOCS_BROWSER=str(Path(browser).resolve()) if browser else "",
        PATH=str(Path(sys.executable).parent)
        + os.pathsep
        + environment.get("PATH", ""),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".apa-rtd-", dir=output.parent
    ) as temporary:
        work = Path(temporary)
        source, staged = work / "source", work / "site"
        source.mkdir()
        shutil.copytree(root / "docs", source / "docs")
        (source / "scripts").mkdir()
        shutil.copyfile(
            root / "scripts/documentation_hooks.py",
            source / "scripts/documentation_hooks.py",
        )
        shutil.copyfile(root / "mkdocs.yml", source / "mkdocs.yml")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "mkdocs",
                "build",
                "--strict",
                "--site-dir",
                str(staged),
            ],
            cwd=source,
            env=build_env,
            check=True,
            timeout=600,
        )
        publish(staged, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--browser")
    args = parser.parse_args()
    browser = args.browser
    if os.environ.get("READTHEDOCS_VERSION_TYPE") != "external" and not browser:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.executable_path
    build(ROOT, args.output, browser, os.environ)


if __name__ == "__main__":
    main()
