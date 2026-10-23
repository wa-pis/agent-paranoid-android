"""Release gates, actual standard-plugin builds and publication recovery."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import tarfile
from dataclasses import asdict
from pathlib import Path

import pytest
from scripts import build_documentation as docs

pytest.importorskip("mkdocs")

from scripts import documentation_hooks as hooks
from scripts import verify_documentation as published_docs

RELEASE = docs.Release("1.6.0", "a" * 40, 123)
IDENTITY = docs.Identity(
    "1.6.0", RELEASE.commit, "b" * 40 + "+dirty", "Maintained stable guidance"
)


def source_tree(root: Path, version: str = "1.6.0") -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text(f'[project]\nversion = "{version}"\n')
    (root / "mkdocs.yml").write_text("site_name: Test\n")
    (root / "docs/releases.json").write_text(
        json.dumps({"stable": "1.6.0", "releases": [asdict(RELEASE)]})
    )
    (root / "docs/index.md").write_text(
        "# Handbook\n\n[Rules](how-to/business-rules.md#checks)\n"
    )
    (root / "docs/how-to").mkdir(exist_ok=True)
    (root / "docs/how-to/business-rules.md").write_text(
        "# Rules\n\n## Checks\n\n[Reference](../reference/cli.md)\n"
    )


@pytest.mark.parametrize(
    "version,commit",
    [("1.6.0rc1", "a" * 40), ("../1.6.0", "a" * 40), ("1.6.0", "main")],
)
def test_catalog_rejects_unbound_or_nonstable_identity(tmp_path, version, commit):
    source_tree(tmp_path)
    (tmp_path / "docs/releases.json").write_text(
        json.dumps(
            {
                "stable": version,
                "releases": [
                    {"version": version, "commit": commit, "verification_run": 1}
                ],
            }
        )
    )
    with pytest.raises(ValueError):
        docs.releases(tmp_path)


@pytest.mark.parametrize(
    "failure", ["wrong_commit", "failed", "wrong_workflow", "draft"]
)
def test_public_gate_rejects_wrong_verification(tmp_path, monkeypatch, failure):
    run = {
        "conclusion": "success",
        "status": "completed",
        "head_sha": RELEASE.commit,
        "path": ".github/workflows/verify-published-release.yml",
    }
    published = {"draft": False, "prerelease": False}
    if failure == "wrong_commit":
        run["head_sha"] = "c" * 40
    if failure == "failed":
        run["conclusion"] = "failure"
    if failure == "wrong_workflow":
        run["path"] = ".github/workflows/docs.yml"
    if failure == "draft":
        published["draft"] = True

    def result(args, **kwargs):
        if args[0] == "git":
            return RELEASE.commit
        return json.dumps(run if "/actions/runs/" in args[-1] else published)

    monkeypatch.setattr(docs, "command", result)
    with pytest.raises(ValueError):
        docs.verify_release(RELEASE, tmp_path)


def test_public_verification_compares_identity_and_each_artifact(monkeypatch):
    identity = {**asdict(IDENTITY), "documentation_revision": "b" * 40}
    files = {
        name: b"fictional artifact"
        for name in ("handbook.pdf", "handbook.html", "handbook.md.zip", "site.zip")
    }
    manifest = {
        **identity,
        "index_sha256": hashlib.sha256(b"fictional entry page").hexdigest(),
        "sha256": {k: hashlib.sha256(v).hexdigest() for k, v in files.items()},
    }
    responses = {
        "": b"fictional entry page",
        "documentation.json": json.dumps(identity).encode(),
        "versions/versions.json": json.dumps(
            [{"version": "1.6.0", "aliases": ["stable"]}]
        ).encode(),
        "versions/stable/documentation.json": json.dumps(identity).encode(),
        "downloads/documentation.json": json.dumps(manifest).encode(),
        **{"downloads/" + k: v for k, v in files.items()},
    }
    monkeypatch.setattr(
        published_docs,
        "download",
        lambda url: responses[url.removeprefix(docs.BASE_URL)],
    )
    published_docs.verify(docs.BASE_URL, identity)
    responses["versions/versions.json"] = b'[{"version":"1.5.0","aliases":["stable"]}]'
    with pytest.raises(ValueError, match="stable alias"):
        published_docs.verify(docs.BASE_URL, identity)
    responses["versions/versions.json"] = b'[{"version":"1.6.0","aliases":["stable"]}]'
    responses["downloads/handbook.pdf"] = b"a stale PDF"
    with pytest.raises(ValueError, match="hash mismatch"):
        published_docs.verify(docs.BASE_URL, identity)
    responses["documentation.json"] = json.dumps(
        {**identity, "package_version": "1.5.0"}
    ).encode()
    with pytest.raises(ValueError, match="identity"):
        published_docs.verify(docs.BASE_URL, identity)


def test_public_verification_rejects_dirty_docs_without_network(monkeypatch):
    def reject(url):
        pytest.fail("dirty docs must fail before network access")

    monkeypatch.setattr(published_docs, "download", reject)
    with pytest.raises(ValueError, match="uncommitted"):
        published_docs.verify(docs.BASE_URL, asdict(IDENTITY))


def test_local_output_cannot_replace_source_or_unrelated_files(tmp_path):
    source_tree(tmp_path)
    other = tmp_path / "unrelated.txt"
    other.write_text("keep")
    for output in (tmp_path, tmp_path / "docs", other):
        with pytest.raises(ValueError):
            docs.build(tmp_path, output, "unused")
    assert other.read_text() == "keep"


def test_shortened_docs_retain_bookmark_anchors():
    expected = {
        "index.md": ("project-status", "the-safe-workflow", "safety-boundaries"),
        "getting-started/installation.md": (
            "accepted-candidate-baseline",
            "install-for-development",
        ),
        "reference/cli.md": (
            "implemented-rc-execution-candidate",
            "common-profile-workflow-16-rc",
            "configured-sql-sessions-16-rc",
        ),
        "reference/configuration.md": (
            "common-transformation-profile-16-rc",
            "transformation-input-limits-16-rc",
            "configured-sql-session-bounds-16-rc",
        ),
    }
    for name, anchors in expected.items():
        body = (docs.ROOT / "docs" / name).read_text()
        for anchor in anchors:
            assert f'id="{anchor}"' in body


@pytest.mark.parametrize("error", [OSError, KeyboardInterrupt])
def test_publication_restores_previous_site_on_failure(tmp_path, monkeypatch, error):
    previous, staged = tmp_path / "site", tmp_path / "staged"
    previous.mkdir()
    staged.mkdir()
    (previous / "index.html").write_text("previous site")
    original = Path.rename

    def rename(path, target):
        if path == staged:
            raise error("fictional publication interruption")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(error):
        docs.publish(staged, previous)
    assert (previous / "index.html").read_text() == "previous site"
    assert not list(tmp_path.glob(".apa-docs-backup-*"))


def test_failed_rollback_retains_previous_site_outside_staging(tmp_path, monkeypatch):
    previous, staged = tmp_path / "site", tmp_path / "staged"
    previous.mkdir()
    staged.mkdir()
    (previous / "index.html").write_text("previous site")
    original = Path.rename

    def rename(path, target):
        if path == staged:
            previous.mkdir()
            (previous / "index.html").write_text("other writer")
            raise OSError("fictional destination collision")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(OSError):
        docs.publish(staged, previous)
    (backup,) = tmp_path.glob(".apa-docs-backup-*")
    assert (backup / "previous/index.html").read_text() == "previous site"
    assert (previous / "index.html").read_text() == "other writer"


def test_standard_plugins_preserve_stable_and_old_versions_in_preview(tmp_path):
    pytest.importorskip("mkdocs")
    pytest.importorskip("mike")
    source = tmp_path / "source"
    source_tree(source)
    (source / "scripts").mkdir()
    shutil.copyfile(
        docs.ROOT / "scripts/documentation_hooks.py",
        source / "scripts/documentation_hooks.py",
    )
    (source / "mkdocs.yml").write_text("""site_name: Fictional Guide
site_url: https://wa-pis.github.io/agent-paranoid-android/
theme:
  name: readthedocs
  highlightjs: false
hooks: [scripts/documentation_hooks.py]
plugins:
  - search
  - mike:
      alias_type: copy
      deploy_prefix: versions
      version_selector: false
  - print-site:
      print_page_basename: handbook
nav:
  - Guide: index.md
  - Rules: how-to/business-rules.md
""")
    (source / "docs/reference").mkdir()
    (source / "docs/reference/cli.md").write_text("# Reference\n")
    (source / "docs/release-evidence-old.md").write_text(
        "# Historical fictional evidence\n"
    )
    for args in (
        ["init", "--initial-branch=main"],
        ["config", "user.name", "Fictional"],
        ["config", "user.email", "fictional@invalid.example"],
        ["add", "."],
        ["-c", "commit.gpgsign=false", "commit", "-m", "fictional docs"],
    ):
        docs.command(["git", *args], cwd=source)
    browser = tmp_path / "fictional-browser"
    browser.write_text(
        f'#!{sys.executable}\nfrom pathlib import Path\nimport sys\nfor arg in sys.argv:\n if arg.startswith("--print-to-pdf="): Path(arg.split("=",1)[1]).write_bytes(b"%PDF-fictional")\n'
    )
    browser.chmod(0o755)
    output, bundle = tmp_path / "site", tmp_path / "site.bundle"
    docs.build(source, output, str(browser), bundle=bundle)
    search = json.loads((output / "search/search_index.json").read_text())["docs"]
    assert any(item["location"].startswith("reference/cli/") for item in search)
    assert not any(
        item["location"].startswith("release-evidence-old/") for item in search
    )
    assert (output / "release-evidence-old/index.html").exists()
    before = (output / "index.html").read_bytes()
    stable_identity = (output / "documentation.json").read_bytes()
    assert (output / "versions/stable/index.html").exists()
    assert (
        'id="how-to-business-rules"' in (output / "downloads/handbook.html").read_text()
    )
    assert (
        "https://wa-pis.github.io/agent-paranoid-android/reference/cli/"
        in (output / "downloads/handbook.html").read_text()
    )
    docs.command(
        ["git", "fetch", str(bundle), "gh-pages:refs/remotes/origin/gh-pages"],
        cwd=source,
    )
    (source / "pyproject.toml").write_text('[project]\nversion = "1.7.0rc1"\n')
    (source / "docs/index.md").write_text("# NEXT VERSION ONLY\n")
    docs.build(source, output, str(browser))
    assert (output / "index.html").read_bytes() == before
    assert (output / "documentation.json").read_bytes() == stable_identity
    assert (output / "versions/1.6.0/index.html").read_bytes() == (
        output / "versions/stable/index.html"
    ).read_bytes()
    assert "NEXT VERSION ONLY" in (output / "versions/next/index.html").read_text()
    assert (
        "Development / not stable"
        in (output / "versions/next/documentation.json").read_text()
    )
    versions = json.loads((output / "versions/versions.json").read_text())
    assert {entry["version"] for entry in versions} == {"1.6.0", "next"}


def test_russian_search_and_navigation_keep_the_language(tmp_path, monkeypatch):
    from bs4 import BeautifulSoup
    from mkdocs.commands.build import build
    from mkdocs.config import load_config
    from urllib.parse import urljoin

    monkeypatch.delenv("MIKE_DOCS_VERSION", raising=False)
    monkeypatch.delenv("DOCS_IDENTITY", raising=False)
    site = tmp_path / "site"
    build(load_config(str(docs.ROOT / "mkdocs.yml"), site_dir=str(site)))
    for path, russian in (
        ("ru/index.html", True),
        ("ru/getting-started/first-csv/index.html", True),
        ("ru/search.html", True),
        ("search.html", False),
    ):
        page = BeautifulSoup((site / path).read_text(), "html.parser")
        base = "https://docs.invalid/versions/stable/"
        target = base + ("ru/search.html" if russian else "search.html")
        for form in page.select("#rtd-search-form, #content_search"):
            assert urljoin(base + path, form["action"]) == target
        assert ("Начало" in page.select_one(".wy-menu-vertical").get_text()) == russian
        home = page.select_one(".wy-breadcrumbs li a")["href"]
        assert urljoin(base + path, home) == base + ("ru/" if russian else "")
    search = BeautifulSoup((site / "ru/search.html").read_text(), "html.parser")
    assert search.select_one("h1").get_text() == "Результаты поиска"
    assert search.select_one("#mkdocs-search-results")["data-no-results-text"] == "Ничего не найдено"
    for path in ("ru/index.html", "history/index.html"):
        page = BeautifulSoup((site / path).read_text(), "html.parser")
        for link in page.select(".rst-footer-buttons a"):
            target = urljoin("https://docs.invalid/" + path, link["href"])
            assert ("/ru/" in target) == path.startswith("ru/")


@pytest.mark.parametrize(
    "path",
    ["https://example.invalid/image.png", "file:///etc/passwd", "../outside.txt"],
)
def test_standalone_resources_are_confined_to_built_site(tmp_path, path):
    with pytest.raises(RuntimeError, match="outside"):
        hooks.local_resource(path, tmp_path / "site")


@pytest.mark.parametrize(
    "name,kind", [("../outside", "file"), ("/absolute", "file"), ("linked", "symlink")]
)
def test_native_state_archive_cannot_escape_build_directory(
    tmp_path, monkeypatch, name, kind
):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w") as archive:
        member = tarfile.TarInfo(name)
        if kind == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "../outside"
        archive.addfile(member)
    from types import SimpleNamespace

    monkeypatch.setattr(
        docs.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=data.getvalue())
    )
    with pytest.raises(ValueError, match="unsafe"):
        docs.extract_state(tmp_path, tmp_path / "site")


def test_attachment_links_to_reference_but_keeps_bundled_anchors():
    result = hooks.portable_html(
        '<html><body><h1 id="guide">Guide</h1><a href="#guide">Guide</a><a href="#reference-cli-command">Reference</a></body></html>',
        {"reference-cli": "reference/cli/"},
        docs.BASE_URL,
    )
    assert 'href="#guide"' in result
    assert (
        'href="https://wa-pis.github.io/agent-paranoid-android/reference/cli/#command"'
        in result
    )
    with pytest.raises(ValueError, match="unresolved"):
        hooks.portable_html('<a href="#unknown">Broken</a>', {}, docs.BASE_URL)
