"""Small MkDocs integration: identity, search scope and standard-tool exports."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from mkdocs.plugins import event_priority


def is_history(source: str) -> bool:
    source = source.removeprefix("ru/")
    name = Path(source).name
    return (
        source.startswith(("adr/", "release-history/", "agent-guides/"))
        or name.startswith(
            (
                "release-",
                "acceptance-",
                "rc3-",
                "rc4-",
                "rc5-",
                "rc6-",
                "security-review-",
                "security-history",
                "unreleased-",
            )
        )
        or name
        in {
            "agent_design.md",
            "implementation_map.md",
            "application-boundaries.md",
            "manual-release-runbook.md",
            "release.md",
            "development.md",
            "openspec-archive.md",
            "changelog-policy.md",
        }
    )


def on_config(config):
    identity = os.environ.get("DOCS_IDENTITY")
    if identity:
        config.extra["documentation"] = json.loads(identity)
    if os.environ.get("MIKE_DOCS_VERSION"):
        config.site_url = (
            "https://wa-pis.github.io/agent-paranoid-android/versions/"
            + os.environ["MIKE_DOCS_VERSION"]
            + "/"
        )
    config.plugins["mike"].config["version_selector"] = bool(
        os.environ.get("MIKE_DOCS_VERSION")
    )
    config.extra["stable_selector"] = (
        "../../versions/stable/"
        if os.environ.get("MIKE_DOCS_VERSION")
        else "versions/stable/"
    )
    if os.environ.get("DOCS_HOST_URL"):
        config.site_url = os.environ["DOCS_HOST_URL"]
        config.plugins["mike"].config["version_selector"] = False
        # Pages remains the accepted stable authority until parallel acceptance.
        config.extra["stable_selector"] = (
            "https://wa-pis.github.io/agent-paranoid-android/versions/stable/"
        )
        config.extra["host_preview"] = os.environ.get("DOCS_HOST_PREVIEW") == "1"
    return config


def on_nav(nav, config, files):
    from mkdocs_print_site_plugin.urls import get_page_key

    config.extra["navigation_pages"] = list(nav.pages)
    for page in nav.pages:
        russian = page.file.src_uri.startswith("ru/")
        for direction in ("previous_page", "next_page"):
            neighbor = getattr(page, direction)
            if neighbor and neighbor.file.src_uri.startswith("ru/") != russian:
                setattr(page, direction, None)
    config.extra["historical_urls"] = {
        file.url
        for file in files.documentation_pages()
        if is_history(file.src_uri) or file.src_uri.removeprefix("ru/") == "history.md"
    }
    config.extra["page_urls"] = {
        get_page_key(file.url): file.url for file in files.documentation_pages()
    }


def on_page_markdown(markdown, page, config, files):
    page.meta["historical"] = (
        is_history(page.file.src_uri)
        or page.file.src_uri.removeprefix("ru/") == "history.md"
    )
    if (
        os.environ.get("DOCS_HOST_URL")
        and page.file.src_uri.removeprefix("ru/") == "versions.md"
    ):
        if page.file.src_uri.startswith("ru/"):
            return "# Параллельная публикация\n\nЭта редакция собрана отдельно и ещё не заменяет принятую публикацию. Выбор управляемых редакций требует настройки проекта сервиса.\n\n[Принятая стабильная версия и сохранённые редакции](https://wa-pis.github.io/agent-paranoid-android/versions/stable/)\n"
        return "# Parallel publication\n\nThis parallel edition does not replace the accepted publication. Managed edition selection requires service project setup.\n\n[Accepted stable guide and retained editions](https://wa-pis.github.io/agent-paranoid-android/versions/stable/)\n"
    if (
        config.extra.get("host_preview")
        and page.file.src_uri.removeprefix("ru/") == "downloads.md"
    ):
        if page.file.src_uri.startswith("ru/"):
            return "# Скачивания в PR-превью\n\nЭто предпросмотр изменений. Скачиваемые форматы здесь не собираются.\n\n[Документация стабильной версии](https://wa-pis.github.io/agent-paranoid-android/versions/stable/ru/downloads/)\n"
        return "# PR preview downloads\n\nThis is a change preview. Downloads are not built here.\n\n[Verified stable downloads](https://wa-pis.github.io/agent-paranoid-android/versions/stable/downloads/)\n"
    return markdown


def portable_html(html: str, page_urls: dict[str, str], site_url: str) -> str:
    """Adapt print-site output to an attachment with explicit reference links."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select(
        ".wy-nav-side, .wy-nav-top, .rst-footer-buttons, footer, .rst-breadcrumbs, .wy-breadcrumbs"
    ):
        node.decompose()
    for section in soup.select("section.print-page.md-section"):
        if not section.select("section.print-page"):
            for link in soup.select('a[href="#' + section["id"] + '"]'):
                if link.find_parent("li"):
                    link.find_parent("li").decompose()
                else:
                    link.decompose()
            section.decompose()
    ids = {node.get("id") for node in soup.select("[id]")}
    for link in soup.select("a[href]"):
        href = link["href"]
        if href == "#":
            continue
        if href.startswith("#") and href[1:] not in ids:
            key = next(
                (
                    key
                    for key in sorted(page_urls, key=len, reverse=True)
                    if href[1:] == key or href[1:].startswith(key + "-")
                ),
                None,
            )
            if key is None:
                raise ValueError(
                    "print-site produced an unresolved handbook link: " + href
                )
            fragment = href[1 + len(key) :].removeprefix("-")
            link["href"] = urljoin(site_url, page_urls[key]) + (
                "#" + fragment if fragment else ""
            )
        elif not href.startswith("#"):
            link["href"] = urljoin(site_url + "handbook/", href)
    return str(soup)


def local_resource(path: str, site: Path) -> tuple[str | None, bytes]:
    """HTMLArk may embed build resources only, never network or other local files."""
    import mimetypes

    parsed = urlsplit(path)
    resource = Path(parsed.path).resolve()
    if parsed.scheme or parsed.netloc or not resource.is_relative_to(site.resolve()):
        raise RuntimeError("standalone export resource is outside the built site")
    return mimetypes.guess_type(str(resource))[0], resource.read_bytes()


@event_priority(-100)
def on_post_build(config):
    site = Path(config.site_dir)
    # MkDocs' built-in search has no per-page exclusion option. Keep history at
    # its original URLs, while current guides and detailed references remain searchable.
    index_path = site / "search/search_index.json"
    index = json.loads(index_path.read_text())
    index["docs"] = [
        item
        for item in index["docs"]
        if item["location"].split("#")[0] not in config.extra["historical_urls"]
    ]
    index_path.write_text(json.dumps(index))
    identity = config.extra.get("documentation")
    if not identity:
        return
    (site / "documentation.json").write_text(json.dumps(identity, indent=2) + "\n")
    if os.environ.get("DOCS_EXPORTS") != "1":
        return

    import htmlark

    downloads = site / "downloads"
    downloads.mkdir(exist_ok=True)
    original_reader = htmlark._get_resource
    try:
        htmlark._get_resource = lambda path: local_resource(path, site)
        attachment = site / "handbook/attachment.html"
        attachment.write_text(
            portable_html(
                (site / "handbook/index.html").read_text(),
                config.extra["page_urls"],
                config.site_url,
            )
        )
        standalone = htmlark.convert_page(str(attachment), parser="html.parser")
        attachment.unlink()
    finally:
        htmlark._get_resource = original_reader
    (downloads / "handbook.html").write_text(standalone)
    with tempfile.TemporaryDirectory(prefix="apa-docs-chrome-") as profile:
        subprocess.run(
            [
                os.environ["DOCS_BROWSER"],
                "--headless",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-background-networking",
                "--host-resolver-rules=MAP * ~NOTFOUND",
                "--no-pdf-header-footer",
                f"--user-data-dir={profile}",
                f"--print-to-pdf={downloads / 'handbook.pdf'}",
                (downloads / "handbook.html").as_uri(),
            ],
            check=True,
            timeout=120,
            capture_output=True,
        )
    if not (downloads / "handbook.pdf").is_file():
        raise RuntimeError("browser did not produce the documentation PDF")
    chapters = [
        page.file.src_uri
        for page in config.extra["navigation_pages"]
        if page.file.src_uri.removeprefix("ru/")
        not in {"history.md", "downloads.md", "versions.md", "roadmap.md"}
    ]
    with zipfile.ZipFile(
        downloads / "handbook.md.zip", "w", zipfile.ZIP_DEFLATED
    ) as archive:
        for source in sorted(Path(config.docs_dir).rglob("*.md")):
            archive.write(source, str(source.relative_to(config.docs_dir)))
        archive.writestr(
            "documentation.json",
            json.dumps({**identity, "chapters": chapters}, indent=2),
        )
    # Create before adding the ZIP itself and final manifest (no recursive archive).
    with tempfile.TemporaryDirectory(prefix="apa-docs-zip-") as temporary:
        archive = shutil.make_archive(str(Path(temporary) / "site"), "zip", site)
        shutil.copyfile(archive, downloads / "site.zip")
    names = ("handbook.pdf", "handbook.html", "handbook.md.zip", "site.zip")
    manifest = {
        **identity,
        "chapters": chapters,
        "index_sha256": hashlib.sha256((site / "index.html").read_bytes()).hexdigest(),
        "sha256": {
            name: hashlib.sha256((downloads / name).read_bytes()).hexdigest()
            for name in names
        },
    }
    (downloads / "documentation.json").write_text(json.dumps(manifest, indent=2) + "\n")
