"""Parallel host builds use fictional docs, Git identities and a fake PDF browser."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import zipfile
from dataclasses import asdict

import pytest

pytest.importorskip("mkdocs")
from scripts import build_documentation as pages
from scripts import build_readthedocs as host


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    (root / "docs/ru").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "pyproject.toml").write_text('[project]\nversion = "1.7.0rc1"\n')
    for name in (
        "index.md",
        "downloads.md",
        "ru/index.md",
        "ru/downloads.md",
        "versions.md",
    ):
        (root / "docs" / name).write_text(
            "# Fictional chapter\n\nFictional content only.\n"
        )
    shutil.copytree(pages.ROOT / "docs/theme", root / "docs/theme")
    shutil.copyfile(
        pages.ROOT / "scripts/documentation_hooks.py",
        root / "scripts/documentation_hooks.py",
    )
    (root / "mkdocs.yml").write_text("""site_name: Fictional
site_url: https://old.invalid/
strict: true
theme:
  name: readthedocs
  highlightjs: false
  custom_dir: docs/theme
  static_templates: [ru/search.html]
hooks: [scripts/documentation_hooks.py]
plugins:
  - search:
      lang: [en, ru]
  - mike:
      version_selector: false
  - print-site:
      print_page_basename: handbook
nav:
  - Guide: index.md
  - Downloads: downloads.md
  - Versions: versions.md
  - Русский:
      - Руководство: ru/index.md
      - Скачать: ru/downloads.md
""")
    for args in (
        ["init", "--initial-branch=main"],
        ["config", "user.name", "Fictional"],
        ["config", "user.email", "fictional@invalid.example"],
        ["add", "."],
        ["-c", "commit.gpgsign=false", "commit", "-m", "fictional docs"],
        ["tag", "v1.7.0rc1"],
    ):
        pages.command(["git", *args], cwd=root)
    return root


def environment(kind="branch", ref="main"):
    return {
        **os.environ,
        "READTHEDOCS_VERSION_TYPE": kind,
        "READTHEDOCS_GIT_IDENTIFIER": ref,
        "READTHEDOCS_CANONICAL_URL": "https://fictional.invalid/en/latest/",
    }


@pytest.mark.parametrize(
    "kind,ref,status",
    [
        ("branch", "main", "Development / not stable"),
        ("external", "42", "PR preview / not stable"),
        ("tag", "v1.7.0rc1", "Release candidate / not stable"),
    ],
)
def test_host_labels_never_accept_a_release(source, kind, ref, status):
    selected = host.edition(source, environment(kind, ref))
    assert selected.identity.status == status
    assert selected.preview == (kind == "external")
    assert selected.identity.package_commit == pages.command(
        ["git", "rev-parse", "HEAD"], cwd=source
    )


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://fictional.invalid/",
        "https://user:password@fictional.invalid/",
        "https://fictional.invalid/?token=x",
        "https://fictional.invalid/#x",
        "https://fictional.invalid/en/latest",
    ],
)
def test_host_rejects_invalid_canonical(source, url):
    env = environment()
    env["READTHEDOCS_CANONICAL_URL"] = url
    with pytest.raises(ValueError, match="HTTPS"):
        host.edition(source, env)


def test_dirty_docs_keep_the_tagged_package_source(source):
    original = pages.command(["git", "rev-parse", "HEAD"], cwd=source)
    (source / "docs/index.md").write_text("# Reviewed fictional correction\n")
    selected = host.edition(source, environment())
    assert selected.identity.package_commit == original
    assert selected.identity.documentation_revision == original + "+dirty"
    with pytest.raises(ValueError, match="clean source"):
        host.edition(source, environment("tag", "v1.7.0rc1"))


@pytest.mark.parametrize(
    "key,value",
    [
        ("READTHEDOCS_GIT_COMMIT_HASH", "a" * 40),
        ("READTHEDOCS_VERSION_TYPE", "unknown"),
    ],
)
def test_invalid_host_context_fails(source, key, value):
    env = environment()
    env[key] = value
    with pytest.raises(ValueError):
        host.edition(source, env)


def test_tag_ref_cannot_relabel_current_checkout(source):
    with pytest.raises(ValueError, match="package tag"):
        host.edition(source, environment("tag", "v1.6.0"))


@pytest.mark.parametrize("preview", [True, False])
def test_actual_host_build_identity_search_and_downloads(source, tmp_path, preview):
    from bs4 import BeautifulSoup

    browser = tmp_path / "fictional-browser"
    browser.write_text(
        f'#!{sys.executable}\nfrom pathlib import Path\nimport sys\nfor arg in sys.argv:\n if arg.startswith("--print-to-pdf="): Path(arg.split("=",1)[1]).write_bytes(b"%PDF-fictional")\n'
    )
    browser.chmod(0o755)
    output = tmp_path / "site"
    env = environment("external" if preview else "branch")
    # Caller settings must not enable exports in PR previews or mike nesting.
    env.update(DOCS_EXPORTS="1", MIKE_DOCS_VERSION="wrong", DOCS_IDENTITY="{}")
    host.build(source, output, None if preview else str(browser), env)
    selected = host.edition(source, env)
    assert json.loads((output / "documentation.json").read_text()) == asdict(
        selected.identity
    )
    assert not (output / "versions/versions.json").exists()
    assert "Parallel publication" in (output / "versions/index.html").read_text()
    page = BeautifulSoup((output / "index.html").read_text(), "html.parser")
    assert page.select_one('link[rel="canonical"]')["href"] == selected.canonical_url
    assert page.select_one('meta[name="robots"]')["content"] == "noindex"
    assert selected.identity.package_commit in page.get_text()
    for language in ("", "ru/"):
        downloads = (output / language / "downloads/index.html").read_text()
        assert (
            ("PR preview downloads" if not language else "Скачивания в PR-превью")
            in downloads
            if preview
            else "Fictional chapter" in downloads
        )
    search = json.loads((output / "search/search_index.json").read_text())
    assert any(item["location"].startswith("ru/") for item in search["docs"])
    manifest_path = output / "downloads/documentation.json"
    if preview:
        assert not manifest_path.exists()
        assert not list((output / "downloads").glob("*.zip"))
        return
    manifest = json.loads(manifest_path.read_text())
    assert (
        manifest["index_sha256"]
        == hashlib.sha256((output / "index.html").read_bytes()).hexdigest()
    )
    assert set(manifest["sha256"]) == {
        "handbook.pdf",
        "handbook.html",
        "handbook.md.zip",
        "site.zip",
    }
    for name, digest in manifest["sha256"].items():
        assert (
            hashlib.sha256((output / "downloads" / name).read_bytes()).hexdigest()
            == digest
        )
    for name in ("handbook.md.zip", "site.zip"):
        with zipfile.ZipFile(output / "downloads" / name) as archive:
            assert (
                json.loads(archive.read("documentation.json"))["package_commit"]
                == selected.identity.package_commit
            )
            assert "versions/versions.json" not in archive.namelist()


def test_failure_preserves_existing_output(source, tmp_path):
    output = tmp_path / "site"
    output.mkdir()
    (output / "known-good").write_text("retained")
    with pytest.raises(ValueError, match="browser"):
        host.build(source, output, None, environment())
    assert (output / "known-good").read_text() == "retained"


def test_stable_tag_build_cannot_claim_public_acceptance(source):
    (source / "pyproject.toml").write_text('[project]\nversion = "1.6.0"\n')
    pages.command(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-am",
            "fictional stable source",
        ],
        cwd=source,
    )
    pages.command(["git", "tag", "v1.6.0"], cwd=source)
    env = environment("tag", "v1.6.0")
    env["READTHEDOCS_VERSION"] = "stable"
    selected = host.edition(source, env)
    assert selected.identity.status == "Parallel edition / awaiting public acceptance"
    assert selected.identity.package_commit == pages.command(
        ["git", "rev-parse", "HEAD"], cwd=source
    )


def test_output_cannot_replace_tracked_scripts(source):
    with pytest.raises(ValueError, match="tracked source"):
        host.build(source, source / "scripts", None, environment("external"))
    assert (source / "scripts/documentation_hooks.py").exists()


def test_failed_strict_build_retains_previous_site(source, tmp_path):
    import subprocess

    output = tmp_path / "site"
    output.mkdir()
    (output / "known-good").write_text("retained")
    (source / "docs/index.md").write_text(
        "# Fictional broken link\n\n[Missing](does-not-exist.md)\n"
    )
    with pytest.raises(subprocess.CalledProcessError):
        host.build(source, output, None, environment("external"))
    assert (output / "known-good").read_text() == "retained"


def test_normal_cli_retains_the_exact_manifest_in_build_log(
    source, tmp_path, monkeypatch, capsys
):
    browser = tmp_path / "fictional-browser"
    browser.write_text(
        f'#!{sys.executable}\nfrom pathlib import Path\nimport sys\nfor arg in sys.argv:\n if arg.startswith("--print-to-pdf="): Path(arg.split("=",1)[1]).write_bytes(b"%PDF-fictional")\n'
    )
    browser.chmod(0o755)
    output = tmp_path / "site"
    for name, value in environment().items():
        if name.startswith("READTHEDOCS_"):
            monkeypatch.setenv(name, value)
    monkeypatch.setattr(host, "ROOT", source)
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_readthedocs", "--output", str(output), "--browser", str(browser)],
    )
    host.main()
    record = next(
        line.removeprefix("DOCS_EXPORT_MANIFEST=")
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("DOCS_EXPORT_MANIFEST=")
    )
    assert json.loads(record) == json.loads(
        (output / "downloads/documentation.json").read_text()
    )


@pytest.mark.parametrize("kind", ["branch", "tag"])
def test_development_package_version_cannot_be_a_stable_edition(source, kind):
    (source / "pyproject.toml").write_text('[project]\nversion = "1.7.0.dev1"\n')
    pages.command(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-am",
            "fictional development source",
        ],
        cwd=source,
    )
    pages.command(["git", "tag", "v1.7.0.dev1"], cwd=source)
    selected = host.edition(
        source, environment(kind, "v1.7.0.dev1" if kind == "tag" else "main")
    )
    assert selected.identity.package_version == "1.7.0.dev1"
    assert selected.identity.status == "Development / not stable"
    assert selected.identity.package_commit == pages.command(
        ["git", "rev-parse", "HEAD"], cwd=source
    )
